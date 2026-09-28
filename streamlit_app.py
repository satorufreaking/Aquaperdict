from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from app import load_scenario
from engine.generate_case import generate_case
from engine.process_output import process_results
from engine.run_simulation import run_simulation

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("aqua.predict.ui")

ROOT = Path(__file__).resolve().parent
SCENARIO_DIR = ROOT / "scenarios"
RESULTS_DIR = ROOT / "results"


def list_scenarios() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*.json"))


def scenario_options() -> list[str]:
    return [path.stem for path in list_scenarios()]


def _ensure_scenario_path(scenario_name: str) -> Path:
    scenario_path = SCENARIO_DIR / f"{scenario_name}.json"
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")
    return scenario_path


def run_pipeline(scenario_name: str):
    scenario_path = _ensure_scenario_path(scenario_name)
    scenario = load_scenario(scenario_path)
    project_root = ROOT

    case_info = generate_case(scenario=scenario, project_root=project_root)
    run_dir = run_simulation(case_info=case_info, scenario=scenario, project_root=project_root)
    csv_path = process_results(run_dir=run_dir, project_root=project_root)
    return scenario, case_info, run_dir, csv_path


def summarize_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["metric_name", "count", "min", "max", "mean", "last"])

    summary = df.groupby("metric_name")["value"].agg(["count", "min", "max", "mean", "last"]).reset_index()
    summary.columns = ["metric_name", "count", "min", "max", "mean", "last"]
    return summary


def render_graph_from_csv(csv_path: Path):
    if not csv_path.exists():
        st.info("No processed CSV available to plot yet.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        st.info("Processed results are empty.")
        return

    if "time" not in df.columns or "value" not in df.columns:
        st.info("The processed CSV does not contain the expected time/value columns for plotting.")
        return

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for metric_name, group in df.groupby("metric_name"):
        ax.plot(group["time"].astype(float), group["value"].astype(float), label=metric_name)
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.set_title("Processed simulation response")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)


def main() -> None:
    st.set_page_config(page_title="AquaPredict", page_icon="🌊", layout="wide")
    st.title("AquaPredict")

    scenario_names = scenario_options()
    if not scenario_names:
        st.error("No scenario JSON files were found in the scenarios folder.")
        st.stop()

    with st.sidebar:
        st.subheader("Project inputs")
        dam_selection = st.selectbox("Dam selection", ["Standard Dam", "Concrete Dam", "Earthen Dam"])
        river_selection = st.selectbox("River selection", ["Main River", "Tributary River", "North Reach"])
        scenario_name = st.selectbox("Scenario selection", scenario_names)
        breach_condition = st.selectbox("Breach condition", ["Overtopping", "Progressive", "Instantaneous", "Custom"])

        scenario_path = _ensure_scenario_path(scenario_name)
        scenario_payload = load_scenario(scenario_path)
        sim_config = scenario_payload.get("simulation", {})
        if "initial_water_level" in sim_config or "initial_water_level" in scenario_payload:
            initial_water_level = st.number_input(
                "Initial water level (m)",
                min_value=0.0,
                value=float(sim_config.get("initial_water_level", scenario_payload.get("initial_water_level", 0.0))),
                step=0.1,
                format="%.2f",
            )
        else:
            st.caption("Initial water level is not supported for the selected case configuration.")
            initial_water_level = None

        run_button = st.button("RUN SIMULATION", type="primary")

    st.subheader("Simulation settings")
    st.write({
        "Dam": dam_selection,
        "River": river_selection,
        "Scenario": scenario_name,
        "Breach condition": breach_condition,
        "Initial water level": initial_water_level if initial_water_level is not None else "Not supported",
    })

    if run_button:
        try:
            with st.spinner("Generating case, launching simulation, and processing outputs..."):
                scenario, case_info, run_dir, csv_path = run_pipeline(scenario_name)

            st.success("Simulation completed successfully.")
            st.session_state["last_run_dir"] = str(run_dir)
            st.session_state["last_csv_path"] = str(csv_path)

            st.subheader("Simulation status")
            st.info(f"Run directory: {run_dir}")
            st.info(f"Generated case: {case_info['generated_case_xml']}")

            csv_file = Path(csv_path)
            if csv_file.exists():
                df = pd.read_csv(csv_file)
                st.subheader("Numerical metrics")
                metrics_summary = summarize_metrics(df)
                st.dataframe(metrics_summary, use_container_width=True)

                st.subheader("Simulation results")
                st.dataframe(df.head(200), use_container_width=True)

                st.subheader("Generated graphs")
                render_graph_from_csv(csv_file)

                with open(csv_file, "rb") as csv_handle:
                    st.download_button(
                        "Download CSV",
                        csv_handle.read(),
                        file_name="aqua_predict_results.csv",
                        mime="text/csv",
                    )
            else:
                st.warning("No processed CSV output was produced for this run.")

        except Exception as exc:
            st.error(f"Simulation failed: {exc}")
            logger.exception("Simulation run failed")
            with st.expander("Error details"):
                st.code(str(exc), language="text")

    else:
        st.caption("Select a scenario and click RUN SIMULATION to start the AquaPredict workflow.")


if __name__ == "__main__":
    main()

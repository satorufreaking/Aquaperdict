from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from engine.generate_case import generate_case
from engine.process_output import process_results
from engine.run_simulation import run_simulation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("aqua.predict")


def load_scenario(scenario_path: Path) -> dict:
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

    with scenario_path.open("r", encoding="utf-8") as handle:
        scenario = json.load(handle)

    if not isinstance(scenario, dict):
        raise ValueError(f"Scenario file must contain a JSON object: {scenario_path}")

    scenario.setdefault("name", scenario_path.stem)
    return scenario


def main() -> int:
    parser = argparse.ArgumentParser(description="AquaPredict command-line workflow")
    parser.add_argument("--scenario", type=Path, required=True, help="Path to scenario JSON")
    parser.add_argument(
        "--phase",
        choices=["generate", "run", "process", "all"],
        default="all",
        help="Workflow stage to run",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Project root. Defaults to this AquaPredict directory",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    scenario = load_scenario(args.scenario)
    logger.info("Loaded scenario: %s", scenario.get("name"))

    case_info = None
    run_dir = None

    if args.phase in {"generate", "all"}:
        case_info = generate_case(scenario=scenario, project_root=project_root)
        logger.info("Generated case in %s", case_info["case_dir"])

    if args.phase in {"run", "all"}:
        if case_info is None:
            case_info = generate_case(scenario=scenario, project_root=project_root)
        run_dir = run_simulation(case_info=case_info, scenario=scenario, project_root=project_root)
        logger.info("Simulation results stored in %s", run_dir)

    if args.phase in {"process", "all"}:
        if run_dir is None:
            run_dir = project_root / "results" / scenario["name"]
            if not run_dir.exists():
                raise FileNotFoundError(
                    "No results directory found for processing. Run the simulation first or use --phase all."
                )
        output_csv = process_results(run_dir=run_dir, project_root=project_root)
        logger.info("Processed outputs exported to %s", output_csv)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

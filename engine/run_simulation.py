from __future__ import annotations

import json
import logging
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def locate_gen_case(project_root: Path) -> Path:
    candidates = [
        project_root.parent / "DualSPHysics-master" / "bin" / "windows" / "GenCase_win64.exe",
        project_root.parent / "DualSPHysics-master" / "bin" / "windows" / "GenCase.exe",
        project_root.parent / "DualSPHysics-master" / "bin" / "windows" / "GenCase_linux64",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "DualSPHysics GenCase executable not found. Expected a bin/windows GenCase_win64.exe in the project parent directory."
    )


def locate_simulator(project_root: Path, prefer: str = "gpu") -> Path:
    search_root = project_root.parent / "DualSPHysics-master" / "bin"
    patterns = [
        "DualSPHysics5.4_win64.exe",
        "DualSPHysics5.4CPU_win64.exe",
        "DualSPHysics5.4_gpu.exe",
        "DualSPHysics5.4CPU.exe",
        "DualSPHysics*.exe",
    ]

    if prefer.lower() == "cpu":
        patterns = [
            "DualSPHysics5.4CPU_win64.exe",
            "DualSPHysics5.4CPU.exe",
            "DualSPHysics*.exe",
        ]

    for pattern in patterns:
        matches = list(search_root.rglob(pattern))
        if matches:
            return matches[0]

    raise FileNotFoundError(
        f"No DualSPHysics simulator executable found under {search_root}. "
        "Please install the Windows release containing the solver binary."
    )


def _make_run_dir(project_root: Path, scenario_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = project_root / "results" / f"{scenario_name}_{timestamp}_{uuid.uuid4().hex[:6]}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _capture_success(stdout: str, stderr: str, returncode: int) -> bool:
    combined = (stdout or "") + "\n" + (stderr or "")
    if returncode != 0:
        return False
    if "Execution aborted" in combined:
        return False
    if "Finished execution" in combined or "All done" in combined:
        return True
    return True


def run_simulation(case_info: dict, scenario: dict, project_root: Path) -> Path:
    case_dir = Path(case_info["case_dir"])
    case_xml = Path(case_info["generated_case_xml"])
    case_name = case_info["case_name"]
    scenario_name = scenario.get("name", case_name)

    gen_case = locate_gen_case(project_root)
    run_dir = _make_run_dir(project_root, scenario_name)
    output_dir = run_dir / "simulation"
    output_dir.mkdir(parents=True, exist_ok=True)

    case_basename = case_xml.stem
    output_basename = case_name
    gen_cmd = [str(gen_case), case_basename, str(output_dir / output_basename), "-save:all"]
    logger.info("Running GenCase: %s", " ".join(gen_cmd))
    gen_process = subprocess.run(gen_cmd, cwd=str(case_dir), capture_output=True, text=True)
    logger.info("GenCase return code: %s", gen_process.returncode)
    if gen_process.stdout:
        logger.info("GenCase stdout:\n%s", gen_process.stdout[-2000:])
    if gen_process.stderr:
        logger.warning("GenCase stderr:\n%s", gen_process.stderr[-2000:])

    if gen_process.returncode != 0:
        raise RuntimeError(f"GenCase failed for scenario '{scenario_name}'. See logs in {run_dir}")

    preferred_engine = str(scenario.get("execution", {}).get("engine", "gpu")).lower()
    simulator = locate_simulator(project_root, prefer=preferred_engine)
    solver_cmd = [str(simulator), "-gpu", str(output_dir / case_name), str(run_dir)]
    if preferred_engine == "cpu":
        solver_cmd = [str(simulator), str(output_dir / case_name), str(run_dir)]

    logger.info("Running DualSPHysics: %s", " ".join(solver_cmd))
    solver_process = subprocess.run(solver_cmd, cwd=str(case_dir), capture_output=True, text=True)
    if solver_process.stdout:
        logger.info("DualSPHysics stdout:\n%s", solver_process.stdout[-4000:])
    if solver_process.stderr:
        logger.warning("DualSPHysics stderr:\n%s", solver_process.stderr[-4000:])

    run_log = run_dir / "run.log"
    with run_log.open("w", encoding="utf-8") as handle:
        handle.write((solver_process.stdout or "") + "\n" + (solver_process.stderr or ""))

    success = _capture_success(solver_process.stdout, solver_process.stderr, solver_process.returncode)
    if not success:
        raise RuntimeError(
            f"DualSPHysics simulation failed for scenario '{scenario_name}'. "
            f"Check {run_log} for full command output."
        )

    logger.info("Simulation succeeded for scenario '%s' and wrote output to %s", scenario_name, run_dir)
    return run_dir

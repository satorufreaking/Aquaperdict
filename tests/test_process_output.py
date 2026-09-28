import csv
from pathlib import Path

from engine.process_output import process_results


def test_process_results_handles_semicolon_csv(tmp_path):
    run_dir = tmp_path / "run_case"
    run_dir.mkdir()

    csv_path = run_dir / "RunPARTs.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=';')
        writer.writerow([
            "Part","TimeStep [s]","Steps","DTsMin","PartRuntime [s]","NpSave"
        ])
        writer.writerow(["0", "0.0", "0", "0", "0.000000", "171496"])
        writer.writerow(["1", "0.010086", "117", "0", "0.805791", "171496"])

    project_root = tmp_path
    out_csv = process_results(run_dir, project_root)
    rows = out_csv.read_text(encoding="utf-8").strip().splitlines()

    assert len(rows) == 3, rows
    assert "TimeStep [s]" in rows[1], rows
    assert "0.010086" in rows[2], rows

from __future__ import annotations

import csv
import io
import logging
import math
from pathlib import Path

logger = logging.getLogger(__name__)


def _detect_delimiter(text: str):
    if text.count(";") > text.count(","):
        return ";"
    return ","


def _find_time_col(fieldnames):
    normalized = [str(name).strip().lower().replace(" ", "").replace("-", "") for name in fieldnames]
    for idx, item in enumerate(normalized):
        if "time" in item or item == "t":
            return fieldnames[idx]
    return None


def _find_metric_col(fieldnames):
    preferred = ["eta", "elevation", "height", "vel", "velocity", "press", "pressure", "energy", "total", "value"]
    for name in fieldnames:
        lower = str(name).strip().lower().replace(" ", "").replace("-", "")
        for token in preferred:
            if token in lower:
                return name
    return fieldnames[-1] if fieldnames else None


def _safe_float(value):
    if value is None:
        return math.nan
    try:
        value = str(value).strip().replace(";", "")
        if value.startswith("#"):
            return math.nan
        if value.count(",") and value.count("."):
            value = value.replace(",", "")
        elif value.count(","):
            value = value.replace(",", "")
        return float(value)
    except ValueError:
        return math.nan


def _extract_rows(csv_path: Path):
    text = csv_path.read_text(encoding="utf-8", errors="ignore")
    lines = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        lines.append(raw_line)

    if not lines:
        return [], []

    delimiter = _detect_delimiter(lines[0])
    reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    fieldnames = reader.fieldnames or []
    rows = list(reader)
    return fieldnames, rows


def process_results(run_dir: Path, project_root: Path) -> Path:
    run_dir = Path(run_dir).resolve()
    output_csv = project_root / "results" / "comparison" / "processed_results.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    records = []
    csv_files = sorted(run_dir.rglob("*.csv"))

    if not csv_files:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        output_csv.write_text("scenario,source_file,time,value\n", encoding="utf-8")
        logger.warning("No CSV outputs found in %s; wrote empty results table.", run_dir)
        return output_csv

    for csv_file in csv_files:
        fieldnames, rows = _extract_rows(csv_file)
        if not fieldnames or not rows:
            continue

        time_col = _find_time_col(fieldnames)
        metric_col = _find_metric_col(fieldnames)
        if metric_col is None or time_col is None:
            continue

        for row in rows:
            time_val = _safe_float(row.get(time_col)) if time_col else math.nan
            metric_val = _safe_float(row.get(metric_col))
            if math.isnan(time_val) or math.isnan(metric_val):
                continue
            records.append({
                "scenario": run_dir.name,
                "source_file": csv_file.name,
                "time": time_val,
                "metric_name": metric_col,
                "value": metric_val,
            })

    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scenario", "source_file", "time", "metric_name", "value"])
        writer.writeheader()
        for record in records:
            writer.writerow(record)

    logger.info("Processed %d numeric rows from %d CSV files into %s", len(records), len(csv_files), output_csv)
    return output_csv

from __future__ import annotations

import json
import logging
import shutil
import uuid
from pathlib import Path
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def _default_case_root(project_root: Path) -> Path:
    workspace_root = project_root.parent
    candidates = [
        workspace_root / "DualSPHysics-master" / "examples" / "main",
        workspace_root / "DualSPHysics-master" / "examples",
        workspace_root / "DualSPHysics-master",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Could not locate the DualSPHysics example directory. "
        "Expected a DualSPHysics-master folder next to AquaPredict."
    )


def discover_case_templates(case_root: Path) -> list[Path]:
    templates = sorted(case_root.rglob("*_Def.xml"))
    logger.info("Discovered %d candidate DualSPHysics XML templates", len(templates))
    return templates


def validate_case_template(xml_path: Path) -> None:
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Could not parse XML case template: {xml_path}") from exc

    if root.tag != "case":
        raise ValueError(f"Case template is not a DualSPHysics case definition: {xml_path}")

    logger.info("Validated XML template: %s", xml_path)


def select_case_template(case_root: Path, scenario: dict) -> Path:
    requested = scenario.get("case_template")
    if requested:
        candidates = [case_root / requested]
        if candidates[0].exists():
            return candidates[0]

        matches = list(case_root.rglob(requested))
        if matches:
            return matches[0]
        raise FileNotFoundError(f"Requested case template not found: {requested}")

    files = discover_case_templates(case_root)
    if not files:
        raise FileNotFoundError(f"No *_Def.xml case templates found under: {case_root}")

    preferred = scenario.get("preferred_case")
    if preferred:
        for item in files:
            if preferred in item.name:
                return item

    logger.info("Using default case template: %s", files[0])
    return files[0]


def generate_case(scenario: dict, project_root: Path) -> dict:
    project_root = project_root.resolve()
    case_root = _default_case_root(project_root)
    template = select_case_template(case_root, scenario)
    validate_case_template(template)

    template_stem = template.stem
    case_name = template_stem.replace("_Def", "") if template_stem.endswith("_Def") else template_stem
    run_label = scenario.get("name", case_name).replace(" ", "_")
    case_dir = project_root / "data" / "generated" / f"{run_label}_{uuid.uuid4().hex[:8]}"
    case_dir.mkdir(parents=True, exist_ok=False)

    destination = case_dir / template.name
    shutil.copy2(template, destination)

    manifest = {
        "scenario": scenario,
        "case_name": case_name,
        "template": str(template),
        "case_dir": str(case_dir),
        "generated_case_xml": str(destination),
    }
    manifest_path = case_dir / "case_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    logger.info("Case generated at %s", case_dir)
    return manifest

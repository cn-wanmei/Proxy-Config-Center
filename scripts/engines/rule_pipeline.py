#!/usr/bin/env python3
"""Unified fail-closed rule pipeline for 3.2."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from engines.rule_intelligence import collect_atoms, detect_pollution, detect_source_count_anomaly
from engines.semantic import analyze

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class PipelineResult:
    ok: bool
    atoms: List[dict]
    kept: List[dict]
    errors: List[str]
    warnings: List[str]
    semantic: Dict[str, Any]
    pollution: List[dict]
    anomalies: List[dict]


def run_pipeline() -> PipelineResult:
    """Run all core rule checks without client/platform semantics."""
    atoms = collect_atoms()
    atom_dicts = [a.to_dict() for a in atoms]
    semantic = analyze(atom_dicts)
    pollution = detect_pollution(atoms)
    anomalies = detect_source_count_anomaly(atoms)

    errors: List[str] = []
    warnings: List[str] = []

    for finding in semantic["findings"]:
        kind = finding["kind"]
        if kind == "conflict":
            errors.append(
                f"E003 conflict: {finding['type']}={finding['value']} policies={','.join(finding['policies'])}"
            )
        elif kind == "shadow":
            errors.append(
                f"E005 shadow: {finding['parent_value']} shadows {finding['child_value']}"
            )
        elif kind == "overlap":
            warnings.append(
                f"W003 overlap: {finding['parent_value']} ↔ {finding['child_value']}"
            )
        elif kind == "duplicate":
            warnings.append(
                f"W001 duplicate: {finding['type']}={finding['value']} policy={finding['policies'][0]}"
            )

    for item in semantic["validation"]:
        errors.append(f"E001 {item['kind']}: {item['rule_id']}")

    for item in pollution:
        if item["kind"] in {"test_domain_pollution", "empty_value", "tld_pollution"}:
            errors.append(f"E006 {item['kind']}: {item['rule'].get('rule_id')}")

    for item in anomalies:
        errors.append(f"E007 {item['kind']}: {item['policy']} count={item['count']}")

    return PipelineResult(
        ok=not errors,
        atoms=atom_dicts,
        kept=atom_dicts,
        errors=errors,
        warnings=warnings,
        semantic=semantic,
        pollution=pollution,
        anomalies=anomalies,
    )


def write_pipeline_artifacts(result: PipelineResult, out: Path, version: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "compiler_version": version,
        "ok": result.ok,
        "summary": {
            "atoms": len(result.atoms),
            "kept": len(result.kept),
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            **result.semantic["summary"],
        },
        "errors": result.errors,
        "warnings": result.warnings,
        "semantic": result.semantic,
        "pollution": result.pollution,
        "source_anomalies": result.anomalies,
    }
    (out / "rule-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "version": version,
        "rule_count": len(result.kept),
        "rules": [
            {
                "rule_id": r["rule_id"],
                "global_rule_id": r["global_rule_id"],
                "sha256": r["sha256"],
                "policy_id": r["policy_id"],
                "type": r["type"],
                "value": r["value"],
                "source_file": r.get("source_file", ""),
                "provenance": r.get("provenance", ""),
            }
            for r in result.kept
        ],
    }
    (out / "rule-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

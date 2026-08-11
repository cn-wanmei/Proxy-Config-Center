#!/usr/bin/env python3
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


def _finding_label(finding: dict) -> str:
    if finding['kind'] in {'duplicate', 'conflict', 'overlap', 'shared'} and 'value' in finding:
        return f"{finding['type']}={finding['value']}"
    if 'parent_value' in finding and 'child_value' in finding:
        return f"{finding['parent_value']} ↔ {finding['child_value']}"
    return finding.get('rule_id') or finding.get('value') or 'unknown'


def run_pipeline() -> PipelineResult:
    atom_objects = collect_atoms()
    atoms = [atom.to_dict() for atom in atom_objects]
    semantic = analyze(atoms)
    pollution = detect_pollution(atom_objects)
    anomalies = detect_source_count_anomaly(atom_objects)
    errors: List[str] = []
    warnings: List[str] = []

    for finding in semantic['findings']:
        kind = finding['kind']
        label = _finding_label(finding)
        if kind == 'conflict':
            policies = ','.join(finding.get('policies', []))
            errors.append(f"E003 conflict: {label} policies={policies}")
        elif kind == 'shadow':
            errors.append(f"E005 shadow: {label}")
        elif kind == 'overlap':
            warnings.append(f"W003 overlap: {label}")
        elif kind == 'duplicate':
            warnings.append(f"W001 duplicate: {label}")
        elif kind == 'shared':
            warnings.append(f"W002 shared rule across policies: {label}")

    errors += [f"E001 {item['kind']}: {item['rule_id']}" for item in semantic['validation']]
    errors += [
        f"E006 {item['kind']}: {item['rule'].get('rule_id')}"
        for item in pollution
        if item['kind'] in {'test_domain_pollution', 'empty_value', 'tld_pollution'}
    ]
    errors += [f"E007 {item['kind']}: {item['policy']} count={item['count']}" for item in anomalies]

    return PipelineResult(
        not errors,
        atoms,
        atoms,
        errors,
        warnings,
        semantic,
        pollution,
        anomalies,
    )


def write_pipeline_artifacts(result: PipelineResult, out: Path, version: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    report = {
        'schema_version': 4,
        'compiler_version': version,
        'ok': result.ok,
        'summary': {
            'atoms': len(result.atoms),
            'kept': len(result.kept),
            'errors': len(result.errors),
            'warnings': len(result.warnings),
            **result.semantic['summary'],
        },
        'errors': result.errors,
        'warnings': result.warnings,
        'semantic': result.semantic,
        'pollution': result.pollution,
        'source_anomalies': result.anomalies,
    }
    (out / 'rule-audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )

    manifest = {
        'schema_version': 4,
        'version': version,
        'rule_count': len(result.kept),
        'rules': [
            {
                'rule_id': rule['rule_id'],
                'global_rule_id': rule['global_rule_id'],
                'sha256': rule['sha256'],
                'policy_id': rule['policy_id'],
                'type': rule['type'],
                'value': rule['value'],
                'source_file': rule.get('source_file', ''),
                'provenance': rule.get('provenance', ''),
            }
            for rule in result.kept
        ],
    }
    (out / 'rule-manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )

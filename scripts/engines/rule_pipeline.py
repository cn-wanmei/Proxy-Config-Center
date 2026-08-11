#!/usr/bin/env python3
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from engines.rule_intelligence import collect_atoms, detect_pollution, detect_source_count_anomaly
from engines.semantic import analyze
ROOT=Path(__file__).resolve().parents[2]
@dataclass
class PipelineResult:
    ok:bool; atoms:List[dict]; kept:List[dict]; errors:List[str]; warnings:List[str]; semantic:Dict[str,Any]; pollution:List[dict]; anomalies:List[dict]
def run_pipeline():
    atom_objects=collect_atoms(); atoms=[a.to_dict() for a in atom_objects]; semantic=analyze(atoms); pollution=detect_pollution(atom_objects); anomalies=detect_source_count_anomaly(atom_objects); errors=[]; warnings=[]
    for f in semantic["findings"]:
        if f["kind"]=="conflict": errors.append(f"E003 conflict: {f['type']}={f['value']} policies={','.join(f['policies'])}")
        elif f["kind"]=="shadow": errors.append(f"E005 shadow: {f['parent_value']} shadows {f['child_value']}")
        elif f["kind"]=="overlap": warnings.append(f"W003 overlap: {f['parent_value']} ↔ {f['child_value']}")
        elif f["kind"]=="duplicate": warnings.append(f"W001 duplicate: {f['type']}={f['value']}")
    errors += [f"E001 {x['kind']}: {x['rule_id']}" for x in semantic["validation"]]
    errors += [f"E006 {x['kind']}: {x['rule'].get('rule_id')}" for x in pollution if x["kind"] in {"test_domain_pollution","empty_value","tld_pollution"}]
    errors += [f"E007 {x['kind']}: {x['policy']} count={x['count']}" for x in anomalies]
    return PipelineResult(not errors,atoms,atoms,errors,warnings,semantic,pollution,anomalies)
def write_pipeline_artifacts(result,out:Path,version:str):
    out.mkdir(parents=True,exist_ok=True)
    report={"schema_version":1,"compiler_version":version,"ok":result.ok,"summary":{"atoms":len(result.atoms),"kept":len(result.kept),"errors":len(result.errors),"warnings":len(result.warnings),**result.semantic["summary"]},"errors":result.errors,"warnings":result.warnings,"semantic":result.semantic,"pollution":result.pollution,"source_anomalies":result.anomalies}
    (out/"rule-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    manifest={"schema_version":1,"version":version,"rule_count":len(result.kept),"rules":[{"rule_id":r["rule_id"],"global_rule_id":r["global_rule_id"],"sha256":r["sha256"],"policy_id":r["policy_id"],"type":r["type"],"value":r["value"],"source_file":r.get("source_file",""),"provenance":r.get("provenance","")} for r in result.kept]}
    (out/"rule-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

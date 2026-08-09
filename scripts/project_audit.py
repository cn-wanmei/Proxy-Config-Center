#!/usr/bin/env python3
"""Project audit and reporting primitives for v1.4-v1.6.

Generates machine-readable Rule Index/Graph, conflict and unreachable reports,
AI coverage, build report, source snapshot and a minimal CycloneDX SBOM.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = ROOT / "core/providers/ai/registry.yaml"
OUT = ROOT / "build/reports"


def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024), b""): h.update(c)
    return h.hexdigest()


def iter_rule_files():
    for base in (ROOT/"core/rules", ROOT/"core/rulesets"):
        if base.exists():
            yield from base.rglob("*.yaml")
            yield from base.rglob("*.yml")
            yield from base.rglob("*.list")


def flatten_domains(obj: Any, prefix=""):
    if isinstance(obj, dict):
        for k,v in obj.items(): yield from flatten_domains(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for v in obj: yield from flatten_domains(v, prefix)
    elif isinstance(obj, str) and ("." in obj or obj.startswith("DOMAIN")):
        yield obj


def rule_index():
    rows=[]
    for p in iter_rule_files():
        try: data=yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception: data=p.read_text(encoding="utf-8", errors="replace").splitlines()
        vals=sorted(set(flatten_domains(data)))
        for v in vals: rows.append({"rule":str(p.relative_to(ROOT)),"match":v})
    return rows


def analyze(index):
    by_match={}
    for row in index: by_match.setdefault(row["match"], []).append(row["rule"])
    conflicts=[{"match":k,"rules":v} for k,v in by_match.items() if len(v)>1]
    unreachable=[]
    seen=set()
    for row in index:
        m=row["match"]
        if m in seen: unreachable.append(row)
        seen.add(m)
    graph={"nodes":[],"edges":[]}
    for row in index:
        r=row["rule"]; m=row["match"]
        graph["nodes"] += [{"id":r,"type":"rule"},{"id":m,"type":"match"}]
        graph["edges"].append({"from":r,"to":m})
    graph["nodes"] = list({n["id"]:n for n in graph["nodes"]}.values())
    return conflicts, unreachable, graph


def ai_report():
    data=yaml.safe_load(PROVIDER.read_text(encoding="utf-8")) if PROVIDER.exists() else {"providers":[]}
    providers=data.get("providers",[])
    return {"schema_version":data.get("schema_version"),"provider_count":len(providers),"providers":providers,
            "coverage": {d:p["id"] for p in providers for d in p.get("domains",[])}}


def build_report():
    build=ROOT/"build"
    files=[]
    if build.exists():
        for p in build.rglob("*"):
            if p.is_file(): files.append({"path":str(p.relative_to(ROOT)),"size":p.stat().st_size,"sha256":sha256(p)})
    version=(ROOT/"VERSION").read_text().strip() if (ROOT/"VERSION").exists() else "unknown"
    try: commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    except Exception: commit=os.environ.get("GITHUB_SHA","unknown")
    return {"version":version,"source_commit":commit,"file_count":len(files),"files":files}


def source_snapshot():
    rows=[]
    for p in sorted(iter_rule_files()):
        rows.append({"path":str(p.relative_to(ROOT)),"sha256":sha256(p),"size":p.stat().st_size})
    return {"snapshot_version":"1.0","source_count":len(rows),"sources":rows}


def sbom():
    comps=[]
    req=ROOT/"requirements.lock"
    if req.exists():
        for line in req.read_text().splitlines():
            if "==" in line:
                name,ver=line.split("==",1); comps.append({"type":"library","name":name,"version":ver})
    return {"bomFormat":"CycloneDX","specVersion":"1.5","version":1,"components":comps}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--explain"); ap.add_argument("--out",default=str(OUT)); args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    idx=rule_index(); conflicts,unreachable,graph=analyze(idx)
    if args.explain:
        print(json.dumps([r for r in idx if r["match"]==args.explain],ensure_ascii=False,indent=2)); return
    reports={
      "rule-index.json":idx,
      "rule-graph.json":graph,
      "rule-conflicts.json":{"count":len(conflicts),"items":conflicts},
      "rule-unreachable.json":{"count":len(unreachable),"items":unreachable},
      "ai-coverage.json":ai_report(),
      "build-report.json":build_report(),
      "rule-source-snapshot.json":source_snapshot(),
      "sbom.json":sbom(),
      "schema-version.json":{"schema_version":"1.0","remote_config":"1.0","release_manifest":"1.0"},
    }
    for name,data in reports.items(): (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Generated {len(reports)} audit reports in {out}")
    if conflicts: print(f"WARNING: {len(conflicts)} duplicate/conflicting matches")
    print(f"Rule index: {len(idx)}; unreachable: {len(unreachable)}; AI providers: {ai_report()['provider_count']}")

if __name__=="__main__": main()

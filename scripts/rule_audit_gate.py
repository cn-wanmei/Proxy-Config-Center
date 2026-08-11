#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; sys.path.insert(0,str(ROOT/"scripts"))
def main():
    p=argparse.ArgumentParser(); p.add_argument("--out",default="dist"); p.add_argument("--write",action="store_true"); a=p.parse_args(); out=Path(a.out); out=out if out.is_absolute() else ROOT/out
    from engines.rule_pipeline import run_pipeline,write_pipeline_artifacts
    r=run_pipeline(); version=(ROOT/"VERSION").read_text(encoding="utf-8").strip()
    if a.write: write_pipeline_artifacts(r,out,version)
    print(json.dumps({"ok":r.ok,"errors":len(r.errors),"warnings":len(r.warnings),"rules":len(r.atoms),"semantic":r.semantic["summary"]},ensure_ascii=False,sort_keys=True))
    if not r.ok:
        print("❌ audit pipeline FAILED (fail-closed)"); [print("  "+e) for e in r.errors[:40]]; return 1
    print("✅ audit pipeline OK"); return 0
if __name__=="__main__": sys.exit(main())

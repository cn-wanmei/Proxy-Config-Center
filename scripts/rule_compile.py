#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent.parent
def compile_rules(out:Path):
    from engines.rule_pipeline import run_pipeline
    result=run_pipeline()
    if not result.ok: raise RuntimeError("audit gate failed; refusing to compile")
    policies={}
    for r in result.kept: policies.setdefault(r["policy_id"],[]).append(r)
    rules_dir=out/"rules"; rules_dir.mkdir(parents=True,exist_ok=True); emitted=[]
    for pid in sorted(policies):
        items=sorted({r["rule_id"]:r for r in policies[pid]}.values(),key=lambda r:(int(r.get("priority",500)),r["type"],r["value"],r["rule_id"]))
        payload={"schema_version":1,"policy_id":pid,"rules":[{"rule_id":r["rule_id"],"global_rule_id":r["global_rule_id"],"sha256":r["sha256"],"type":r["type"],"value":r["value"],"priority":r["priority"],"source_file":r.get("source_file",""),"provenance":r.get("provenance","")} for r in items]}
        path=rules_dir/f"{pid}.yaml"; path.write_text(yaml.safe_dump(payload,allow_unicode=True,sort_keys=False),encoding="utf-8"); emitted.append({"policy_id":pid,"path":str(path.relative_to(ROOT)),"rule_count":len(items)})
    version=(ROOT/"VERSION").read_text(encoding="utf-8").strip(); manifest={"schema_version":1,"compiler":"rule-compiler-3.2","version":version,"deterministic":True,"policy_count":len(emitted),"rule_count":len(result.kept),"policies":emitted}; (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return manifest
def main():
    p=argparse.ArgumentParser(); p.add_argument("--out",default="dist"); a=p.parse_args(); out=Path(a.out); out=out if out.is_absolute() else ROOT/out
    try: m=compile_rules(out)
    except Exception as e: print(f"❌ rule compile FAILED: {e}"); return 1
    print(json.dumps(m,ensure_ascii=False,sort_keys=True)); print("✅ rule compile OK"); return 0
if __name__=="__main__": raise SystemExit(main())

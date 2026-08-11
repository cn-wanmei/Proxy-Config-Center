#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import List
ROOT=Path(__file__).resolve().parents[2]; CORE=ROOT/"core"
def audit_core_boundary()->List[str]:
    errors=[]
    if not CORE.exists(): return ["core/ missing"]
    for entry in CORE.iterdir():
        if entry.name!="rules": errors.append(f"{entry.relative_to(ROOT)}: non-rule core domain is forbidden")
    rules=CORE/"rules"
    if not rules.exists(): return errors+["core/rules/ missing"]
    forbidden=("mixed-port","external-controller","proxy-groups:","proxies:","tun:","fake-ip","rule-providers:")
    for p in rules.rglob("*"):
        if p.is_file() and p.suffix in {".yaml",".yml",".json",".md"}:
            text=p.read_text(encoding="utf-8",errors="replace").lower()
            for token in forbidden:
                if token in text: errors.append(f"{p.relative_to(ROOT)}: forbidden client/runtime key '{token}'")
    return errors
def assert_core_boundary():
    errors=audit_core_boundary()
    if errors: raise SystemExit("CORE BOUNDARY VIOLATION:\n  "+"\n  ".join(errors))
if __name__=="__main__": assert_core_boundary(); print("OK core boundary")

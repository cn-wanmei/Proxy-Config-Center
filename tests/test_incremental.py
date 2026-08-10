#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from engines.incremental import fingerprint_core, platforms_to_rebuild, commit_cache

def test_fp_and_plan():
    a = fingerprint_core(); assert a == fingerprint_core() and len(a) == 64
    plan = platforms_to_rebuild(["clash-meta"], force=True)
    assert "clash-meta" in plan["rebuild"]
    commit_cache(plan["core_fp"], plan["platform_fps"], set(plan["rebuild"]))

if __name__ == "__main__":
    test_fp_and_plan(); print("OK incremental")

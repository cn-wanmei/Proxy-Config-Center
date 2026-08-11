#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from canonical_ir import build_canonical_ir, is_canonical
from platform_ir import build_platform_ir

def test_separation():
    cir = build_canonical_ir()
    assert is_canonical(cir)
    pir = build_platform_ir(cir, "clash-meta")
    assert pir.platform == "clash-meta" and hasattr(pir, "routing_mode")
    assert not is_canonical(pir)

if __name__ == "__main__":
    test_separation(); print("OK canonical/platform IR separation")

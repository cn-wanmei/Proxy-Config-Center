#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rule_compile import compile_rules


def test_compile():
    with TemporaryDirectory() as tmp:
        manifest = compile_rules(Path(tmp))
        assert manifest["deterministic"] is True
        assert manifest["rule_count"] > 0
        assert manifest["policy_count"] > 0
        assert (Path(tmp) / "manifest.json").exists()
        assert list((Path(tmp) / "rules").glob("*.yaml"))


if __name__ == "__main__":
    test_compile()
    print("OK rule compile 3.2")

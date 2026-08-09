#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from explain_rule import explain
from rule_graph import build_graph


def main() -> int:
    graph = build_graph()
    assert graph["nodes"]["rules"], "rule graph is empty"
    assert graph["nodes"]["strategies"], "strategy graph is empty"
    result = explain("openai.com")
    assert result["matched"], "OpenAI representative must resolve"
    assert result["selected"]["strategy_group"] == "ai"
    print("✅ rule intelligence regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build machine-readable Rule -> Strategy, conflict, and reachability graphs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rule_audit import audit, load, suffix_covers

ROOT = Path(__file__).resolve().parent.parent


def build_graph() -> dict:
    index, duplicates, conflicts, unreachable, invalid_targets = audit()
    graph = {
        "version": 1,
        "nodes": {"rules": index["rules"], "strategies": index["services"]},
        "edges": [],
        "conflicts": conflicts,
        "unreachable": unreachable,
        "duplicates": duplicates,
        "invalid_targets": invalid_targets,
    }
    for n, rule in enumerate(index["rules"]):
        rid = f"{rule['source']}#{rule['rule_index']}:{rule['type']}:{rule['value']}"
        graph["edges"].append({"from": rid, "to": rule["group"], "kind": "routes-to", "priority": rule["priority"]})
    return graph


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out", default="build/audit/rule-graph.json")
    args = parser.parse_args()
    graph = build_graph()
    print(json.dumps({
        "rules": len(graph["nodes"]["rules"]),
        "strategies": len(graph["nodes"]["strategies"]),
        "conflicts": len(graph["conflicts"]),
        "duplicates": len(graph["duplicates"]),
        "unreachable": len(graph["unreachable"]),
        "invalid_targets": len(graph["invalid_targets"]),
    }, ensure_ascii=False, sort_keys=True))
    if args.write:
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    blocking = bool(graph["conflicts"] or graph["unreachable"] or graph["invalid_targets"])
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())

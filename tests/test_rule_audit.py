#!/usr/bin/env python3
"""Regression tests for Rule -> Strategy Group coverage auditing."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rule_audit import audit  # noqa: E402


def main() -> int:
    index, duplicates, conflicts, unreachable, invalid_targets = audit()
    summary = index["summary"]
    assert summary["service_groups"] > 0
    assert summary["rules"] > 0
    assert not invalid_targets, invalid_targets
    assert not unreachable, unreachable
    semantic_conflicts = [
        c for c in conflicts
        if c["kind"] == "duplicate" and c["rule"]["group"] != c["previous"]["group"]
    ]
    assert not semantic_conflicts, semantic_conflicts
    print(
        "Rule audit OK: "
        f"{summary['service_groups']} groups, {summary['rules']} rules, "
        f"{len(duplicates)} duplicate(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

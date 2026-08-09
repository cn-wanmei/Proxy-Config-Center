#!/usr/bin/env python3
"""Explain the first matching routing rule for a domain."""

import argparse
import json
from pathlib import Path

from rule_audit import audit, load, suffix_covers

ROOT = Path(__file__).resolve().parent.parent


def matches(rule: dict, domain: str) -> bool:
    value = rule["value"].lower().lstrip(".")
    candidate = domain.lower().rstrip(".")
    if rule["type"] == "domain-suffix":
        return suffix_covers(value, candidate)
    if rule["type"] == "domain":
        return candidate == value
    if rule["type"] == "domain-keyword":
        return value in candidate
    return False


def trace(domain: str) -> dict:
    index, *_ = audit()
    candidates = [r for r in index["rules"] if matches(r, domain)]
    candidates.sort(key=lambda r: (r["priority"], r["source"], r["rule_index"]))
    if not candidates:
        return {"domain": domain, "matched": False, "fallback": "final"}
    first = candidates[0]
    return {
        "domain": domain,
        "matched": True,
        "strategy_group": first["group"],
        "priority": first["priority"],
        "type": first["type"],
        "pattern": first["value"],
        "source": first["source"],
        "rule_index": first["rule_index"],
        "shadowed_candidates": candidates[1:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    args = parser.parse_args()
    print(json.dumps(trace(args.domain), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

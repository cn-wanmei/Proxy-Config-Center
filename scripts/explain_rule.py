#!/usr/bin/env python3
"""Explain which Core rule and strategy group matches a domain."""
from __future__ import annotations

import argparse
import json
import ipaddress
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def matches(rule_type: str, value: str, query: str) -> bool:
    q = query.lower().rstrip(".")
    v = value.lower().rstrip(".")
    if rule_type in {"domain", "DOMAIN"}:
        return q == v
    if rule_type in {"domain-suffix", "DOMAIN-SUFFIX"}:
        return q == v or q.endswith("." + v)
    if rule_type in {"domain-keyword", "DOMAIN-KEYWORD"}:
        return v in q
    if rule_type in {"ip-cidr", "IP-CIDR", "ipcidr"}:
        try:
            return ipaddress.ip_address(q) in ipaddress.ip_network(v, strict=False)
        except ValueError:
            return False
    return False


def explain(query: str) -> dict:
    priority_data = load(ROOT / "core/rules/priority.yaml").get("priority") or []
    priority = {x["id"]: int(x.get("value", 999)) for x in priority_data}
    services = load(ROOT / "core/proxy-groups/service.yaml").get("groups") or []
    names = {x["id"]: x.get("name", {}) for x in services}
    matches_found = []
    for path in sorted((ROOT / "core/rules/services").glob("*.yaml")):
        data = load(path)
        group = data.get("group") or str(data.get("id", "")).removeprefix("service-")
        for idx, rule in enumerate(data.get("rules") or []):
            for value in rule.get("values") or []:
                if matches(str(rule.get("type", "")), str(value), query):
                    matches_found.append({
                        "source": path.name,
                        "rule_index": idx,
                        "type": rule.get("type"),
                        "value": value,
                        "strategy_group": group,
                        "priority": priority.get(group, 500),
                        "name": names.get(group, {}),
                    })
    matches_found.sort(key=lambda x: (x["priority"], x["source"], x["rule_index"]))
    return {"query": query, "matched": bool(matches_found), "matches": matches_found, "selected": matches_found[0] if matches_found else None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = explain(args.domain)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["matched"] else 1
    print(f"Domain: {result['query']}")
    if not result["matched"]:
        print("Matched: no")
        return 1
    selected = result["selected"]
    print(f"Selected: {selected['strategy_group']} / {selected['name'].get('zh', '')}")
    print(f"Priority: {selected['priority']}")
    print(f"Rule: {selected['type']} {selected['value']}")
    print(f"Source: {selected['source']}[{selected['rule_index']}]")
    if len(result["matches"]) > 1:
        print(f"Other matches: {len(result['matches']) - 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

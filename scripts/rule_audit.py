#!/usr/bin/env python3
"""Rule coverage audit and Rule -> Strategy Group index generator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"
SPECIAL_GROUPS = {"direct", "reject", "proxy-mode"}

from engines.utils import (
    DEFAULT_PRIORITY,
    FALLBACK_PRIORITY,
    get_priority_map,
    load_yaml,
)


def load(path: Path) -> dict:
    """Backward-compatible wrapper; prefer load_yaml for new code."""
    return load_yaml(path)


def suffix_covers(a: str, b: str) -> bool:
    a = a.lower().lstrip(".")
    b = b.lower().lstrip(".")
    return b == a or b.endswith("." + a)


def audit() -> Tuple[dict, List[dict], List[dict], List[dict], List[dict]]:
    pri = load_yaml(CORE / "rules" / "priority.yaml").get("priority") or []
    priority = get_priority_map(pri)
    services = load_yaml(CORE / "proxy-groups" / "service.yaml").get("groups") or []
    service_ids = {x["id"] for x in services}
    rules: List[dict] = []

    for path in sorted((CORE / "rules" / "services").glob("*.yaml")):
        data = load_yaml(path)
        group = data.get("group") or str(data.get("id", "")).removeprefix("service-")
        for rule_index, rule in enumerate(data.get("rules") or []):
            rule_type = rule.get("type")
            for value in rule.get("values") or []:
                rules.append(
                    {
                        "source": path.name,
                        "rule_index": rule_index,
                        "group": group,
                        "priority": priority.get(group, DEFAULT_PRIORITY),
                        "type": rule_type,
                        "value": str(value),
                    }
                )

    rules.sort(key=lambda x: (x["priority"], x["source"], x["rule_index"], x["value"]))
    invalid_targets: List[dict] = []
    duplicates: List[dict] = []
    conflicts: List[dict] = []
    unreachable: List[dict] = []
    seen: Dict[Tuple[str, str], dict] = {}

    for rule in rules:
        key = (str(rule["type"]), rule["value"].lower())
        if key in seen:
            previous = seen[key]
            duplicates.append({"rule": rule, "previous": previous})
            if previous["group"] != rule["group"]:
                conflicts.append({"kind": "duplicate", "rule": rule, "previous": previous})
        else:
            seen[key] = rule
        if rule["group"] not in service_ids and rule["group"] not in SPECIAL_GROUPS:
            invalid_targets.append(rule)

    suffixes = [r for r in rules if r["type"] == "domain-suffix"]
    for rule in suffixes:
        for previous in suffixes:
            if previous is rule:
                continue
            if previous["priority"] < rule["priority"] and suffix_covers(previous["value"], rule["value"]):
                unreachable.append({"rule": rule, "covered_by": previous})
                conflicts.append({"kind": "suffix-overlap", "rule": rule, "higher_priority": previous})
                break

    index: Dict[str, Any] = {
        "version": 1,
        "services": [],
        "rules": rules,
        "summary": {},
    }
    for service in services:
        service_id = service["id"]
        service_rules = [r for r in rules if r["group"] == service_id]
        index["services"].append(
            {
                "id": service_id,
                "name": service.get("name", {}),
                "priority": priority.get(service_id, DEFAULT_PRIORITY),
                "rule_count": len(service_rules),
                "rules": service_rules,
            }
        )

    # Surface dual-source domain_suffix overlaps as informational notes
    source_suffixes: Dict[str, set] = {}
    try:
        src_data = load_yaml(CORE / "rules" / "sources.yaml")
        for sid, meta in (src_data.get("sources") or {}).items():
            source_suffixes[sid] = {s.lower() for s in (meta or {}).get("domain_suffix") or []}
    except Exception:
        source_suffixes = {}

    dual_source_notes: List[dict] = []
    for rule in rules:
        if rule["type"] != "domain-suffix":
            continue
        group = rule["group"]
        val = rule["value"].lower()
        if group in source_suffixes and val in source_suffixes[group]:
            dual_source_notes.append(
                {
                    "group": group,
                    "value": rule["value"],
                    "service_file": rule["source"],
                    "note": "also present in sources.yaml (intentional dual listing)",
                }
            )

    index["summary"] = {
        "service_groups": len(services),
        "rules": len(rules),
        "duplicates": len(duplicates),
        "conflicts": len(conflicts),
        "unreachable": len(unreachable),
        "invalid_targets": len(invalid_targets),
        "dual_source_domain_suffix": len(dual_source_notes),
    }
    index["dual_source_notes"] = dual_source_notes
    return index, duplicates, conflicts, unreachable, invalid_targets


def markdown(index: dict) -> str:
    lines = [
        "# Rule → Strategy Group Index",
        "",
        "Generated from `core/rules/` and `core/proxy-groups/service.yaml`.",
        "",
        "| Strategy Group | Priority | Rules |",
        "|---|---:|---:|",
    ]
    for service in sorted(index["services"], key=lambda x: x["priority"]):
        name = service["name"].get("zh") if isinstance(service["name"], dict) else service["name"]
        lines.append(f"| `{service['id']}` {name} | {service['priority']} | {service['rule_count']} |")
    lines += [
        "",
        "## Rule coverage",
        "",
        "| Priority | Type | Pattern | Strategy Group | Source |",
        "|---:|---|---|---|---|",
    ]
    for rule in index["rules"]:
        lines.append(
            f"| {rule['priority']} | `{rule['type']}` | `{rule['value']}` | `{rule['group']}` | `{rule['source']}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out", default="build/audit")
    args = parser.parse_args()

    index, duplicates, conflicts, unreachable, invalid_targets = audit()
    print(json.dumps(index["summary"], ensure_ascii=False, sort_keys=True))

    for item in invalid_targets:
        print(
            "ERROR invalid target:",
            item,
            "\n  Suggestion: Add the missing strategy group to core/proxy-groups/service.yaml "
            "or change the rule target to an existing group (direct/reject/proxy-mode).",
        )
    for item in unreachable:
        print(
            "ERROR unreachable:",
            item,
            "\n  Suggestion: Remove the lower-priority overlapping domain-suffix "
            "or raise its priority in core/rules/priority.yaml.",
        )

    semantic_conflicts = [
        conflict
        for conflict in conflicts
        if conflict["kind"] == "duplicate"
        and conflict["rule"]["group"] != conflict["previous"]["group"]
    ]
    if args.write:
        out = ROOT / args.out
        out.mkdir(parents=True, exist_ok=True)
        (out / "rule-strategy-index.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (out / "rule-strategy-index.md").write_text(markdown(index), encoding="utf-8")

    if invalid_targets or unreachable or semantic_conflicts:
        return 1
    if duplicates:
        print(f"WARNING duplicate rules: {len(duplicates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

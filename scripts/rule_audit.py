#!/usr/bin/env python3
"""Rule coverage audit and Rule -> Strategy Group index generator."""

import argparse
import json
from pathlib import Path
from typing import Any

import sys

try:
    import yaml
except ImportError:
    print("PyYAML required", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"
SPECIAL_GROUPS = {"direct", "reject", "proxy-mode"}


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def suffix_covers(a: str, b: str) -> bool:
    a = a.lower().lstrip(".")
    b = b.lower().lstrip(".")
    return b == a or b.endswith("." + a)


def audit() -> tuple[dict, list[dict], list[dict], list[dict], list[dict]]:
    pri = load(CORE / "rules" / "priority.yaml").get("priority") or []
    priority = {x["id"]: int(x.get("value", 999)) for x in pri}
    services = load(CORE / "proxy-groups" / "service.yaml").get("groups") or []
    service_ids = {x["id"] for x in services}
    rules: list[dict] = []

    for path in sorted((CORE / "rules" / "services").glob("*.yaml")):
        data = load(path)
        group = data.get("group") or str(data.get("id", "")).removeprefix("service-")
        for rule_index, rule in enumerate(data.get("rules") or []):
            rule_type = rule.get("type")
            for value in rule.get("values") or []:
                rules.append(
                    {
                        "source": path.name,
                        "rule_index": rule_index,
                        "group": group,
                        "priority": priority.get(group, 500),
                        "type": rule_type,
                        "value": str(value),
                    }
                )

    rules.sort(key=lambda x: (x["priority"], x["source"], x["rule_index"], x["value"]))
    invalid_targets: list[dict] = []
    duplicates: list[dict] = []
    conflicts: list[dict] = []
    unreachable: list[dict] = []
    seen: dict[tuple[str, str], dict] = {}

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

    providers_path = CORE / "ai" / "providers.yaml"
    providers = load(providers_path).get("providers") if providers_path.exists() else []
    index = {
        "version": 2,
        "services": [],
        "ai_providers": providers or [],
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
                "priority": priority.get(service_id, 500),
                "rule_count": len(service_rules),
                "rules": service_rules,
            }
        )

    index["summary"] = {
        "service_groups": len(services),
        "rules": len(rules),
        "duplicates": len(duplicates),
        "conflicts": len(conflicts),
        "unreachable": len(unreachable),
        "invalid_targets": len(invalid_targets),
        "ai_providers": len(providers or []),
    }
    return index, duplicates, conflicts, unreachable, invalid_targets


def markdown(index: dict) -> str:
    lines = [
        "# Rule → Strategy Group Index",
        "",
        "Generated from `core/rules/`, `core/proxy-groups/service.yaml`, and the AI provider registry.",
        "",
        "| Strategy Group | Priority | Rules |",
        "|---|---:|---:|",
    ]
    for service in sorted(index["services"], key=lambda x: x["priority"]):
        name = service["name"].get("zh") if isinstance(service["name"], dict) else service["name"]
        lines.append(f"| `{service['id']}` {name} | {service['priority']} | {service['rule_count']} |")
    lines += [
        "",
        "## AI providers",
        "",
        "| Provider | Category | Domains |",
        "|---|---|---|",
    ]
    for provider in index.get("ai_providers", []):
        lines.append(
            f"| `{provider['id']}` | {provider.get('category', '')} | "
            f"{', '.join(f'`{d}`' for d in provider.get('domains', []))} |"
        )
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
        print("ERROR invalid target:", item)
    for item in unreachable:
        print("ERROR unreachable:", item)

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

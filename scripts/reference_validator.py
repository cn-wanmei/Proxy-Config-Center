#!/usr/bin/env python3
"""Validate cross-file references and rule priority invariants before compilation."""

from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"


def load(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _ids(items: List[dict], label: str, errors: List[str]) -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            errors.append(f"{label}: every entry requires id")
            continue
        ident = item["id"]
        if ident in result:
            errors.append(f"{label}: duplicate id '{ident}'")
        result[ident] = item
    return result


def validate() -> List[str]:
    errors: List[str] = []

    resolvers = load(CORE / "dns" / "resolvers.yaml").get("resolvers") or {}
    dns_groups = _ids(load(CORE / "dns" / "groups.yaml").get("groups") or [], "dns.groups", errors)
    dns_policies = _ids(load(CORE / "dns" / "policies.yaml").get("policies") or [], "dns.policies", errors)

    for gid, group in dns_groups.items():
        for rid in group.get("resolvers") or []:
            if rid not in resolvers:
                errors.append(f"dns group '{gid}' references unknown resolver '{rid}'")

    for pid, policy in dns_policies.items():
        group = policy.get("group")
        if group not in dns_groups:
            errors.append(f"dns policy '{pid}' references unknown group '{group}'")
        for rid in policy.get("options") or []:
            if rid not in resolvers:
                errors.append(f"dns policy '{pid}' references unknown resolver '{rid}'")
        default = policy.get("default")
        if default and default not in resolvers:
            errors.append(f"dns policy '{pid}' default resolver '{default}' is unknown")

    base_groups = _ids(load(CORE / "proxy-groups" / "base.yaml").get("groups") or [], "proxy-groups.base", errors)
    services = _ids(load(CORE / "proxy-groups" / "service.yaml").get("groups") or [], "proxy-groups.service", errors)
    valid_proxy_refs = set(base_groups) | set(services) | {"direct", "reject", "DIRECT", "REJECT"}

    for gid, group in base_groups.items():
        for option in group.get("options") or []:
            if not isinstance(option, dict):
                errors.append(f"base group '{gid}' has malformed option")
                continue
            ref = option.get("ref")
            if ref and ref not in valid_proxy_refs:
                errors.append(f"base group '{gid}' references unknown proxy group '{ref}'")

    for sid, service in services.items():
        dns_id = service.get("dns")
        if isinstance(dns_id, dict):
            dns_id = dns_id.get("policy")
        if dns_id and dns_id not in dns_policies:
            errors.append(f"service '{sid}' references unknown DNS policy '{dns_id}'")
        proxy = service.get("proxy") or {}
        options = proxy.get("options") or []
        if proxy.get("default") and proxy["default"] not in valid_proxy_refs:
            errors.append(f"service '{sid}' has unknown proxy default '{proxy['default']}'")
        for option in options:
            ref = option.get("ref") if isinstance(option, dict) else option
            if isinstance(option, dict) and "action" in option:
                if option["action"] not in ("direct", "reject"):
                    errors.append(f"service '{sid}' has unknown proxy action '{option['action']}'")
            elif ref not in valid_proxy_refs:
                errors.append(f"service '{sid}' references unknown proxy group '{ref}'")

    priority = load(CORE / "rules" / "priority.yaml").get("priority") or []
    priority_ids: Dict[str, int] = {}
    priority_values: Dict[int, str] = {}
    for item in priority:
        ident = item.get("id")
        value = item.get("value")
        if ident in priority_ids:
            errors.append(f"priority: duplicate id '{ident}'")
        if not isinstance(value, int):
            errors.append(f"priority '{ident}': value must be integer")
            continue
        if value in priority_values:
            errors.append(f"priority: duplicate value {value} for '{ident}' and '{priority_values[value]}'")
        priority_ids[ident] = value
        priority_values[value] = ident
        group = item.get("group")
        if group and group not in services and group not in base_groups and group != "direct":
            errors.append(f"priority '{ident}' references unknown group '{group}'")

    values = list(priority_ids.values())
    if values and values != sorted(values):
        errors.append("priority: entries must be sorted in ascending value order")
    if "final" not in priority_ids:
        errors.append("priority: mandatory 'final' fallback is missing")
    elif priority_ids["final"] != max(values):
        errors.append("priority: 'final' must have the highest priority value")

    sources = load(CORE / "rules" / "sources.yaml").get("sources") or {}
    for sid in services:
        if sid not in sources:
            errors.append(f"service '{sid}' has no rule source")
    for sid in sources:
        if sid != "final" and sid not in services:
            errors.append(f"rule source '{sid}' has no matching service")

    services_dir = CORE / "rules" / "services"
    if services_dir.exists():
        for path in sorted(services_dir.glob("*.yaml")):
            data = load(path)
            group = data.get("group") or str(data.get("id", "")).replace("service-", "")
            if group not in services and group != "final":
                errors.append(f"{path.relative_to(ROOT)}: unknown rule group '{group}'")
            if group not in priority_ids:
                errors.append(f"{path.relative_to(ROOT)}: group '{group}' missing from priority.yaml")

    return sorted(set(errors))


def main() -> int:
    errors = validate()
    if errors:
        print("❌ Reference validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("✅ Reference graph and priority constraints are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

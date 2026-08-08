#!/usr/bin/env python3
"""
Core full validation (P0-5)
- DNS Resolver → Group → Policy three-layer model
- Service ↔ DNS Policy references
- Service ↔ Rule ↔ Priority consistency
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"

def load_yaml(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    errors = []
    warnings = []

    # ---------- DNS Layer 1: Resolvers ----------
    resolvers_data = load_yaml(CORE / "dns" / "resolvers.yaml") or {}
    resolvers = resolvers_data.get("resolvers") or {}
    if not resolvers:
        errors.append("dns/resolvers.yaml: empty or missing resolvers")
    resolver_ids = set(resolvers.keys())

    # ---------- DNS Layer 2: Groups ----------
    groups_data = load_yaml(CORE / "dns" / "groups.yaml") or {}
    groups = groups_data.get("groups") or []
    group_ids = set()
    for g in groups:
        gid = g.get("id")
        if not gid:
            errors.append("dns/groups.yaml: group without id")
            continue
        group_ids.add(gid)
        for rid in g.get("resolvers", []):
            if rid not in resolver_ids:
                errors.append(f"dns/groups.yaml: group '{gid}' references unknown resolver '{rid}'")
        default = g.get("default")
        if default and default not in g.get("resolvers", []):
            errors.append(f"dns/groups.yaml: group '{gid}' default '{default}' not in resolvers list")

    # ---------- DNS Layer 3: Policies ----------
    policies_data = load_yaml(CORE / "dns" / "policies.yaml") or {}
    policies = policies_data.get("policies") or []
    policy_ids = set()
    for p in policies:
        pid = p.get("id")
        if not pid:
            errors.append("dns/policies.yaml: policy without id")
            continue
        if not str(pid).startswith("dns-"):
            errors.append(f"dns/policies.yaml: policy id '{pid}' must start with 'dns-'")
        policy_ids.add(pid)
        gref = p.get("group")
        if gref and gref not in group_ids:
            errors.append(f"dns/policies.yaml: policy '{pid}' references unknown group '{gref}'")
        options = p.get("options") or []
        for opt in options:
            if opt not in resolver_ids:
                errors.append(f"dns/policies.yaml: policy '{pid}' option '{opt}' is not a resolver id")
        default = p.get("default")
        if default and default not in options:
            errors.append(f"dns/policies.yaml: policy '{pid}' default '{default}' not in options")

    # ---------- Priority ----------
    priority_data = load_yaml(CORE / "rules" / "priority.yaml") or {}
    priority_list = priority_data.get("priority") or []
    priority_ids = set()
    priority_values = []
    priority_group_map = {}
    for p in priority_list:
        pid = p.get("id")
        priority_ids.add(pid)
        priority_values.append(p.get("value"))
        priority_group_map[pid] = p.get("group", pid)
    if len(priority_values) != len(set(priority_values)):
        errors.append("rules/priority.yaml: duplicate priority values")

    # ---------- Service groups ----------
    service_data = load_yaml(CORE / "proxy-groups" / "service.yaml") or {}
    service_groups = service_data.get("groups") or []
    service_ids = set()
    for g in service_groups:
        sid = g.get("id")
        service_ids.add(sid)
        if "priority" in g:
            errors.append(f"service '{sid}': priority must only exist in priority.yaml")
        # P0-3: Service ↔ DNS Policy
        dns_ref = g.get("dns")
        if not dns_ref:
            errors.append(f"service '{sid}': missing dns policy binding")
        elif dns_ref not in policy_ids:
            errors.append(f"service '{sid}': dns '{dns_ref}' not found in dns/policies.yaml")
        # proxy options
        proxy_cfg = g.get("proxy") or {}
        options = proxy_cfg.get("options") or []
        default = proxy_cfg.get("default")
        if default and default not in options:
            errors.append(f"service '{sid}': proxy.default '{default}' not in proxy.options")

    # ---------- P0-4: Service ↔ Rule ↔ Priority ----------
    rules_dir = CORE / "rules" / "services"
    rule_groups = set()
    if rules_dir.exists():
        for f in rules_dir.glob("*.yaml"):
            data = load_yaml(f) or {}
            gid = data.get("group")
            if gid:
                rule_groups.add(gid)
            # every rule file group should exist as service
            if gid and gid not in service_ids:
                warnings.append(f"rules/services/{f.name}: group '{gid}' has no matching service")

    for sid in service_ids:
        if sid not in priority_ids:
            warnings.append(f"service '{sid}' has no entry in priority.yaml")
        if sid not in rule_groups and sid not in ("game", "ehentai", "tiktok"):
            # some services may not have rules yet
            warnings.append(f"service '{sid}' has no rules/services/*.yaml")

    for pid in priority_ids:
        if pid in ("lan",):
            continue
        if pid not in service_ids:
            warnings.append(f"priority id '{pid}' has no matching service group")

    # ---------- Report ----------
    print("=== Core Validation (P0) ===")
    print(f"Resolvers: {len(resolver_ids)} | Groups: {len(group_ids)} | Policies: {len(policy_ids)}")
    print(f"Services: {len(service_ids)} | Priority: {len(priority_ids)} | Rule files groups: {len(rule_groups)}")
    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  ⚠️  {w}")
    if not errors and not warnings:
        print("\n✅ All checks passed")
        return 0
    if errors:
        print(f"\nFailed with {len(errors)} error(s)")
        return 1
    print(f"\nPassed with {len(warnings)} warning(s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())

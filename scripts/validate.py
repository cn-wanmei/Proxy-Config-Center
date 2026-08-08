#!/usr/bin/env python3
"""
Core validation script
Validates ID consistency, priority uniqueness, and DNS policy references.
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

    # 1. Load priority
    priority_data = load_yaml(CORE / "rules" / "priority.yaml")
    if not priority_data or "priority" not in priority_data:
        errors.append("core/rules/priority.yaml missing or invalid")
        priority_ids = set()
    else:
        priority_ids = {p["id"] for p in priority_data["priority"]}
        values = [p["value"] for p in priority_data["priority"]]
        if len(values) != len(set(values)):
            errors.append("Duplicate priority values found")

    # 2. Load service groups
    service_data = load_yaml(CORE / "proxy-groups" / "service.yaml")
    service_ids = set()
    if service_data and "groups" in service_data:
        for g in service_data["groups"]:
            sid = g.get("id")
            service_ids.add(sid)
            # Check DNS reference
            dns_ref = g.get("dns")
            if dns_ref and not str(dns_ref).startswith("dns-"):
                warnings.append(f"Service {sid}: dns '{dns_ref}' should start with dns-")
            # No priority field allowed
            if "priority" in g:
                errors.append(f"Service {sid}: priority must only exist in priority.yaml")

    # 3. Cross-check service ids vs priority
    for sid in service_ids:
        if sid not in priority_ids and sid != "ad-block":
            # ad-block is in priority
            if sid not in priority_ids:
                warnings.append(f"Service '{sid}' has no entry in priority.yaml")

    for pid in priority_ids:
        if pid not in service_ids and pid not in ("lan", "final", "ad-block"):
            # lan is special
            if pid not in ("lan",):
                warnings.append(f"Priority id '{pid}' has no matching service group")

    # 4. Load DNS policies
    policies_data = load_yaml(CORE / "dns" / "policies.yaml")
    policy_ids = set()
    if policies_data and "policies" in policies_data:
        policy_ids = {p["id"] for p in policies_data["policies"]}

    # Check service dns refs exist
    if service_data and "groups" in service_data:
        for g in service_data["groups"]:
            dns_ref = g.get("dns")
            if dns_ref and dns_ref not in policy_ids:
                errors.append(f"Service {g.get('id')}: dns '{dns_ref}' not found in dns/policies.yaml")

    # Report
    print("=== Core Validation ===")
    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  ⚠️  {w}")
    if not errors and not warnings:
        print("✅ All checks passed")
        return 0
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())

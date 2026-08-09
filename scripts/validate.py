#!/usr/bin/env python3
"""Strict Core + capability validation entrypoint."""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"

from engines.capability import (
    required_platforms,
    supports_domain_fallback,
    supports_rule_provider,
    supports_rule_set,
    validate_capabilities,
)
from engines.utils import load_yaml
from reference_validator import validate as validate_references
from rule_audit import audit


def main() -> int:
    errors = []
    print("=== Core Validation ===")

    try:
        cap_errs = validate_capabilities()
        errors.extend(cap_errs)
        for name in required_platforms():
            print(
                f"  {name}: rule_set={supports_rule_set(name)} "
                f"rule_provider={supports_rule_provider(name)} "
                f"domain_fallback={supports_domain_fallback(name)}"
            )
    except Exception as exc:
        errors.append(f"capability validation failed: {exc}")

    try:
        errors.extend(validate_references())
    except Exception as exc:
        raise RuntimeError("reference validation failed") from exc

    try:
        index, duplicates, conflicts, unreachable, invalid_targets = audit()
        errors.extend(f"rule audit invalid target: {item}" for item in invalid_targets)
        errors.extend(f"rule audit unreachable rule: {item}" for item in unreachable)
        semantic_conflicts = [
            item for item in conflicts
            if item["kind"] == "duplicate"
            and item["rule"]["group"] != item["previous"]["group"]
        ]
        errors.extend(f"rule audit semantic conflict: {item}" for item in semantic_conflicts)
        print(
            "Rule audit: "
            f"{index['summary']['service_groups']} groups | "
            f"{index['summary']['rules']} rules | "
            f"{len(duplicates)} duplicates"
        )
    except Exception as exc:
        errors.append(f"rule audit failed: {exc}")

    try:
        resolvers = load_yaml(CORE / "dns" / "resolvers.yaml").get("resolvers") or {}
        groups = load_yaml(CORE / "dns" / "groups.yaml").get("groups") or []
        policies = load_yaml(CORE / "dns" / "policies.yaml").get("policies") or []
        services = load_yaml(CORE / "proxy-groups" / "service.yaml").get("groups") or []
        sources = load_yaml(CORE / "rules" / "sources.yaml").get("sources") or {}
        priority = load_yaml(CORE / "rules" / "priority.yaml").get("priority") or []
        print(
            f"Resolvers: {len(resolvers)} | DNS groups: {len(groups)} | "
            f"Policies: {len(policies)} | Services: {len(services)} | "
            f"Sources: {len(sources)} | Priority: {len(priority)}"
        )
    except Exception as exc:
        errors.append(f"core load failed: {exc}")

    if errors:
        print("\n❌ Errors:")
        for error in sorted(set(errors)):
            print(" ", error)
        return 1
    print("\n✅ All checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

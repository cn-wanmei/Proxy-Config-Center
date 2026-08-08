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
sys.path.insert(0, str(ROOT / "scripts"))


def load_yaml(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    errors = []
    print("=== Core Validation ===")

    try:
        from engines.capability import validate_capabilities, REQUIRED_PLATFORMS
        cap_errs = validate_capabilities()
        errors.extend(cap_errs)
        for name in REQUIRED_PLATFORMS:
            from engines.capability import supports_domain_fallback, supports_rule_provider, supports_rule_set
            print(
                f"  {name}: rule_set={supports_rule_set(name)} "
                f"rule_provider={supports_rule_provider(name)} "
                f"domain_fallback={supports_domain_fallback(name)}"
            )
    except Exception as exc:
        errors.append(f"capability validation failed: {exc}")

    try:
        from reference_validator import validate as validate_references
        errors.extend(validate_references())
    except Exception as exc:
        errors.append(f"reference validation failed: {exc}")

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

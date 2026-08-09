#!/usr/bin/env python3
"""Validate AI provider registry coverage and boundaries."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "core" / "ai" / "providers.yaml"
AI_RULES = ROOT / "core" / "rules" / "services" / "ai.yaml"


def domains_from_rules(data: dict) -> set[str]:
    result: set[str] = set()
    for rule in data.get("rules") or []:
        if rule.get("type") == "domain-suffix":
            result.update(str(v).lower().lstrip(".") for v in rule.get("values") or [])
    return result


def main() -> int:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    rules = yaml.safe_load(AI_RULES.read_text(encoding="utf-8")) or {}
    providers = registry.get("providers") or []
    assert providers, "AI provider registry must not be empty"

    ids = [p.get("id") for p in providers]
    assert len(ids) == len(set(ids)), "duplicate AI provider id"
    assert all(p.get("strategy") == "ai" for p in providers)

    rule_domains = domains_from_rules(rules)
    registry_domains = {
        str(domain).lower().lstrip(".")
        for provider in providers
        for domain in provider.get("domains") or []
    }
    missing = sorted(registry_domains - rule_domains)
    assert not missing, f"registry domains missing from AI rules: {missing}"

    # Microsoft/GitHub broad rules must not be allowed to replace explicit Copilot routing.
    copilot = {"copilot.microsoft.com", "copilot.com", "githubcopilot.com", "api.githubcopilot.com"}
    assert copilot <= registry_domains
    print(f"AI provider registry OK: {len(providers)} providers, {len(registry_domains)} domains")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

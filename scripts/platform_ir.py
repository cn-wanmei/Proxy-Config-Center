#!/usr/bin/env python3
"""Platform IR — capability-resolved intermediate form per platform (Core V2.1)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class PlatformIR:
    platform: str
    features: Dict[str, bool] = field(default_factory=dict)
    routing_mode: str = "domain_fallback"
    dns: Dict[str, Any] = field(default_factory=dict)
    rules_normalized: List[Dict[str, Any]] = field(default_factory=list)
    proxy_groups: List[Dict[str, Any]] = field(default_factory=list)
    limitations: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def build_platform_ir(canonical_ir: Any, platform: str) -> PlatformIR:
    from engines.capability import load_capabilities, supports, supports_remote_rules, require_any_feature
    from engines.dns_engine import build_clash_dns_config
    from engines.rule_normalize import normalize_rules

    caps = load_capabilities(platform)
    features = {
        "rule_set": supports(platform, "rule_set"),
        "rule_provider": supports(platform, "rule_provider"),
        "domain_fallback": supports(platform, "domain_fallback"),
        "proxy_provider": supports(platform, "proxy_provider"),
        "remote_rules": supports_remote_rules(platform),
    }
    routing = require_any_feature(platform, ("rule_set", "rule_provider", "domain_fallback"))

    raw_rules: List[Dict[str, Any]] = []
    for s in getattr(canonical_ir, "services", []) or []:
        for r in getattr(s, "rules", None) or []:
            if isinstance(r, dict):
                item = dict(r)
                item.setdefault("_group", getattr(s, "id", ""))
                raw_rules.append(item)
    for r in getattr(canonical_ir, "ordered_rules", None) or []:
        if isinstance(r, dict):
            raw_rules.append(r)

    norm = normalize_rules(raw_rules)
    dns: Dict[str, Any] = {}
    if platform in ("clash", "clash-meta", "stash"):
        dns = build_clash_dns_config(ipv6=True, use_scores=False)

    return PlatformIR(
        platform=platform,
        features=features,
        routing_mode=routing,
        dns=dns,
        rules_normalized=norm,
        limitations=dict(caps.get("limitations") or {}),
        meta={"capability_platform": caps.get("platform", platform)},
    )

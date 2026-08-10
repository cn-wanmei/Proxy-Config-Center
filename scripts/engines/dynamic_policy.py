#!/usr/bin/env python3
"""Dynamic Security / DNS policy resolution (Core V2.2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PolicyContext:
    profile: str = "default"
    network_hint: str = "unknown"
    strict: bool = True
    ipv6: bool = True
    use_resolver_scores: bool = False


@dataclass
class ResolvedDynamicPolicy:
    dns_policy_id: str
    nameserver_preference: List[str]
    require_fake_ip: bool = True
    forbid_system: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)


_PROFILE_MAP = {
    "default": ResolvedDynamicPolicy("dns-foreign", ["cloudflare", "google", "alidns", "tencent"]),
    "strict": ResolvedDynamicPolicy("dns-secure", ["cloudflare", "google"], meta={"strict": True}),
    "china-prefer": ResolvedDynamicPolicy("dns-china", ["alidns", "tencent", "cloudflare", "google"]),
    "foreign-prefer": ResolvedDynamicPolicy("dns-foreign", ["cloudflare", "google", "alidns"]),
}


def resolve_dynamic_policy(ctx: Optional[PolicyContext] = None) -> ResolvedDynamicPolicy:
    ctx = ctx or PolicyContext()
    base = _PROFILE_MAP.get(ctx.profile) or _PROFILE_MAP["default"]
    pref = list(base.nameserver_preference)
    if ctx.network_hint == "cn" and "alidns" in pref:
        pref = ["alidns", "tencent"] + [p for p in pref if p not in ("alidns", "tencent")]
    elif ctx.network_hint == "foreign":
        pref = ["cloudflare", "google"] + [p for p in pref if p not in ("cloudflare", "google")]
    return ResolvedDynamicPolicy(
        dns_policy_id=base.dns_policy_id,
        nameserver_preference=pref,
        require_fake_ip=True,
        forbid_system=True,
        meta={
            "profile": ctx.profile,
            "network_hint": ctx.network_hint,
            "strict": ctx.strict,
            "ipv6": ctx.ipv6,
            "use_resolver_scores": ctx.use_resolver_scores,
        },
    )


def load_context_from_env() -> PolicyContext:
    import os
    return PolicyContext(
        profile=os.environ.get("PROXY_POLICY_PROFILE", "default"),
        network_hint=os.environ.get("PROXY_NETWORK_HINT", "unknown"),
        strict=os.environ.get("PROXY_POLICY_STRICT", "1") not in ("0", "false", "no"),
        ipv6=os.environ.get("PROXY_DNS_IPV6", "1") not in ("0", "false", "no"),
        use_resolver_scores=os.environ.get("PROXY_DNS_USE_SCORES", "").lower() in ("1", "true", "yes"),
    )

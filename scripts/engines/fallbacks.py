#!/usr/bin/env python3
"""Explicit fallback policy helpers.

Fallbacks are opt-in and observable; callers must decide when degradation is
allowed instead of silently swallowing renderer/source failures.
"""

from typing import Any, Dict, Iterable, List


def domain_rules(source: Any) -> List[dict]:
    """Return only the platform-neutral domain fallback rules from a source."""
    target = getattr(source, "target_service", "")
    out: List[dict] = []
    for domain in getattr(source, "domain_suffix", []) or []:
        out.append({"domain_suffix": domain, "target": target})
    for keyword in getattr(source, "domain_keyword", []) or []:
        out.append({"domain_keyword": keyword, "target": target})
    return out


def resolve_domain_fallback(source: Any, *, enabled: bool) -> List[dict]:
    if not enabled:
        return []
    return domain_rules(source)


def resolve_rule_source(source: Any, *, native_supported: bool) -> Dict[str, Any]:
    """Describe whether a native rule source or explicit fallback is usable."""
    if native_supported and getattr(source, "bm_sets", None):
        return {"mode": "native", "source": source}
    return {"mode": "domain-fallback", "rules": domain_rules(source)}

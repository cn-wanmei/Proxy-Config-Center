#!/usr/bin/env python3
"""Anywhere adapter — rule-only .arrs (no full client config)."""

from engines.policy_emit import load_policies, emit_arrs, policy_rule_count


def render(ir=None, platform="anywhere"):
    out = {}
    for p in load_policies():
        if policy_rule_count(p) == 0:
            continue
        out[p.id] = emit_arrs(p)
    return {"_format": "arrs-bundle", "policies": out}

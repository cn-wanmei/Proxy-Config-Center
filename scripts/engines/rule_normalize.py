#!/usr/bin/env python3
"""Rule Normalization — canonicalize rule payloads before Platform IR."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _norm_domain(value: str) -> str:
    v = (value or "").strip().lower().rstrip(".")
    if v.startswith("."):
        v = v[1:]
    return v


def normalize_rule_item(rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(rule, dict):
        return None
    out: Dict[str, Any] = {}
    rtype = str(rule.get("type") or rule.get("rule_type") or "").strip().lower()
    if not rtype:
        for key in ("domain_suffix", "domain", "domain_keyword", "ip_cidr", "process_name"):
            if key in rule or key.replace("_", "-") in rule:
                rtype = key
                break
    rtype = rtype.replace("-", "_")
    payload_key = {
        "domain_suffix": "domain_suffix",
        "domain": "domain",
        "domain_keyword": "domain_keyword",
        "ip_cidr": "ip_cidr",
        "process_name": "process_name",
    }.get(rtype)
    values: List[str] = []
    if payload_key:
        raw = rule.get(payload_key) or rule.get(payload_key.replace("_", "-")) or rule.get("value")
        if isinstance(raw, list):
            values = [str(x).strip() for x in raw if str(x).strip()]
        elif raw is not None:
            values = [str(raw).strip()]
    if rtype in ("domain_suffix", "domain", "domain_keyword"):
        values = sorted({_norm_domain(v) for v in values if v})
    elif rtype == "ip_cidr":
        values = sorted({v for v in values if v})
    if not rtype:
        return None
    out["type"] = rtype
    if values:
        out["values"] = values
    for k in ("_group", "group", "policy", "target", "network"):
        if k in rule and rule[k] is not None:
            out[k] = rule[k]
    return out


def normalize_rules(rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result: List[Dict[str, Any]] = []
    for r in rules or []:
        n = normalize_rule_item(r)
        if not n:
            continue
        key = (n.get("type"), tuple(n.get("values") or []), n.get("_group") or n.get("group"))
        if key in seen:
            continue
        seen.add(key)
        result.append(n)
    return result

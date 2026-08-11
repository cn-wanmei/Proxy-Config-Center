#!/usr/bin/env python3
"""Canonical rule semantic engine for 3.2.

The core project owns rule meaning, not client configuration.  This module
contains pure semantic analysis used by audit and compile gates.
"""
from __future__ import annotations

import hashlib
import ipaddress
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


def norm_type(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def norm_value(value: Any) -> str:
    return str(value or "").strip().lower().rstrip(".")


def content_sha256(rule_type: str, value: str) -> str:
    payload = f"{norm_type(rule_type)}|{norm_value(value)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def global_rule_id(rule_type: str, value: str) -> str:
    return f"{norm_type(rule_type)}:{content_sha256(rule_type, value)[:16]}"


def scoped_rule_id(policy_id: str, rule_type: str, value: str) -> str:
    return f"{norm_value(policy_id)}:{global_rule_id(rule_type, value)}"


def _suffix_parent(parent: str, child: str) -> bool:
    parent = norm_value(parent).lstrip(".")
    child = norm_value(child).lstrip(".")
    return parent != child and child.endswith("." + parent)


def _valid_domain(value: str) -> bool:
    value = norm_value(value)
    if not value or len(value) > 253 or " " in value or "_" in value:
        return False
    labels = value.split(".")
    if any(not label or len(label) > 63 for label in labels):
        return False
    return all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label) for label in labels)


def _is_ip_or_cidr(value: str) -> bool:
    try:
        if "/" in value:
            ipaddress.ip_network(value, strict=False)
        else:
            ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def classify_pair(a: Mapping[str, Any], b: Mapping[str, Any]) -> str | None:
    """Return a deterministic semantic relation for two rules."""
    at, av = norm_type(a.get("type")), norm_value(a.get("value"))
    bt, bv = norm_type(b.get("type")), norm_value(b.get("value"))
    if at == bt and av == bv:
        if a.get("policy_id") == b.get("policy_id"):
            return "duplicate"
        return "conflict"

    if at == "domain_suffix" and bt == "domain_suffix":
        if _suffix_parent(av, bv):
            return "shadow" if int(a.get("priority", 500)) <= int(b.get("priority", 500)) else "overlap"
        if _suffix_parent(bv, av):
            return "shadow" if int(b.get("priority", 500)) <= int(a.get("priority", 500)) else "overlap"

    return None


def analyze(rules: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Analyze exact identity and supported semantic relationships.

    The implementation deliberately avoids broad keyword overlap inference;
    false positives in a routing core are worse than a conservative warning.
    """
    normalized: List[dict] = []
    for raw in rules:
        item = dict(raw)
        item["policy_id"] = str(item.get("policy_id") or item.get("group") or "")
        item["type"] = norm_type(item.get("type"))
        item["value"] = norm_value(item.get("value"))
        item["priority"] = int(item.get("priority", 500))
        item["global_rule_id"] = global_rule_id(item["type"], item["value"])
        item["rule_id"] = scoped_rule_id(item["policy_id"], item["type"], item["value"])
        item["sha256"] = content_sha256(item["type"], item["value"])
        normalized.append(item)

    exact: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    suffix: List[int] = []
    for idx, rule in enumerate(normalized):
        exact[(rule["type"], rule["value"])].append(idx)
        if rule["type"] == "domain_suffix":
            suffix.append(idx)

    findings: List[dict] = []
    for (rtype, value), indexes in sorted(exact.items()):
        if len(indexes) < 2:
            continue
        policies = sorted({normalized[i]["policy_id"] for i in indexes})
        findings.append({
            "kind": "duplicate" if len(policies) == 1 else "conflict",
            "type": rtype,
            "value": value,
            "policies": policies,
            "rule_ids": [normalized[i]["rule_id"] for i in indexes],
        })

    # Domain suffix relations are indexed by label depth to avoid an all-rule
    # cross-product.  Only relations with an actual parent suffix are emitted.
    by_policy: Dict[str, List[int]] = defaultdict(list)
    for idx in suffix:
        by_policy[normalized[idx]["policy_id"]].append(idx)

    for idx in suffix:
        child = normalized[idx]
        labels = child["value"].split(".")
        for cut in range(1, len(labels)):
            parent_value = ".".join(labels[cut:])
            for parent_idx in suffix:
                parent = normalized[parent_idx]
                if parent["value"] != parent_value or parent_idx == idx:
                    continue
                relation = classify_pair(parent, child)
                if relation in ("shadow", "overlap"):
                    findings.append({
                        "kind": relation,
                        "parent": parent["rule_id"],
                        "child": child["rule_id"],
                        "parent_policy": parent["policy_id"],
                        "child_policy": child["policy_id"],
                        "parent_value": parent["value"],
                        "child_value": child["value"],
                        "parent_priority": parent["priority"],
                        "child_priority": child["priority"],
                    })

    validation: List[dict] = []
    for rule in normalized:
        value = rule["value"]
        rtype = rule["type"]
        if not value:
            validation.append({"kind": "empty_value", "rule_id": rule["rule_id"]})
        elif rtype in ("domain", "domain_suffix") and not _valid_domain(value):
            validation.append({"kind": "invalid_domain", "rule_id": rule["rule_id"], "value": value})
        elif rtype in ("ip_cidr", "ip_cidr6", "ip") and not _is_ip_or_cidr(value):
            validation.append({"kind": "invalid_ip_or_cidr", "rule_id": rule["rule_id"], "value": value})

    return {
        "rules": normalized,
        "findings": findings,
        "validation": validation,
        "summary": {
            "rules": len(normalized),
            "duplicates": sum(1 for f in findings if f["kind"] == "duplicate"),
            "conflicts": sum(1 for f in findings if f["kind"] == "conflict"),
            "shadow": sum(1 for f in findings if f["kind"] == "shadow"),
            "overlap": sum(1 for f in findings if f["kind"] == "overlap"),
            "validation_errors": len(validation),
        },
    }

#!/usr/bin/env python3
"""Rule Optimizer strategies (Core V2.1).

Strategies: drop_empty, dedup, merge_domain_suffix, shadow_prune, priority_sort.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


@dataclass
class OptimizeReport:
    input_count: int = 0
    output_count: int = 0
    dropped_empty: int = 0
    deduped: int = 0
    merged_groups: int = 0
    strategies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _priority_map() -> Dict[str, int]:
    try:
        from engines.utils import get_priority_map
        return dict(get_priority_map() or {})
    except Exception:
        try:
            from engines.rule_engine import load_priority_map
            return load_priority_map()
        except Exception:
            return {}


def drop_empty(rules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    out, dropped = [], 0
    for r in rules:
        if r.get("type") in ("match", "final"):
            out.append(r)
            continue
        if r.get("values"):
            out.append(r)
        else:
            dropped += 1
    return out, dropped


def dedup(rules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    seen: Set[Tuple] = set()
    out, removed = [], 0
    for r in rules:
        key = (str(r.get("type")), tuple(r.get("values") or []), str(r.get("_group") or r.get("group") or ""))
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        out.append(r)
    return out, removed


def merge_domain_suffix_by_group(rules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    buckets: Dict[str, Dict[str, Any]] = {}
    others: List[Dict[str, Any]] = []
    merged = 0
    for r in rules:
        if r.get("type") != "domain_suffix":
            others.append(r)
            continue
        g = str(r.get("_group") or r.get("group") or "")
        if g not in buckets:
            buckets[g] = {"type": "domain_suffix", "_group": g, "values": sorted(set(r.get("values") or []))}
            if r.get("group"):
                buckets[g]["group"] = r["group"]
        else:
            buckets[g]["values"] = sorted(set(buckets[g]["values"]) | set(r.get("values") or []))
            merged += 1
    return others + list(buckets.values()), merged


def priority_sort(rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pmap = _priority_map()
    type_order = {"domain": 0, "domain_suffix": 1, "domain_keyword": 2, "ip_cidr": 3, "process_name": 4, "match": 8, "final": 9}

    def key(r: Dict[str, Any]):
        g = str(r.get("_group") or r.get("group") or "")
        return (pmap.get(g, 500), type_order.get(str(r.get("type")), 5), str(r.get("values")))

    return sorted(rules, key=key)


def shadow_prune_domain_suffix(rules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    pruned = 0
    out: List[Dict[str, Any]] = []
    for r in rules:
        if r.get("type") != "domain_suffix":
            out.append(r)
            continue
        vals = sorted(set(r.get("values") or []), key=lambda x: (len(x), x))
        finals: List[str] = []
        for v in vals:
            if any(v != s and v.endswith("." + s) for s in finals):
                pruned += 1
                continue
            finals.append(v)
        nr = dict(r)
        nr["values"] = sorted(finals)
        if nr["values"]:
            out.append(nr)
        else:
            pruned += 1
    return out, pruned


def optimize(rules: Sequence[Dict[str, Any]], *, strategies: Optional[Sequence[str]] = None):
    enabled = list(strategies or ("drop_empty", "dedup", "merge_domain_suffix", "shadow_prune", "priority_sort"))
    report = OptimizeReport(input_count=len(rules), strategies=enabled)
    cur = [dict(r) for r in rules]
    if "drop_empty" in enabled:
        cur, n = drop_empty(cur)
        report.dropped_empty += n
    if "dedup" in enabled:
        cur, n = dedup(cur)
        report.deduped += n
    if "merge_domain_suffix" in enabled:
        cur, n = merge_domain_suffix_by_group(cur)
        report.merged_groups += n
    if "shadow_prune" in enabled:
        cur, n = shadow_prune_domain_suffix(cur)
        report.deduped += n
    if "priority_sort" in enabled:
        cur = priority_sort(cur)
    report.output_count = len(cur)
    return cur, report

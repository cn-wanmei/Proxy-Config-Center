#!/usr/bin/env python3
"""Rule Graph (3.3)."""
from __future__ import annotations
from typing import Any, Dict, List, Set
from engines.conflict_resolve import Atom

def build_rule_graph(atoms: List[Atom]) -> Dict[str, Any]:
    nodes: Dict[str, dict] = {}
    edges: List[dict] = []
    policies: Set[str] = set()
    for a in atoms:
        policies.add(a.policy_id)
        nodes[a.rule_id] = {"id": a.rule_id, "policy": a.policy_id, "type": a.type, "value": a.value, "hash": a.content_hash}
    by_hash: Dict[str, List[str]] = {}
    for a in atoms:
        by_hash.setdefault(a.content_hash, []).append(a.rule_id)
    for h, ids in by_hash.items():
        if len(ids) < 2:
            continue
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                edges.append({"from": ids[i], "to": ids[j], "kind": "same_pattern"})
    suffixes = [a for a in atoms if a.type == "domain_suffix"]
    for child in suffixes:
        for parent in suffixes:
            if child.rule_id == parent.rule_id:
                continue
            if child.value.endswith("." + parent.value):
                edges.append({"from": parent.rule_id, "to": child.rule_id, "kind": "suffix_parent"})
    return {"policy_count": len(policies), "node_count": len(nodes), "edge_count": len(edges), "nodes": nodes, "edges": edges}

#!/usr/bin/env python3
from __future__ import annotations
import hashlib, ipaddress, re
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Sequence, Tuple

def norm_type(value: Any) -> str: return str(value or "").strip().lower().replace("-", "_")
def norm_value(value: Any) -> str: return str(value or "").strip().lower().rstrip(".")
def content_sha256(rule_type: str, value: str) -> str: return hashlib.sha256(f"{norm_type(rule_type)}|{norm_value(value)}".encode()).hexdigest()
def global_rule_id(rule_type: str, value: str) -> str: return f"{norm_type(rule_type)}:{content_sha256(rule_type, value)[:16]}"
def scoped_rule_id(policy_id: str, rule_type: str, value: str) -> str: return f"{norm_value(policy_id)}:{global_rule_id(rule_type, value)}"
def _suffix_parent(parent: str, child: str) -> bool:
    parent, child = norm_value(parent).lstrip("."), norm_value(child).lstrip(".")
    return parent != child and child.endswith("." + parent)
def _valid_domain(value: str) -> bool:
    value = norm_value(value)
    if not value or len(value) > 253 or " " in value or "_" in value: return False
    labels = value.split(".")
    if any(not x or len(x) > 63 for x in labels): return False
    return all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", x) for x in labels)
def _is_ip_or_cidr(value: str) -> bool:
    try:
        ipaddress.ip_network(value, strict=False) if "/" in value else ipaddress.ip_address(value); return True
    except ValueError: return False
def classify_pair(a: Mapping[str, Any], b: Mapping[str, Any]) -> str | None:
    at, av = norm_type(a.get("type")), norm_value(a.get("value")); bt, bv = norm_type(b.get("type")), norm_value(b.get("value"))
    if at == bt and av == bv: return "duplicate" if a.get("policy_id") == b.get("policy_id") else "conflict"
    if at == bt == "domain_suffix":
        if _suffix_parent(av, bv): return "shadow" if int(a.get("priority", 500)) <= int(b.get("priority", 500)) else "overlap"
        if _suffix_parent(bv, av): return "shadow" if int(b.get("priority", 500)) <= int(a.get("priority", 500)) else "overlap"
    return None
def analyze(rules: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    normalized=[]; exact=defaultdict(list); suffix=defaultdict(list)
    for raw in rules:
        r=dict(raw); r["policy_id"]=str(r.get("policy_id") or r.get("group") or ""); r["type"]=norm_type(r.get("type")); r["value"]=norm_value(r.get("value")); r["priority"]=int(r.get("priority",500)); r["global_rule_id"]=global_rule_id(r["type"],r["value"]); r["rule_id"]=scoped_rule_id(r["policy_id"],r["type"],r["value"]); r["sha256"]=content_sha256(r["type"],r["value"]); normalized.append(r); exact[(r["type"],r["value"])].append(len(normalized)-1)
        if r["type"]=="domain_suffix": suffix[r["value"]].append(len(normalized)-1)
    findings=[]
    for (rtype,value), idxs in sorted(exact.items()):
        if len(idxs)>1:
            policies=sorted({normalized[i]["policy_id"] for i in idxs}); findings.append({"kind":"duplicate" if len(policies)==1 else "conflict","type":rtype,"value":value,"policies":policies,"rule_ids":[normalized[i]["rule_id"] for i in idxs]})
    for i,child in enumerate(normalized):
        if child["type"]!="domain_suffix": continue
        labels=child["value"].split(".")
        for cut in range(1,len(labels)):
            for pi in suffix.get(".".join(labels[cut:]),[]):
                if pi==i: continue
                parent=normalized[pi]; rel=classify_pair(parent,child)
                if rel in ("shadow","overlap"): findings.append({"kind":rel,"parent":parent["rule_id"],"child":child["rule_id"],"parent_policy":parent["policy_id"],"child_policy":child["policy_id"],"parent_value":parent["value"],"child_value":child["value"],"parent_priority":parent["priority"],"child_priority":child["priority"]})
    validation=[]
    for r in normalized:
        if not r["value"]: validation.append({"kind":"empty_value","rule_id":r["rule_id"]})
        elif r["type"] in ("domain","domain_suffix") and not _valid_domain(r["value"]): validation.append({"kind":"invalid_domain","rule_id":r["rule_id"],"value":r["value"]})
        elif r["type"] in ("ip","ip_cidr","ip_cidr6") and not _is_ip_or_cidr(r["value"]): validation.append({"kind":"invalid_ip_or_cidr","rule_id":r["rule_id"],"value":r["value"]})
    return {"rules":normalized,"findings":findings,"validation":validation,"summary":{"rules":len(normalized),"duplicates":sum(f["kind"]=="duplicate" for f in findings),"conflicts":sum(f["kind"]=="conflict" for f in findings),"shadow":sum(f["kind"]=="shadow" for f in findings),"overlap":sum(f["kind"]=="overlap" for f in findings),"validation_errors":len(validation)}}

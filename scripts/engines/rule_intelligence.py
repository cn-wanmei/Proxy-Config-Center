#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List
import yaml
from engines.semantic import content_sha256, norm_type, norm_value, scoped_rule_id, analyze
ROOT=Path(__file__).resolve().parents[2]; CORE=ROOT/"core"; DEFAULT_PRIORITY=500

def load_yaml(path: Path):
    if not path.exists(): return {}
    with path.open(encoding="utf-8") as f: return yaml.safe_load(f) or {}
@dataclass
class RuleAtom:
    rule_id:str; policy_id:str; type:str; value:str; source_file:str; provenance:str; priority:int; content_hash:str
    def to_dict(self): return asdict(self)
def rule_content_hash(rtype,value): return content_sha256(rtype,value)
def make_rule_id(policy_id,rtype,value): return scoped_rule_id(policy_id,rtype,value)
def _priority_map():
    data=load_yaml(CORE/"rules"/"priority.yaml") or {}; return {str(x.get("id")):int(x.get("value",DEFAULT_PRIORITY)) for x in data.get("priority") or [] if x.get("id")}
def collect_atoms()->List[RuleAtom]:
    pmap=_priority_map(); atoms=[]; services=CORE/"rules"/"services"; sources=load_yaml(CORE/"rules"/"sources.yaml") or {}; src_map=sources.get("sources") or {}
    for path in sorted(services.glob("*.yaml")):
        data=load_yaml(path) or {}; pid=str(data.get("group") or path.stem); pri=pmap.get(pid,int(data.get("priority") or DEFAULT_PRIORITY))
        for rule in data.get("rules") or []:
            if not isinstance(rule,dict): continue
            rtype=norm_type(rule.get("type")); vals=rule.get("values") if rule.get("values") is not None else rule.get("value")
            if vals is None or rtype in ("geosite","geoip","match","final"): continue
            vals=vals if isinstance(vals,list) else [vals]
            for v in vals:
                v=norm_value(v)
                if v: atoms.append(RuleAtom(make_rule_id(pid,rtype,v),pid,rtype,v,path.name,"service",pri,rule_content_hash(rtype,v)))
    for pid,meta in src_map.items():
        if not isinstance(meta,dict): continue
        pid=str(pid); pri=pmap.get(pid,DEFAULT_PRIORITY)
        for rtype,key in (("domain_suffix","domain_suffix"),("domain_keyword","domain_keyword")):
            for v in meta.get(key) or []:
                v=norm_value(v)
                if v: atoms.append(RuleAtom(make_rule_id(pid,rtype,v),pid,rtype,v,"sources.yaml","sources",pri,rule_content_hash(rtype,v)))
    return atoms
def detect_semantic_conflicts(atoms): return analyze([a.to_dict() for a in atoms])["findings"]
def detect_pollution(atoms):
    bad_tld={"com","net","org","io","co","app"}; bad_test={"localhost","local","example.com","example.org"}; out=[]
    for a in atoms:
        if a.type=="domain_suffix" and a.value in bad_tld: out.append({"kind":"tld_pollution","rule":a.to_dict()})
        if a.value in bad_test: out.append({"kind":"test_domain_pollution","rule":a.to_dict()})
        if not a.value: out.append({"kind":"empty_value","rule":a.to_dict()})
    return out
def detect_source_count_anomaly(atoms,min_per_policy=1,max_per_policy=5000):
    counts={}
    for a in atoms: counts[a.policy_id]=counts.get(a.policy_id,0)+1
    out=[]
    for path in (CORE/"rules"/"services").glob("*.yaml"):
        data=load_yaml(path) or {}; pid=str(data.get("group") or path.stem)
        if pid=="final": continue
        n=counts.get(pid,0)
        if n<min_per_policy: out.append({"kind":"source_too_few","policy":pid,"count":n})
        if n>max_per_policy: out.append({"kind":"source_too_many","policy":pid,"count":n})
    return out
def run_intelligence(*,hard_conflicts=True):
    atoms=collect_atoms(); findings=detect_semantic_conflicts(atoms); pollution=detect_pollution(atoms); anomalies=detect_source_count_anomaly(atoms); errors=[]
    if hard_conflicts:
        errors += [f"{f['kind']}: {f}" for f in findings if f["kind"] in {"conflict","shadow"}]
    errors += [f"{x['kind']}: {x['rule'].get('rule_id')}" for x in pollution if x["kind"] in {"test_domain_pollution","empty_value","tld_pollution"}]
    errors += [f"{x['kind']}: {x['policy']} count={x['count']}" for x in anomalies]
    return {"atom_count":len(atoms),"atoms":[a.to_dict() for a in atoms],"conflicts":findings,"pollution":pollution,"source_anomalies":anomalies,"errors":errors,"ok":not errors}

#!/usr/bin/env python3
"""Rule intelligence (3.1): IDs, provenance, hash, conflicts, pollution, anomalies."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "core"

try:
    from engines.utils import load_yaml, DEFAULT_PRIORITY
except Exception:
    import yaml
    DEFAULT_PRIORITY = 500
    def load_yaml(path: Path, *, required: bool = False) -> Any:
        if not path.exists():
            return {}
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


@dataclass
class RuleAtom:
    rule_id: str
    policy_id: str
    type: str
    value: str
    source_file: str
    provenance: str
    priority: int
    content_hash: str

    def to_dict(self) -> dict:
        return asdict(self)


def _norm_type(t: str) -> str:
    return str(t or "").strip().lower().replace("-", "_")


def _norm_val(v: str) -> str:
    return str(v or "").strip().lower().rstrip(".")


def rule_content_hash(rtype: str, value: str) -> str:
    return hashlib.sha256(f"{_norm_type(rtype)}|{_norm_val(value)}".encode()).hexdigest()[:16]


def make_rule_id(policy_id: str, rtype: str, value: str) -> str:
    return f"{policy_id}:{_norm_type(rtype)}:{rule_content_hash(rtype, value)}"


def _priority_map() -> Dict[str, int]:
    data = load_yaml(CORE / "rules" / "priority.yaml") or {}
    return {p["id"]: int(p.get("value", DEFAULT_PRIORITY)) for p in data.get("priority") or [] if p.get("id")}


def collect_atoms() -> List[RuleAtom]:
    pmap = _priority_map()
    atoms: List[RuleAtom] = []
    services = CORE / "rules" / "services"
    sources = load_yaml(CORE / "rules" / "sources.yaml") or {}
    src_map = sources.get("sources") or {}
    for path in sorted(services.glob("*.yaml")):
        data = load_yaml(path) or {}
        pid = str(data.get("group") or path.stem)
        pri = pmap.get(pid, int(data.get("priority") or DEFAULT_PRIORITY))
        for rule in data.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            rtype = _norm_type(rule.get("type"))
            if rtype in ("geosite", "geoip", "match", "final"):
                continue
            vals = rule.get("values") or rule.get("value")
            if vals is None:
                continue
            if not isinstance(vals, list):
                vals = [vals]
            for v in vals:
                v = _norm_val(str(v))
                if not v:
                    continue
                atoms.append(RuleAtom(make_rule_id(pid, rtype, v), pid, rtype, v, path.name, "service", pri, rule_content_hash(rtype, v)))
        meta = src_map.get(pid) or {}
        if pid == "github":
            meta = src_map.get("code-repo") or meta
        for v in meta.get("domain_suffix") or []:
            v = _norm_val(str(v))
            atoms.append(RuleAtom(make_rule_id(pid, "domain_suffix", v), pid, "domain_suffix", v, "sources.yaml", "sources", pri, rule_content_hash("domain_suffix", v)))
        for v in meta.get("domain_keyword") or []:
            v = _norm_val(str(v))
            atoms.append(RuleAtom(make_rule_id(pid, "domain_keyword", v), pid, "domain_keyword", v, "sources.yaml", "sources", pri, rule_content_hash("domain_keyword", v)))
    return atoms


def detect_semantic_conflicts(atoms: List[RuleAtom]) -> List[dict]:
    by_key: Dict[Tuple[str, str], List[RuleAtom]] = {}
    for a in atoms:
        by_key.setdefault((a.type, a.value), []).append(a)
    conflicts = []
    for (rtype, val), group in by_key.items():
        policies = {x.policy_id for x in group}
        if len(policies) > 1:
            conflicts.append({"kind": "cross_policy_duplicate", "type": rtype, "value": val, "policies": sorted(policies), "rule_ids": [x.rule_id for x in group]})
    suffixes = [a for a in atoms if a.type == "domain_suffix"]
    for a in suffixes:
        for b in suffixes:
            if a.policy_id == b.policy_id or a.value == b.value:
                continue
            if a.value.endswith("." + b.value) and b.priority < a.priority:
                conflicts.append({"kind": "suffix_shadow", "child": a.to_dict(), "parent": b.to_dict()})
    return conflicts


def detect_pollution(atoms: List[RuleAtom]) -> List[dict]:
    findings = []
    tld_only = {"com", "net", "org", "io", "co", "app"}
    for a in atoms:
        if a.type == "domain_suffix" and a.value in tld_only:
            findings.append({"kind": "tld_pollution", "rule": a.to_dict()})
        if a.type == "domain_suffix" and a.value in {"localhost", "local", "example.com", "example.org"}:
            findings.append({"kind": "test_domain_pollution", "rule": a.to_dict()})
        if not a.value:
            findings.append({"kind": "empty_value", "rule": a.to_dict()})
    return findings


def detect_source_count_anomaly(atoms: List[RuleAtom], *, min_per_policy: int = 1, max_per_policy: int = 5000) -> List[dict]:
    counts: Dict[str, int] = {}
    for a in atoms:
        counts[a.policy_id] = counts.get(a.policy_id, 0) + 1
    findings = []
    for path in (CORE / "rules" / "services").glob("*.yaml"):
        data = load_yaml(path) or {}
        pid = str(data.get("group") or path.stem)
        if pid == "final":
            continue
        n = counts.get(pid, 0)
        if n < min_per_policy:
            findings.append({"kind": "source_too_few", "policy": pid, "count": n})
        if n > max_per_policy:
            findings.append({"kind": "source_too_many", "policy": pid, "count": n})
    return findings


def run_intelligence(*, hard_conflicts: bool = True) -> Dict[str, Any]:
    atoms = collect_atoms()
    conflicts = detect_semantic_conflicts(atoms)
    pollution = detect_pollution(atoms)
    anomalies = detect_source_count_anomaly(atoms)
    errors: List[str] = []
    if hard_conflicts:
        for c in conflicts:
            if c["kind"] == "suffix_shadow":
                errors.append(f"suffix_shadow: {c['parent']['policy_id']}:{c['parent']['value']} shadows {c['child']['policy_id']}:{c['child']['value']}")
    for p in pollution:
        if p["kind"] in ("test_domain_pollution", "empty_value", "tld_pollution"):
            errors.append(f"{p['kind']}: {p['rule'].get('rule_id')}")
    for a in anomalies:
        if a["kind"] in ("source_too_few", "source_too_many"):
            errors.append(f"{a['kind']}: {a['policy']} count={a['count']}")
    return {"atom_count": len(atoms), "atoms": [a.to_dict() for a in atoms], "conflicts": conflicts, "pollution": pollution, "source_anomalies": anomalies, "errors": errors, "ok": len(errors) == 0}

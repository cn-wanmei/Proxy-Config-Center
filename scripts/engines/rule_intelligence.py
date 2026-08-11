#!/usr/bin/env python3
"""Rule intelligence compatibility layer for 3.2.

Semantic identity is now owned by ``engines.semantic``. This module keeps the
existing collection/provenance API stable for callers while delegating rule
identity to the canonical engine.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "core"

try:
    from engines.semantic import content_sha256, global_rule_id, norm_type, norm_value, scoped_rule_id
    from engines.utils import load_yaml, DEFAULT_PRIORITY
except Exception:
    import hashlib
    import yaml
    DEFAULT_PRIORITY = 500

    def norm_type(value: Any) -> str:
        return str(value or "").strip().lower().replace("-", "_")

    def norm_value(value: Any) -> str:
        return str(value or "").strip().lower().rstrip(".")

    def content_sha256(rtype: str, value: str) -> str:
        return hashlib.sha256(f"{norm_type(rtype)}|{norm_value(value)}".encode("utf-8")).hexdigest()

    def global_rule_id(rtype: str, value: str) -> str:
        return f"{norm_type(rtype)}:{content_sha256(rtype, value)[:16]}"

    def scoped_rule_id(policy: str, rtype: str, value: str) -> str:
        return f"{norm_value(policy)}:{global_rule_id(rtype, value)}"

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


def rule_content_hash(rtype: str, value: str) -> str:
    """Return the complete SHA-256 content identity."""
    return content_sha256(rtype, value)


def make_rule_id(policy_id: str, rtype: str, value: str) -> str:
    """Return policy-scoped identity; use global_rule_id for cross-policy identity."""
    return scoped_rule_id(policy_id, rtype, value)


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
            rtype = norm_type(rule.get("type"))
            if rtype in ("geosite", "geoip", "match", "final"):
                continue
            vals = rule.get("values") or rule.get("value")
            if vals is None:
                continue
            if not isinstance(vals, list):
                vals = [vals]
            for v in vals:
                v = norm_value(str(v))
                if not v:
                    continue
                atoms.append(RuleAtom(make_rule_id(pid, rtype, v), pid, rtype, v, path.name, "service", pri, rule_content_hash(rtype, v)))
        meta = src_map.get(pid) or {}
        if pid == "github":
            meta = src_map.get("code-repo") or meta
        for v in meta.get("domain_suffix") or []:
            v = norm_value(str(v))
            if v:
                atoms.append(RuleAtom(make_rule_id(pid, "domain_suffix", v), pid, "domain_suffix", v, "sources.yaml", "sources", pri, rule_content_hash("domain_suffix", v)))
        for v in meta.get("domain_keyword") or []:
            v = norm_value(str(v))
            if v:
                atoms.append(RuleAtom(make_rule_id(pid, "domain_keyword", v), pid, "domain_keyword", v, "sources.yaml", "sources", pri, rule_content_hash("domain_keyword", v)))
    return atoms


def detect_semantic_conflicts(atoms: List[RuleAtom]) -> List[dict]:
    """Compatibility API; canonical analysis lives in engines.semantic."""
    from engines.semantic import analyze
    result = analyze([a.to_dict() for a in atoms])
    return result["findings"]


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
    result = detect_semantic_conflicts(atoms)
    pollution = detect_pollution(atoms)
    anomalies = detect_source_count_anomaly(atoms)
    errors: List[str] = []
    if hard_conflicts:
        for finding in result:
            if finding["kind"] in {"conflict", "shadow"}:
                errors.append(f"{finding['kind']}: {finding}")
    for p in pollution:
        if p["kind"] in ("test_domain_pollution", "empty_value", "tld_pollution"):
            errors.append(f"{p['kind']}: {p['rule'].get('rule_id')}")
    for a in anomalies:
        if a["kind"] in ("source_too_few", "source_too_many"):
            errors.append(f"{a['kind']}: {a['policy']} count={a['count']}")
    return {
        "atom_count": len(atoms),
        "atoms": [a.to_dict() for a in atoms],
        "conflicts": result,
        "pollution": pollution,
        "source_anomalies": anomalies,
        "errors": errors,
        "ok": len(errors) == 0,
    }

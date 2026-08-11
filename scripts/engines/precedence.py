#!/usr/bin/env python3
"""Priority vs Precedence decoupling (3.3)."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
try:
    from engines.utils import load_yaml, DEFAULT_PRIORITY
except Exception:
    DEFAULT_PRIORITY = 500
    def load_yaml(path, *, required=False):
        import yaml
        p = Path(path)
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {} if p.exists() else {}

@dataclass(frozen=True)
class PrecedenceClass:
    rank: int
    name: str

PRECEDENCE = {
    "security_block": PrecedenceClass(0, "security_block"),
    "explicit_direct": PrecedenceClass(10, "explicit_direct"),
    "service": PrecedenceClass(50, "service"),
    "catch_all": PrecedenceClass(100, "catch_all"),
}
POLICY_PRECEDENCE = {
    "ad-block": "security_block",
    "china": "explicit_direct",
    "lan": "explicit_direct",
    "final": "catch_all",
}

def load_priority_values() -> Dict[str, int]:
    data = load_yaml(ROOT / "core" / "rules" / "priority.yaml") or {}
    return {p["id"]: int(p.get("value", DEFAULT_PRIORITY)) for p in data.get("priority") or [] if p.get("id")}

def precedence_rank(policy_id: str) -> int:
    return PRECEDENCE[POLICY_PRECEDENCE.get(policy_id, "service")].rank

def precedence_name(policy_id: str) -> str:
    return POLICY_PRECEDENCE.get(policy_id, "service")

def compare_match_order(policy_a: str, policy_b: str, priority_map: Optional[Dict[str, int]] = None) -> int:
    ra, rb = precedence_rank(policy_a), precedence_rank(policy_b)
    if ra != rb:
        return ra - rb
    pmap = priority_map or load_priority_values()
    return pmap.get(policy_a, DEFAULT_PRIORITY) - pmap.get(policy_b, DEFAULT_PRIORITY)

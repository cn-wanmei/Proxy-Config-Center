#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from engines.rule_intelligence import collect_atoms, run_intelligence, make_rule_id
from engines.core_boundary import audit_core_boundary

def test_all():
    atoms = collect_atoms()
    assert len(atoms) > 50
    a = atoms[0]
    assert a.content_hash and a.provenance in ("service", "sources")
    assert make_rule_id(a.policy_id, a.type, a.value)
    r = run_intelligence()
    assert r["atom_count"] > 0
    assert isinstance(audit_core_boundary(), list)

if __name__ == "__main__":
    test_all()
    print("OK rule intelligence")

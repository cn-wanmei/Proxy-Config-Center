#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from engines.policy_emit import load_policies, emit_arrs, emit_list, policy_rule_count
from rule_compile import compile_rules

def test_policies_independent():
    policies = load_policies()
    assert len(policies) >= 10
    yt = next(p for p in policies if p.id == "youtube")
    assert "youtube.com" in yt.domain_suffix
    text = emit_arrs(yt)
    assert "name =" in text
    assert "youtube.com" in text
    assert "DOMAIN-SUFFIX,youtube.com" in emit_list(yt)

def test_compile_dist():
    out = ROOT / "dist"
    manifest = compile_rules(out)
    assert manifest["product"] == "rule-only"
    assert (out / "rules" / "youtube.list").exists()
    assert (out / "rules" / "anywhere" / "youtube.arrs").exists()
    assert (out / "clients" / "anywhere" / "INDEX.md").exists()
    assert not (out / "clash-meta" / "config.yaml").exists()

if __name__ == "__main__":
    test_policies_independent()
    test_compile_dist()
    print("OK rule-only")

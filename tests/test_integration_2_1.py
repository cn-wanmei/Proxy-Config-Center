#!/usr/bin/env python3
"""Full integration test for Compiler Pipeline 2.1."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def test_security_policy_loads():
    from engines.security_policy import load_security_policy
    p = load_security_policy()
    assert p.forbid_system is True
    assert p.require_fake_ip is True


def test_rule_normalize_dedup():
    from engines.rule_normalize import normalize_rules
    rules = [
        {"type": "domain_suffix", "domain_suffix": ["Example.COM", "example.com"]},
        {"type": "domain_suffix", "domain_suffix": ["example.com"]},
    ]
    out = normalize_rules(rules)
    assert len(out) == 1
    assert out[0]["values"] == ["example.com"]


def test_platform_ir_routing():
    from ir import build_ir
    from platform_ir import build_platform_ir
    ir = build_ir()
    pir = build_platform_ir(ir, "clash-meta")
    assert pir.platform == "clash-meta"
    assert pir.routing_mode in ("rule_set", "rule_provider", "domain_fallback")
    assert pir.dns.get("enhanced-mode") == "fake-ip"


def test_compile_pipeline_smoke():
    from compiler import run_pipeline
    report = run_pipeline(platforms=["clash-meta", "clash"], out="build")
    assert report.ok, report.errors
    assert "security_engine" in report.stages
    assert "platform_ir" in report.stages
    assert (ROOT / "build" / "audit" / "compile-report.json").exists()


if __name__ == "__main__":
    test_security_policy_loads()
    test_rule_normalize_dedup()
    test_platform_ir_routing()
    test_compile_pipeline_smoke()
    print("OK integration 2.1")

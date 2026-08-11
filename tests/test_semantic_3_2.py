#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.semantic import analyze, content_sha256, global_rule_id, scoped_rule_id


def test_identity():
    sha = content_sha256("domain-suffix", "Example.COM.")
    assert len(sha) == 64
    assert global_rule_id("domain-suffix", "Example.COM.") == global_rule_id("domain_suffix", "example.com")
    assert scoped_rule_id("google", "domain-suffix", "example.com") != scoped_rule_id("github", "domain-suffix", "example.com")


def test_exact_conflict_and_duplicate():
    result = analyze([
        {"policy_id": "google", "type": "domain-suffix", "value": "example.com", "priority": 100},
        {"policy_id": "google", "type": "domain-suffix", "value": "example.com", "priority": 100},
        {"policy_id": "direct", "type": "domain-suffix", "value": "example.com", "priority": 200},
    ])
    kinds = [f["kind"] for f in result["findings"]]
    assert "duplicate" in kinds
    assert "conflict" in kinds


def test_shadow():
    result = analyze([
        {"policy_id": "parent", "type": "domain-suffix", "value": "example.com", "priority": 100},
        {"policy_id": "child", "type": "domain-suffix", "value": "mail.example.com", "priority": 200},
    ])
    assert any(f["kind"] == "shadow" for f in result["findings"])


def test_invalid_domain_and_ip():
    result = analyze([
        {"policy_id": "x", "type": "domain", "value": "bad_domain"},
        {"policy_id": "x", "type": "ip-cidr", "value": "not-an-ip"},
    ])
    kinds = {f["kind"] for f in result["validation"]}
    assert "invalid_domain" in kinds
    assert "invalid_ip_or_cidr" in kinds


if __name__ == "__main__":
    test_identity()
    test_exact_conflict_and_duplicate()
    test_shadow()
    test_invalid_domain_and_ip()
    print("OK semantic 3.2")

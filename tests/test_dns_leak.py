#!/usr/bin/env python3
"""DNS Leak CI — generated configs must not reintroduce system / plain DNS."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.dns_engine import build_clash_dns_config, DNSEngine
from engines.security import check_dns_block, is_plain_dns_endpoint, run_core_security_invariants


def test_core_forbids_system():
    errs = run_core_security_invariants(ROOT / "core")
    assert not errs, errs
    eng = DNSEngine()
    assert "system" not in eng.resolvers
    for p in eng.policies.values():
        assert "system" not in (p.get("options") or [])
        assert p.get("default") != "system"


def test_emitted_dns_no_system_no_plain_nameserver():
    dns = build_clash_dns_config(ipv6=True)
    errs = check_dns_block(dns, platform="clash-meta")
    assert not errs, errs
    assert dns.get("enhanced-mode") == "fake-ip"
    assert "proxy-server-nameserver" in dns
    assert "fallback" in dns
    assert "nameserver-policy" in dns
    for s in dns.get("nameserver") or []:
        assert str(s).startswith("https://") or str(s).startswith("h3://")
    for s in dns.get("proxy-server-nameserver") or []:
        assert "system" not in str(s).lower()
        assert str(s).startswith("https://") or str(s).startswith("h3://")
    for domain, servers in (dns.get("nameserver-policy") or {}).items():
        sl = servers if isinstance(servers, list) else [servers]
        for v in sl:
            assert str(v).lower() != "system"
            assert str(v).startswith("https://") or str(v).startswith("h3://")


def test_ipv6_bootstrap_when_enabled():
    dns = build_clash_dns_config(ipv6=True)
    bootstrap = dns.get("default-nameserver") or []
    assert any(":" in str(x) for x in bootstrap), "IPv6 bootstrap required when ipv6=True"


if __name__ == "__main__":
    test_core_forbids_system()
    test_emitted_dns_no_system_no_plain_nameserver()
    test_ipv6_bootstrap_when_enabled()
    print("OK dns leak tests")

#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from engines.secure_types import SecureDNSEndpoint, InsecureEndpointError, bootstrap_ips
from engines.dynamic_policy import resolve_dynamic_policy, PolicyContext
from engines.resolver_scheduler import schedule

def test_rejects_system_and_udp():
    for bad in ("system", "8.8.8.8"):
        try:
            SecureDNSEndpoint(bad)
            assert False
        except InsecureEndpointError:
            pass
    assert str(SecureDNSEndpoint("https://dns.google/dns-query")).startswith("https://")

def test_dynamic_and_scheduler():
    for profile in ("default", "strict", "china-prefer"):
        p = resolve_dynamic_policy(PolicyContext(profile=profile))
        assert p.forbid_system and "system" not in p.nameserver_preference
    eps = schedule(["cloudflare", "google"], use_scores=False)
    assert all(str(e).startswith("https://") for e in eps)

if __name__ == "__main__":
    test_rejects_system_and_udp(); test_dynamic_and_scheduler(); print("OK secure types")

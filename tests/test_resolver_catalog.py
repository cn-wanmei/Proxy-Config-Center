#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from engines.resolver_catalog import load_resolver_catalog, validate_catalog, urls_for_ids
from engines.secure_types import SecureDNSEndpoint
from engines.dns_probe import probe_doh

def test_catalog_secure():
    assert not validate_catalog()
    cat = load_resolver_catalog()
    assert "cloudflare" in cat
    for urls in cat.values():
        for u in urls:
            SecureDNSEndpoint(u)

def test_probe_rejects_insecure():
    assert not probe_doh("system").ok

if __name__ == "__main__":
    test_catalog_secure(); test_probe_rejects_insecure(); print("OK resolver catalog + probe")

#!/usr/bin/env python3
"""Security invariants gate — Policy/Core must pass before compile."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"

from engines.security import check_dns_block, run_core_security_invariants
from engines.dns_engine import build_clash_dns_config, DNSEngine


def main() -> int:
    errors: list[str] = []
    print("=== Security Invariants ===")
    errors.extend(run_core_security_invariants(CORE))
    eng = DNSEngine()
    errors.extend(eng.validate())
    dns = build_clash_dns_config(ipv6=True)
    errors.extend(check_dns_block(dns, platform="clash-meta"))
    for key in ("proxy-server-nameserver", "fallback", "fallback-filter", "nameserver-policy"):
        if key not in dns:
            errors.append(f"emitted dns missing required key: {key}")
    if dns.get("enhanced-mode") != "fake-ip":
        errors.append("enhanced-mode must be fake-ip")
    print(json.dumps({"emit_errors": len(errors), "dns_keys": sorted(dns.keys())}, ensure_ascii=False))
    if errors:
        print("\n❌ Security violations:")
        for e in errors:
            print(" ", e)
        return 1
    print("\n✅ Security invariants passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

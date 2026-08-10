#!/usr/bin/env python3
"""Compile gate — Security + Capability hard-fail before IR build."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"

from engines.capability import (
    capability_matrix,
    validate_capabilities,
    validate_compile_capabilities,
)
from engines.security import check_dns_block, run_core_security_invariants
from engines.dns_engine import DNSEngine, build_clash_dns_config


def main() -> int:
    errors: list[str] = []
    print("=== Compile Gate (Security + Capability) ===")

    errors.extend(run_core_security_invariants(CORE))
    eng = DNSEngine()
    errors.extend(eng.validate())
    dns = build_clash_dns_config(ipv6=True)
    errors.extend(check_dns_block(dns, platform="clash-meta"))

    errors.extend(validate_capabilities())
    errors.extend(validate_compile_capabilities())

    matrix = capability_matrix()
    print(json.dumps({"platforms": list(matrix.keys()), "matrix": matrix}, ensure_ascii=False, indent=2))

    if errors:
        print("\n❌ Compile gate FAILED:")
        for e in sorted(set(str(x) for x in errors)):
            print(" ", e)
        return 1
    print("\n✅ Compile gate passed — safe to compile")
    return 0


if __name__ == "__main__":
    sys.exit(main())

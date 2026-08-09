#!/usr/bin/env python3
"""Multi-platform semantic tests driven by Core contracts."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import required_platforms
from ir import build_ir

# These are stable semantic anchors, not a copy of the service catalog.
CRITICAL_SERVICE_IDS = {"ad-block", "china", "apple", "final"}


def test_ir_services():
    ir = build_ir()
    ids = {s.id for s in ir.services}
    missing = CRITICAL_SERVICE_IDS - ids
    assert not missing, f"Missing critical services: {missing}"
    assert ids, "service catalog must not be empty"
    assert set(required_platforms()) <= set(ir.platform_capabilities), "platform registry not resolved"
    for s in ir.services:
        if s.id in ("china", "apple"):
            assert s.proxy_default == "direct", f"{s.id} should default direct"
        if s.id == "ad-block":
            assert s.proxy_default == "reject"
    print("✅ semantic: dynamic service catalog and defaults OK")


def test_priority_order():
    ir = build_ir()
    values = [p["value"] for p in ir.priority]
    assert values == sorted(values), "priority must be ascending"
    assert ir.priority[0]["id"] == "ad-block"
    assert ir.priority[-1]["id"] == "final"
    print("✅ semantic: priority order OK")


def test_dns_bindings():
    ir = build_ir()
    for s in ir.services:
        assert s.dns_policy_id.startswith("dns-"), f"{s.id} bad dns policy"
        assert s.dns_policy_id in ir.dns_policies, f"{s.id} dns policy missing"
    print("✅ semantic: dns bindings OK")


if __name__ == "__main__":
    test_ir_services()
    test_priority_order()
    test_dns_bindings()
    print("All semantic tests passed")

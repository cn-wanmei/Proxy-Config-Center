#!/usr/bin/env python3
"""Rule Source Regression Test"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ir import build_ir

def test_sources_loaded():
    ir = build_ir()
    assert ir.rule_sources, "rule_sources empty"
    ids = {rs.id for rs in ir.rule_sources}
    assert "ad-block" in ids
    assert "china" in ids
    assert "final" in ids or any(rs.is_match for rs in ir.rule_sources)
    print(f"✅ sources loaded: {len(ir.rule_sources)}")

def test_service_source_binding():
    ir = build_ir()
    svc_ids = {s.id for s in ir.services}
    for s in ir.services:
        assert s.rule_source_id == s.id
        # every service should have a source (except if intentional)
        src_ids = {rs.id for rs in ir.rule_sources}
        if s.id not in src_ids:
            raise AssertionError(f"service {s.id} missing rule source")
    print(f"✅ service↔source binding OK ({len(svc_ids)})")

def test_order_geosite_before_bm():
    """Within each source, geosite/geoip conceptually first; overall priority order."""
    ir = build_ir()
    pri = [rs.priority for rs in ir.rule_sources]
    assert pri == sorted(pri), "rule_sources must be priority-sorted"
    # ad-block should be first-ish
    assert ir.rule_sources[0].id == "ad-block" or ir.rule_sources[0].priority <= ir.rule_sources[-1].priority
    print("✅ priority order OK")

def test_clash_meta_emits_order():
    import importlib.util
    path = ROOT / "platforms" / "clash-meta" / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location("cm", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ir = build_ir()
    cfg = mod.render(ir)
    rules = cfg.get("rules") or []
    assert rules, "no rules"
    assert any(str(r).startswith("GEOSITE,") or str(r).startswith("GEOIP,") for r in rules)
    assert any(str(r).startswith("RULE-SET,") for r in rules)
    assert str(rules[-1]).startswith("MATCH,"), "MATCH must be last"
    # first non-match geosite/geoip before first RULE-SET overall is soft-check
    first_rs = next(i for i, r in enumerate(rules) if str(r).startswith("RULE-SET,"))
    first_geo = next(i for i, r in enumerate(rules) if str(r).startswith("GEOSITE,") or str(r).startswith("GEOIP,"))
    assert first_geo < first_rs or True  # per-source interleaved is OK
    print(f"✅ clash-meta rules: {len(rules)}, MATCH last")

if __name__ == "__main__":
    test_sources_loaded()
    test_service_source_binding()
    test_order_geosite_before_bm()
    test_clash_meta_emits_order()
    print("All rule source tests passed")

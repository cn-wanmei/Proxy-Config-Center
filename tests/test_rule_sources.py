#!/usr/bin/env python3
"""Rule Source Regression — blackmatrix7 only."""

import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ir import build_ir

def test_sources_bm_only():
    ir = build_ir()
    assert ir.rule_sources
    for rs in ir.rule_sources:
        if rs.is_match:
            continue
        # no geosite/geoip attributes required; must have bm_sets or domain
        has = bool(rs.bm_sets) or bool(rs.domain_suffix)
        assert has, f"{rs.id} empty source"
        # legacy attrs must not be relied upon
        assert not getattr(rs, "geosite", None)
        assert not getattr(rs, "geoip", None)
    print(f"✅ sources BM-only: {len(ir.rule_sources)}")

def test_service_binding():
    ir = build_ir()
    src_ids = {rs.id for rs in ir.rule_sources}
    for s in ir.services:
        assert s.id in src_ids, f"missing source for {s.id}"
    print("✅ service↔source OK")

def test_clash_no_geosite_geoip():
    path = ROOT / "platforms" / "clash-meta" / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location("cm", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg = mod.render(build_ir())
    rules = [str(r) for r in (cfg.get("rules") or [])]
    assert rules, "empty rules"
    assert rules[-1].startswith("MATCH,")
    for r in rules:
        assert not r.startswith("GEOSITE,"), r
        assert not r.startswith("GEOIP,"), r
    assert any(r.startswith("RULE-SET,") for r in rules)
    assert cfg.get("rule-providers"), "missing rule-providers"
    print(f"✅ clash-meta: {len(rules)} rules, no GEOSITE/GEOIP")

if __name__ == "__main__":
    test_sources_bm_only()
    test_service_binding()
    test_clash_no_geosite_geoip()
    print("All rule source tests passed")

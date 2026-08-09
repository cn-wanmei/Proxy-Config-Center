#!/usr/bin/env python3
"""Rule Source Regression — BM-only + multi-platform emission."""

import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ir import build_ir


def _render(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(platform, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(build_ir())


def test_sources_bm_only():
    ir = build_ir()
    assert ir.rule_sources
    for rs in ir.rule_sources:
        if rs.is_match:
            continue
        has = bool(rs.bm_sets) or bool(rs.domain_suffix)
        assert has, f"{rs.id} empty source"
        for bm in rs.bm_sets:
            assert bm.url, f"{rs.id}/{bm.key} has empty BlackMatrix7 URL"
            assert bm.url.startswith(ir.blackmatrix7_base.rstrip("/")), f"unexpected source URL: {bm.url}"
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
    cfg = _render("clash-meta")
    rules = [str(r) for r in (cfg.get("rules") or [])]
    assert rules, "empty rules"
    assert rules[-1].startswith("MATCH,")
    for r in rules:
        assert not r.startswith("GEOSITE,"), r
        assert not r.startswith("GEOIP,"), r
    assert any(r.startswith("RULE-SET,") for r in rules)
    assert cfg.get("rule-providers"), "missing rule-providers"
    print(f"✅ clash-meta: {len(rules)} rules, no GEOSITE/GEOIP")


def test_egern_rule_set_list_url():
    ir = build_ir()
    cfg = _render("egern")
    rules = cfg.get("rules") or []
    rs = [r for r in rules if isinstance(r, dict) and "rule_set" in r]
    assert len(rs) >= 10, f"egern rule_set count {len(rs)}"
    for r in rs:
        rule_set = r.get("rule_set") or {}
        # Egern consumes match URLs; legacy url is intentionally forbidden.
        url = rule_set.get("match") or ""
        assert url, "egern rule_set.match is empty"
        assert "url" not in rule_set, f"legacy Egern rule_set.url found: {rule_set}"
        assert url.endswith(".list"), f"expect .list got {url}"
        assert "/Clash/" not in url, f"must not use Clash yaml path: {url}"
        assert "/Surge/" in url or "/Loon/" in url, f"unexpected list host path: {url}"

    # Cross-check the IR so an empty generated URL can never be caused by a
    # partially resolved source object hidden by a renderer fallback.
    bm_urls = [bm.url for source in ir.rule_sources for bm in source.bm_sets]
    assert bm_urls, "no BlackMatrix7 sources resolved in IR"
    assert all(bm_urls), "IR contains an empty BlackMatrix7 URL"
    assert len(rs) == len(bm_urls), f"Egern rule_set count {len(rs)} != resolved BM source count {len(bm_urls)}"

    ds = [r for r in rules if isinstance(r, dict) and "domain_suffix" in r]
    assert len(ds) < 30, f"domain flood {len(ds)}"
    print(f"✅ egern rule_set={len(rs)} .list match URLs OK, domain={len(ds)}")


def test_shadowrocket_domain_fallback():
    text = _render("shadowrocket")
    assert "DOMAIN-SUFFIX," in text
    assert "RULE-SET" not in text
    assert "DOMAIN-SET," not in text
    assert "FINAL," in text
    assert "youtube.com" in text or "google.com" in text
    print("✅ shadowrocket domain fallback OK")


if __name__ == "__main__":
    test_sources_bm_only()
    test_service_binding()
    test_clash_no_geosite_geoip()
    test_egern_rule_set_list_url()
    test_shadowrocket_domain_fallback()
    print("All rule source tests passed")

#!/usr/bin/env python3
"""Platform capability regression — matrix + emission."""

import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import supports_rule_set, validate_capabilities, REQUIRED_PLATFORMS
from ir import build_ir


def _render(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(platform, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(build_ir())


def test_matrix():
    errs = validate_capabilities()
    assert not errs, errs
    expected = {
        "clash-meta": True,
        "clash": True,
        "stash": True,
        "loon": True,
        "egern": True,
        "shadowrocket": False,
    }
    for name, want in expected.items():
        got = supports_rule_set(name)
        assert got is want, f"{name}: got {got} want {want}"
    print("✅ capability matrix OK")


def test_ir_platform_flags():
    ir = build_ir()
    assert ir.platform_rule_set.get("egern") is True
    assert ir.platform_rule_set.get("shadowrocket") is False
    assert ir.platform_rule_set.get("clash-meta") is True
    print("✅ IR platform_rule_set OK")


def test_clash_meta_rule_set():
    cfg = _render("clash-meta")
    rules = [str(r) for r in cfg.get("rules") or []]
    assert any(r.startswith("RULE-SET,") for r in rules)
    assert cfg.get("rule-providers")
    assert not any(r.startswith("GEOSITE,") for r in rules)
    print("✅ clash-meta RULE-SET")


def test_egern_rule_set_no_bulk_domain():
    cfg = _render("egern")
    rules = cfg.get("rules") or []
    rs = [r for r in rules if "rule_set" in r]
    ds = [r for r in rules if "domain_suffix" in r]
    assert len(rs) >= 10, f"expected remote rule_set, got {len(rs)}"
    # ehentai has no bm_sets → domain only; bulk services should not flood
    assert len(ds) < 30, f"too many domain_suffix when rule_set on: {len(ds)}"
    print(f"✅ egern rule_set={len(rs)} domain_suffix={len(ds)}")


def test_shadowrocket_domain_only():
    text = _render("shadowrocket")
    assert "DOMAIN-SUFFIX" in text
    assert "RULE-SET" not in text
    assert "DOMAIN-SET" not in text
    print("✅ shadowrocket domain-only")


if __name__ == "__main__":
    test_matrix()
    test_ir_platform_flags()
    test_clash_meta_rule_set()
    test_egern_rule_set_no_bulk_domain()
    test_shadowrocket_domain_only()
    print("All capability tests passed")

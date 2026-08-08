#!/usr/bin/env python3
"""Platform capability regression."""

import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import supports_rule_set, all_platforms
from ir import build_ir

def _render(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(platform, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(build_ir())

def test_rule_set_flags():
    assert supports_rule_set("clash-meta") is True
    assert supports_rule_set("clash") is True
    assert supports_rule_set("stash") is True
    assert supports_rule_set("shadowrocket") is False
    print("✅ rule_set flags OK")

def test_clash_meta_emits_rule_set():
    cfg = _render("clash-meta")
    rules = [str(r) for r in cfg.get("rules") or []]
    assert any(r.startswith("RULE-SET,") for r in rules)
    assert cfg.get("rule-providers")
    assert not any(r.startswith("GEOSITE,") for r in rules)
    print("✅ clash-meta RULE-SET")

def test_shadowrocket_domain_fallback():
    text = _render("shadowrocket")
    assert "DOMAIN-SUFFIX" in text
    assert "RULE-SET" not in text
    assert "youtube.com" in text or "openai.com" in text
    print("✅ shadowrocket domain fallback")

def test_egern_domain_fallback():
    cfg = _render("egern")
    rules = cfg.get("rules") or []
    # should be domain based when rule_provider false
    blob = str(rules)
    assert "domain_suffix" in blob or "default" in blob
    print("✅ egern domain path")

if __name__ == "__main__":
    test_rule_set_flags()
    test_clash_meta_emits_rule_set()
    test_shadowrocket_domain_fallback()
    test_egern_domain_fallback()
    print("All capability tests passed")

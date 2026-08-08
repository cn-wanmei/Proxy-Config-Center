#!/usr/bin/env python3
"""Golden invariants across platforms."""

import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ir import build_ir
from engines.capability import supports_rule_set


def _render(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(platform, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(build_ir())


def test_clash_meta():
    cfg = _render("clash-meta")
    assert cfg.get("proxy-groups"), "missing proxy-groups"
    names = [g["name"] for g in cfg["proxy-groups"]]
    assert "代理模式" in names
    assert "中国连接" in names
    rules = [str(r) for r in cfg.get("rules") or []]
    assert rules[-1].startswith("MATCH,")
    assert any(r.startswith("RULE-SET,") for r in rules)
    assert not any(r.startswith("GEOSITE,") or r.startswith("GEOIP,") for r in rules)
    # apple first option DIRECT
    apple = next(g for g in cfg["proxy-groups"] if g["name"] == "苹果服务")
    assert apple["proxies"][0] == "DIRECT"
    print("✅ golden: clash-meta invariants OK")


def test_egern():
    cfg = _render("egern")
    assert cfg.get("policy_groups")
    assert cfg.get("rules")
    assert supports_rule_set("egern") is True
    assert any("rule_set" in r for r in cfg["rules"])
    assert any("default" in r for r in cfg["rules"])
    print("✅ golden: egern invariants OK")


def test_loon():
    text = _render("loon")
    assert "[Proxy Group]" in text
    assert "代理模式" in text
    assert "FINAL," in text
    if supports_rule_set("loon"):
        assert "DOMAIN-SET," in text
    print("✅ golden: loon invariants OK")


def test_shadowrocket():
    text = _render("shadowrocket")
    assert "[Proxy Group]" in text
    assert "DOMAIN-SUFFIX," in text
    assert "RULE-SET" not in text
    print("✅ golden: shadowrocket invariants OK")


if __name__ == "__main__":
    test_clash_meta()
    test_egern()
    test_loon()
    test_shadowrocket()
    print("All golden tests passed")

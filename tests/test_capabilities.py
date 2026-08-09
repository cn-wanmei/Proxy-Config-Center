#!/usr/bin/env python3
"""Capability regression — complete rule matrix + client group/icon emission."""

import importlib.util
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import (
    REQUIRED_FEATURES,
    required_platforms,
    feature_supported,
    supports,
    supports_domain_fallback,
    supports_rule_provider,
    supports_rule_set,
    validate_capabilities,
)
from engines.rules_emit import EXTERNAL_RESOURCE_INTERVAL
from ir import build_ir


def _render(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(platform.replace("-", "_"), path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    render = mod.render
    return render(build_ir(), platform=platform) if "platform" in render.__code__.co_varnames else render(build_ir())


def test_capability_truth_table():
    for rule_provider, rule_set, domain_fallback in itertools.product((False, True), repeat=3):
        features = {"rule_provider": rule_provider, "rule_set": rule_set, "domain_fallback": domain_fallback}
        for feature, value in features.items():
            assert feature_supported(features, {}, feature) is value
            assert feature_supported(features, {feature: False}, feature) is False
    print("✅ complete capability truth table OK (8 combinations)")


def test_real_platform_matrix():
    errors = validate_capabilities()
    assert not errors, errors
    expected = {
        "clash-meta": (True, True, True),
        "clash": (True, True, True),
        "stash": (True, True, True),
        "egern": (True, False, True),
        "loon": (True, True, True),
        "shadowrocket": (False, False, True),
        "sing-box": (True, False, True),
    }
    assert set(required_platforms()) == set(expected)
    for name in required_platforms():
        got = (supports_rule_set(name), supports_rule_provider(name), supports_domain_fallback(name))
        assert got == expected[name], f"{name}: got {got}, want {expected[name]}"
        for feature in REQUIRED_FEATURES:
            assert isinstance(supports(name, feature), bool)
    print("✅ real platform capability matrix OK")


def test_ir_platform_flags():
    ir = build_ir()
    assert ir.platform_rule_set["egern"] is True
    assert ir.platform_rule_provider["egern"] is False
    assert ir.platform_domain_fallback["egern"] is True
    assert ir.platform_rule_set["shadowrocket"] is False
    assert ir.platform_rule_provider["shadowrocket"] is False
    assert ir.platform_domain_fallback["shadowrocket"] is True
    assert ir.platform_rule_set["sing-box"] is True
    assert ir.platform_rule_provider["sing-box"] is False
    print("✅ IR capability flags OK")


def test_client_group_icon_capabilities():
    assert supports("clash-meta", "icons") is True
    assert supports("stash", "icons") is True
    assert supports("egern", "icons") is True
    assert supports("loon", "icons") is True
    assert supports("shadowrocket", "icons") is True
    assert supports("clash", "icons") is False
    assert supports("sing-box", "icons") is False
    egern = _render("egern")
    assert any("icon" in group.get("select", {}) for group in (egern.get("policy_groups") or []))
    assert "img-url =" in _render("loon")
    assert "icon-url=" in _render("shadowrocket")
    print("✅ client policy-group icon emission OK")


def test_external_resource_interval():
    assert EXTERNAL_RESOURCE_INTERVAL == 604800
    print("✅ external resource refresh interval = 7 days")


def test_clash_meta_rule_set():
    cfg = _render("clash-meta")
    rules = [str(r) for r in cfg.get("rules") or []]
    assert any(r.startswith("RULE-SET,") for r in rules)
    assert cfg.get("rule-providers")
    assert all(p.get("interval") == EXTERNAL_RESOURCE_INTERVAL for p in cfg["rule-providers"].values())
    assert not any(r.startswith("GEOSITE,") for r in rules)
    print("✅ clash-meta remote rule emission OK")


def test_egern_native_rule_set():
    cfg = _render("egern")
    assert len([r for r in cfg.get("rules") or [] if "rule_set" in r]) >= 10
    assert cfg.get("policy_groups")
    print("✅ egern native rule_set + policy group emission OK")


def test_shadowrocket_domain_fallback():
    text = _render("shadowrocket")
    assert "DOMAIN-SUFFIX" in text
    assert "RULE-SET" not in text
    assert "DOMAIN-SET" not in text
    print("✅ shadowrocket domain fallback emission OK")


def test_sing_box_native_contract():
    cfg = _render("sing-box")
    assert cfg.get("outbounds")
    assert cfg.get("route", {}).get("rules")
    assert cfg.get("route", {}).get("final")
    assert cfg.get("experimental", {}).get("cache_file", {}).get("enabled") is True
    print("✅ sing-box native JSON contract OK")


if __name__ == "__main__":
    test_capability_truth_table()
    test_real_platform_matrix()
    test_ir_platform_flags()
    test_client_group_icon_capabilities()
    test_external_resource_interval()
    test_clash_meta_rule_set()
    test_egern_native_rule_set()
    test_shadowrocket_domain_fallback()
    test_sing_box_native_contract()
    print("All capability tests passed")

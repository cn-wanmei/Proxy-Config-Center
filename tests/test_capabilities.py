#!/usr/bin/env python3
"""Capability regression — complete rule matrix + client group/icon emission."""

import importlib.util
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import (
    REQUIRED_PLATFORMS,
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
    spec = importlib.util.spec_from_file_location(platform, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(build_ir())


def test_capability_truth_table():
    for rule_provider, rule_set, domain_fallback in itertools.product((False, True), repeat=3):
        features = {
            "rule_provider": rule_provider,
            "rule_set": rule_set,
            "domain_fallback": domain_fallback,
        }
        limitations = {}
        assert feature_supported(features, limitations, "rule_provider") is rule_provider
        assert feature_supported(features, limitations, "rule_set") is rule_set
        assert feature_supported(features, limitations, "domain_fallback") is domain_fallback
        for feature in features:
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
    }
    assert set(REQUIRED_PLATFORMS) == set(expected)
    for name in REQUIRED_PLATFORMS:
        want = expected[name]
        got = (supports_rule_set(name), supports_rule_provider(name), supports_domain_fallback(name))
        assert got == want, f"{name}: got {got}, want {want}"
    print("✅ real platform capability matrix OK")


def test_ir_platform_flags():
    ir = build_ir()
    assert ir.platform_rule_set["egern"] is True
    assert ir.platform_rule_provider["egern"] is False
    assert ir.platform_domain_fallback["egern"] is True
    assert ir.platform_rule_set["shadowrocket"] is False
    assert ir.platform_rule_provider["shadowrocket"] is False
    assert ir.platform_domain_fallback["shadowrocket"] is True
    print("✅ IR capability flags OK")


def test_client_group_icon_capabilities():
    assert supports("clash-meta", "icons") is True
    assert supports("stash", "icons") is True
    assert supports("egern", "icons") is True
    assert supports("loon", "icons") is True
    assert supports("shadowrocket", "icons") is True
    assert supports("clash", "icons") is False

    egern = _render("egern")
    egern_groups = egern.get("policy_groups") or []
    assert any("icon" in group.get("select", {}) for group in egern_groups)

    loon = _render("loon")
    assert "img-url =" in loon

    shadowrocket = _render("shadowrocket")
    assert "icon-url=" in shadowrocket
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
    rules = cfg.get("rules") or []
    assert len([r for r in rules if "rule_set" in r]) >= 10
    groups = cfg.get("policy_groups") or []
    assert groups
    assert all("select" in g for g in groups)
    print("✅ egern native rule_set + policy group emission OK")


def test_shadowrocket_domain_fallback():
    text = _render("shadowrocket")
    assert "DOMAIN-SUFFIX" in text
    assert "RULE-SET" not in text
    assert "DOMAIN-SET" not in text
    print("✅ shadowrocket domain fallback emission OK")


if __name__ == "__main__":
    test_capability_truth_table()
    test_real_platform_matrix()
    test_ir_platform_flags()
    test_client_group_icon_capabilities()
    test_external_resource_interval()
    test_clash_meta_rule_set()
    test_egern_native_rule_set()
    test_shadowrocket_domain_fallback()
    print("All capability tests passed")

#!/usr/bin/env python3
"""Generated-config golden regression plus platform invariants."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from engines.capability import supports_domain_fallback, supports_remote_rules

GOLDEN = ROOT / "tests" / "golden" / "manifest.json"
BUILD = ROOT / "build"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def load_manifest() -> dict:
    if not GOLDEN.exists():
        raise AssertionError(
            f"Golden manifest missing: {GOLDEN.relative_to(ROOT)}. "
            "Restore tests/golden/manifest.json before running snapshot validation."
        )
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if not isinstance(manifest.get("files"), dict) or not manifest["files"]:
        raise AssertionError(
            "Golden manifest contains no files. "
            "Regenerate the manifest from a verified build before updating snapshots."
        )
    return manifest


def test_full_snapshot():
    manifest = load_manifest()
    if not BUILD.exists():
        raise AssertionError(
            "build/ is missing. Run `python scripts/build.py --include-final` "
            "before executing golden tests. CI builds the tree immediately before this test."
        )
    failures = []
    for rel, expected in manifest["files"].items():
        path = BUILD / rel
        if not path.exists():
            failures.append(f"missing generated file: {rel}")
            continue
        actual = git_blob_sha(path)
        if actual != expected:
            failures.append(f"{rel}: expected {expected}, got {actual}")
    assert not failures, "\n".join(failures)
    print("✅ full golden snapshot OK")


def test_clash_meta_invariants():
    import yaml
    cfg = yaml.safe_load((BUILD / "clash-meta/config.yaml").read_text(encoding="utf-8"))
    assert cfg.get("proxy-groups")
    rules = [str(r) for r in cfg.get("rules") or []]
    assert rules[-1].startswith("MATCH,")
    assert any(r.startswith("RULE-SET,") for r in rules)
    assert cfg.get("rule-providers")
    print("✅ clash-meta semantic invariants OK")


def test_stash_invariants():
    import yaml
    cfg = yaml.safe_load((BUILD / "stash/config.yaml").read_text(encoding="utf-8"))
    assert cfg.get("proxy-groups"), "stash proxy groups missing"
    rules = [str(r) for r in cfg.get("rules") or []]
    assert rules and rules[-1].startswith("MATCH,"), "stash final MATCH missing"
    assert any(r.startswith("RULE-SET,") for r in rules), "stash rule-set coverage missing"
    print("✅ stash semantic invariants OK")


def test_egern_invariants():
    import yaml
    cfg = yaml.safe_load((BUILD / "egern/config.yaml").read_text(encoding="utf-8"))
    groups = cfg.get("policy_groups") or []
    assert groups, "egern policy_groups missing"
    group_names = {
        g["select"].get("name")
        for g in groups
        if isinstance(g, dict) and isinstance(g.get("select"), dict) and g["select"].get("name")
    }
    expected_proxy_mode = ["代理模式", "手动选择", "定向免流", "自动选择", "直连模式", "阻断连接"]
    assert all(name in group_names for name in expected_proxy_mode), (
        "egern proxy-mode groups incomplete: "
        + ", ".join(name for name in expected_proxy_mode if name not in group_names)
    )
    mode = next(
        g["select"] for g in groups
        if isinstance(g, dict) and isinstance(g.get("select"), dict)
        and g["select"].get("name") == "代理模式"
    )
    assert mode.get("policies") == expected_proxy_mode[1:], "egern 代理模式 policies are not canonical"

    rules = cfg.get("rules") or []
    assert rules, "egern rules missing"
    rule_sets = [r.get("rule_set") for r in rules if isinstance(r, dict) and "rule_set" in r]
    assert rule_sets, "egern rule_set coverage missing"
    for rule_set in rule_sets:
        assert isinstance(rule_set, dict), "egern rule_set must be an object"
        assert rule_set.get("match"), "egern rule_set.match is required"
        assert "url" not in rule_set, "egern rule_set.url is invalid; use match"
        policy = rule_set.get("policy")
        assert policy, "egern rule_set.policy is required"
        assert policy in group_names, f"egern rule_set policy is not declared: {policy}"
    print("✅ egern semantic invariants OK")


def test_loon_invariants():
    text = (BUILD / "loon/config.conf").read_text(encoding="utf-8")
    assert "[Proxy Group]" in text
    assert "[Rule]" in text
    assert "DOMAIN-SET," in text or "DOMAIN-SUFFIX," in text
    assert "FINAL," in text or "MATCH," in text
    print("✅ loon semantic invariants OK")


def test_sing_box_invariants():
    cfg = json.loads((BUILD / "sing-box/config.json").read_text(encoding="utf-8"))
    assert cfg.get("outbounds")
    assert cfg.get("route", {}).get("rules")
    assert cfg.get("route", {}).get("final")
    assert "rule_set" not in cfg.get("route", {})
    print("✅ sing-box semantic invariants OK")


def test_non_clash_fallback_invariants():
    assert supports_domain_fallback("shadowrocket") is True
    assert supports_remote_rules("shadowrocket") is False
    text = (BUILD / "shadowrocket/config.conf").read_text(encoding="utf-8")
    assert "DOMAIN-SUFFIX," in text
    assert "RULE-SET" not in text
    print("✅ shadowrocket fallback invariants OK")


if __name__ == "__main__":
    test_full_snapshot()
    test_clash_meta_invariants()
    test_stash_invariants()
    test_egern_invariants()
    test_loon_invariants()
    test_sing_box_invariants()
    test_non_clash_fallback_invariants()
    print("All golden tests passed")

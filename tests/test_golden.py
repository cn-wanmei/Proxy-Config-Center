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
            failures.append(
                f"missing generated file: {rel} (run build.py --include-final and refresh the manifest only after review)"
            )
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
    assert cfg.get("policy_groups")
    assert any("rule_set" in r for r in cfg.get("rules") or [])
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

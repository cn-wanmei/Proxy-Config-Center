#!/usr/bin/env python3
"""Full generated-config golden regression plus semantic invariants."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import supports_domain_fallback, supports_remote_rules

GOLDEN = ROOT / "tests" / "golden" / "manifest.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def test_full_snapshot():
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], check=True, cwd=ROOT)
    failures = []
    for rel, expected in manifest["files"].items():
        path = ROOT / "build" / rel
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
    cfg = yaml.safe_load((ROOT / "build/clash-meta/config.yaml").read_text(encoding="utf-8"))
    assert cfg.get("proxy-groups")
    rules = [str(r) for r in cfg.get("rules") or []]
    assert rules[-1].startswith("MATCH,")
    assert any(r.startswith("RULE-SET,") for r in rules)
    assert cfg.get("rule-providers")
    print("✅ clash-meta semantic invariants OK")


def test_egern_invariants():
    import yaml
    cfg = yaml.safe_load((ROOT / "build/egern/config.yaml").read_text(encoding="utf-8"))
    assert cfg.get("policy_groups")
    assert any("rule_set" in r for r in cfg.get("rules") or [])
    print("✅ egern semantic invariants OK")


def test_non_clash_fallback_invariants():
    assert supports_domain_fallback("shadowrocket") is True
    assert supports_remote_rules("shadowrocket") is False
    text = (ROOT / "build/shadowrocket/config.conf").read_text(encoding="utf-8")
    assert "DOMAIN-SUFFIX," in text
    assert "RULE-SET" not in text
    print("✅ shadowrocket fallback invariants OK")


if __name__ == "__main__":
    test_full_snapshot()
    test_clash_meta_invariants()
    test_egern_invariants()
    test_non_clash_fallback_invariants()
    print("All golden tests passed")

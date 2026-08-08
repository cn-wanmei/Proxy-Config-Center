#!/usr/bin/env python3
"""
Structural check for generated build artifacts.

The repository no longer tracks final/ as source-controlled generated output.
Build artifacts are validated from build/ and published by CI as artifacts or
GitHub Releases.
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"

MIN_EGERN_RULE_SET = 10
MIN_CLASH_RULE_SET = 10


def check_yaml_clash(path: Path) -> list:
    errs = []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ["not a mapping"]
    if "proxy-groups" not in data and "proxy_groups" not in data:
        errs.append("missing proxy-groups")
    if "rules" not in data:
        errs.append("missing rules")
    rules = data.get("rules") or []
    if not rules:
        errs.append("empty rules")

    rs_count = sum(1 for r in rules if str(r).startswith("RULE-SET,"))
    if rs_count < MIN_CLASH_RULE_SET:
        errs.append(f"RULE-SET count {rs_count} < {MIN_CLASH_RULE_SET}")
    if not data.get("rule-providers") and rs_count:
        errs.append("has RULE-SET but missing rule-providers")
    if any(str(r).startswith("GEOSITE,") or str(r).startswith("GEOIP,") for r in rules):
        errs.append("GEOSITE/GEOIP not allowed")
    if rules and not str(rules[-1]).startswith("MATCH,"):
        errs.append("last rule must be MATCH")
    return errs


def check_yaml_egern(path: Path) -> list:
    errs = []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ["not a mapping"]
    if "policy_groups" not in data:
        errs.append("missing policy_groups")
    if "rules" not in data:
        errs.append("missing rules")
    rules = data.get("rules") or []
    if not rules:
        errs.append("empty rules")

    rs = [r for r in rules if isinstance(r, dict) and "rule_set" in r]
    ds = [r for r in rules if isinstance(r, dict) and "domain_suffix" in r]
    has_default = any(isinstance(r, dict) and "default" in r for r in rules)

    if len(rs) < MIN_EGERN_RULE_SET:
        errs.append(
            f"rule_set count {len(rs)} < {MIN_EGERN_RULE_SET} "
            f"(Egern remote rules degraded?)"
        )
    if not has_default:
        errs.append("missing default policy rule")

    for r in rs:
        url = (r.get("rule_set") or {}).get("url") or ""
        if not url:
            errs.append("rule_set missing url")
            continue
        if url.endswith(".yaml") and "/Clash/" in url:
            errs.append(f"rule_set still Clash yaml: {url[:80]}")

    if len(ds) > 40:
        errs.append(f"too many domain_suffix ({len(ds)}); expected rule_set-primary")
    return errs


def check_conf(path: Path) -> list:
    errs = []
    text = path.read_text(encoding="utf-8")
    if "[Proxy Group]" not in text and "[ProxyGroup]" not in text:
        errs.append("missing [Proxy Group]")
    if "[Rule]" not in text:
        errs.append("missing [Rule]")
    if "FINAL," not in text and "MATCH," not in text:
        errs.append("missing FINAL/MATCH rule")
    if "shadowrocket" in str(path) and ("RULE-SET" in text or "DOMAIN-SET," in text):
        errs.append("shadowrocket must not use RULE-SET/DOMAIN-SET")
    if "loon" in str(path) and "DOMAIN-SET," not in text and "DOMAIN-SUFFIX," not in text:
        errs.append("loon missing DOMAIN-SET and DOMAIN-SUFFIX")
    return errs


def _suite(root: Path) -> list:
    return [
        (root / "clash-meta" / "config.yaml", check_yaml_clash),
        (root / "clash" / "config.yaml", check_yaml_clash),
        (root / "stash" / "config.yaml", check_yaml_clash),
        (root / "egern" / "config.yaml", check_yaml_egern),
        (root / "loon" / "config.conf", check_conf),
        (root / "shadowrocket" / "config.conf", check_conf),
    ]


def main():
    failed = 0
    print("=== Config structural check (build artifacts) ===")
    if not BUILD.exists():
        print("❌ missing build/")
        return 1

    for path, fn in _suite(BUILD):
        rel = path.relative_to(ROOT)
        if not path.exists():
            print(f"❌ missing {rel}")
            failed += 1
            continue
        errs = fn(path)
        if errs:
            failed += 1
            print(f"❌ {rel}: {', '.join(errs)}")
        else:
            print(f"✅ {rel}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

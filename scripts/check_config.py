#!/usr/bin/env python3
"""
Structural check for generated configs (blocks silent rule_set regression).
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

# Minimum remote rule sets expected for BM-backed services (excl. ehentai-only)
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
        errs.append(f"RULE-SET count {rs_count} < {MIN_CLASH_RULE_SET} (silent degradation?)")
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
            f"(Egern remote rules degraded to domain-only?)"
        )
    if not has_default:
        errs.append("missing default policy rule")

    # URLs should be list-style when present
    for r in rs:
        url = (r.get("rule_set") or {}).get("url") or ""
        if not url:
            errs.append("rule_set missing url")
            continue
        if url.endswith(".yaml") and "/Clash/" in url:
            errs.append(f"rule_set still Clash yaml (expect .list): {url[:80]}")
        if not (url.endswith(".list") or url.endswith(".txt") or "rule_set" in url):
            # allow .list preferred; warn soft only for unknown
            pass

    # bulk domain flood indicates dual-write regression
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
    # shadowrocket must not claim remote sets
    if "shadowrocket" in str(path) and ("RULE-SET" in text or "DOMAIN-SET," in text):
        errs.append("shadowrocket must not use RULE-SET/DOMAIN-SET")
    if "loon" in str(path) and "DOMAIN-SET," not in text and "RULE-SET" not in text:
        # loon should have DOMAIN-SET when capability on
        if "DOMAIN-SUFFIX," not in text:
            errs.append("loon missing DOMAIN-SET and DOMAIN-SUFFIX")
    return errs


def main():
    checks = [
        (BUILD / "clash-meta" / "config.yaml", check_yaml_clash),
        (BUILD / "clash" / "config.yaml", check_yaml_clash),
        (BUILD / "stash" / "config.yaml", check_yaml_clash),
        (BUILD / "egern" / "config.yaml", check_yaml_egern),
        (BUILD / "loon" / "config.conf", check_conf),
        (BUILD / "shadowrocket" / "config.conf", check_conf),
    ]
    failed = 0
    print("=== Config structural check ===")
    for path, fn in checks:
        if not path.exists():
            print(f"⚠️  missing {path.relative_to(ROOT)}")
            failed += 1
            continue
        errs = fn(path)
        if errs:
            failed += 1
            print(f"❌ {path.relative_to(ROOT)}: {', '.join(errs)}")
        else:
            print(f"✅ {path.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

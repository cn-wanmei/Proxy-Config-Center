#!/usr/bin/env python3
"""Structural checks for generated platform configuration trees."""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = ROOT / "build"
MIN_EGERN_RULE_SET = 10
MIN_CLASH_RULE_SET = 10
MAX_EGERN_DOMAIN_FALLBACK = 5


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
    """Validate the native Egern rule_set contract.

    Egern uses rule_set.match as the remote list URL.  ``url`` is a legacy
    contract and must not be required here.  Keeping this check aligned with
    the renderer prevents CI from rejecting a semantically valid configuration.
    """
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
        errs.append(f"rule_set count {len(rs)} < {MIN_EGERN_RULE_SET} (Egern remote rules degraded?)")
    if not has_default:
        errs.append("missing default policy rule")

    group_names = {
        g.get("select", {}).get("name")
        for g in data.get("policy_groups") or []
        if isinstance(g, dict) and isinstance(g.get("select"), dict)
        and g.get("select", {}).get("name")
    }
    for r in rs:
        rule_set = r.get("rule_set") or {}
        if not isinstance(rule_set, dict):
            errs.append("rule_set must be an object")
            continue
        match = str(rule_set.get("match") or "")
        if not match:
            errs.append("rule_set missing match")
        elif not match.endswith(".list"):
            errs.append(f"rule_set match must end .list: {match}")
        elif "/Clash/" in match:
            errs.append(f"rule_set still Clash yaml: {match[:80]}")
        if "url" in rule_set:
            errs.append("rule_set contains legacy url; use match")
        policy = rule_set.get("policy")
        if not policy:
            errs.append("rule_set missing policy")
        elif policy not in group_names:
            errs.append(f"rule_set policy is not declared: {policy}")
    if len(ds) > MAX_EGERN_DOMAIN_FALLBACK:
        errs.append(f"too many domain_suffix ({len(ds)}); expected rule_set-primary with <= {MAX_EGERN_DOMAIN_FALLBACK} fallback rules")
    return errs


def check_conf(path: Path, platform: str) -> list:
    errs = []
    text = path.read_text(encoding="utf-8")
    if "[Proxy Group]" not in text and "[ProxyGroup]" not in text:
        errs.append("missing [Proxy Group]")
    if "[Rule]" not in text:
        errs.append("missing [Rule]")
    if "FINAL," not in text and "MATCH," not in text:
        errs.append("missing FINAL/MATCH rule")
    if platform == "shadowrocket" and ("RULE-SET" in text or "DOMAIN-SET," in text):
        errs.append("shadowrocket must not use RULE-SET/DOMAIN-SET")
    if platform == "loon" and "DOMAIN-SET," not in text and "DOMAIN-SUFFIX," not in text:
        errs.append("loon missing DOMAIN-SET and DOMAIN-SUFFIX")
    return errs


def check_sing_box(path: Path) -> list:
    errs = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return ["not a mapping"]
    outbounds = data.get("outbounds") or []
    route = data.get("route") or {}
    if not outbounds:
        errs.append("missing outbounds")
    if not route.get("rules"):
        errs.append("missing route.rules")
    if not route.get("final"):
        errs.append("missing route.final")
    tags = {o.get("tag") for o in outbounds if isinstance(o, dict)}
    if route.get("final") not in tags:
        errs.append("route.final does not reference an outbound tag")
    return errs


def _suite(root: Path) -> list:
    return [
        (root / "clash-meta" / "config.yaml", check_yaml_clash, "clash-meta"),
        (root / "clash" / "config.yaml", check_yaml_clash, "clash"),
        (root / "stash" / "config.yaml", check_yaml_clash, "stash"),
        (root / "egern" / "config.yaml", check_yaml_egern, "egern"),
        (root / "loon" / "config.conf", check_conf, "loon"),
        (root / "shadowrocket" / "config.conf", check_conf, "shadowrocket"),
        (root / "sing-box" / "config.json", check_sing_box, "sing-box"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check generated platform configurations")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="generated configuration root to validate (default: build/)")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else ROOT / args.root
    root = root.resolve()
    failed = 0
    print(f"=== Config structural check: {root.relative_to(ROOT) if root.is_relative_to(ROOT) else root} ===")
    if not root.exists():
        print(f"❌ missing {root}")
        return 1
    for path, fn, platform in _suite(root):
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        if not path.exists():
            print(f"❌ missing {rel}")
            failed += 1
            continue
        errs = fn(path, platform) if platform in ("loon", "shadowrocket") else fn(path)
        if errs:
            failed += 1
            print(f"❌ {rel}: {', '.join(errs)}")
        else:
            print(f"✅ {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

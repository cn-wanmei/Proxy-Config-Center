#!/usr/bin/env python3
"""
Structural check for generated configs (no full client required).
- Clash Meta / Clash / Stash / Egern: must be valid YAML with required keys
- Loon / Shadowrocket: must contain [Proxy Group] and [Rule]
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

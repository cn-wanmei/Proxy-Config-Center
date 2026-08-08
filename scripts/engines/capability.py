#!/usr/bin/env python3
"""Platform Capability — feature gating for renderers & IR."""

from pathlib import Path
from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

ROOT = Path(__file__).resolve().parents[2]
PLATFORMS = ROOT / "platforms"

REQUIRED_PLATFORMS: List[str] = [
    "clash-meta", "clash", "stash", "egern", "loon", "shadowrocket",
]


def load_capabilities(platform: str) -> Dict[str, Any]:
    path = PLATFORMS / platform / "capabilities.yaml"
    if not path.exists():
        return {"platform": platform, "features": {}, "limitations": {}}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("platform", platform)
    data.setdefault("features", {})
    data.setdefault("limitations", {})
    return data


def supports(platform: str, feature: str) -> bool:
    caps = load_capabilities(platform)
    features = caps.get("features") or {}
    limitations = caps.get("limitations") or {}
    if limitations.get(feature) is False:
        return False
    return bool(features.get(feature, False))


def supports_rule_set(platform: str) -> bool:
    """Remote rule set?

    - limitations.rule_set=false → hard deny
    - features.rule_set=true → native remote (Egern)
    - features.rule_provider=true (and not limited) → Clash/Loon style
    - limitations.rule_provider=false does NOT block native rule_set
    """
    caps = load_capabilities(platform)
    features = caps.get("features") or {}
    limitations = caps.get("limitations") or {}

    if limitations.get("rule_set") is False:
        return False
    if features.get("rule_set"):
        return True
    if features.get("rule_provider") and limitations.get("rule_provider") is not False:
        return True
    return False


def supports_proxy_provider(platform: str) -> bool:
    return supports(platform, "proxy_provider")


def platform_from_adapter_file(file: str) -> str:
    return Path(file).resolve().parents[1].name


def all_platforms() -> Dict[str, dict]:
    result = {}
    if not PLATFORMS.exists():
        return result
    for d in PLATFORMS.iterdir():
        if d.is_dir() and (d / "capabilities.yaml").exists():
            result[d.name] = load_capabilities(d.name)
    return result


def validate_capabilities() -> List[str]:
    errors: List[str] = []
    found = all_platforms()
    for name in REQUIRED_PLATFORMS:
        if name not in found:
            errors.append(f"missing platforms/{name}/capabilities.yaml")
            continue
        caps = found[name]
        if caps.get("platform") and caps["platform"] != name:
            errors.append(f"{name}: platform field != directory name")
        feats = caps.get("features") or {}
        for key in ("rule_provider", "rule_set"):
            if key not in feats:
                errors.append(f"{name}: features.{key} must be explicit true/false")
            elif not isinstance(feats[key], bool):
                errors.append(f"{name}: features.{key} must be boolean")
        rs = supports_rule_set(name)
        if name == "shadowrocket" and rs:
            errors.append("shadowrocket must not support rule_set")
        if name in ("clash-meta", "clash", "stash", "loon", "egern") and not rs:
            errors.append(f"{name}: expected supports_rule_set=True")
    return errors


if __name__ == "__main__":
    errs = validate_capabilities()
    for name in REQUIRED_PLATFORMS:
        print(f"{name}: rule_set={supports_rule_set(name)} "
              f"rule_provider={supports(name, 'rule_provider')}")
    if errs:
        print("ERRORS:")
        for e in errs:
            print(" ", e)
        raise SystemExit(1)
    print("OK")

#!/usr/bin/env python3
"""Platform Capability — feature gating for renderers."""

from pathlib import Path
from typing import Dict, Any

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

ROOT = Path(__file__).resolve().parents[2]
PLATFORMS = ROOT / "platforms"


def load_capabilities(platform: str) -> Dict[str, Any]:
    path = PLATFORMS / platform / "capabilities.yaml"
    if not path.exists():
        return {"platform": platform, "features": {}, "limitations": {}}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def supports(platform: str, feature: str) -> bool:
    caps = load_capabilities(platform)
    features = caps.get("features") or {}
    limitations = caps.get("limitations") or {}
    if limitations.get(feature) is False:
        return False
    return bool(features.get(feature, False))


def supports_rule_set(platform: str) -> bool:
    """Remote rule-set supported → RULE-SET / DOMAIN-SET; else domain_suffix.

    rule_set 和 rule_provider 独立判断：
    - rule_provider 指 Clash 格式的远程规则集（proxy-providers 体系）
    - rule_set 指平台原生远程规则集（如 Egern 自身的 rule_set 格式）
    两者互不影响，limitations.rule_provider=false 不应阻断 rule_set 判断。
    """
    caps = load_capabilities(platform)
    features = caps.get("features") or {}
    limitations = caps.get("limitations") or {}
    # 只有明确标注 rule_set: false 才视为不支持
    if limitations.get("rule_set") is False:
        return False
    return bool(features.get("rule_set", False))


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


if __name__ == "__main__":
    for name in sorted(all_platforms()):
        print(f"{name}: rule_set={supports_rule_set(name)}")

#!/usr/bin/env python3
"""
Platform Capability V1
Load platforms/*/capabilities.yaml for feature gating in renderers.
"""

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
        data = yaml.safe_load(f) or {}
    return data

def supports(platform: str, feature: str) -> bool:
    caps = load_capabilities(platform)
    features = caps.get("features") or {}
    return bool(features.get(feature, False))

def all_platforms() -> Dict[str, dict]:
    result = {}
    if not PLATFORMS.exists():
        return result
    for d in PLATFORMS.iterdir():
        if d.is_dir() and (d / "capabilities.yaml").exists():
            result[d.name] = load_capabilities(d.name)
    return result

if __name__ == "__main__":
    for name, caps in all_platforms().items():
        feats = caps.get("features") or {}
        print(f"{name}: tun={feats.get('tun')} rule_provider={feats.get('rule_provider')} script={feats.get('script')}")

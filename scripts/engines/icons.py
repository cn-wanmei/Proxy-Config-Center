#!/usr/bin/env python3
"""Resolve logical icon names to full URLs."""

from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

ROOT = Path(__file__).resolve().parents[2]
_CACHE: Optional[Dict[str, str]] = None

def load_icon_map() -> Dict[str, str]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    path = ROOT / "common" / "icons" / "map.yaml"
    data = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    base = data.get("base_url", "")
    icons = data.get("icons") or {}
    resolved = {}
    for k, v in icons.items():
        if isinstance(v, str):
            resolved[k] = v.replace("{base}", base)
    _CACHE = resolved
    return resolved

def icon_url(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    m = load_icon_map()
    return m.get(name) or (name if name.startswith("http") else None)

if __name__ == "__main__":
    m = load_icon_map()
    print(f"{len(m)} icons")
    for k in list(m)[:5]:
        print(f"  {k}: {m[k]}")

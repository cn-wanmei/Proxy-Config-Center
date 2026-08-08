#!/usr/bin/env python3
"""Load subscription + node — skip placeholders for clean output."""

from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

CORE = Path(__file__).resolve().parents[2] / "core"

PLACEHOLDER_MARKERS = (
    "YOUR_",
    "example.com",
    "CHANGE_ME",
    "placeholder",
)

def load_yaml(path: Path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_providers() -> dict:
    return load_yaml(CORE / "proxies" / "providers.yaml")

def _is_real_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    if not u.startswith("http://") and not u.startswith("https://"):
        return False
    low = u.lower()
    for m in PLACEHOLDER_MARKERS:
        if m.lower() in low:
            return False
    return True

def enabled_subscriptions(data: dict = None) -> List[dict]:
    data = data or load_providers()
    out = []
    for s in data.get("subscriptions") or []:
        if not s.get("enabled", True):
            continue
        if not _is_real_url(s.get("url", "")):
            continue
        out.append(s)
    return out

def enabled_nodes(data: dict = None) -> List[dict]:
    data = data or load_providers()
    out = []
    for n in data.get("nodes") or []:
        if not n.get("enabled", False):
            continue
        item = {k: v for k, v in n.items() if k != "enabled"}
        out.append(item)
    return out

def health_check(data: dict = None) -> dict:
    data = data or load_providers()
    return data.get("health_check") or {
        "enable": True,
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
    }

def clash_proxy_providers(data: dict = None) -> dict:
    data = data or load_providers()
    hc = health_check(data)
    providers = {}
    for s in enabled_subscriptions(data):
        name = s.get("name", {})
        if isinstance(name, dict):
            pname = name.get("zh") or name.get("en") or s.get("id", "sub")
        else:
            pname = str(name)
        providers[pname] = {
            "type": "http",
            "url": s["url"].strip(),
            "interval": s.get("interval", 86400),
            "path": f"./providers/{s.get('id', 'sub')}.yaml",
            "health-check": {
                "enable": hc.get("enable", True),
                "url": hc.get("url"),
                "interval": hc.get("interval", 300),
            },
        }
    return providers

def clash_inline_proxies(data: dict = None) -> List[dict]:
    return enabled_nodes(data)

def provider_names(data: dict = None) -> List[str]:
    return list(clash_proxy_providers(data).keys())

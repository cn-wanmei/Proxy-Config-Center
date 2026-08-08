#!/usr/bin/env python3
"""Load subscription + node placeholders from core/proxies/providers.yaml"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

CORE = Path(__file__).resolve().parents[2] / "core"

def load_yaml(path: Path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_providers() -> dict:
    return load_yaml(CORE / "proxies" / "providers.yaml")

def enabled_subscriptions(data: dict = None) -> List[dict]:
    data = data or load_providers()
    out = []
    for s in data.get("subscriptions") or []:
        if s.get("enabled", True):
            out.append(s)
    return out

def enabled_nodes(data: dict = None) -> List[dict]:
    data = data or load_providers()
    out = []
    for n in data.get("nodes") or []:
        if n.get("enabled", False):
            # strip internal flags
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
    """Build Clash/Meta proxy-providers mapping."""
    data = data or load_providers()
    hc = health_check(data)
    providers = {}
    for s in enabled_subscriptions(data):
        name = s.get("name", {})
        if isinstance(name, dict):
            pname = name.get("zh") or name.get("en") or s.get("id", "sub")
        else:
            pname = str(name)
        url = s.get("url") or "YOUR_SUBSCRIBE_URL"
        providers[pname] = {
            "type": "http",
            "url": url,
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
    data = data or load_providers()
    names = []
    for s in enabled_subscriptions(data):
        name = s.get("name", {})
        if isinstance(name, dict):
            names.append(name.get("zh") or name.get("en") or s.get("id"))
        else:
            names.append(str(name))
    return names

if __name__ == "__main__":
    d = load_providers()
    print("subs", len(enabled_subscriptions(d)), "nodes", len(enabled_nodes(d)))
    print("providers", list(clash_proxy_providers(d).keys()))

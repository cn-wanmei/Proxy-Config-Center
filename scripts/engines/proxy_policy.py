#!/usr/bin/env python3
"""
Proxy Policy V1
Resolve base + service proxy groups into display-ready policy lists.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

CORE = Path(__file__).resolve().parents[2] / "core"

def load_yaml(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def display_name(g: dict) -> str:
    name = g.get("name", {})
    if isinstance(name, dict):
        return name.get("zh") or name.get("en") or g.get("id", "unknown")
    return str(name)

def resolve_token(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)

def load_base_groups() -> List[dict]:
    data = load_yaml(CORE / "proxy-groups" / "base.yaml") or {}
    return data.get("groups") or []

def load_service_groups() -> List[dict]:
    data = load_yaml(CORE / "proxy-groups" / "service.yaml") or {}
    return data.get("groups") or []

def build_id_map(base: List[dict], services: List[dict]) -> Dict[str, str]:
    m = {"direct": "DIRECT", "reject": "REJECT"}
    for g in base + services:
        m[g["id"]] = display_name(g)
    return m

def expand_options(options: List[Any], id_to_display: Dict[str, str]) -> List[str]:
    out = []
    for o in options or []:
        if isinstance(o, dict):
            if "ref" in o:
                out.append(id_to_display.get(o["ref"], o["ref"]))
            elif "action" in o:
                act = o["action"]
                out.append("DIRECT" if act == "direct" else "REJECT" if act == "reject" else act)
        else:
            out.append(resolve_token(str(o), id_to_display))
    return out

def put_default_first(policies: List[str], default: str, id_to_display: Dict[str, str]) -> List[str]:
    if not default:
        return policies
    d = resolve_token(default, id_to_display)
    if d in policies:
        return [d] + [p for p in policies if p != d]
    return policies

def resolve_all() -> Tuple[List[dict], Dict[str, str]]:
    """Return list of {id, name, type, proxies, icon, ...} and id_to_display."""
    base = load_base_groups()
    services = load_service_groups()
    id_to_display = build_id_map(base, services)

    result = []
    for g in base:
        opts = g.get("options") or []
        proxies = expand_options(opts, id_to_display)
        entry = {
            "id": g["id"],
            "name": id_to_display[g["id"]],
            "type": g.get("type", "select"),
            "proxies": proxies,
            "include-all-nodes": g.get("include-all-nodes", False),
            "filter": g.get("filter"),
            "icon": g.get("icon"),
        }
        result.append(entry)

    for g in services:
        proxy_cfg = g.get("proxy") or {}
        options = proxy_cfg.get("options") or []
        default = proxy_cfg.get("default")
        proxies = expand_options(options, id_to_display)
        proxies = put_default_first(proxies, default, id_to_display)
        entry = {
            "id": g["id"],
            "name": id_to_display[g["id"]],
            "type": g.get("type", "select"),
            "proxies": proxies or ["DIRECT"],
            "dns": g.get("dns"),
            "icon": g.get("icon"),
        }
        result.append(entry)

    return result, id_to_display

if __name__ == "__main__":
    groups, m = resolve_all()
    print(f"Proxy Policy V1: {len(groups)} groups")
    for g in groups[:4]:
        print(f"  {g['name']}: {g['proxies'][:4]}")

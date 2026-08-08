#!/usr/bin/env python3
"""
Rule Engine V1
Load service rules, bind priority, produce ordered rule list for IR.
"""

from pathlib import Path
from typing import Any, Dict, List

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

def load_priority_map() -> Dict[str, int]:
    data = load_yaml(CORE / "rules" / "priority.yaml") or {}
    return {p["id"]: p.get("value", 999) for p in data.get("priority") or []}

def load_ordered_rules() -> List[dict]:
    """Return rules sorted by priority (ascending = higher priority)."""
    priority_map = load_priority_map()
    rules_dir = CORE / "rules" / "services"
    all_rules: List[dict] = []
    if not rules_dir.exists():
        return all_rules
    for f in sorted(rules_dir.glob("*.yaml")):
        data = load_yaml(f) or {}
        gid = data.get("group") or str(data.get("id", "")).replace("service-", "")
        order = priority_map.get(gid, 500)
        for r in data.get("rules") or []:
            item = dict(r)
            item["_group"] = data.get("group", gid)
            item["_priority"] = order
            item["_source"] = f.name
            all_rules.append(item)
    return sorted(all_rules, key=lambda x: (x.get("_priority", 999), x.get("_source", "")))

def emit_clash_rules(rules: List[dict], id_to_display: Dict[str, str]) -> List[str]:
    out: List[str] = []
    for r in rules:
        target = id_to_display.get(r.get("_group"), r.get("_group", "其它连接"))
        rtype = r.get("type", "")
        values = r.get("values") or []
        if rtype == "domain-suffix":
            for v in values:
                out.append(f"DOMAIN-SUFFIX,{v},{target}")
        elif rtype == "domain-keyword":
            for v in values:
                out.append(f"DOMAIN-KEYWORD,{v},{target}")
        elif rtype == "geosite":
            for v in values:
                out.append(f"GEOSITE,{v},{target}")
        elif rtype == "geoip":
            for v in values:
                no_res = ",no-resolve" if r.get("no_resolve") else ""
                out.append(f"GEOIP,{v},{target}{no_res}")
        elif rtype == "match":
            out.append(f"MATCH,{target}")
    if not any(x.startswith("MATCH,") for x in out):
        out.append(f"MATCH,{id_to_display.get('final', '其它连接')}")
    return out

if __name__ == "__main__":
    rules = load_ordered_rules()
    print(f"Rule Engine V1: {len(rules)} rules loaded")
    for r in rules[:5]:
        print(f"  p={r['_priority']} group={r['_group']} type={r.get('type')}")

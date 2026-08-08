#!/usr/bin/env python3
"""
Core → IR loader
Loads all Core YAML and builds Intermediate Representation.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"

def load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

@dataclass
class IR:
    config_base: dict = field(default_factory=dict)
    config_runtime: dict = field(default_factory=dict)
    dns_resolvers: dict = field(default_factory=dict)
    dns_groups: list = field(default_factory=list)
    dns_policies: list = field(default_factory=list)
    proxy_base: list = field(default_factory=list)
    proxy_service: list = field(default_factory=list)
    priority: list = field(default_factory=list)
    rules: list = field(default_factory=list)  # sorted by priority

def build_ir() -> IR:
    ir = IR()

    # Config
    ir.config_base = load_yaml(CORE / "config" / "base.yaml") or {}
    ir.config_runtime = load_yaml(CORE / "config" / "runtime.yaml") or {}

    # DNS
    resolvers = load_yaml(CORE / "dns" / "resolvers.yaml") or {}
    ir.dns_resolvers = resolvers.get("resolvers", {})
    groups = load_yaml(CORE / "dns" / "groups.yaml") or {}
    ir.dns_groups = groups.get("groups", [])
    policies = load_yaml(CORE / "dns" / "policies.yaml") or {}
    ir.dns_policies = policies.get("policies", [])

    # Proxy groups
    base = load_yaml(CORE / "proxy-groups" / "base.yaml") or {}
    ir.proxy_base = base.get("groups", [])
    service = load_yaml(CORE / "proxy-groups" / "service.yaml") or {}
    ir.proxy_service = service.get("groups", [])

    # Priority
    prio = load_yaml(CORE / "rules" / "priority.yaml") or {}
    ir.priority = sorted(prio.get("priority", []), key=lambda x: x.get("value", 999))

    # Rules - load all service rule files and sort by priority map
    priority_map = {p["id"]: p.get("value", 999) for p in ir.priority}
    group_map = {p["id"]: p.get("group", p["id"]) for p in ir.priority}

    rules_dir = CORE / "rules" / "services"
    all_rules = []
    if rules_dir.exists():
        for f in rules_dir.glob("*.yaml"):
            data = load_yaml(f)
            if not data:
                continue
            gid = data.get("group") or data.get("id", "").replace("service-", "")
            order = priority_map.get(gid, 500)
            for r in data.get("rules", []):
                r["_group"] = data.get("group", gid)
                r["_priority"] = order
                all_rules.append(r)

    ir.rules = sorted(all_rules, key=lambda x: x.get("_priority", 999))
    return ir

if __name__ == "__main__":
    ir = build_ir()
    print(f"Loaded IR: {len(ir.proxy_base)} base groups, {len(ir.proxy_service)} service groups, {len(ir.rules)} rules")

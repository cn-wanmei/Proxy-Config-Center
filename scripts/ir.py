#!/usr/bin/env python3
"""Core → Resolved IR with ResolvedRuleSource."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
class ResolvedService:
    id: str
    name_zh: str
    name_en: str
    type: str
    proxy_options: List[str]
    proxy_default: str
    dns_policy_id: str
    dns_default_resolver: str
    dns_options: List[str]
    icon: str
    rule_source_id: str = ""

@dataclass
class ResolvedRuleSource:
    id: str
    target_service: str
    geosite: List[str] = field(default_factory=list)
    geoip: List[str] = field(default_factory=list)
    domain_suffix: List[str] = field(default_factory=list)
    domain_keyword: List[str] = field(default_factory=list)
    blackmatrix7_path: Optional[str] = None
    blackmatrix7_behavior: str = "classical"
    blackmatrix7_url: Optional[str] = None
    is_match: bool = False
    priority: int = 500

@dataclass
class ResolvedIR:
    config_base: dict = field(default_factory=dict)
    config_runtime: dict = field(default_factory=dict)
    resolvers: Dict[str, dict] = field(default_factory=dict)
    dns_groups: Dict[str, dict] = field(default_factory=dict)
    dns_policies: Dict[str, dict] = field(default_factory=dict)
    base_groups: List[dict] = field(default_factory=list)
    services: List[ResolvedService] = field(default_factory=list)
    rules: List[dict] = field(default_factory=list)
    priority: List[dict] = field(default_factory=list)
    rule_sources: List[ResolvedRuleSource] = field(default_factory=list)
    blackmatrix7_base: str = ""
    id_to_display: Dict[str, str] = field(default_factory=dict)

def _display_name(g: dict) -> str:
    name = g.get("name", {})
    if isinstance(name, dict):
        return name.get("zh") or name.get("en") or g.get("id", "unknown")
    return str(name)

def build_ir() -> ResolvedIR:
    ir = ResolvedIR()
    ir.config_base = load_yaml(CORE / "config" / "base.yaml") or {}
    ir.config_runtime = load_yaml(CORE / "config" / "runtime.yaml") or {}

    resolvers_data = load_yaml(CORE / "dns" / "resolvers.yaml") or {}
    ir.resolvers = resolvers_data.get("resolvers") or {}

    groups_data = load_yaml(CORE / "dns" / "groups.yaml") or {}
    for g in groups_data.get("groups") or []:
        ir.dns_groups[g["id"]] = g

    policies_data = load_yaml(CORE / "dns" / "policies.yaml") or {}
    for p in policies_data.get("policies") or []:
        ir.dns_policies[p["id"]] = p

    base = load_yaml(CORE / "proxy-groups" / "base.yaml") or {}
    ir.base_groups = base.get("groups") or []
    for g in ir.base_groups:
        ir.id_to_display[g["id"]] = _display_name(g)

    svc_data = load_yaml(CORE / "proxy-groups" / "service.yaml") or {}
    services_raw = svc_data.get("groups") or []

    pri_data = load_yaml(CORE / "rules" / "priority.yaml") or {}
    ir.priority = pri_data.get("priority") or []
    pri_map = {p["id"]: p.get("value", 999) for p in ir.priority}

    for g in services_raw:
        sid = g["id"]
        name = g.get("name", {})
        zh = name.get("zh", sid) if isinstance(name, dict) else str(name)
        en = name.get("en", sid) if isinstance(name, dict) else str(name)
        ir.id_to_display[sid] = zh

        proxy_cfg = g.get("proxy") or {}
        options = list(proxy_cfg.get("options") or [])
        default = proxy_cfg.get("default") or (options[0] if options else "proxy-mode")

        dns_id = g.get("dns") or "dns-foreign"
        if isinstance(dns_id, dict):
            dns_id = dns_id.get("policy") or "dns-foreign"
        policy = ir.dns_policies.get(dns_id) or {}

        ir.services.append(ResolvedService(
            id=sid, name_zh=zh, name_en=en, type=g.get("type", "select"),
            proxy_options=options, proxy_default=default,
            dns_policy_id=dns_id,
            dns_default_resolver=policy.get("default") or "cloudflare",
            dns_options=list(policy.get("options") or []),
            icon=g.get("icon") or "",
            rule_source_id=sid,
        ))

    src_data = load_yaml(CORE / "rules" / "sources.yaml") or {}
    ir.blackmatrix7_base = src_data.get("blackmatrix7_base") or (
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash"
    )
    sources = src_data.get("sources") or {}
    for sid in sorted(sources.keys(), key=lambda i: pri_map.get(i, 500)):
        meta = sources[sid] or {}
        bm = meta.get("blackmatrix7") or {}
        if isinstance(bm, str):
            bm_path, bm_beh = bm, "classical"
        else:
            bm_path = bm.get("path")
            bm_beh = bm.get("behavior") or "classical"
        bm_url = f"{ir.blackmatrix7_base}/{bm_path}" if bm_path else None
        ir.rule_sources.append(ResolvedRuleSource(
            id=sid, target_service=sid,
            geosite=list(meta.get("geosite") or []),
            geoip=list(meta.get("geoip") or []),
            domain_suffix=list(meta.get("domain_suffix") or []),
            domain_keyword=list(meta.get("domain_keyword") or []),
            blackmatrix7_path=bm_path,
            blackmatrix7_behavior=bm_beh,
            blackmatrix7_url=bm_url,
            is_match=bool(meta.get("match")),
            priority=pri_map.get(sid, 500),
        ))

    rules_dir = CORE / "rules" / "services"
    all_rules = []
    if rules_dir.exists():
        for f in sorted(rules_dir.glob("*.yaml")):
            data = load_yaml(f) or {}
            gid = data.get("group") or str(data.get("id", "")).replace("service-", "")
            for r in data.get("rules") or []:
                item = dict(r)
                item["_group"] = gid
                item["_priority"] = pri_map.get(gid, 500)
                all_rules.append(item)
    ir.rules = sorted(all_rules, key=lambda x: x.get("_priority", 999))
    return ir

if __name__ == "__main__":
    ir = build_ir()
    print(f"services={len(ir.services)} sources={len(ir.rule_sources)}")
    for rs in ir.rule_sources[:4]:
        print(f"  p={rs.priority} {rs.id} gs={rs.geosite} bm={rs.blackmatrix7_path}")

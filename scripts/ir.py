#!/usr/bin/env python3
"""Core → Resolved IR — rules, references, groups, icons, and capabilities."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from engines.capability import (
    all_platforms,
    required_platforms,
    supports_domain_fallback,
    supports_rule_provider,
    supports_rule_set,
)
from engines.utils import load_yaml

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"


@dataclass
class IconRef:
    id: str
    url: str = ""


@dataclass
class ProxyGroup:
    id: str
    name_zh: str
    name_en: str
    type: str
    options: List[Any] = field(default_factory=list)
    default: str = ""
    include_all_nodes: bool = False
    filter: str = ""
    icon: str = ""


@dataclass
class Node:
    id: str
    name: str
    type: str
    options: Dict[str, Any] = field(default_factory=dict)


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
class BMSet:
    key: str
    path: str
    url: str
    behavior: str = "classical"
    sha256: str = ""


@dataclass
class ResolvedRuleSource:
    id: str
    target_service: str
    bm_sets: List[BMSet] = field(default_factory=list)
    domain_suffix: List[str] = field(default_factory=list)
    domain_keyword: List[str] = field(default_factory=list)
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
    proxy_groups: List[ProxyGroup] = field(default_factory=list)
    services: List[ResolvedService] = field(default_factory=list)
    nodes: List[Node] = field(default_factory=list)
    icons: Dict[str, IconRef] = field(default_factory=dict)
    rules: List[dict] = field(default_factory=list)
    priority: List[dict] = field(default_factory=list)
    rule_sources: List[ResolvedRuleSource] = field(default_factory=list)
    blackmatrix7_base: str = ""
    id_to_display: Dict[str, str] = field(default_factory=dict)
    platform_capabilities: Dict[str, dict] = field(default_factory=dict)
    platform_rule_set: Dict[str, bool] = field(default_factory=dict)
    platform_rule_provider: Dict[str, bool] = field(default_factory=dict)
    platform_domain_fallback: Dict[str, bool] = field(default_factory=dict)


def _display_name(g: dict) -> str:
    name = g.get("name", {})
    if isinstance(name, dict):
        return name.get("zh") or name.get("en") or g.get("id", "unknown")
    return str(name)


def _parse_bm(base: str, key: str, bm: Any) -> Optional[BMSet]:
    if not bm:
        return None
    if isinstance(bm, str):
        path, beh, sha256 = bm, "classical", ""
    else:
        path = bm.get("path")
        beh = bm.get("behavior") or "classical"
        sha256 = bm.get("sha256") or ""
    if not path:
        return None
    return BMSet(key=key, path=path, url=f"{base}/{path}", behavior=beh, sha256=sha256)


def _load_dns(ir: ResolvedIR) -> None:
    resolvers_data = load_yaml(CORE / "dns" / "resolvers.yaml")
    ir.resolvers = resolvers_data.get("resolvers") or {}
    groups_data = load_yaml(CORE / "dns" / "groups.yaml")
    ir.dns_groups = {g["id"]: g for g in groups_data.get("groups") or []}
    policies_data = load_yaml(CORE / "dns" / "policies.yaml")
    ir.dns_policies = {p["id"]: p for p in policies_data.get("policies") or []}


def _load_groups(ir: ResolvedIR) -> None:
    base = load_yaml(CORE / "proxy-groups" / "base.yaml")
    ir.base_groups = base.get("groups") or []
    for g in ir.base_groups:
        gid = g["id"]
        ir.id_to_display[gid] = _display_name(g)
        name = g.get("name", {})
        ir.proxy_groups.append(ProxyGroup(
            id=gid,
            name_zh=name.get("zh", gid) if isinstance(name, dict) else str(name),
            name_en=name.get("en", gid) if isinstance(name, dict) else str(name),
            type=g.get("type", "select"),
            options=list(g.get("options") or []),
            default=g.get("default") or "",
            include_all_nodes=bool(g.get("include-all-nodes")),
            filter=g.get("filter") or "",
            icon=g.get("icon") or "",
        ))


def _load_services(ir: ResolvedIR) -> None:
    svc_data = load_yaml(CORE / "proxy-groups" / "service.yaml")
    pri_data = load_yaml(CORE / "rules" / "priority.yaml")
    ir.priority = pri_data.get("priority") or []
    for g in svc_data.get("groups") or []:
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


def _load_nodes(ir: ResolvedIR) -> None:
    providers = load_yaml(CORE / "proxies" / "providers.yaml")
    for node in providers.get("nodes") or []:
        if not node.get("enabled", False):
            continue
        nid = str(node.get("id") or node.get("name") or "node")
        name = str(node.get("name") or nid)
        ntype = str(node.get("type") or "")
        ir.nodes.append(Node(id=nid, name=name, type=ntype, options=dict(node)))


def _load_rule_sources(ir: ResolvedIR) -> None:
    src_data = load_yaml(CORE / "rules" / "sources.yaml")
    ir.blackmatrix7_base = src_data.get("blackmatrix7_base") or (
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash"
    )
    sources = src_data.get("sources") or {}
    pri_map = {p["id"]: p.get("value", 999) for p in ir.priority}
    for sid in sorted(sources.keys(), key=lambda i: pri_map.get(i, 500)):
        meta = sources[sid] or {}
        bm_sets: List[BMSet] = []
        primary = _parse_bm(ir.blackmatrix7_base, sid, meta.get("blackmatrix7"))
        if primary:
            bm_sets.append(primary)
        for i, extra in enumerate(meta.get("blackmatrix7_extra") or []):
            es = _parse_bm(ir.blackmatrix7_base, f"{sid}-extra{i}", extra)
            if es:
                bm_sets.append(es)
        ir.rule_sources.append(ResolvedRuleSource(
            id=sid, target_service=sid, bm_sets=bm_sets,
            domain_suffix=list(meta.get("domain_suffix") or []),
            domain_keyword=list(meta.get("domain_keyword") or []),
            is_match=bool(meta.get("match")),
            priority=pri_map.get(sid, 500),
        ))


def _load_rules(ir: ResolvedIR) -> None:
    pri_map = {p["id"]: p.get("value", 999) for p in ir.priority}
    rules_dir = CORE / "rules" / "services"
    all_rules = []
    if rules_dir.exists():
        for f in sorted(rules_dir.glob("*.yaml")):
            data = load_yaml(f)
            gid = data.get("group") or str(data.get("id", "")).replace("service-", "")
            for r in data.get("rules") or []:
                if r.get("type") in ("geosite", "geoip"):
                    continue
                item = dict(r)
                item["_group"] = gid
                item["_priority"] = pri_map.get(gid, 500)
                all_rules.append(item)
    ir.rules = sorted(all_rules, key=lambda x: x.get("_priority", 999))


def _load_platforms(ir: ResolvedIR) -> None:
    ir.platform_capabilities = all_platforms()
    for name in required_platforms():
        ir.platform_rule_set[name] = supports_rule_set(name)
        ir.platform_rule_provider[name] = supports_rule_provider(name)
        ir.platform_domain_fallback[name] = supports_domain_fallback(name)


def build_ir() -> ResolvedIR:
    ir = ResolvedIR()
    ir.config_base = load_yaml(CORE / "config" / "base.yaml")
    ir.config_runtime = load_yaml(CORE / "config" / "runtime.yaml")
    _load_dns(ir)
    _load_groups(ir)
    _load_services(ir)
    _load_nodes(ir)
    _load_rule_sources(ir)
    _load_rules(ir)
    _load_platforms(ir)
    return ir


if __name__ == "__main__":
    ir = build_ir()
    print(f"services={len(ir.services)} nodes={len(ir.nodes)} sources={len(ir.rule_sources)}")
    print("platform_rule_set:", ir.platform_rule_set)
    print("platform_rule_provider:", ir.platform_rule_provider)
    print("platform_domain_fallback:", ir.platform_domain_fallback)

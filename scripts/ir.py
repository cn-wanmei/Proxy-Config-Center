#!/usr/bin/env python3
"""Core → Resolved IR — rules, references, and platform capabilities."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import (
    all_platforms,
    supports_domain_fallback,
    supports_rule_provider,
    supports_rule_set,
    REQUIRED_PLATFORMS,
)


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"missing core file: {path}")
    with path.open(encoding="utf-8") as f:
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
    services: List[ResolvedService] = field(default_factory=list)
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
    pri_data = load_yaml(CORE / "rules" / "priority.yaml") or {}
    ir.priority = pri_data.get("priority") or []
    pri_map = {p["id"]: p.get("value", 999) for p in ir.priority}

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

    src_data = load_yaml(CORE / "rules" / "sources.yaml") or {}
    ir.blackmatrix7_base = src_data.get("blackmatrix7_base") or (
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash"
    )
    sources = src_data.get("sources") or {}

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
            id=sid, target_service=sid,
            bm_sets=bm_sets,
            domain_suffix=list(meta.get("domain_suffix") or []),
            domain_keyword=list(meta.get("domain_keyword") or []),
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
                if r.get("type") in ("geosite", "geoip"):
                    continue
                item = dict(r)
                item["_group"] = gid
                item["_priority"] = pri_map.get(gid, 500)
                all_rules.append(item)
    ir.rules = sorted(all_rules, key=lambda x: x.get("_priority", 999))

    ir.platform_capabilities = all_platforms()
    for name in REQUIRED_PLATFORMS:
        ir.platform_rule_set[name] = supports_rule_set(name)
        ir.platform_rule_provider[name] = supports_rule_provider(name)
        ir.platform_domain_fallback[name] = supports_domain_fallback(name)

    return ir


if __name__ == "__main__":
    ir = build_ir()
    print(f"services={len(ir.services)} sources={len(ir.rule_sources)}")
    print("platform_rule_set:", ir.platform_rule_set)
    print("platform_rule_provider:", ir.platform_rule_provider)
    print("platform_domain_fallback:", ir.platform_domain_fallback)

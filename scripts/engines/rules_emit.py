#!/usr/bin/env python3
"""Emit rules from IR.rule_sources using platform capabilities."""

from typing import Any, Dict, List, Tuple


def _target(rs, id_to_display: Dict[str, str]) -> str:
    return id_to_display.get(rs.target_service, rs.target_service)


def _has_bm(rs) -> bool:
    return bool(getattr(rs, "bm_sets", None))


def emit_clash_style(ir: Any, id_to_display: Dict[str, str], use_rule_set: bool) -> Tuple[dict, List[str]]:
    rule_providers: dict = {}
    rules: List[str] = []

    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = _target(rs, id_to_display)

        if use_rule_set and _has_bm(rs):
            for bm in rs.bm_sets:
                rule_providers[bm.key] = {
                    "type": "http",
                    "behavior": bm.behavior or "classical",
                    "url": bm.url,
                    "path": f"./ruleset/{bm.key}.yaml",
                    "interval": 86400,
                }
                rules.append(f"RULE-SET,{bm.key},{target}")
            # no bulk domain when remote set present
            continue

        for d in rs.domain_suffix:
            rules.append(f"DOMAIN-SUFFIX,{d},{target}")
        for d in rs.domain_keyword:
            rules.append(f"DOMAIN-KEYWORD,{d},{target}")

    rules.append(f"MATCH,{id_to_display.get('final', '其它连接')}")
    return rule_providers, rules


def emit_loon_style(ir: Any, id_to_display: Dict[str, str], use_rule_set: bool) -> List[str]:
    lines: List[str] = []
    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = _target(rs, id_to_display)
        if use_rule_set and _has_bm(rs):
            for bm in rs.bm_sets:
                url = bm.url
                if "/rule/Clash/" in url and url.endswith(".yaml"):
                    url = url.replace("/rule/Clash/", "/rule/Loon/").replace(".yaml", ".list")
                lines.append(f"DOMAIN-SET,{url},{target}")
            continue
        for d in rs.domain_suffix:
            lines.append(f"DOMAIN-SUFFIX,{d},{target}")
        for d in rs.domain_keyword:
            lines.append(f"DOMAIN-KEYWORD,{d},{target}")
    lines.append(f"FINAL,{id_to_display.get('final', '其它连接')}")
    return lines


def emit_egern_style(ir: Any, id_to_display: Dict[str, str], use_rule_set: bool) -> List[dict]:
    rules: List[dict] = []
    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = _target(rs, id_to_display)
        if use_rule_set and _has_bm(rs):
            for bm in rs.bm_sets:
                rules.append({"rule_set": {"url": bm.url, "policy": target}})
            # skip domain bulk when remote set exists
            continue
        for d in rs.domain_suffix:
            rules.append({"domain_suffix": {"match": d, "policy": target}})
        for d in rs.domain_keyword:
            rules.append({"domain_keyword": {"match": d, "policy": target}})
    rules.append({"default": {"policy": id_to_display.get("final", "其它连接")}})
    return rules


def emit_shadowrocket_style(ir: Any, id_to_display: Dict[str, str]) -> List[str]:
    lines: List[str] = []
    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = _target(rs, id_to_display)
        for d in rs.domain_suffix:
            lines.append(f"DOMAIN-SUFFIX,{d},{target}")
        for d in rs.domain_keyword:
            lines.append(f"DOMAIN-KEYWORD,{d},{target}")
    lines.append(f"FINAL,{id_to_display.get('final', '其它连接')}")
    return lines

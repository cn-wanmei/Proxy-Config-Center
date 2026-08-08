#!/usr/bin/env python3
"""
Emit platform rules from IR.rule_sources using capabilities:
  rule_set supported → remote blackmatrix7 providers
  otherwise         → domain_suffix / domain_keyword fallback
"""

from typing import Any, Dict, List, Tuple


def _target(rs, id_to_display: Dict[str, str]) -> str:
    return id_to_display.get(rs.target_service, rs.target_service)


def emit_clash_style(ir: Any, id_to_display: Dict[str, str], use_rule_set: bool) -> Tuple[dict, List[str]]:
    """Returns (rule_providers, rules lines) for Clash / Meta / Stash."""
    rule_providers: dict = {}
    rules: List[str] = []

    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = _target(rs, id_to_display)

        if use_rule_set and getattr(rs, "bm_sets", None):
            for bm in rs.bm_sets:
                rule_providers[bm.key] = {
                    "type": "http",
                    "behavior": bm.behavior or "classical",
                    "url": bm.url,
                    "path": f"./ruleset/{bm.key}.yaml",
                    "interval": 86400,
                }
                rules.append(f"RULE-SET,{bm.key},{target}")
        else:
            for d in rs.domain_suffix:
                rules.append(f"DOMAIN-SUFFIX,{d},{target}")
            for d in rs.domain_keyword:
                rules.append(f"DOMAIN-KEYWORD,{d},{target}")

    rules.append(f"MATCH,{id_to_display.get('final', '其它连接')}")
    return rule_providers, rules


def emit_loon_style(ir: Any, id_to_display: Dict[str, str], use_rule_set: bool) -> List[str]:
    """Loon [Rule] lines."""
    lines: List[str] = []
    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = _target(rs, id_to_display)
        if use_rule_set and getattr(rs, "bm_sets", None):
            # Loon remote domain-set (blackmatrix7 Clash classical still works as list for many clients)
            for bm in rs.bm_sets:
                # Prefer Loon path if URL contains /Clash/ → swap to /Loon/ .list when possible
                url = bm.url
                if "/rule/Clash/" in url and url.endswith(".yaml"):
                    # domain-set URL: use same repo Loon list if exists pattern
                    loon_url = url.replace("/rule/Clash/", "/rule/Loon/").replace(".yaml", ".list")
                    lines.append(f"DOMAIN-SET,{loon_url},{target}")
                else:
                    lines.append(f"DOMAIN-SET,{url},{target}")
        for d in rs.domain_suffix:
            lines.append(f"DOMAIN-SUFFIX,{d},{target}")
        for d in rs.domain_keyword:
            lines.append(f"DOMAIN-KEYWORD,{d},{target}")
    lines.append(f"FINAL,{id_to_display.get('final', '其它连接')}")
    return lines


def emit_egern_style(ir: Any, id_to_display: Dict[str, str], use_rule_set: bool) -> List[dict]:
    """Egern rules list (dict form). Egern prefers domain rules; optional rule_set if supported."""
    rules: List[dict] = []
    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match:
            continue
        target = _target(rs, id_to_display)
        if use_rule_set and getattr(rs, "bm_sets", None):
            for bm in rs.bm_sets:
                rules.append({
                    "rule_set": {
                        "url": bm.url,
                        "policy": target,
                    }
                })
        for d in rs.domain_suffix:
            rules.append({"domain_suffix": {"match": d, "policy": target}})
        for d in rs.domain_keyword:
            rules.append({"domain_keyword": {"match": d, "policy": target}})
    rules.append({"default": {"policy": id_to_display.get("final", "其它连接")}})
    return rules


def emit_shadowrocket_style(ir: Any, id_to_display: Dict[str, str]) -> List[str]:
    """Shadowrocket: always domain fallback (no rule_provider)."""
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

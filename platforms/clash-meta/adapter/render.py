#!/usr/bin/env python3
"""Clash Meta Renderer — geosite/rule-set, selectable DNS, no placeholder subs."""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import yaml
except ImportError:
    yaml = None

try:
    from engines.icons import icon_url
except Exception:
    def icon_url(name):
        return name if name and str(name).startswith("http") else None

try:
    from engines.proxies import (
        load_providers,
        clash_proxy_providers,
        clash_inline_proxies,
        provider_names,
    )
except Exception:
    def load_providers():
        return {}
    def clash_proxy_providers(data=None):
        return {}
    def clash_inline_proxies(data=None):
        return []
    def provider_names(data=None):
        return []


def _load_rule_providers_map() -> dict:
    path = ROOT / "core" / "rules" / "rule-providers.yaml"
    if not path.exists() or not yaml:
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _resolve_proxy_ref(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


def render(ir: Any) -> dict:
    id_to_display = dict(getattr(ir, "id_to_display", {}) or {})
    pdata = load_providers()
    pnames = provider_names(pdata)
    inline_proxies = clash_inline_proxies(pdata)
    providers = clash_proxy_providers(pdata)

    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        display = name.get("zh") if isinstance(name, dict) else str(name)
        id_to_display[g["id"]] = display or g["id"]

    proxy_groups: List[dict] = []

    for g in getattr(ir, "base_groups", []) or []:
        entry = {
            "name": id_to_display.get(g["id"], g["id"]),
            "type": g.get("type", "select"),
        }
        if g.get("include-all-nodes") or g["id"] in ("manual-select", "auto-select", "free-flow"):
            if pnames:
                entry["include-all-providers"] = True
                entry["use"] = list(pnames)
            if inline_proxies:
                entry["proxies"] = [n["name"] for n in inline_proxies if n.get("name")]
            if not entry.get("proxies") and not pnames:
                # 无订阅时仅留空组结构，用 DIRECT 占位避免客户端报错
                entry["proxies"] = ["DIRECT"]
            if g.get("filter"):
                entry["filter"] = g["filter"]
            if g.get("type") == "url-test":
                entry["url"] = "http://www.gstatic.com/generate_204"
                entry["interval"] = 300
        else:
            proxies = []
            for o in g.get("options") or []:
                if isinstance(o, dict):
                    if "ref" in o:
                        proxies.append(id_to_display.get(o["ref"], o["ref"]))
                    elif "action" in o:
                        act = o["action"]
                        proxies.append(
                            "DIRECT" if act == "direct" else "REJECT" if act == "reject" else act
                        )
                else:
                    proxies.append(_resolve_proxy_ref(str(o), id_to_display))
            if proxies:
                entry["proxies"] = proxies

        iu = icon_url(g.get("icon"))
        if iu:
            entry["icon"] = iu
        proxy_groups.append(entry)

    for s in getattr(ir, "services", []) or []:
        if hasattr(s, "id"):
            sid, name_zh = s.id, s.name_zh
            options, default = s.proxy_options, s.proxy_default
            icon, gtype = s.icon, s.type
        else:
            sid = s["id"]
            name = s.get("name", {})
            name_zh = name.get("zh", sid) if isinstance(name, dict) else str(name)
            proxy_cfg = s.get("proxy") or {}
            options = proxy_cfg.get("options") or []
            default = proxy_cfg.get("default") or (options[0] if options else "proxy-mode")
            icon = s.get("icon", "")
            gtype = s.get("type", "select")

        id_to_display[sid] = name_zh
        proxies = [_resolve_proxy_ref(o, id_to_display) for o in options]
        if default:
            dname = _resolve_proxy_ref(default, id_to_display)
            if dname in proxies:
                proxies = [dname] + [p for p in proxies if p != dname]

        entry = {"name": name_zh, "type": gtype, "proxies": proxies or ["DIRECT"]}
        iu = icon_url(icon)
        if iu:
            entry["icon"] = iu
        proxy_groups.append(entry)

    # ---- DNS 可选手动：全部 resolvers 列入 nameserver，不写死单域名策略 ----
    resolvers = getattr(ir, "resolvers", {}) or {}
    nameserver = []
    for rid in ("alidns", "tencent", "google", "cloudflare"):
        r = resolvers.get(rid) or {}
        for s in r.get("servers") or []:
            if s not in nameserver:
                nameserver.append(s)
    if not nameserver:
        nameserver = [
            "https://dns.alidns.com/dns-query",
            "https://cloudflare-dns.com/dns-query",
            "https://dns.google/dns-query",
        ]

    # ---- rule-providers (blackmatrix7) + GEOSITE/GEOIP rules ----
    rp_meta = _load_rule_providers_map()
    base_url = rp_meta.get("base_url") or (
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash"
    )
    rule_providers = {}
    rules: List[str] = []

    # priority order from IR services order
    for s in getattr(ir, "services", []) or []:
        sid = s.id if hasattr(s, "id") else s["id"]
        target = id_to_display.get(sid, sid)
        meta = (rp_meta.get("providers") or {}).get(sid) or {}

        for gs in meta.get("geosite") or []:
            rules.append(f"GEOSITE,{gs},{target}")
        for gi in meta.get("geoip") or []:
            rules.append(f"GEOIP,{gi},{target},no-resolve")

        bm = meta.get("blackmatrix7")
        if bm:
            pname = sid
            rule_providers[pname] = {
                "type": "http",
                "behavior": meta.get("behavior") or "classical",
                "url": f"{base_url}/{bm}",
                "path": f"./ruleset/{pname}.yaml",
                "interval": 86400,
            }
            rules.append(f"RULE-SET,{pname},{target}")

        for d in meta.get("domains") or []:
            rules.append(f"DOMAIN-SUFFIX,{d},{target}")

    # IR domain rules as supplement (skip if already covered heavily)
    for r in getattr(ir, "rules", []) or []:
        target = id_to_display.get(r.get("_group"), r.get("_group", "其它连接"))
        rtype = r.get("type", "")
        values = r.get("values") or []
        if rtype == "match":
            continue
        if rtype == "domain-suffix":
            for v in values:
                line = f"DOMAIN-SUFFIX,{v},{target}"
                if line not in rules:
                    rules.append(line)

    rules.append(f"MATCH,{id_to_display.get('final', '其它连接')}")

    config = {
        "mixed-port": 7890,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "ipv6": True,
        "dns": {
            "enable": True,
            "ipv6": True,
            "enhanced-mode": "fake-ip",
            "fake-ip-range": "198.18.0.1/16",
            # 多上游并列，客户端/内核按序或策略选用，不写死单域名绑定
            "nameserver": nameserver,
            "default-nameserver": ["223.5.5.5", "119.29.29.29", "1.1.1.1"],
        },
        "proxy-groups": proxy_groups,
        "rule-providers": rule_providers,
        "rules": rules,
    }

    # 仅在有真实订阅时写入 proxy-providers
    if providers:
        config["proxy-providers"] = providers
    if inline_proxies:
        config["proxies"] = inline_proxies

    return config

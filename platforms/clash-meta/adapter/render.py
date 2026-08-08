#!/usr/bin/env python3
"""Clash Meta Renderer — clean subs, selectable DNS, geosite rules, icons."""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

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


def _resolve_proxy_ref(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)


def _resolver_to_clash(resolver_id: str, resolvers: dict) -> List[str]:
    r = resolvers.get(resolver_id) or {}
    if r.get("type") == "system":
        return ["system"]
    return list(r.get("servers") or []) or ["system"]


# blackmatrix7 rule-provider URLs (Clash format) when geosite missing
RULE_PROVIDER_URLS = {
    "Apple": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Apple/Apple.yaml",
    "OpenAI": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/OpenAI/OpenAI.yaml",
    "GitHub": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/GitHub/GitHub.yaml",
    "Microsoft": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Microsoft/Microsoft.yaml",
    "Telegram": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Telegram/Telegram.yaml",
    "Twitter": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Twitter/Twitter.yaml",
    "Netflix": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Netflix/Netflix.yaml",
    "TikTok": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/TikTok/TikTok.yaml",
    "Spotify": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Spotify/Spotify.yaml",
    "YouTube": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/YouTube/YouTube.yaml",
    "Google": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Google/Google.yaml",
    "Steam": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Steam/Steam.yaml",
    "Advertising": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Advertising/Advertising.yaml",
}

# service id → rule-provider name + target group display key
SERVICE_RULE_PROVIDER = {
    "apple": ("Apple", "苹果服务"),
    "ai": ("OpenAI", "人工智能"),
    "github": ("GitHub", "代码仓库"),
    "microsoft": ("Microsoft", "微软服务"),
    "telegram": ("Telegram", "电报通讯"),
    "twitter": ("Twitter", "推特社交"),
    "netflix": ("Netflix", "奈飞影视"),
    "tiktok": ("TikTok", "抖音国际"),
    "spotify": ("Spotify", "声破天乐"),
    "youtube": ("YouTube", "油管视频"),
    "google": ("Google", "谷歌服务"),
    "game": ("Steam", "游戏平台"),
    "ad-block": ("Advertising", "广告拦截"),
}


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

    # ---- Selectable DNS policy groups (手动选择 DNS) ----
    resolvers = getattr(ir, "resolvers", {}) or {}
    dns_options = []
    for rid in ("system", "alidns", "tencent", "google", "cloudflare"):
        if rid in resolvers or rid == "system":
            label = {
                "system": "系统DNS",
                "alidns": "阿里DNS",
                "tencent": "腾讯DNS",
                "google": "谷歌DNS",
                "cloudflare": "CF DNS",
            }.get(rid, rid)
            dns_options.append(label)
    # Virtual select group for UI (Clash can't switch nameserver live easily;
    # we expose named groups users can reference; default nameserver stays flexible)
    # Actual DNS: only nameserver list, NO hard-coded nameserver-policy

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
                # no nodes yet — empty select with DIRECT only (clean)
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

    # DNS 手动选择策略组（仅作策略入口，不写死 nameserver-policy）
    proxy_groups.append({
        "name": "DNS选择",
        "type": "select",
        "proxies": dns_options or ["系统DNS", "阿里DNS", "腾讯DNS", "谷歌DNS", "CF DNS"],
        "icon": icon_url("auto") or "",
    })

    rules: List[str] = []
    # RULE-SET from blackmatrix7 first (higher priority coverage)
    for sid, (rp_name, target) in SERVICE_RULE_PROVIDER.items():
        target = id_to_display.get(sid, target)
        rules.append(f"RULE-SET,{rp_name},{target}")

    for r in getattr(ir, "rules", []) or []:
        target = id_to_display.get(r.get("_group"), r.get("_group", "其它连接"))
        rtype = r.get("type", "")
        values = r.get("values") or []
        if rtype == "domain-suffix":
            for v in values:
                rules.append(f"DOMAIN-SUFFIX,{v},{target}")
        elif rtype == "domain-keyword":
            for v in values:
                rules.append(f"DOMAIN-KEYWORD,{v},{target}")
        elif rtype == "geosite":
            for v in values:
                rules.append(f"GEOSITE,{v},{target}")
        elif rtype == "geoip":
            for v in values:
                no_res = ",no-resolve" if r.get("no_resolve") else ""
                rules.append(f"GEOIP,{v},{target}{no_res}")
        elif rtype == "match":
            rules.append(f"MATCH,{target}")

    if not any(x.startswith("MATCH,") for x in rules):
        rules.append(f"MATCH,{id_to_display.get('final', '其它连接')}")

    # DNS: only nameserver candidates — user selects via client / DNS选择 group
    # No hard-coded nameserver-policy
    nameserver = []
    for rid in ("cloudflare", "google", "alidns", "tencent"):
        nameserver.extend(_resolver_to_clash(rid, resolvers))
    # dedupe keep order
    seen = set()
    ns = []
    for x in nameserver:
        if x not in seen and x != "system":
            seen.add(x)
            ns.append(x)
    if not ns:
        ns = ["https://cloudflare-dns.com/dns-query", "https://dns.alidns.com/dns-query"]

    rule_providers = {}
    for name, url in RULE_PROVIDER_URLS.items():
        rule_providers[name] = {
            "type": "http",
            "behavior": "classical",
            "url": url,
            "path": f"./ruleset/{name}.yaml",
            "interval": 86400,
        }

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
            "nameserver": ns,
            # nameserver-policy 不写死，由用户在客户端按需配置
        },
        "proxy-groups": proxy_groups,
        "rule-providers": rule_providers,
        "rules": rules,
    }

    # 仅有真实订阅时才写入 proxy-providers
    if providers:
        config["proxy-providers"] = providers
    if inline_proxies:
        config["proxies"] = inline_proxies

    # clean empty icon
    for g in config["proxy-groups"]:
        if not g.get("icon"):
            g.pop("icon", None)

    return config

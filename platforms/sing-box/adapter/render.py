#!/usr/bin/env python3
"""sing-box renderer: Core/IR -> native JSON configuration."""

from typing import Any, Dict, List

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.proxies import enabled_nodes, load_providers

DIRECT = "direct"
REJECT = "block"


def _tag(ref: str) -> str:
    if ref in ("direct", "DIRECT"):
        return DIRECT
    if ref in ("reject", "REJECT"):
        return REJECT
    return str(ref)


def _selector(tag: str, members: List[str], default: str | None = None) -> dict:
    members = list(dict.fromkeys(m for m in members if m))
    if not members:
        members = [DIRECT, REJECT]
    if default not in members:
        default = members[0]
    return {"type": "selector", "tag": tag, "outbounds": members, "default": default}


def _node(node: dict) -> dict:
    kind = str(node.get("type") or "").lower()
    tag = str(node.get("name") or node.get("id") or "node")
    out = {"type": kind, "tag": tag}
    mapping = {"port": "server_port", "password": "password", "uuid": "uuid"}
    for src, dst in mapping.items():
        if src in node:
            out[dst] = node[src]
    if "server" in node:
        out["server"] = node["server"]
    for key in ("method", "flow", "network", "packet_encoding", "up_mbps", "down_mbps", "server_ports", "hop_interval"):
        if key in node:
            out[key] = node[key]
    tls = node.get("tls")
    if isinstance(tls, dict) and tls:
        out["tls"] = dict(tls)
    elif node.get("tls") is True:
        out["tls"] = {"enabled": True}
    for key in ("transport", "multiplex", "obfs", "plugin", "plugin_opts"):
        if key in node:
            out[key] = node[key]
    if kind not in {"shadowsocks", "vmess", "trojan", "vless", "hysteria", "hysteria2", "tuic", "wireguard", "http", "socks"}:
        raise ValueError(f"unsupported sing-box node type: {kind}")
    return out


def render(ir: Any, platform: str = "sing-box") -> dict:
    outbounds: List[dict] = [
        {"type": "direct", "tag": DIRECT},
        {"type": "block", "tag": REJECT},
    ]
    nodes = [_node(node) for node in enabled_nodes(load_providers())]
    outbounds.extend(nodes)
    node_tags = [n["tag"] for n in nodes]

    groups: Dict[str, dict] = {}
    for group in getattr(ir, "base_groups", []) or []:
        gid = group["id"]
        members = []
        for option in group.get("options") or []:
            if isinstance(option, dict):
                if "ref" in option:
                    members.append(_tag(option["ref"]))
                elif option.get("action") == "direct":
                    members.append(DIRECT)
                elif option.get("action") == "reject":
                    members.append(REJECT)
            else:
                members.append(_tag(str(option)))
        if group.get("include-all-nodes"):
            members.extend(node_tags)
        if gid in ("manual-select", "auto-select", "free-flow") and not members:
            members.extend(node_tags)
        if group.get("type") == "url-test":
            groups[gid] = {
                "type": "urltest", "tag": gid,
                "outbounds": list(dict.fromkeys(members or [DIRECT, REJECT])),
                "url": "https://www.gstatic.com/generate_204", "interval": "5m",
            }
        else:
            groups[gid] = _selector(gid, members, group.get("default"))

    for service in getattr(ir, "services", []) or []:
        groups[service.id] = _selector(
            service.id,
            [_tag(o) for o in service.proxy_options],
            _tag(service.proxy_default),
        )
    outbounds.extend(groups.values())

    route_rules: List[dict] = []
    rule_sets = []
    for source in getattr(ir, "rule_sources", []) or []:
        target = source.target_service
        for domain in source.domain_suffix:
            route_rules.append({"domain_suffix": [domain], "action": "route", "outbound": target})
        for keyword in source.domain_keyword:
            route_rules.append({"domain_keyword": [keyword], "action": "route", "outbound": target})

        native_tags = []
        for bm in source.bm_sets:
            url = str(bm.url).lower()
            if url.endswith((".json", ".srs")):
                fmt = "binary" if url.endswith(".srs") else "source"
                tag = f"{source.id}-{bm.key}"
                native_tags.append(tag)
                rule_sets.append({
                    "type": "remote", "tag": tag, "format": fmt,
                    "url": bm.url, "update_interval": "168h",
                })
        if native_tags:
            route_rules.insert(0, {"rule_set": native_tags, "action": "route", "outbound": target})

    return {
        "log": {"level": "info"},
        "outbounds": outbounds,
        "route": {
            "auto_detect_interface": True,
            "rule_set": rule_sets,
            "rules": route_rules,
            "final": "proxy-mode" if "proxy-mode" in groups else DIRECT,
        },
        "experimental": {"cache_file": {
            "enabled": True,
            "cache_id": "proxy-config-center",
            "store_fakeip": True,
        }},
    }

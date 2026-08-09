#!/usr/bin/env python3
"""sing-box renderer: Core/IR -> native JSON configuration."""

from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from engines.proxies import enabled_nodes, load_providers

DIRECT = "direct"
REJECT = "block"


def _tag(ir: Any, ref: str) -> str:
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
    return {
        "type": "selector",
        "tag": tag,
        "outbounds": members,
        "default": default,
    }


def _node(node: dict) -> dict:
    """Convert the repository's explicit node model to sing-box native fields."""
    kind = str(node.get("type") or "").lower()
    tag = str(node.get("name") or node.get("id") or f"node-{abs(hash(str(node))) % 100000}")
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


def _service_rule(service: Any) -> List[dict]:
    rules = []
    for domain in service.get("domain_suffix", []) if isinstance(service, dict) else []:
        rules.append({"domain_suffix": [domain], "action": "route", "outbound": service["target"]})
    return rules


def render(ir: Any, platform: str = "sing-box") -> dict:
    outbounds: List[dict] = [
        {"type": "direct", "tag": DIRECT},
        {"type": "block", "tag": REJECT},
    ]

    nodes = []
    for node in enabled_nodes(load_providers()):
        nodes.append(_node(node))
    outbounds.extend(nodes)
    node_tags = [n["tag"] for n in nodes]

    groups: Dict[str, dict] = {}
    for group in getattr(ir, "base_groups", []) or []:
        gid = group["id"]
        members = []
        for option in group.get("options") or []:
            if isinstance(option, dict):
                if "ref" in option:
                    members.append(_tag(ir, option["ref"]))
                elif option.get("action") == "direct":
                    members.append(DIRECT)
                elif option.get("action") == "reject":
                    members.append(REJECT)
            else:
                members.append(_tag(ir, str(option)))
        if group.get("include-all-nodes"):
            members.extend(node_tags)
        if gid in ("manual-select", "auto-select", "free-flow") and not members:
            members.extend(node_tags)
        if group.get("type") == "url-test":
            groups[gid] = {
                "type": "urltest",
                "tag": gid,
                "outbounds": list(dict.fromkeys(members or [DIRECT, REJECT])),
                "url": "https://www.gstatic.com/generate_204",
                "interval": "5m",
            }
        else:
            groups[gid] = _selector(gid, members, group.get("default"))

    for service in getattr(ir, "services", []) or []:
        groups[service.id] = _selector(
            service.id,
            [_tag(ir, o) for o in service.proxy_options],
            _tag(ir, service.proxy_default),
        )

    outbounds.extend(groups.values())

    route_rules: List[dict] = []
    for rule_source in getattr(ir, "rule_sources", []) or []:
        target = rule_source.target_service
        for domain in rule_source.domain_suffix:
            route_rules.append({
                "domain_suffix": [domain],
                "action": "route",
                "outbound": target,
            })
        for keyword in rule_source.domain_keyword:
            route_rules.append({
                "domain_keyword": [keyword],
                "action": "route",
                "outbound": target,
            })

    rule_sets = []
    for source in getattr(ir, "rule_sources", []) or []:
        for bm in source.bm_sets:
            # Current Core sources are Clash YAML/LIST. Do not lie to sing-box by
            # treating those as native rule-set files; only native JSON/SRS URLs
            # are promoted to remote rule-sets.
            if str(bm.url).lower().endswith((".json", ".srs")):
                fmt = "binary" if str(bm.url).lower().endswith(".srs") else "source"
                rule_sets.append({
                    "type": "remote",
                    "tag": f"{source.id}-{bm.key}",
                    "format": fmt,
                    "url": bm.url,
                    "update_interval": "168h",
                })

    if rule_sets:
        route_rules.insert(0, {"rule_set": [r["tag"] for r in rule_sets], "action": "route", "outbound": "proxy-mode"})

    config = {
        "log": {"level": "info"},
        "outbounds": outbounds,
        "route": {
            "auto_detect_interface": True,
            "rule_set": rule_sets,
            "rules": route_rules,
            "final": "proxy-mode" if "proxy-mode" in groups else DIRECT,
        },
        "experimental": {
            "cache_file": {
                "enabled": True,
                "cache_id": "proxy-config-center",
                "store_fakeip": True,
            }
        },
    }
    return config

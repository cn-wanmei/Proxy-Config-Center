#!/usr/bin/env python3
"""
DNS Engine V2 — leak-aware resolver/group/policy + Clash-family DNS builder.

Goals:
- Prefer DoH over plaintext UDP
- Minimal bootstrap IPs only for resolving DoH hostnames
- proxy-server-nameserver for node domain resolution
- nameserver-policy from service/domain bindings
- fallback + fallback-filter against pollution
- Avoid system DNS on foreign paths
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

CORE = Path(__file__).resolve().parents[2] / "core"

try:
    from engines.utils import load_yaml
except Exception:  # pragma: no cover
    import yaml

    def load_yaml(path: Path, *, required: bool = False) -> Any:
        if not path.exists():
            return {}
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


BOOTSTRAP_IPV4 = ["223.5.5.5", "1.1.1.1"]

SECURE_DOH = [
    "https://cloudflare-dns.com/dns-query",
    "https://1.1.1.1/dns-query",
    "https://dns.google/dns-query",
]
CHINA_DOH = [
    "https://dns.alidns.com/dns-query",
    "https://doh.pub/dns-query",
]

DEFAULT_DOMAIN_POLICY_MAP = {
    "+.apple.com": "dns-system",
    "+.icloud.com": "dns-system",
    "+.push.apple.com": "dns-system",
    "+.mzstatic.com": "dns-system",
    "+.cn": "dns-china",
    "+.baidu.com": "dns-china",
    "+.qq.com": "dns-china",
    "+.google.com": "dns-google",
    "+.youtube.com": "dns-google",
    "+.googleapis.com": "dns-google",
    "+.gstatic.com": "dns-google",
    "+.openai.com": "dns-foreign",
    "+.anthropic.com": "dns-foreign",
    "+.telegram.org": "dns-foreign",
    "+.t.me": "dns-foreign",
    "+.twitter.com": "dns-foreign",
    "+.x.com": "dns-foreign",
    "+.netflix.com": "dns-cloudflare",
    "+.spotify.com": "dns-cloudflare",
    "+.github.com": "dns-cloudflare",
    "+.githubusercontent.com": "dns-cloudflare",
}


class DNSEngine:
    def __init__(self) -> None:
        resolvers_data = load_yaml(CORE / "dns" / "resolvers.yaml") or {}
        self.resolvers: Dict[str, dict] = resolvers_data.get("resolvers") or {}

        groups_data = load_yaml(CORE / "dns" / "groups.yaml") or {}
        self.groups: Dict[str, dict] = {
            g["id"]: g for g in (groups_data.get("groups") or [])
        }

        policies_data = load_yaml(CORE / "dns" / "policies.yaml") or {}
        self.policies: Dict[str, dict] = {
            p["id"]: p for p in (policies_data.get("policies") or [])
        }

    def resolver_servers(self, resolver_id: str, *, allow_system: bool = False) -> List[str]:
        r = self.resolvers.get(resolver_id) or {}
        if r.get("type") == "system":
            return ["system"] if allow_system else []
        return list(r.get("servers") or [])

    def policy_default_servers(self, policy_id: str, *, allow_system: bool = False) -> List[str]:
        policy = self.policies.get(policy_id) or {}
        default = policy.get("default")
        if not default:
            return list(SECURE_DOH)
        servers = self.resolver_servers(default, allow_system=allow_system)
        return servers if servers else list(SECURE_DOH)

    def validate(self) -> List[str]:
        errors: List[str] = []
        for gid, g in self.groups.items():
            for rid in g.get("resolvers") or []:
                if rid not in self.resolvers:
                    errors.append(f"group '{gid}' unknown resolver '{rid}'")
        for pid, p in self.policies.items():
            if p.get("group") not in self.groups:
                errors.append(f"policy '{pid}' unknown group '{p.get('group')}'")
            for opt in p.get("options") or []:
                if opt not in self.resolvers:
                    errors.append(f"policy '{pid}' option '{opt}' not a resolver")
            if p.get("default") not in (p.get("options") or []):
                errors.append(f"policy '{pid}' default not in options")
        return errors

    def build_nameserver_policy(
        self,
        domain_map: Optional[Dict[str, str]] = None,
        *,
        allow_system: bool = False,
    ) -> dict:
        domain_map = domain_map or DEFAULT_DOMAIN_POLICY_MAP
        result: Dict[str, Any] = {}
        for domain, policy_id in domain_map.items():
            use_system = allow_system or policy_id == "dns-system"
            servers = self.policy_default_servers(policy_id, allow_system=use_system)
            if not servers:
                servers = list(SECURE_DOH)
            result[domain] = servers if len(servers) > 1 else servers[0]
        return result

    def build_clash_dns(
        self,
        *,
        ipv6: bool = True,
        include_nameserver_policy: bool = True,
    ) -> dict:
        nameserver: List[str] = []
        for srv in SECURE_DOH + CHINA_DOH:
            if srv not in nameserver:
                nameserver.append(srv)

        proxy_ns = list(SECURE_DOH)

        dns: Dict[str, Any] = {
            "enable": True,
            "ipv6": bool(ipv6),
            "enhanced-mode": "fake-ip",
            "fake-ip-range": "198.18.0.1/16",
            "use-hosts": True,
            "respect-rules": True,
            "default-nameserver": list(BOOTSTRAP_IPV4),
            "nameserver": nameserver,
            "proxy-server-nameserver": proxy_ns,
            "fallback": list(SECURE_DOH),
            "fallback-filter": {
                "geoip": True,
                "geoip-code": "CN",
                "ipcidr": ["240.0.0.0/4"],
            },
        }
        if include_nameserver_policy:
            nsp = self.build_nameserver_policy(allow_system=True)
            if nsp:
                dns["nameserver-policy"] = nsp
        return dns


def build_clash_dns_config(*, ipv6: bool = True) -> dict:
    return DNSEngine().build_clash_dns(ipv6=ipv6)


if __name__ == "__main__":
    eng = DNSEngine()
    errs = eng.validate()
    print(f"DNS Engine V2: {len(eng.resolvers)} resolvers, {len(eng.policies)} policies")
    if errs:
        for e in errs:
            print("  ❌", e)
    else:
        print("  ✅ valid")
    dns = eng.build_clash_dns()
    print("clash dns keys:", sorted(dns.keys()))
    print("default-nameserver:", dns.get("default-nameserver"))
    print("proxy-server-nameserver:", dns.get("proxy-server-nameserver"))
    print("nameserver-policy entries:", len(dns.get("nameserver-policy") or {}))

#!/usr/bin/env python3
"""
DNS Engine V2 (Core V2 compiler) — secure-only DNS emission.

Forbidden:
- system DNS
- plaintext UDP/TCP 53 nameservers in emitted client config (except minimal bootstrap IPs)

Required:
- DoH / DoT / H3 for resolution paths
- proxy-server-nameserver
- fallback + fallback-filter
- nameserver-policy
- explicit ipv4 / ipv6 handling

P2: optional latency-based DoH ranking (use_scores / PROXY_DNS_USE_SCORES).
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
BOOTSTRAP_IPV6 = ["2400:3200::1", "2606:4700:4700::1111"]

SECURE_DOH = [
    "https://cloudflare-dns.com/dns-query",
    "https://1.1.1.1/dns-query",
    "https://dns.google/dns-query",
]
CHINA_DOH = [
    "https://dns.alidns.com/dns-query",
    "https://doh.pub/dns-query",
]


def rank_doh_urls(urls: List[str], *, use_scores: bool = False, timeout: float = 3.0) -> List[str]:
    """Optionally reorder DoH URLs by live latency scores (P2)."""
    if not use_scores or not urls:
        return list(urls)
    try:
        from engines.resolver_score import load_ranked_from_report, rank_urls, score_urls, write_score_report
        cached = load_ranked_from_report()
        if cached:
            known = set(urls)
            ordered = [u for u in cached if u in known]
            for u in urls:
                if u not in ordered:
                    ordered.append(u)
            return ordered if ordered else list(urls)
        scored = score_urls(urls, timeout=timeout, probes=1)
        write_score_report(scored)
        return rank_urls(urls, timeout=timeout, probes=1, exclude_failed=True)
    except Exception:
        return list(urls)


DEFAULT_DOMAIN_POLICY_MAP = {
    "+.apple.com": "dns-china",
    "+.icloud.com": "dns-china",
    "+.push.apple.com": "dns-china",
    "+.mzstatic.com": "dns-china",
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

    def resolver_servers(self, resolver_id: str) -> List[str]:
        r = self.resolvers.get(resolver_id) or {}
        if str(r.get("type") or "").lower() == "system":
            return []
        out: List[str] = []
        for s in r.get("servers") or []:
            s = str(s)
            if s.lower() == "system":
                continue
            out.append(s)
        return out

    def policy_default_servers(self, policy_id: str) -> List[str]:
        policy = self.policies.get(policy_id) or {}
        default = policy.get("default")
        if not default:
            return list(SECURE_DOH)
        servers = self.resolver_servers(str(default))
        return servers if servers else list(SECURE_DOH)

    def validate(self) -> List[str]:
        errors: List[str] = []
        for rid, r in self.resolvers.items():
            if str(r.get("type") or "").lower() == "system":
                errors.append(f"resolver '{rid}' type=system forbidden")
            for s in r.get("servers") or []:
                if str(s).lower() == "system":
                    errors.append(f"resolver '{rid}' contains system")
        for gid, g in self.groups.items():
            for rid in g.get("resolvers") or []:
                if rid not in self.resolvers:
                    errors.append(f"group '{gid}' unknown resolver '{rid}'")
                if rid == "system":
                    errors.append(f"group '{gid}' references system")
        for pid, p in self.policies.items():
            if p.get("group") not in self.groups:
                errors.append(f"policy '{pid}' unknown group '{p.get('group')}'")
            for opt in p.get("options") or []:
                if str(opt) == "system":
                    errors.append(f"policy '{pid}' option system forbidden")
                elif opt not in self.resolvers:
                    errors.append(f"policy '{pid}' option '{opt}' not a resolver")
            if p.get("default") not in (p.get("options") or []):
                errors.append(f"policy '{pid}' default not in options")
            if str(p.get("default") or "") == "system":
                errors.append(f"policy '{pid}' default system forbidden")
        return errors

    def build_nameserver_policy(
        self,
        domain_map: Optional[Dict[str, str]] = None,
    ) -> dict:
        domain_map = domain_map or DEFAULT_DOMAIN_POLICY_MAP
        result: Dict[str, Any] = {}
        for domain, policy_id in domain_map.items():
            if policy_id == "dns-system":
                policy_id = "dns-china"
            servers = self.policy_default_servers(policy_id)
            if not servers:
                servers = list(SECURE_DOH)
            result[domain] = servers if len(servers) > 1 else servers[0]
        return result

    def build_clash_dns(
        self,
        *,
        ipv6: bool = True,
        include_nameserver_policy: bool = True,
        use_scores: bool = False,
    ) -> dict:
        nameserver: List[str] = []
        for srv in SECURE_DOH + CHINA_DOH:
            if srv not in nameserver:
                nameserver.append(srv)
        nameserver = rank_doh_urls(nameserver, use_scores=use_scores)
        secure_ranked = rank_doh_urls(list(SECURE_DOH), use_scores=use_scores)

        bootstrap = list(BOOTSTRAP_IPV4)
        if ipv6:
            bootstrap = list(BOOTSTRAP_IPV4) + list(BOOTSTRAP_IPV6)

        dns: Dict[str, Any] = {
            "enable": True,
            "ipv6": bool(ipv6),
            "enhanced-mode": "fake-ip",
            "fake-ip-range": "198.18.0.1/16",
            "use-hosts": True,
            "respect-rules": True,
            "default-nameserver": bootstrap,
            "nameserver": nameserver,
            "proxy-server-nameserver": list(secure_ranked),
            "fallback": list(secure_ranked),
            "fallback-filter": {
                "geoip": True,
                "geoip-code": "CN",
                "ipcidr": ["240.0.0.0/4"],
            },
        }
        if include_nameserver_policy:
            nsp = self.build_nameserver_policy()
            if nsp:
                dns["nameserver-policy"] = nsp
        return dns


def build_clash_dns_config(*, ipv6: bool = True, use_scores: bool = False) -> dict:
    return DNSEngine().build_clash_dns(ipv6=ipv6, use_scores=use_scores)


if __name__ == "__main__":
    eng = DNSEngine()
    errs = eng.validate()
    print(f"DNS Engine V2: {len(eng.resolvers)} resolvers, {len(eng.policies)} policies")
    if errs:
        for e in errs:
            print("  \u274c", e)
        raise SystemExit(1)
    print("  \u2705 valid")
    dns = eng.build_clash_dns()
    print("keys", sorted(dns.keys()))

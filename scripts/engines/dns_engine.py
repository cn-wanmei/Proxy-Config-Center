#!/usr/bin/env python3
"""
DNS Engine V1
Resolve Resolver → Group → Policy and build nameserver-policy maps.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

CORE = Path(__file__).resolve().parents[2] / "core"

def load_yaml(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

class DNSEngine:
    def __init__(self):
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
        if r.get("type") == "system":
            return ["system"]
        return list(r.get("servers") or [])

    def policy_default_servers(self, policy_id: str) -> List[str]:
        policy = self.policies.get(policy_id) or {}
        default = policy.get("default")
        if not default:
            return ["system"]
        return self.resolver_servers(default)

    def validate(self) -> List[str]:
        errors = []
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

    def build_nameserver_policy(self, domain_map: Optional[Dict[str, str]] = None) -> dict:
        """domain_map: domain -> policy_id"""
        domain_map = domain_map or DEFAULT_DOMAIN_POLICY_MAP
        result = {}
        for domain, policy_id in domain_map.items():
            servers = self.policy_default_servers(policy_id)
            result[domain] = servers if len(servers) > 1 else (servers[0] if servers else "system")
        return result

# Default domain → policy bindings (Core V1)
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
    "+.openai.com": "dns-foreign",
    "+.anthropic.com": "dns-foreign",
    "+.telegram.org": "dns-foreign",
    "+.twitter.com": "dns-foreign",
    "+.x.com": "dns-foreign",
    "+.netflix.com": "dns-cloudflare",
    "+.spotify.com": "dns-cloudflare",
    "+.github.com": "dns-cloudflare",
}

if __name__ == "__main__":
    eng = DNSEngine()
    errs = eng.validate()
    print(f"DNS Engine V1: {len(eng.resolvers)} resolvers, {len(eng.policies)} policies")
    if errs:
        for e in errs:
            print("  ❌", e)
    else:
        print("  ✅ valid")

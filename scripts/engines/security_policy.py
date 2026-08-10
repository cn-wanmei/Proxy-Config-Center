#!/usr/bin/env python3
"""Security Policy abstraction — load core/security/policy.yaml and apply."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "core" / "security" / "policy.yaml"

try:
    from engines.utils import load_yaml
except Exception:  # pragma: no cover
    import yaml

    def load_yaml(path: Path, *, required: bool = False) -> Any:
        if not path.exists():
            return {}
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


@dataclass
class SecurityPolicy:
    raw: Dict[str, Any] = field(default_factory=dict)
    forbid_system: bool = True
    forbid_plaintext_nameserver: bool = True
    require_fake_ip: bool = True
    require_proxy_server_nameserver: bool = True
    require_fallback: bool = True
    require_nameserver_policy: bool = True
    allowed_schemes: List[str] = field(default_factory=lambda: ["https://", "h3://", "tls://"])
    no_silent_degradation: bool = True
    require_routing_capability: bool = True
    reverse_validate_emit: bool = True
    immutable_artifacts: bool = True
    require_sha256: bool = True

    @classmethod
    def load(cls, path: Path = POLICY_PATH) -> "SecurityPolicy":
        data = load_yaml(path) or {}
        dns = data.get("dns") or {}
        compile_ = data.get("compile") or {}
        release = data.get("release") or {}
        return cls(
            raw=data,
            forbid_system=bool(dns.get("forbid_system", True)),
            forbid_plaintext_nameserver=bool(dns.get("forbid_plaintext_nameserver", True)),
            require_fake_ip=bool(dns.get("require_fake_ip", True)),
            require_proxy_server_nameserver=bool(dns.get("require_proxy_server_nameserver", True)),
            require_fallback=bool(dns.get("require_fallback", True)),
            require_nameserver_policy=bool(dns.get("require_nameserver_policy", True)),
            allowed_schemes=list(dns.get("allowed_schemes") or ["https://", "h3://", "tls://"]),
            no_silent_degradation=bool(compile_.get("no_silent_degradation", True)),
            require_routing_capability=bool(compile_.get("require_routing_capability", True)),
            reverse_validate_emit=bool(compile_.get("reverse_validate_emit", True)),
            immutable_artifacts=bool(release.get("immutable_artifacts", True)),
            require_sha256=bool(release.get("require_sha256", True)),
        )

    def validate_dns_block(self, dns: Dict[str, Any], *, platform: str = "") -> List[str]:
        from engines.security import check_dns_block
        errors = check_dns_block(dns, platform=platform)
        if self.require_fake_ip and dns.get("enhanced-mode") not in (None, "fake-ip"):
            if dns.get("enhanced-mode") != "fake-ip":
                errors.append("policy: enhanced-mode must be fake-ip")
        if self.require_proxy_server_nameserver and "proxy-server-nameserver" not in dns:
            errors.append("policy: proxy-server-nameserver required")
        if self.require_fallback and "fallback" not in dns:
            errors.append("policy: fallback required")
        if self.require_nameserver_policy and "nameserver-policy" not in dns:
            errors.append("policy: nameserver-policy required")
        return errors


def load_security_policy() -> SecurityPolicy:
    return SecurityPolicy.load()

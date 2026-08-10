#!/usr/bin/env python3
"""Security Engine — invariants that must hold before/after compile.

Policy → Security validation → IR → Capability → Compiler.
No silent degradation: violations raise or return hard errors.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

_PLAIN_DNS_IP = re.compile(
    r"^(?:\d{1,3}\.){3}\d{1,3}$|"
    r"^\[?[0-9a-fA-F:]+\]?$"
)
_DOH = re.compile(r"^https://", re.I)
_DOT = re.compile(r"^tls://", re.I)
_DOH3 = re.compile(r"^h3://", re.I)
_SYSTEM_TOKENS = frozenset({"system", "SYSTEM", "localhost"})


class SecurityViolation(Exception):
    def __init__(self, code: str, message: str, path: str = ""):
        self.code = code
        self.path = path
        super().__init__(f"[{code}] {message}" + (f" @ {path}" if path else ""))


def is_secure_dns_endpoint(server: str) -> bool:
    s = (server or "").strip()
    if not s or s.lower() == "system":
        return False
    if _DOH.match(s) or _DOT.match(s) or _DOH3.match(s):
        return True
    return False


def is_plain_dns_endpoint(server: str) -> bool:
    s = (server or "").strip()
    if not s or is_secure_dns_endpoint(s):
        return False
    if _PLAIN_DNS_IP.match(s) or s.endswith(":53"):
        return True
    if "://" not in s and not s.startswith("dhcp"):
        return True
    return False


def check_dns_block(dns: Dict[str, Any], *, platform: str = "") -> List[str]:
    errors: List[str] = []
    if not isinstance(dns, dict):
        return ["dns block missing or not a mapping"]
    if dns.get("enable") is False:
        errors.append("dns.enable must not be false under DNS security policy")
    mode = str(dns.get("enhanced-mode") or dns.get("enhanced_mode") or "")
    if platform.startswith("clash") or platform in ("stash", "clash-meta", "clash"):
        if mode and mode != "fake-ip":
            errors.append(f"enhanced-mode must be fake-ip, got {mode!r}")
    for key in ("nameserver", "fallback", "proxy-server-nameserver", "default-nameserver"):
        vals = dns.get(key)
        if vals is None:
            continue
        if isinstance(vals, str):
            vals = [vals]
        if not isinstance(vals, list):
            continue
        for i, v in enumerate(vals):
            sv = str(v)
            if sv.lower() in _SYSTEM_TOKENS:
                errors.append(f"{key}[{i}] forbids system DNS")
            if key == "default-nameserver":
                continue
            if is_plain_dns_endpoint(sv):
                errors.append(f"{key}[{i}] plaintext/UDP53 DNS forbidden: {sv}")
            if not is_secure_dns_endpoint(sv):
                if not _PLAIN_DNS_IP.match(sv):
                    errors.append(f"{key}[{i}] must be DoH/DoT/H3: {sv}")
    nsp = dns.get("nameserver-policy") or {}
    if isinstance(nsp, dict):
        for domain, servers in nsp.items():
            sl = servers if isinstance(servers, list) else [servers]
            for v in sl:
                sv = str(v)
                if sv.lower() == "system":
                    errors.append(f"nameserver-policy[{domain}] forbids system DNS")
                elif not is_secure_dns_endpoint(sv):
                    errors.append(f"nameserver-policy[{domain}] insecure: {sv}")
    return errors


def check_resolver_core(resolvers: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for rid, r in (resolvers or {}).items():
        if not isinstance(r, dict):
            continue
        if str(r.get("type") or "").lower() == "system":
            errors.append(f"resolver '{rid}' type=system is forbidden in Core V2")
        for i, s in enumerate(r.get("servers") or []):
            if str(s).lower() == "system":
                errors.append(f"resolver '{rid}' servers[{i}] system forbidden")
            elif is_plain_dns_endpoint(str(s)) and not is_secure_dns_endpoint(str(s)):
                errors.append(f"resolver '{rid}' servers[{i}] plaintext DNS forbidden: {s}")
    return errors


def check_policies_core(policies: List[dict]) -> List[str]:
    errors: List[str] = []
    for p in policies or []:
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "?")
        for opt in p.get("options") or []:
            if str(opt).lower() == "system":
                errors.append(f"policy '{pid}' option 'system' forbidden")
        if str(p.get("default") or "").lower() == "system":
            errors.append(f"policy '{pid}' default 'system' forbidden")
    return errors


def run_core_security_invariants(core_root) -> List[str]:
    from pathlib import Path
    from engines.utils import load_yaml
    core = Path(core_root)
    errors: List[str] = []
    resolvers = (load_yaml(core / "dns" / "resolvers.yaml") or {}).get("resolvers") or {}
    policies = (load_yaml(core / "dns" / "policies.yaml") or {}).get("policies") or []
    errors.extend(check_resolver_core(resolvers))
    errors.extend(check_policies_core(policies))
    return errors


def assert_capability_or_raise(platform: str, feature: str, supported: bool) -> None:
    if not supported:
        raise SecurityViolation(
            "CAPABILITY_MISSING",
            f"platform '{platform}' does not support required feature '{feature}'; "
            "silent degradation is forbidden",
            path=platform,
        )

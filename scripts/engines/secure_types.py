#!/usr/bin/env python3
"""Secure-by-construction types — insecure values cannot be represented."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

_SECURE_SCHEME = re.compile(r"^(https|h3|tls)://", re.I)
_BOOTSTRAP_V4 = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_BOOTSTRAP_V6 = re.compile(r"^[0-9a-fA-F:]+$")


class InsecureEndpointError(ValueError):
    pass


@dataclass(frozen=True)
class SecureDNSEndpoint:
    url: str

    def __post_init__(self) -> None:
        u = (self.url or "").strip()
        if not _SECURE_SCHEME.match(u):
            raise InsecureEndpointError(f"insecure DNS endpoint rejected: {u!r}")
        if "system" in u.lower():
            raise InsecureEndpointError("system DNS is not representable")
        object.__setattr__(self, "url", u)

    def __str__(self) -> str:
        return self.url


@dataclass(frozen=True)
class BootstrapIP:
    ip: str

    def __post_init__(self) -> None:
        ip = (self.ip or "").strip()
        if not (_BOOTSTRAP_V4.match(ip) or (":" in ip and _BOOTSTRAP_V6.match(ip))):
            raise InsecureEndpointError(f"invalid bootstrap IP: {ip!r}")
        if ip.lower() == "system":
            raise InsecureEndpointError("system is not a bootstrap IP")
        object.__setattr__(self, "ip", ip)

    def __str__(self) -> str:
        return self.ip


def secure_endpoints(urls: Sequence[str]) -> Tuple[SecureDNSEndpoint, ...]:
    return tuple(SecureDNSEndpoint(u) for u in urls)


def bootstrap_ips(ips: Sequence[str]) -> Tuple[BootstrapIP, ...]:
    return tuple(BootstrapIP(ip) for ip in ips)


def as_secure_url_list(endpoints: Iterable[SecureDNSEndpoint]) -> List[str]:
    return [e.url for e in endpoints]

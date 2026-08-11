#!/usr/bin/env python3
"""Real DoH probe (Core V2.3)."""

from __future__ import annotations

import base64
import struct
import time
import urllib.request
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlencode

from engines.secure_types import SecureDNSEndpoint, InsecureEndpointError


@dataclass
class ProbeResult:
    url: str
    ok: bool
    latency_ms: Optional[float]
    status: Optional[int] = None
    error: str = ""


def _build_dns_query(name: str = "example.com") -> bytes:
    header = struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0)
    qname = b""
    for label in name.split("."):
        qname += bytes([len(label)]) + label.encode("ascii")
    qname += b"\x00"
    return header + qname + struct.pack("!HH", 1, 1)


def probe_doh(url: str, *, timeout: float = 3.0, name: str = "example.com") -> ProbeResult:
    try:
        secure = SecureDNSEndpoint(url)
    except InsecureEndpointError as exc:
        return ProbeResult(url=url, ok=False, latency_ms=None, error=str(exc))
    probe_url = secure.url
    if probe_url.startswith("h3://"):
        probe_url = "https://" + probe_url[5:]
    if probe_url.startswith("tls://"):
        return ProbeResult(url=url, ok=False, latency_ms=None, error="tls probe not implemented")
    q = _build_dns_query(name)
    b64 = base64.urlsafe_b64encode(q).decode("ascii").rstrip("=")
    full = probe_url + ("&" if "?" in probe_url else "?") + urlencode({"dns": b64})
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(
            full,
            headers={"Accept": "application/dns-message", "User-Agent": "Proxy-Config-Center/2.3"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            status = getattr(resp, "status", 200)
            ms = (time.perf_counter() - t0) * 1000.0
            ok = status == 200 and len(body) > 0
            return ProbeResult(url=url, ok=ok, latency_ms=ms if ok else None, status=status, error="" if ok else f"status={status}")
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return ProbeResult(url=url, ok=False, latency_ms=ms, error=f"{type(exc).__name__}: {exc}")


def probe_many(urls: List[str], *, timeout: float = 3.0) -> List[ProbeResult]:
    return [probe_doh(u, timeout=timeout) for u in urls]

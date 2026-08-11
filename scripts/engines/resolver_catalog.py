#!/usr/bin/env python3
"""Resolver catalog — SSOT from core/dns/resolvers.yaml (2.3)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Sequence

from engines.secure_types import SecureDNSEndpoint, InsecureEndpointError

ROOT = Path(__file__).resolve().parents[2]
RESOLVERS_PATH = ROOT / "core" / "dns" / "resolvers.yaml"


def _load_yaml(path: Path) -> Any:
    try:
        from engines.utils import load_yaml
        return load_yaml(path) or {}
    except Exception:
        import yaml
        if not path.exists():
            return {}
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_resolver_catalog() -> Dict[str, List[str]]:
    data = _load_yaml(RESOLVERS_PATH)
    out: Dict[str, List[str]] = {}
    for rid, body in (data.get("resolvers") or {}).items():
        if not isinstance(body, dict):
            continue
        secure: List[str] = []
        for s in body.get("servers") or []:
            try:
                secure.append(SecureDNSEndpoint(str(s)).url)
            except InsecureEndpointError:
                continue
        if secure:
            out[str(rid)] = secure
    return out


def validate_catalog() -> List[str]:
    errors: List[str] = []
    cat = load_resolver_catalog()
    if not cat:
        errors.append("resolver catalog empty or all endpoints rejected")
    for rid, urls in cat.items():
        if not urls:
            errors.append(f"resolver {rid}: no secure servers")
        for u in urls:
            if not (u.startswith("https://") or u.startswith("h3://") or u.startswith("tls://")):
                errors.append(f"resolver {rid}: insecure url leaked: {u}")
    return errors


def urls_for_ids(ids: Sequence[str]) -> List[str]:
    cat = load_resolver_catalog()
    out: List[str] = []
    for rid in ids:
        for u in cat.get(rid, []):
            if u not in out:
                out.append(u)
    return out


def all_secure_urls() -> List[str]:
    out: List[str] = []
    for urls in load_resolver_catalog().values():
        for u in urls:
            if u not in out:
                out.append(u)
    return out

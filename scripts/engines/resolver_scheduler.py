#!/usr/bin/env python3
"""Resolver intelligent scheduling (Core V2.2)."""

from __future__ import annotations

from typing import Dict, List, Sequence

from engines.secure_types import SecureDNSEndpoint, as_secure_url_list, secure_endpoints

RESOLVER_CATALOG: Dict[str, List[str]] = {
    "cloudflare": ["https://cloudflare-dns.com/dns-query", "https://1.1.1.1/dns-query"],
    "google": ["https://dns.google/dns-query"],
    "alidns": ["https://dns.alidns.com/dns-query"],
    "tencent": ["https://doh.pub/dns-query"],
}


def urls_for_resolver_ids(ids: Sequence[str]) -> List[str]:
    out: List[str] = []
    for rid in ids:
        for u in RESOLVER_CATALOG.get(rid, []):
            if u not in out:
                out.append(u)
    return as_secure_url_list(secure_endpoints(out))


def schedule(preference: Sequence[str], *, use_scores: bool = False, timeout: float = 3.0) -> List[SecureDNSEndpoint]:
    base_urls = urls_for_resolver_ids(preference)
    if not base_urls:
        base_urls = urls_for_resolver_ids(["cloudflare", "google"])
    if use_scores:
        try:
            from engines.resolver_score import load_ranked_from_report, rank_urls, score_urls, write_score_report
            cached = load_ranked_from_report()
            if cached:
                known = set(base_urls)
                ordered = [u for u in cached if u in known]
                for u in base_urls:
                    if u not in ordered:
                        ordered.append(u)
                return list(secure_endpoints(ordered))
            scored = score_urls(base_urls, timeout=timeout, probes=1)
            write_score_report(scored)
            ranked = rank_urls(base_urls, timeout=timeout, probes=1, exclude_failed=True)
            return list(secure_endpoints(ranked))
        except Exception:
            pass
    return list(secure_endpoints(base_urls))

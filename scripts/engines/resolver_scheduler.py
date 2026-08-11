#!/usr/bin/env python3
"""Resolver scheduling (2.3) — catalog + optional real probe scores."""

from __future__ import annotations

from typing import List, Sequence

from engines.resolver_catalog import urls_for_ids, all_secure_urls, validate_catalog
from engines.secure_types import SecureDNSEndpoint, secure_endpoints


def schedule(preference: Sequence[str], *, use_scores: bool = False, timeout: float = 3.0) -> List[SecureDNSEndpoint]:
    errs = validate_catalog()
    if errs:
        base_urls = urls_for_ids(["cloudflare", "google"]) or all_secure_urls()
    else:
        base_urls = urls_for_ids(preference) or urls_for_ids(["cloudflare", "google"]) or all_secure_urls()
    if not base_urls:
        raise RuntimeError("no secure resolvers available in catalog")
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
            if ranked:
                return list(secure_endpoints(ranked))
        except Exception:
            pass
    return list(secure_endpoints(base_urls))

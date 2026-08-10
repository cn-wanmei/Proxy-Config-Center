#!/usr/bin/env python3
"""Resolver score unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.resolver_score import ResolverScore, rank_urls
from engines.dns_engine import build_clash_dns_config, rank_doh_urls


def test_rank_urls_fail_open_empty_probe():
    from engines import resolver_score as rs

    def fake_score(urls, timeout=3.0, probes=1):
        return [ResolverScore(url=u, ok=False, latency_ms=9999, score=9999 + 5000) for u in urls]

    original = rs.score_urls
    rs.score_urls = fake_score
    try:
        urls = ["https://a.example/dns-query", "https://b.example/dns-query"]
        ranked = rank_urls(urls, exclude_failed=True)
        assert ranked == urls
    finally:
        rs.score_urls = original


def test_rank_doh_urls_static_without_scores():
    urls = ["https://dns.google/dns-query", "https://cloudflare-dns.com/dns-query"]
    assert rank_doh_urls(urls, use_scores=False) == urls


def test_build_clash_dns_without_scores_stable():
    dns = build_clash_dns_config(ipv6=True, use_scores=False)
    assert dns["nameserver"]
    assert all(str(s).startswith("https://") or str(s).startswith("h3://") for s in dns["nameserver"])


if __name__ == "__main__":
    test_rank_urls_fail_open_empty_probe()
    test_rank_doh_urls_static_without_scores()
    test_build_clash_dns_without_scores_stable()
    print("OK resolver score tests")

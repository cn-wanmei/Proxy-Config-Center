#!/usr/bin/env python3
"""Resolver scoring — latency probe, rank, failover order (P2).

Produces a ranked list of DoH endpoints for emit-time ordering.
Offline / probe failure: keep static order (no silent empty list).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCORE_PATH = ROOT / "build" / "audit" / "resolver-scores.json"

WEIGHT_FAIL_PENALTY = 5000.0
DEFAULT_TIMEOUT = 3.0


@dataclass
class ResolverScore:
    url: str
    ok: bool
    latency_ms: Optional[float] = None
    status: Optional[int] = None
    error: Optional[str] = None
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def probe_latency(url: str, timeout: float = DEFAULT_TIMEOUT) -> ResolverScore:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/dns-json, application/dns-message, */*",
            "User-Agent": "Proxy-Config-Center-ResolverScore/2.0",
        },
        method="GET",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = int(getattr(resp, "status", None) or resp.getcode())
            try:
                resp.read(64)
            except Exception:
                pass
        elapsed = (time.perf_counter() - t0) * 1000.0
        ok = 200 <= code < 500
        score = elapsed if ok else elapsed + WEIGHT_FAIL_PENALTY
        return ResolverScore(url=url, ok=ok, latency_ms=round(elapsed, 2), status=code, score=round(score, 2))
    except urllib.error.HTTPError as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        code = int(exc.code)
        return ResolverScore(
            url=url, ok=True, latency_ms=round(elapsed, 2), status=code, score=round(elapsed, 2),
            error="http_error_reachable",
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ResolverScore(
            url=url, ok=False, latency_ms=round(elapsed, 2), error=str(exc),
            score=round(elapsed + WEIGHT_FAIL_PENALTY, 2),
        )


def score_urls(urls: Sequence[str], *, timeout: float = DEFAULT_TIMEOUT, probes: int = 1) -> List[ResolverScore]:
    results: List[ResolverScore] = []
    for url in urls:
        samples: List[ResolverScore] = []
        for _ in range(max(1, probes)):
            samples.append(probe_latency(url, timeout=timeout))
        ok_samples = [s for s in samples if s.ok and s.latency_ms is not None]
        if ok_samples:
            avg = sum(s.latency_ms for s in ok_samples if s.latency_ms is not None) / len(ok_samples)
            best = ok_samples[0]
            results.append(ResolverScore(
                url=url, ok=True, latency_ms=round(avg, 2), status=best.status,
                score=round(avg, 2), error=best.error,
            ))
        else:
            results.append(samples[-1])
    results.sort(key=lambda r: (not r.ok, r.score))
    return results


def rank_urls(
    urls: Sequence[str],
    *,
    timeout: float = DEFAULT_TIMEOUT,
    probes: int = 1,
    exclude_failed: bool = True,
) -> List[str]:
    scored = score_urls(urls, timeout=timeout, probes=probes)
    ordered = [s.url for s in scored if s.ok] if exclude_failed else [s.url for s in scored]
    if not ordered:
        return list(urls)
    if not exclude_failed:
        return ordered
    failed = [s.url for s in scored if not s.ok]
    return ordered + failed


def write_score_report(scored: List[ResolverScore], path: Path = DEFAULT_SCORE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_by": "engines.resolver_score",
        "count": len(scored),
        "healthy": sum(1 for s in scored if s.ok),
        "results": [s.to_dict() for s in scored],
        "ranked": [s.url for s in scored if s.ok] + [s.url for s in scored if not s.ok],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_ranked_from_report(path: Path = DEFAULT_SCORE_PATH) -> Optional[List[str]]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ranked = data.get("ranked")
        if isinstance(ranked, list) and ranked:
            return [str(u) for u in ranked]
    except Exception:
        return None
    return None

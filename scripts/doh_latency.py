#!/usr/bin/env python3
"""DNS latency test + resolver score report (P2)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from engines.dns_engine import CHINA_DOH, SECURE_DOH
from engines.resolver_score import DEFAULT_SCORE_PATH, rank_urls, score_urls, write_score_report
from engines.utils import load_yaml


def collect_urls() -> list[str]:
    urls: list[str] = []
    data = load_yaml(ROOT / "core" / "dns" / "resolvers.yaml") or {}
    for _rid, r in (data.get("resolvers") or {}).items():
        for s in r.get("servers") or []:
            s = str(s)
            if s.startswith("https://") and s not in urls:
                urls.append(s)
    for s in SECURE_DOH + CHINA_DOH:
        if s.startswith("https://") and s not in urls:
            urls.append(s)
    return urls


def main() -> int:
    parser = argparse.ArgumentParser(description="DoH latency / resolver scoring")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--probes", type=int, default=1)
    parser.add_argument("--write", type=str, default=str(DEFAULT_SCORE_PATH))
    parser.add_argument("--apply-emit", action="store_true")
    args = parser.parse_args()

    urls = collect_urls()
    scored = score_urls(urls, timeout=args.timeout, probes=args.probes)
    path = write_score_report(scored, Path(args.write))
    ranked = rank_urls(urls, timeout=args.timeout, probes=args.probes, exclude_failed=True)

    print(json.dumps({
        "total": len(scored),
        "healthy": sum(1 for s in scored if s.ok),
        "report": str(path),
        "fastest": ranked[0] if ranked else None,
    }, ensure_ascii=False))
    for s in scored:
        mark = "OK" if s.ok else "FAIL"
        lat = f"{s.latency_ms}ms" if s.latency_ms is not None else "n/a"
        print(f"  [{mark}] {lat:>10}  score={s.score:<8}  {s.url}")

    if args.apply_emit:
        print("RANKED_FOR_EMIT:")
        for u in ranked:
            print(" ", u)
    return 0


if __name__ == "__main__":
    sys.exit(main())

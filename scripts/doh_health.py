#!/usr/bin/env python3
"""DoH health detection — optional network check for Core resolvers."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"

from engines.utils import load_yaml
from engines.dns_engine import SECURE_DOH, CHINA_DOH


def collect_doh_urls() -> List[str]:
    urls: List[str] = []
    data = load_yaml(CORE / "dns" / "resolvers.yaml") or {}
    for rid, r in (data.get("resolvers") or {}).items():
        if str(r.get("type") or "").lower() == "system":
            continue
        for s in r.get("servers") or []:
            s = str(s)
            if s.startswith("https://") and s not in urls:
                urls.append(s)
    for s in SECURE_DOH + CHINA_DOH:
        if s.startswith("https://") and s not in urls:
            urls.append(s)
    return urls


def probe(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/dns-json, application/dns-message, */*",
            "User-Agent": "Proxy-Config-Center-DoH-Health/2.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            return {"url": url, "ok": 200 <= int(code) < 500, "status": int(code)}
    except urllib.error.HTTPError as exc:
        return {"url": url, "ok": True, "status": int(exc.code), "note": "http_error_reachable"}
    except Exception as exc:
        return {"url": url, "ok": False, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--write", type=str, default="")
    args = parser.parse_args()

    urls = collect_doh_urls()
    results = [probe(u, timeout=args.timeout) for u in urls]
    failed = [r for r in results if not r.get("ok")]
    report = {"total": len(results), "failed": len(failed), "results": results}
    print(json.dumps({"total": report["total"], "failed": report["failed"]}, ensure_ascii=False))
    for r in results:
        mark = "OK" if r.get("ok") else "FAIL"
        print(f"  [{mark}] {r.get('url')} {r.get('status', r.get('error', ''))}")

    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.strict and failed:
        print("❌ DoH health strict mode: unreachable endpoints present")
        return 1
    print("✅ DoH health check complete" + (" (strict)" if args.strict else " (report-only)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

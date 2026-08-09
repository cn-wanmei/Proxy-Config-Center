#!/usr/bin/env python3
"""Check remote rule sources with retry, local cache, and integrity reporting."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import List, Tuple

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "core" / "rules" / "sources.yaml"
CACHE = ROOT / ".cache" / "rule-sources"
TIMEOUT = 12
RETRIES = 3
CACHE_TTL = 24 * 60 * 60


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def fetch(url: str) -> Tuple[bytes, str]:
    last = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Proxy-Config-Center/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                body = response.read()
                status = int(getattr(response, "status", 200))
                if status >= 400:
                    raise RuntimeError(f"HTTP {status}")
                return body, f"HTTP {status}"
        except Exception as exc:
            last = exc
            if attempt + 1 < RETRIES:
                time.sleep(1 + attempt)
    raise RuntimeError(str(last))


def cached_fetch(url: str) -> Tuple[bytes, str, bool, dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = cache_key(url)
    data_path = CACHE / f"{key}.bin"
    meta_path = CACHE / f"{key}.json"
    if data_path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if time.time() - float(meta.get("fetched_at", 0)) < CACHE_TTL:
            return data_path.read_bytes(), "cache", True, meta
    body, status = fetch(url)
    meta = {"url": url, "fetched_at": time.time(), "sha256": hashlib.sha256(body).hexdigest(), "size": len(body)}
    data_path.write_bytes(body)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return body, status, False, meta


def source_urls() -> List[Tuple[str, str, str]]:
    data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    base = (data.get("blackmatrix7_base") or "").rstrip("/")
    result = []
    for sid, meta in (data.get("sources") or {}).items():
        if not isinstance(meta, dict):
            continue
        bm = meta.get("blackmatrix7")
        if isinstance(bm, dict) and bm.get("path"):
            result.append((sid, f"{base}/{bm['path']}", str(bm.get("sha256") or "")))
        for idx, extra in enumerate(meta.get("blackmatrix7_extra") or []):
            if isinstance(extra, dict) and extra.get("path"):
                result.append((f"{sid}-extra{idx}", f"{base}/{extra['path']}", str(extra.get("sha256") or "")))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-integrity", action="store_true", help="fail if a source has no sha256 pin")
    parser.add_argument("--write", action="store_true", help="write build/audit/rule-source-lock.json")
    parser.add_argument("--out", default="build/audit/rule-source-lock.json")
    args = parser.parse_args()

    failures = []
    lock = {"version": 1, "ttl_seconds": CACHE_TTL, "sources": []}
    for name, url, expected in source_urls():
        try:
            body, status, cached, meta = cached_fetch(url)
            actual = hashlib.sha256(body).hexdigest()
            if args.strict_integrity and not expected:
                raise RuntimeError("missing sha256 pin")
            if expected and actual != expected:
                raise RuntimeError(f"sha256 mismatch: expected {expected}, got {actual}")
            lock["sources"].append({"id": name, "url": url, "sha256": actual, "size": len(body), "cached": cached, "status": status})
            suffix = " cache" if cached else ""
            print(f"✅ {name}: {status}{suffix} sha256={actual[:16]}…")
        except Exception as exc:
            failures.append(f"{name}: {url}: {exc}")
            print(f"❌ {name}: {exc}")

    if args.write:
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✅ wrote {out}")

    if failures:
        print("\nRule source health failures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("\n✅ all configured rule sources are healthy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

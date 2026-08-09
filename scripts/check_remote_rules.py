#!/usr/bin/env python3
"""Validate declared latest remote-rule URLs and their published assets."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/"


def fetch(url: str, timeout: float) -> tuple[int, str]:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "Proxy-Config-Center/remote-rule-check"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.geturl()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.geturl()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed: {url}: {exc.reason}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="dist/release-manifest.json")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if manifest.get("remote_policy") != "latest":
        raise SystemExit("remote_policy must be latest")

    assets = [item["asset"] for item in manifest.get("clients", []) + manifest.get("rules", [])]
    if not assets:
        raise SystemExit("manifest contains no remote assets")

    failures = []
    for asset in assets:
        url = args.base_url.rstrip("/") + "/" + asset
        try:
            status, final_url = fetch(url, args.timeout)
        except RuntimeError as exc:
            failures.append(str(exc))
            continue
        if status != 200:
            failures.append(f"HTTP {status}: {url} -> {final_url}")
        else:
            print(f"OK HTTP 200: {url}")

    if failures:
        print("Remote latest URL validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Validated {len(assets)} latest remote assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

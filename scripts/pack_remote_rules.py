#!/usr/bin/env python3
"""Download the declared upstream rule sources into release-native assets."""
from __future__ import annotations

import argparse
import urllib.error
import urllib.request
from pathlib import Path

from ir import build_ir


def fetch(url: str, target: Path, timeout: float) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Proxy-Config-Center/release-rule-pack"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}: {url}")
            data = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed: {url}: {exc.reason}") from exc
    if not data:
        raise RuntimeError(f"empty rule source: {url}")
    target.write_bytes(data)


def list_url(url: str) -> str:
    if "/rule/Clash/" in url:
        return url.replace("/rule/Clash/", "/rule/Surge/").replace(".yaml", ".list")
    if url.endswith(".yaml"):
        return url[:-5] + ".list"
    return url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/rules")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    ir = build_ir()
    seen: set[str] = set()

    for source in ir.rule_sources:
        for bm in source.bm_sets:
            ext = ".list" if bm.path.endswith(".list") else ".yaml"
            yaml_asset = f"rule-{bm.key}{ext}"
            if yaml_asset not in seen:
                fetch(bm.url, output / yaml_asset, args.timeout)
                seen.add(yaml_asset)

            if ext == ".yaml":
                list_asset = f"rule-{bm.key}.list"
                if list_asset not in seen:
                    fetch(list_url(bm.url), output / list_asset, args.timeout)
                    seen.add(list_asset)
            elif "/rule/Clash/" in bm.url:
                list_asset = f"rule-{bm.key}.list"
                if list_asset not in seen:
                    fetch(list_url(bm.url), output / list_asset, args.timeout)
                    seen.add(list_asset)

    if not seen:
        raise SystemExit("No remote rule assets were generated")
    print(f"Generated {len(seen)} remote rule assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

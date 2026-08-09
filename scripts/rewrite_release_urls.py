#!/usr/bin/env python3
"""Rewrite supported client rule URLs to the stable raw latest-rules branch."""
from __future__ import annotations

import argparse
from pathlib import Path

from ir import build_ir

BASE = "https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/"


def list_url(url: str, flavor: str) -> str:
    if "/rule/Clash/" in url:
        return url.replace("/rule/Clash/", f"/rule/{flavor}/").replace(".yaml", ".list")
    return url


def rewrite_root(root: Path, ir=None) -> int:
    root = Path(root)
    replacements: dict[str, str] = {}
    ir = ir or build_ir()
    for source in ir.rule_sources:
        for bm in source.bm_sets:
            if bm.url.endswith(".yaml"):
                replacements[bm.url] = f"{BASE}rule-{bm.key}.yaml"
                replacements[list_url(bm.url, "Surge")] = f"{BASE}rule-{bm.key}.list"
            else:
                replacements[bm.url] = f"{BASE}rule-{bm.key}.list"

    files = [p for p in root.rglob("*") if p.is_file() and p.suffix in {".yaml", ".yml", ".conf", ".json"}]
    changed = 0
    for path in files:
        if path.name in {"release-manifest.json"}:
            continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="dist")
    args = parser.parse_args()
    changed = rewrite_root(Path(args.root))
    print(f"Rewrote raw latest-rules URLs in {changed} client assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

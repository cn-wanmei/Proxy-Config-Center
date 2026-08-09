#!/usr/bin/env python3
"""Rewrite supported client rule URLs to stable latest-rules assets."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from ir import build_ir

BASE = "https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/"
BLACKMATRIX = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/"
FLAVORS = ("Clash", "Surge", "Loon", "Shadowrocket", "Stash", "Egern")
CLIENT_ASSETS = {
    "clash.yaml",
    "clash-meta.yaml",
    "stash.yaml",
    "egern.yaml",
    "loon.conf",
    "shadowrocket.conf",
    "sing-box.json",
}


def rewrite_root(root: Path, ir=None) -> int:
    root = Path(root)
    replacements: dict[str, str] = {}
    ir = ir or build_ir()
    for source in ir.rule_sources:
        for bm in source.bm_sets:
            path = str(bm.path).lstrip("/")
            ext = Path(path).suffix.lower()
            target_ext = ".yaml" if ext == ".yaml" else ".list"
            target = f"{BASE}rule-{bm.key}{target_ext}"
            for flavor in FLAVORS:
                source_url = f"{BLACKMATRIX}{flavor}/{path}"
                replacements[source_url] = target
            # Some generators use a Surge path derived from a Clash YAML source.
            if ext == ".yaml":
                list_path = path[:-5] + ".list"
                for flavor in FLAVORS:
                    replacements[f"{BLACKMATRIX}{flavor}/{list_path}"] = f"{BASE}rule-{bm.key}.list"

    # Only rewrite generated client entrypoints.  Rule source metadata such as
    # dist/sources.yaml intentionally retains the authoritative upstream source
    # URL; rewriting that metadata would destroy provenance and can trigger a
    # false-positive leftover check when the upstream base URL is not a client
    # rule reference.
    files = [
        root / name
        for name in sorted(CLIENT_ASSETS)
        if (root / name).is_file()
    ]
    changed = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        # Fail closed if a generated client still contains a BlackMatrix rule URL.
        if BLACKMATRIX in updated:
            leftovers = re.findall(
                r"https://raw\.githubusercontent\.com/blackmatrix7/ios_rule_script/[^\s,\"']+",
                updated,
            )
            raise RuntimeError(
                f"unrewritten BlackMatrix rule URL in client {path}: {leftovers[:1]}"
            )
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

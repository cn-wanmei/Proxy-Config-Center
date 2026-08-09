#!/usr/bin/env python3
"""Validate the flat release distribution after URL rewriting and manifest generation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from validate_remote_configs import validate

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "common/schemas/release-manifest.schema.json"
CLIENTS = {"clash.yaml", "clash-meta.yaml", "stash.yaml", "egern.yaml", "loon.conf", "shadowrocket.conf", "sing-box.json"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else ROOT / args.root
    manifest_path = root / "release-manifest.json"
    if not manifest_path.exists():
        raise SystemExit("missing dist/release-manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = [e.message for e in Draft202012Validator(schema).iter_errors(manifest)]
    names = {x.get("name") for x in manifest.get("clients", [])}
    if names != CLIENTS:
        errors.append(f"client manifest mismatch: {sorted(names)}")
    if len(manifest.get("clients", [])) != 7:
        errors.append("manifest must contain exactly seven clients")
    for item in manifest.get("clients", []) + manifest.get("rules", []):
        if not item.get("latest_url", "").startswith("https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/"):
            errors.append(f"non-latest URL: {item.get('latest_url')}")
        path = root / item.get("asset", "")
        if not path.exists():
            errors.append(f"missing asset: {item.get('asset')}")
        elif path.stat().st_size != item.get("size"):
            errors.append(f"size mismatch: {item.get('asset')}")
    client_result = validate(root, require_latest=True)
    errors.extend(client_result["errors"])
    if errors:
        for error in errors:
            print(f"❌ {error}")
        return 1
    print(f"✅ release distribution contract valid: 7 clients / {len(manifest['rules'])} rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

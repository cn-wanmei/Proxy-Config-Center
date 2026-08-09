#!/usr/bin/env python3
"""Validate and emit provenance for generated distribution artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "common/schemas/release-manifest.schema.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = [e.message for e in validator.iter_errors(data)]
    for artifact in data.get("clients", []) + data.get("rules", []):
        url = artifact.get("latest_url", "")
        if not url.startswith("https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/"):
            errors.append(f"non-latest Raw URL: {url}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT / "build")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out", default="build/audit/supply-chain.json")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else ROOT / args.root
    errors = []
    manifest_result = None
    if args.manifest:
        manifest = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
        try:
            errors.extend(validate_manifest(manifest))
            manifest_result = {"path": str(manifest), "valid": not errors}
        except Exception as exc:
            errors.append(f"manifest: {type(exc).__name__}: {exc}")
            manifest_result = {"path": str(manifest), "valid": False}
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = os.getenv("GITHUB_SHA", "unknown")
    files = []
    if root.exists():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files.append({"path": str(path.relative_to(root)), "size": path.stat().st_size, "sha256": sha256(path)})
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "commit": commit,
        "release": os.getenv("GITHUB_REF_NAME", ""),
        "manifest": manifest_result,
        "artifacts": files,
        "ok": not errors,
        "errors": errors,
    }
    if args.write:
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

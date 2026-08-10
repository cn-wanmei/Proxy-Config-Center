#!/usr/bin/env python3
"""Release tag immutability gate (Core V2.1)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent


def read_version() -> str:
    p = ROOT / "VERSION"
    if not p.exists():
        raise SystemExit("VERSION file missing")
    return p.read_text(encoding="utf-8").strip()


def normalize_tag(tag: str) -> str:
    tag = tag.strip()
    if not tag.startswith("v"):
        tag = "v" + tag
    if not re.match(r"^v\d+\.\d+\.\d+$", tag):
        raise SystemExit(f"invalid tag format: {tag} (expected vX.Y.Z)")
    return tag


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def tag_exists(tag: str) -> bool:
    try:
        git("rev-parse", "-q", "--verify", f"refs/tags/{tag}")
        return True
    except Exception:
        return False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pins(pins_path: Path) -> List[str]:
    errors: List[str] = []
    if not pins_path.exists():
        return [f"pins missing: {pins_path}"]
    data = json.loads(pins_path.read_text(encoding="utf-8"))
    for art in data.get("artifacts") or []:
        path = ROOT / art["path"]
        if not path.exists():
            errors.append(f"missing artifact for pin: {art['path']}")
            continue
        digest = sha256(path)
        if digest != art.get("sha256"):
            errors.append(f"IMMUTABLE VIOLATION: {art['path']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Release tag immutability gate")
    parser.add_argument("--tag")
    parser.add_argument("--pins", type=Path, default=ROOT / "build" / "audit" / "artifact-pins.json")
    parser.add_argument("--verify-existing", action="store_true")
    parser.add_argument("--require-pins", action="store_true")
    parser.add_argument("--require-source-date-epoch", action="store_true")
    args = parser.parse_args()

    errors: List[str] = []
    version = read_version()
    tag = normalize_tag(args.tag or version)

    if tag[1:] != version:
        errors.append(f"tag {tag} does not match VERSION={version}")

    try:
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "verify_release_workflow.py")], cwd=ROOT)
    except subprocess.CalledProcessError:
        errors.append("release workflow contract check failed")

    exists = tag_exists(tag)
    print(json.dumps({
        "tag": tag,
        "version": version,
        "tag_exists": exists,
        "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH", ""),
    }, ensure_ascii=False))

    if args.require_source_date_epoch and not os.environ.get("SOURCE_DATE_EPOCH"):
        errors.append("SOURCE_DATE_EPOCH not set")

    pins = args.pins if args.pins.is_absolute() else ROOT / args.pins
    if exists:
        print(f"tag {tag} already exists — immutability forbids retag/overwrite")
        if args.verify_existing:
            errors.extend(verify_pins(pins))
        else:
            errors.append(f"tag {tag} already exists (immutable); refuse new release with same tag")
    else:
        if args.require_pins or pins.exists():
            if not pins.exists() and args.require_pins:
                errors.append(f"pins required but missing: {pins}")
            elif pins.exists():
                data = json.loads(pins.read_text(encoding="utf-8"))
                if not data.get("artifacts"):
                    errors.append("pins file has no artifacts")
                else:
                    print(f"pins ok: {len(data['artifacts'])} artifacts")

    if errors:
        print("\u274c release tag gate FAILED")
        for e in errors:
            print(" ", e)
        return 1
    print(f"\u2705 release tag gate OK for {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

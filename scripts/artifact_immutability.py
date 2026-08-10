#!/usr/bin/env python3
"""Release Artifact Immutability — verify pinned SHA256 sets."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pins", type=Path, default=ROOT / "build" / "audit" / "artifact-pins.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    pins = args.pins if args.pins.is_absolute() else ROOT / args.pins
    if not pins.exists():
        msg = f"pin file missing: {pins}"
        if args.strict:
            print("\u274c", msg)
            return 1
        print("skip:", msg)
        return 0
    data = json.loads(pins.read_text(encoding="utf-8"))
    errors = []
    checked = 0
    for art in data.get("artifacts") or []:
        path = ROOT / art["path"]
        if not path.exists():
            errors.append(f"missing artifact: {art['path']}")
            continue
        digest = sha256(path)
        checked += 1
        if digest != art.get("sha256"):
            errors.append(f"hash mismatch: {art['path']}")
    print(json.dumps({"checked": checked, "errors": len(errors)}, ensure_ascii=False))
    if errors:
        for e in errors:
            print(" ", e)
        return 1 if args.strict else 0
    print("\u2705 artifact pins consistent with workspace")
    return 0


if __name__ == "__main__":
    sys.exit(main())

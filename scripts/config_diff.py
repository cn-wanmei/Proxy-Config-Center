#!/usr/bin/env python3
"""Guardrail and machine-readable diff for Core/platform source changes."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_TOTAL = int(os.getenv("MAX_CONFIG_CHANGED_LINES", "2500"))
MAX_FILE = int(os.getenv("MAX_CONFIG_CHANGED_LINES_PER_FILE", "800"))


def collect(base_sha: str, head: str = "HEAD") -> dict:
    proc = subprocess.run(
        ["git", "diff", "--numstat", f"{base_sha}...{head}", "--", "core", "platforms"],
        text=True, capture_output=True, check=True,
    )
    files, total, failures = [], 0, []
    for line in proc.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        added, deleted, path = int(parts[0]), int(parts[1]), parts[2]
        changed = added + deleted
        total += changed
        item = {"path": path, "added": added, "deleted": deleted, "changed": changed}
        files.append(item)
        if changed > MAX_FILE:
            failures.append(f"{path}: {changed} changed lines > {MAX_FILE}")
    if total > MAX_TOTAL:
        failures.append(f"total Core/platform changes {total} > {MAX_TOTAL}")
    return {"version": 1, "base": base_sha, "head": head, "total_changed": total, "files": files,
            "limits": {"total": MAX_TOTAL, "per_file": MAX_FILE}, "failures": failures, "ok": not failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.getenv("BASE_SHA", ""))
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out", default="build/audit/config-diff.json")
    args = parser.parse_args()
    if not args.base:
        print("ℹ️ BASE_SHA not provided; skipping cross-commit diff guard")
        return 0
    result = collect(args.base, args.head)
    for item in result["files"]:
        print(f"{item['path']}: +{item['added']} -{item['deleted']} ({item['changed']})")
    print(f"Core/platform diff: {result['total_changed']} changed lines")
    if args.write:
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result["failures"]:
        print("❌ Large configuration-source change detected:")
        for failure in result["failures"]:
            print(f"  - {failure}")
        return 1
    print("✅ configuration-source diff within safety limits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

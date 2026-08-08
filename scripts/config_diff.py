#!/usr/bin/env python3
"""Guardrail for unexpectedly large generated configuration changes."""

import os
import subprocess
import sys

MAX_TOTAL = int(os.getenv("MAX_GENERATED_CHANGED_LINES", "2500"))
MAX_FILE = int(os.getenv("MAX_GENERATED_CHANGED_LINES_PER_FILE", "800"))


def main() -> int:
    proc = subprocess.run(
        ["git", "diff", "--numstat", "--", "build"],
        text=True,
        capture_output=True,
        check=True,
    )
    total = 0
    failures = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        if not added.isdigit() or not deleted.isdigit():
            continue
        changed = int(added) + int(deleted)
        total += changed
        print(f"{path}: +{added} -{deleted} ({changed})")
        if changed > MAX_FILE:
            failures.append(f"{path}: {changed} changed lines > {MAX_FILE}")

    print(f"Generated config diff: {total} changed lines (limit {MAX_TOTAL})")
    if total > MAX_TOTAL:
        failures.append(f"total generated changes {total} > {MAX_TOTAL}")
    if failures:
        print("❌ Large generated diff detected:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("✅ generated diff within safety limits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Secondary parse validation of generated artifacts (post-compile)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import yaml
except ImportError:
    print("PyYAML required")
    sys.exit(1)

from engines.security import check_dns_block


def load_any(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return None


def main() -> int:
    roots = []
    for name in ("build", "final"):
        p = ROOT / name
        if p.is_dir():
            roots.append(p)
    if not roots:
        print("no build/ or final/ — skip secondary parse")
        return 0

    errors = []
    checked = 0
    for root in roots:
        for path in root.rglob("*"):
            if path.suffix not in (".yaml", ".yml", ".json"):
                continue
            try:
                data = load_any(path)
            except Exception as exc:
                errors.append(f"{path}: parse failed: {exc}")
                continue
            if not isinstance(data, dict):
                continue
            checked += 1
            dns = data.get("dns")
            if isinstance(dns, dict):
                for e in check_dns_block(dns, platform=path.parent.name):
                    errors.append(f"{path}: {e}")

    print(f"secondary parse: {checked} configs")
    if errors:
        print("❌")
        for e in errors:
            print(" ", e)
        return 1
    print("✅ secondary parse OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

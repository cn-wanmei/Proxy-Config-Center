#!/usr/bin/env python3
"""Strict boundary guard: Core may contain rules only."""
from __future__ import annotations

from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "core"
ALLOWED_TOP_LEVEL = {"rules"}


def audit_core_boundary() -> List[str]:
    errors: List[str] = []
    if not CORE.exists():
        return ["core/ missing"]

    for entry in sorted(CORE.iterdir()):
        if entry.name not in ALLOWED_TOP_LEVEL:
            errors.append(f"{entry.relative_to(ROOT)}: non-rule core domain is forbidden")

    rules = CORE / "rules"
    if not rules.exists():
        errors.append("core/rules/ missing")
        return errors

    forbidden_tokens = (
        "mixed-port",
        "external-controller",
        "dns:",
        "proxies:",
        "proxy-groups:",
        "tun:",
        "fake-ip",
        "rule-providers:",
    )
    for path in sorted(rules.rglob("*")):
        if not path.is_file() or path.suffix not in {".yaml", ".yml", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for token in forbidden_tokens:
            if token in text:
                errors.append(f"{path.relative_to(ROOT)}: forbidden client/runtime key '{token}'")

    return errors


def assert_core_boundary() -> None:
    errors = audit_core_boundary()
    if errors:
        raise SystemExit("CORE BOUNDARY VIOLATION:\n  " + "\n  ".join(errors))


if __name__ == "__main__":
    assert_core_boundary()
    print("OK core boundary")

#!/usr/bin/env python3
"""Core boundary guard (3.1) — client config logic must not flow into Core."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "core"
FORBIDDEN_IMPORTS = re.compile(r"(platforms\.|adapter\.render|build_clash_dns|emit_platform|full.?client)", re.I)


def audit_core_boundary() -> List[str]:
    errors: List[str] = []
    if not CORE.exists():
        return ["core/ missing"]
    for path in sorted(CORE.rglob("*")):
        if not path.is_file() or path.suffix not in {".yaml", ".yml", ".py", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(ROOT))
        if path.suffix in {".yaml", ".yml"}:
            if "mixed-port" in text or "external-controller" in text:
                errors.append(f"{rel}: client runtime keys in core/")
        if path.suffix == ".py" and FORBIDDEN_IMPORTS.search(text):
            errors.append(f"{rel}: forbidden client import in core python")
    rc = ROOT / "scripts" / "rule_compile.py"
    if rc.exists():
        t = rc.read_text(encoding="utf-8")
        if "render_platform(" in t or "from build import" in t:
            errors.append("rule_compile.py must not invoke full client render")
    return errors


def assert_core_boundary() -> None:
    errs = audit_core_boundary()
    if errs:
        raise SystemExit("CORE BOUNDARY VIOLATION:\n  " + "\n  ".join(errs))

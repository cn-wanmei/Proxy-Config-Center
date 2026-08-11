#!/usr/bin/env python3
"""Rule audit gate (3.1) — fail-closed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist/audit")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    errors: list[str] = []
    from engines.core_boundary import audit_core_boundary
    errors.extend(audit_core_boundary())
    from engines.rule_intelligence import run_intelligence
    report = run_intelligence(hard_conflicts=True)
    errors.extend(report["errors"])
    try:
        from rule_audit import audit
        index, duplicates, conflicts, unreachable, invalid_targets = audit()
        for r in invalid_targets:
            errors.append(f"invalid_target: {r.get('group')} {r.get('type')} {r.get('value')}")
        for c in conflicts:
            errors.append(
                f"audit_conflict: {c.get('kind')} {c['rule'].get('group')}/{c['rule'].get('value')} vs {c['previous'].get('group')}"
            )
        summary = index.get("summary") or {}
    except Exception as exc:
        errors.append(f"rule_audit_crashed: {type(exc).__name__}: {exc}")
        summary = {}
    payload = {
        "ok": len(errors) == 0,
        "errors": errors,
        "intelligence": {
            "atom_count": report.get("atom_count"),
            "conflicts": len(report.get("conflicts") or []),
            "pollution": len(report.get("pollution") or []),
            "source_anomalies": report.get("source_anomalies"),
        },
        "legacy_summary": summary,
    }
    if args.write:
        out.mkdir(parents=True, exist_ok=True)
        (out / "audit-gate.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / "rule-atoms.json").write_text(json.dumps(report.get("atoms") or [], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "error_count": len(errors), "atoms": report.get("atom_count")}, ensure_ascii=False))
    if errors:
        print("\u274c audit gate FAILED (fail-closed)")
        for e in errors[:50]:
            print(" ", e)
        return 1
    print("\u2705 audit gate OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

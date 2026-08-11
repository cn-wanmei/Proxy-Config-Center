#!/usr/bin/env python3
"""Unified Audit gate (3.3) via rule_pipeline."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    from engines.rule_pipeline import run_pipeline, write_pipeline_artifacts
    result = run_pipeline()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "0"
    if args.write:
        write_pipeline_artifacts(result, out, version)
    print(json.dumps({"ok": result.ok, "error_count": len(result.errors), "warning_count": len(result.warnings), "atoms": len(result.atoms), "kept": len(result.kept)}, ensure_ascii=False))
    if not result.ok:
        print("\u274c audit pipeline FAILED (fail-closed)")
        for e in result.errors[:40]:
            print(f"  {e}")
        return 1
    print("\u2705 audit pipeline OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())

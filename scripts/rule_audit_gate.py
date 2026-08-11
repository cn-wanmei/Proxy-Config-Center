#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))


def main() -> int:
    parser = argparse.ArgumentParser(description='Fail-closed rule audit gate')
    parser.add_argument('--out', default='.audit')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    out = Path(args.out)
    out = out if out.is_absolute() else ROOT / out

    from engines.rule_pipeline import run_pipeline, write_pipeline_artifacts

    result = run_pipeline()
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    if args.write:
        write_pipeline_artifacts(result, out, version)

    summary = {
        'ok': result.ok,
        'errors': len(result.errors),
        'warnings': len(result.warnings),
        'rules': len(result.atoms),
        'semantic': result.semantic['summary'],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not result.ok:
        print('❌ audit pipeline FAILED (fail-closed)')
        for error in result.errors[:40]:
            print('  ' + error)
        return 1

    print('✅ audit pipeline OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

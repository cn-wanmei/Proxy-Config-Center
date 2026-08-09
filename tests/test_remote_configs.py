#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_remote_configs import validate


def main() -> int:
    result = validate(ROOT / "build")
    if not result["ok"]:
        for error in result["errors"]:
            print(f"❌ {error}")
        return 1
    assert len(result["clients"]) == 7
    print("✅ seven-client semantic contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

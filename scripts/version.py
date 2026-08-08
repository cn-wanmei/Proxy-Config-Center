#!/usr/bin/env python3
"""Single source of truth for release version metadata."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "VERSION"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def read_version() -> str:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version):
        raise ValueError(f"invalid VERSION: {version!r}")
    return version


def main() -> int:
    print(read_version())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

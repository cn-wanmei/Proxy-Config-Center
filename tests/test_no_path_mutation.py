#!/usr/bin/env python3
"""Guard against reintroducing global sys.path mutation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    offenders = []
    for path in list((ROOT / "scripts").rglob("*.py")) + list((ROOT / "tests").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "sys.path.insert" in text or "sys.path.append" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, f"global sys.path mutation found: {offenders}"
    print("No global sys.path mutation found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rule_compile import compile_rules


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_compile_is_deterministic():
    with TemporaryDirectory() as first, TemporaryDirectory() as second:
        m1 = compile_rules(Path(first))
        m2 = compile_rules(Path(second))
        r1 = Path(first) / "rules"
        r2 = Path(second) / "rules"

        assert m1["online_raw"] is True
        assert m1["package_release"] is False
        assert m1["clients"][0]["client"] == "loon"
        assert tree_hash(r1) == tree_hash(r2)

        global_total = r1 / "Loon" / "Global" / "Global.list"
        google_total = r1 / "Loon" / "Global" / "Google" / "Google.list"
        youtube = r1 / "Loon" / "Global" / "Google" / "YouTube.list"
        google_play = r1 / "Loon" / "Global" / "Google" / "GooglePlay.list"

        assert global_total.exists()
        assert google_total.exists()
        assert youtube.exists()
        assert google_play.exists()

        text = google_total.read_text(encoding="utf-8")
        assert text.startswith("# NAME: Google\n")
        assert "# TOTAL: " in text
        assert "DOMAIN-SUFFIX,google.com" in text

        # The Google aggregate must contain its children, while child files remain independent.
        assert "DOMAIN-SUFFIX,youtube.com" in text
        assert youtube.read_text(encoding="utf-8").startswith("# NAME: YouTube\n")
        assert google_play.read_text(encoding="utf-8").startswith("# NAME: GooglePlay\n")


if __name__ == "__main__":
    test_compile_is_deterministic()
    print("OK rule compile 4.0")

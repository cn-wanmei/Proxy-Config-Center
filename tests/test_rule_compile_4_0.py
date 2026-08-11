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


def test_compile_is_deterministic_for_all_clients():
    with TemporaryDirectory() as first, TemporaryDirectory() as second:
        m1 = compile_rules(Path(first))
        m2 = compile_rules(Path(second))
        r1 = Path(first) / "rules"
        r2 = Path(second) / "rules"

        assert m1["online_raw"] is True
        assert m1["package_release"] is False
        clients = {item["client"] for item in m1["clients"]}
        assert clients == {"loon", "shadowrocket", "stash", "surge"}
        assert tree_hash(r1) == tree_hash(r2)

        for client in sorted(clients):
            client_root = r1 / client.title() if client != "shadowrocket" else r1 / "Shadowrocket"
            if client == "surge":
                client_root = r1 / "Surge"
            elif client == "stash":
                client_root = r1 / "Stash"
            elif client == "loon":
                client_root = r1 / "Loon"

            global_total = client_root / "Global" / "Global.list"
            google_total = client_root / "Global" / "Google" / "Google.list"
            youtube = client_root / "Global" / "Google" / "YouTube.list"
            google_play = client_root / "Global" / "Google" / "GooglePlay.list"

            assert global_total.exists(), client
            assert google_total.exists(), client
            assert youtube.exists(), client
            assert google_play.exists(), client

            text = google_total.read_text(encoding="utf-8")
            assert text.startswith("# NAME: Google\n")
            assert "# TOTAL: " in text
            assert "DOMAIN-SUFFIX,google.com" in text
            assert "DOMAIN-SUFFIX,youtube.com" in text
            assert youtube.read_text(encoding="utf-8").startswith("# NAME: YouTube\n")
            assert google_play.read_text(encoding="utf-8").startswith("# NAME: GooglePlay\n")


if __name__ == "__main__":
    test_compile_is_deterministic_for_all_clients()
    print("OK rule compile 4.0 all clients")

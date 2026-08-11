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


def rule_values_from_file(path: Path, client: str) -> list[str]:
    values: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("name =") or line.startswith("routing =") or line == "payload:":
            continue
        if client == "anywhere":
            _, value = line.split(",", 1)
            values.append(value.strip())
        else:
            if line.startswith("-"):
                line = line[1:].strip()
            if "," in line:
                values.append(line.split(",", 1)[1].strip())
    return values


def assert_alphabetical(values: list[str]) -> None:
    assert values == sorted(values, key=lambda value: (value.casefold(), value))


def test_compile_is_deterministic_for_all_clients():
    with TemporaryDirectory() as first, TemporaryDirectory() as second:
        m1 = compile_rules(Path(first))
        m2 = compile_rules(Path(second))
        r1 = Path(first) / "rules"
        r2 = Path(second) / "rules"

        assert m1["online_raw"] is True
        assert m1["package_release"] is False
        clients = {item["client"] for item in m1["clients"]}
        assert clients == {"anywhere", "clashmeta", "loon", "shadowrocket", "stash", "surge"}
        assert tree_hash(r1) == tree_hash(r2)

        roots = {
            "anywhere": r1 / "Anywhere",
            "clashmeta": r1 / "ClashMeta",
            "loon": r1 / "Loon",
            "shadowrocket": r1 / "Shadowrocket",
            "stash": r1 / "Stash",
            "surge": r1 / "Surge",
        }
        for client, client_root in roots.items():
            global_total = client_root / "Global" / ("Global.arrs" if client == "anywhere" else "Global.yaml" if client == "clashmeta" else "Global.list")
            google_total = client_root / "Global" / "Google" / ("Google.arrs" if client == "anywhere" else "Google.yaml" if client == "clashmeta" else "Google.list")
            youtube = client_root / "Global" / "Google" / ("YouTube.arrs" if client == "anywhere" else "YouTube.yaml" if client == "clashmeta" else "YouTube.list")
            google_play = client_root / "Global" / "Google" / ("GooglePlay.arrs" if client == "anywhere" else "GooglePlay.yaml" if client == "clashmeta" else "GooglePlay.list")

            assert global_total.exists(), client
            assert google_total.exists(), client
            assert youtube.exists(), client
            assert google_play.exists(), client

            text = google_total.read_text(encoding="utf-8")
            if client == "anywhere":
                assert text.startswith("name = Google\nrouting = 0\n")
                assert "2, google.com" in text
            elif client == "clashmeta":
                assert text.startswith("payload:\n")
                assert "- DOMAIN-SUFFIX,google.com" in text
            else:
                assert text.startswith("# NAME: Google\n")
                assert "DOMAIN-SUFFIX,google.com" in text
            assert_alphabetical(rule_values_from_file(google_total, client))
            assert youtube.read_text(encoding="utf-8").startswith("name = YouTube\n" if client == "anywhere" else "payload:\n" if client == "clashmeta" else "# NAME: YouTube\n")
            assert google_play.read_text(encoding="utf-8").startswith("name = GooglePlay\n" if client == "anywhere" else "payload:\n" if client == "clashmeta" else "# NAME: GooglePlay\n")


if __name__ == "__main__":
    test_compile_is_deterministic_for_all_clients()
    print("OK rule compile 4.0 all clients; alphabetical RAW ordering enforced")

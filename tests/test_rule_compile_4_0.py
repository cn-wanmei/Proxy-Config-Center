#!/usr/bin/env python3
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from rule_compile import compile_rules


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(b'\0')
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_compile_is_deterministic():
    with TemporaryDirectory() as first, TemporaryDirectory() as second:
        m1 = compile_rules(Path(first))
        m2 = compile_rules(Path(second))
        r1 = Path(first) / 'rules'
        r2 = Path(second) / 'rules'
        assert m1['online_raw'] is True
        assert m1['package_release'] is False
        assert m1['clients'][0]['client'] == 'loon'
        assert tree_hash(r1) == tree_hash(r2)

        google = r1 / 'rules' if (r1 / 'rules').exists() else r1
        google_files = list(google.rglob('Google.list'))
        youtube_files = list(google.rglob('YouTube.list'))
        play_files = list(google.rglob('GooglePlay.list'))
        assert google_files
        assert youtube_files
        assert play_files
        assert any('/Loon/Global/Google/Google.list' in str(p).replace('\\', '/') for p in google_files)
        assert any('/Loon/Global/Google/YouTube.list' in str(p).replace('\\', '/') for p in youtube_files)
        assert any('/Loon/Global/Google/GooglePlay.list' in str(p).replace('\\', '/') for p in play_files)

        text = google_files[0].read_text(encoding='utf-8')
        assert text.startswith('# NAME: Google\n')
        assert 'DOMAIN-SUFFIX,google.com' in text


if __name__ == '__main__':
    test_compile_is_deterministic()
    print('OK rule compile 4.0')

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
        assert m1['deterministic'] is True
        assert m1['online_raw'] is True
        assert m1['package_release'] is False
        assert m1['rule_count'] > 0
        assert tree_hash(r1) == tree_hash(r2)
        assert sorted(p.name for p in r1.glob('*.yaml')) == sorted(p.name for p in r2.glob('*.yaml'))


if __name__ == '__main__':
    test_compile_is_deterministic()
    print('OK rule compile 4.0')

#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from engines.semantic import analyze, content_sha256, global_rule_id, scoped_rule_id


def test_identity():
    assert len(content_sha256('domain-suffix', 'Example.COM.')) == 64
    assert global_rule_id('domain-suffix', 'Example.COM.') == global_rule_id('domain_suffix', 'example.com')
    assert scoped_rule_id('a', 'domain-suffix', 'example.com') != scoped_rule_id('b', 'domain-suffix', 'example.com')


def test_relations():
    duplicate = analyze([
        {'policy_id': 'a', 'type': 'domain-suffix', 'value': 'example.com', 'priority': 100},
        {'policy_id': 'a', 'type': 'domain-suffix', 'value': 'example.com', 'priority': 100},
    ])
    assert 'duplicate' in {finding['kind'] for finding in duplicate['findings']}

    conflict = analyze([
        {'policy_id': 'a', 'type': 'domain-suffix', 'value': 'example.com', 'priority': 100},
        {'policy_id': 'a', 'type': 'domain-suffix', 'value': 'example.com', 'priority': 200},
    ])
    assert 'conflict' in {finding['kind'] for finding in conflict['findings']}

    shared = analyze([
        {'policy_id': 'a', 'type': 'domain-suffix', 'value': 'example.com', 'priority': 100},
        {'policy_id': 'b', 'type': 'domain-suffix', 'value': 'example.com', 'priority': 100},
    ])
    assert 'shared' in {finding['kind'] for finding in shared['findings']}

    shadow = analyze([
        {'policy_id': 'a', 'type': 'domain-suffix', 'value': 'example.com', 'priority': 100},
        {'policy_id': 'a', 'type': 'domain-suffix', 'value': 'mail.example.com', 'priority': 200},
    ])
    assert 'shadow' in {finding['kind'] for finding in shadow['findings']}


def test_validation():
    result = analyze([
        {'policy_id': 'x', 'type': 'domain', 'value': 'bad_domain'},
        {'policy_id': 'x', 'type': 'ip-cidr', 'value': 'not-an-ip'},
    ])
    kinds = {item['kind'] for item in result['validation']}
    assert {'invalid_domain', 'invalid_ip_or_cidr'} <= kinds


if __name__ == '__main__':
    test_identity(); test_relations(); test_validation()
    print('OK semantic 4.0')

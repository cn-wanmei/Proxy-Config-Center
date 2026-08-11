#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import ipaddress
import re
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Sequence


def norm_type(value: Any) -> str:
    return str(value or '').strip().lower().replace('-', '_')


def norm_value(value: Any) -> str:
    return str(value or '').strip().lower().rstrip('.')


def content_sha256(rule_type: str, value: str) -> str:
    return hashlib.sha256(f'{norm_type(rule_type)}|{norm_value(value)}'.encode()).hexdigest()


def global_rule_id(rule_type: str, value: str) -> str:
    return f'{norm_type(rule_type)}:{content_sha256(rule_type, value)[:16]}'


def scoped_rule_id(policy_id: str, rule_type: str, value: str) -> str:
    return f'{norm_value(policy_id)}:{global_rule_id(rule_type, value)}'


def _suffix_parent(parent: str, child: str) -> bool:
    parent, child = norm_value(parent).lstrip('.'), norm_value(child).lstrip('.')
    return parent != child and child.endswith('.' + parent)


def _valid_domain(value: str) -> bool:
    value = norm_value(value)
    if not value or len(value) > 253 or ' ' in value or '_' in value:
        return False
    labels = value.split('.')
    if any(not x or len(x) > 63 for x in labels):
        return False
    return all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?[a-z0-9]?', x) for x in labels)


def _is_ip_or_cidr(value: str) -> bool:
    try:
        ipaddress.ip_network(value, strict=False) if '/' in value else ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def classify_pair(a: Mapping[str, Any], b: Mapping[str, Any]) -> str | None:
    at, av = norm_type(a.get('type')), norm_value(a.get('value'))
    bt, bv = norm_type(b.get('type')), norm_value(b.get('value'))
    if at == bt and av == bv:
        if a.get('policy_id') != b.get('policy_id'):
            return 'shared'
        if int(a.get('priority', 500)) == int(b.get('priority', 500)):
            return 'duplicate'
        return 'conflict'
    if at == bt == 'domain_suffix' and a.get('policy_id') == b.get('policy_id'):
        if _suffix_parent(av, bv):
            return 'shadow' if int(a.get('priority', 500)) <= int(b.get('priority', 500)) else 'overlap'
        if _suffix_parent(bv, av):
            return 'shadow' if int(b.get('priority', 500)) <= int(a.get('priority', 500)) else 'overlap'
    return None


def analyze(rules: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    normalized = []
    exact = defaultdict(list)
    suffix = defaultdict(list)
    for raw in rules:
        rule = dict(raw)
        rule['policy_id'] = str(rule.get('policy_id') or rule.get('group') or '')
        rule['type'] = norm_type(rule.get('type'))
        rule['value'] = norm_value(rule.get('value'))
        rule['priority'] = int(rule.get('priority', 500))
        rule['global_rule_id'] = global_rule_id(rule['type'], rule['value'])
        rule['rule_id'] = scoped_rule_id(rule['policy_id'], rule['type'], rule['value'])
        rule['sha256'] = content_sha256(rule['type'], rule['value'])
        normalized.append(rule)
        exact[(rule['type'], rule['value'])].append(len(normalized) - 1)
        if rule['type'] == 'domain_suffix':
            suffix[rule['value']].append(len(normalized) - 1)

    findings = []
    for (rtype, value), indexes in sorted(exact.items()):
        if len(indexes) < 2:
            continue
        policies = sorted({normalized[i]['policy_id'] for i in indexes})
        priorities = sorted({normalized[i]['priority'] for i in indexes})
        rule_ids = [normalized[i]['rule_id'] for i in indexes]
        if len(policies) > 1:
            findings.append({
                'kind': 'shared',
                'type': rtype,
                'value': value,
                'policies': policies,
                'priorities': priorities,
                'rule_ids': rule_ids,
            })
            # The same matcher in independent policy files is not a conflict.
            continue
        kind = 'duplicate' if len(priorities) == 1 else 'conflict'
        findings.append({
            'kind': kind,
            'type': rtype,
            'value': value,
            'policies': policies,
            'priorities': priorities,
            'rule_ids': rule_ids,
        })

    emitted_pairs = set()
    for child_index, child in enumerate(normalized):
        if child['type'] != 'domain_suffix':
            continue
        labels = child['value'].split('.')
        for cut in range(1, len(labels)):
            parent_value = '.'.join(labels[cut:])
            for parent_index in suffix.get(parent_value, []):
                if parent_index == child_index:
                    continue
                parent = normalized[parent_index]
                relation = classify_pair(parent, child)
                if relation not in {'shadow', 'overlap'}:
                    continue
                pair = tuple(sorted((parent['rule_id'], child['rule_id'])) + [relation])
                if pair in emitted_pairs:
                    continue
                emitted_pairs.add(pair)
                findings.append({
                    'kind': relation,
                    'parent': parent['rule_id'],
                    'child': child['rule_id'],
                    'parent_policy': parent['policy_id'],
                    'child_policy': child['policy_id'],
                    'parent_value': parent['value'],
                    'child_value': child['value'],
                    'parent_priority': parent['priority'],
                    'child_priority': child['priority'],
                })

    validation = []
    for rule in normalized:
        if not rule['value']:
            validation.append({'kind': 'empty_value', 'rule_id': rule['rule_id']})
        elif rule['type'] in ('domain', 'domain_suffix') and not _valid_domain(rule['value']):
            validation.append({'kind': 'invalid_domain', 'rule_id': rule['rule_id'], 'value': rule['value']})
        elif rule['type'] in ('ip', 'ip_cidr', 'ip_cidr6') and not _is_ip_or_cidr(rule['value']):
            validation.append({'kind': 'invalid_ip_or_cidr', 'rule_id': rule['rule_id'], 'value': rule['value']})

    return {
        'rules': normalized,
        'findings': findings,
        'validation': validation,
        'summary': {
            'rules': len(normalized),
            'duplicates': sum(f['kind'] == 'duplicate' for f in findings),
            'shared': sum(f['kind'] == 'shared' for f in findings),
            'conflicts': sum(f['kind'] == 'conflict' for f in findings),
            'shadow': sum(f['kind'] == 'shadow' for f in findings),
            'overlap': sum(f['kind'] == 'overlap' for f in findings),
            'validation_errors': len(validation),
        },
    }

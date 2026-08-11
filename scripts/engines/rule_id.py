#!/usr/bin/env python3
"""Rule ID / Hash semantics (3.3). content_hash=full SHA256; rule_id=policy:type:hash16."""
from __future__ import annotations
import hashlib
from typing import Sequence

def canonical_pattern(rtype: str, value: str) -> str:
    t = str(rtype or "").strip().lower().replace("-", "_")
    v = str(value or "").strip().lower().rstrip(".")
    if v.startswith("."):
        v = v[1:]
    return f"{t}|{v}"

def content_hash(rtype: str, value: str) -> str:
    return hashlib.sha256(canonical_pattern(rtype, value).encode("utf-8")).hexdigest()

def content_hash16(rtype: str, value: str) -> str:
    return content_hash(rtype, value)[:16]

def make_rule_id(policy_id: str, rtype: str, value: str) -> str:
    return f"{policy_id}:{str(rtype).replace('-', '_')}:{content_hash16(rtype, value)}"

def payload_sha256(parts: Sequence[str]) -> str:
    h = hashlib.sha256()
    for line in parts:
        h.update(line.encode("utf-8")); h.update(b"\n")
    return h.hexdigest()

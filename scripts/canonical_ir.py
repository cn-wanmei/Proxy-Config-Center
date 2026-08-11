#!/usr/bin/env python3
"""Canonical IR — platform-agnostic IR (2.3). Platform shape via platform_ir."""

from __future__ import annotations
from typing import Any
from ir import build_ir as build_canonical_ir  # noqa: F401
from ir import IconRef, Node, ProxyGroup, ResolvedService  # noqa: F401

def is_canonical(obj: Any) -> bool:
    if obj is None:
        return False
    if hasattr(obj, "routing_mode"):
        return False
    return hasattr(obj, "services") or hasattr(obj, "proxy_groups")

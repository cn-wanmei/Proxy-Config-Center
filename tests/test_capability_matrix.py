#!/usr/bin/env python3
"""Capability hard-fail matrix tests (Core V2)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import (
    assert_platform_compilable,
    capability_matrix,
    validate_compile_capabilities,
    required_platforms,
)


def test_matrix_covers_all_required_platforms():
    matrix = capability_matrix()
    for name in required_platforms():
        assert name in matrix
        row = matrix[name]
        assert "rule_set" in row
        assert "rule_provider" in row
        assert "domain_fallback" in row


def test_compile_capabilities_pass():
    errs = validate_compile_capabilities()
    assert not errs, errs


def test_every_platform_compilable():
    for name in required_platforms():
        assert_platform_compilable(name)


if __name__ == "__main__":
    test_matrix_covers_all_required_platforms()
    test_compile_capabilities_pass()
    test_every_platform_compilable()
    print("OK capability matrix")

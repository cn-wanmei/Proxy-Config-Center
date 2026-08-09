#!/usr/bin/env python3
"""Shared side-effect-free engine utilities.

Provides cached YAML loading and shared priority constants used across
IR compilation, rule audit, and validation.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ---------------------------------------------------------------------------
# Priority constants (replace previous magic numbers 500 / 999)
# ---------------------------------------------------------------------------
DEFAULT_PRIORITY: int = 500
FALLBACK_PRIORITY: int = 999


class CoreLoadError(Exception):
    """Structured error for missing or invalid Core files."""

    def __init__(self, path: Path, reason: str, suggestion: str = ""):
        self.path = path
        self.reason = reason
        self.suggestion = suggestion
        msg = f"Core load failed: {path}\n  Reason: {reason}"
        if suggestion:
            msg += f"\n  Suggestion: {suggestion}"
        super().__init__(msg)


def _mtime_key(path: Path) -> tuple:
    try:
        return (str(path.resolve()), path.stat().st_mtime_ns)
    except OSError:
        return (str(path), 0)


@lru_cache(maxsize=128)
def _load_yaml_cached(path_str: str, mtime_ns: int) -> Any:
    path = Path(path_str)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data is not None else {}


def load_yaml(path: Path, *, required: bool = True) -> Any:
    """Load a YAML file with process-level caching keyed by path + mtime."""
    path = Path(path)
    if not path.exists():
        if required:
            raise CoreLoadError(
                path,
                reason="file does not exist",
                suggestion="Ensure the Core file is present and the path is correct relative to the repository root.",
            )
        return {}
    try:
        key = _mtime_key(path)
        return _load_yaml_cached(key[0], key[1])
    except yaml.YAMLError as exc:
        raise CoreLoadError(
            path,
            reason=f"invalid YAML syntax: {exc}",
            suggestion="Run a YAML linter to locate the syntax error.",
        ) from exc
    except OSError as exc:
        raise CoreLoadError(
            path,
            reason=f"I/O error: {exc}",
            suggestion="Check file permissions and that the path is readable.",
        ) from exc


def clear_yaml_cache() -> None:
    _load_yaml_cached.cache_clear()


def get_priority_map(priority_list: Optional[List[dict]] = None) -> Dict[str, int]:
    if not priority_list:
        return {}
    return {
        str(item["id"]): int(item.get("value", DEFAULT_PRIORITY))
        for item in priority_list
        if isinstance(item, dict) and "id" in item
    }

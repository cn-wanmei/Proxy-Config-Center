#!/usr/bin/env python3
"""Shared side-effect-free engine utilities."""

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"missing core file: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

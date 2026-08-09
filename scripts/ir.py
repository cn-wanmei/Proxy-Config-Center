#!/usr/bin/env python3
"""Core → Resolved IR — rules, references, groups, icons, and capabilities."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from engines.capability import (
    all_platforms,
    required_platforms,
    supports_domain_fallback,
    supports_rule_provider,
    supports_rule_set,
)
from engines.utils import load_yaml

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"


@dataclass
class IconRef:
    id: str
    url: str = ""


@dataclass
class ProxyGroup:
    id: str
    name_zh: str
    name_en: str
    type: str
    options: List[Any] = field(default_factory=list)
    default: str = ""
    include_all_nodes: bool = False
    filter: str = ""
    icon: str = ""

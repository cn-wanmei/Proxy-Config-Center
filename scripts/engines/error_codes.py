#!/usr/bin/env python3
"""Standard error codes (3.3)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class RuleError:
    code: str
    message: str
    path: str = ""
    detail: Optional[Dict[str, Any]] = None
    def to_dict(self) -> dict:
        d = {"code": self.code, "message": self.message}
        if self.path: d["path"] = self.path
        if self.detail: d["detail"] = self.detail
        return d
    def __str__(self) -> str:
        base = f"[{self.code}] {self.message}"
        return base + (f" @ {self.path}" if self.path else "")

E_CORE_BOUNDARY = "E_CORE_BOUNDARY"
E_NORMALIZE = "E_NORMALIZE"
E_SEMANTIC_CONFLICT = "E_SEMANTIC_CONFLICT"
E_SUFFIX_SHADOW = "E_SUFFIX_SHADOW"
E_CROSS_POLICY = "E_CROSS_POLICY"
E_POLLUTION = "E_POLLUTION"
E_SOURCE_ANOMALY = "E_SOURCE_ANOMALY"
E_AUDIT_FAIL = "E_AUDIT_FAIL"
E_PIPELINE = "E_PIPELINE"

def format_errors(errors: List[RuleError]) -> str:
    return "\n".join(f"  {e}" for e in errors)

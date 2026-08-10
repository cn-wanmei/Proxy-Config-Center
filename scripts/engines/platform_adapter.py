#!/usr/bin/env python3
"""Platform abstraction — secure emit hard-fail (Core V2.2)."""

from __future__ import annotations

import importlib.util
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class EmitResult:
    platform: str
    config: Any
    kind: str
    security_ok: bool = True
    errors: List[str] = field(default_factory=list)


class PlatformAdapter(ABC):
    name: str

    @abstractmethod
    def render(self, ir: Any, platform_ir: Optional[Any] = None) -> EmitResult:
        ...

    def validate_emit(self, result: EmitResult) -> List[str]:
        errors: List[str] = []
        cfg = result.config
        if not isinstance(cfg, dict):
            return errors
        dns = cfg.get("dns")
        if isinstance(dns, dict) and self.name in ("clash", "clash-meta", "stash"):
            from engines.security_policy import load_security_policy
            from engines.secure_types import InsecureEndpointError, SecureDNSEndpoint
            policy = load_security_policy()
            errors.extend(policy.validate_dns_block(dns, platform=self.name))
            for key in ("nameserver", "fallback", "proxy-server-nameserver"):
                for u in dns.get(key) or []:
                    try:
                        SecureDNSEndpoint(str(u))
                    except InsecureEndpointError as exc:
                        errors.append(f"{self.name}:{key}: {exc}")
        return errors


class FileRendererAdapter(PlatformAdapter):
    def __init__(self, name: str, kind: str = "yaml"):
        self.name = name
        self.kind = kind

    def render(self, ir: Any, platform_ir: Optional[Any] = None) -> EmitResult:
        path = ROOT / "platforms" / self.name / "adapter" / "render.py"
        spec = importlib.util.spec_from_file_location(f"adapter_{self.name}", path)
        if spec is None or spec.loader is None:
            return EmitResult(self.name, None, self.kind, False, [f"missing renderer: {path}"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if "platform" in inspect.signature(mod.render).parameters:
            cfg = mod.render(ir, platform=self.name)
        else:
            cfg = mod.render(ir)
        result = EmitResult(platform=self.name, config=cfg, kind=self.kind)
        errs = self.validate_emit(result)
        result.errors = errs
        result.security_ok = not errs
        return result


REGISTRY: Dict[str, PlatformAdapter] = {}


def get_adapter(platform: str) -> PlatformAdapter:
    kinds = {
        "clash-meta": "yaml", "clash": "yaml", "stash": "yaml", "egern": "yaml",
        "loon": "text", "shadowrocket": "text", "sing-box": "json",
    }
    if platform not in REGISTRY:
        REGISTRY[platform] = FileRendererAdapter(platform, kinds.get(platform, "yaml"))
    return REGISTRY[platform]


def emit_platform(platform: str, ir: Any) -> EmitResult:
    adapter = get_adapter(platform)
    result = adapter.render(ir)
    if not result.security_ok:
        from engines.security import SecurityViolation
        raise SecurityViolation(
            "INSECURE_EMIT_BLOCKED",
            "; ".join(result.errors) or "security validation failed",
            path=platform,
        )
    return result

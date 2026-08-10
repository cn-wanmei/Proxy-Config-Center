#!/usr/bin/env python3
"""Incremental compilation cache (Core V2.2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

ROOT = Path(__file__).resolve().parents[2]
CACHE_PATH = ROOT / "build" / "audit" / "incremental-cache.json"


def _hash_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint_core(core: Path = ROOT / "core") -> str:
    h = hashlib.sha256()
    if not core.exists():
        return h.hexdigest()
    for path in sorted(core.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        rel = str(path.relative_to(core)).replace("\\", "/")
        h.update(rel.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def fingerprint_platform(platform: str) -> str:
    h = hashlib.sha256()
    base = ROOT / "platforms" / platform
    for rel in ("capabilities.yaml", "adapter/render.py"):
        p = base / rel
        h.update(rel.encode())
        h.update(_hash_file(p).encode())
    for eng in (
        "scripts/engines/dns_engine.py",
        "scripts/engines/security_policy.py",
        "scripts/engines/secure_types.py",
        "scripts/engines/resolver_scheduler.py",
        "scripts/engines/dynamic_policy.py",
        "scripts/engines/rules_emit.py",
    ):
        h.update(eng.encode())
        h.update(_hash_file(ROOT / eng).encode())
    return h.hexdigest()


def load_cache(path: Path = CACHE_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {"core": "", "platforms": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"core": "", "platforms": {}}


def save_cache(cache: Dict[str, Any], path: Path = CACHE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def platforms_to_rebuild(platforms: Iterable[str], *, force: bool = False) -> Dict[str, Any]:
    core_fp = fingerprint_core()
    cache = load_cache()
    rebuild: List[str] = []
    skipped: List[str] = []
    fps: Dict[str, str] = {}
    core_changed = force or cache.get("core") != core_fp
    prev_plat = cache.get("platforms") or {}
    for name in platforms:
        pfp = fingerprint_platform(name)
        fps[name] = pfp
        if force or core_changed or prev_plat.get(name) != pfp:
            rebuild.append(name)
        else:
            skipped.append(name)
    return {"rebuild": rebuild, "skipped": skipped, "core_fp": core_fp, "platform_fps": fps, "core_changed": core_changed}


def commit_cache(core_fp: str, platform_fps: Dict[str, str], rebuilt: Set[str]) -> None:
    cache = load_cache()
    cache["core"] = core_fp
    plats = dict(cache.get("platforms") or {})
    for name, fp in platform_fps.items():
        if name in rebuilt or name not in plats:
            plats[name] = fp
    for name in rebuilt:
        if name in platform_fps:
            plats[name] = platform_fps[name]
    cache["platforms"] = plats
    save_cache(cache)

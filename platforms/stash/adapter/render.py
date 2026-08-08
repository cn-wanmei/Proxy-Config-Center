#!/usr/bin/env python3
"""Stash renderer — Clash-compatible core + Stash profile flags.

Uses shared Clash-family emitter with platform='stash' so capabilities
and future Stash-only fields (profile.store-selected, etc.) stay correct.
"""
import importlib.util
from pathlib import Path
from typing import Any


def render(ir: Any) -> dict:
    path = Path(__file__).resolve().parents[2] / "clash-meta" / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location("cm_stash", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg = mod.render(ir, platform="stash")

    # Stash-specific defaults (safe no-ops on pure Clash clients)
    profile = cfg.setdefault("profile", {})
    if isinstance(profile, dict):
        profile.setdefault("store-selected", True)
        profile.setdefault("store-fake-ip", True)
    return cfg

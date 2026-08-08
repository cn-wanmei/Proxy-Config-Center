#!/usr/bin/env python3
"""Clash — reuse Clash Meta IR renderer."""
import importlib.util
from pathlib import Path

def render(ir):
    path = Path(__file__).resolve().parents[2] / "clash-meta" / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location("cm", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(ir)

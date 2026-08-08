#!/usr/bin/env python3
"""
Stash Renderer (Clash-compatible YAML subset)
"""

import importlib.util
from pathlib import Path

def render(ir):
    meta_path = Path(__file__).resolve().parents[2] / "clash-meta" / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location("cm_render", meta_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render(ir)

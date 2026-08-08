#!/usr/bin/env python3
"""Original Clash Renderer (subset of Clash Meta)."""

import importlib.util
from pathlib import Path

def render(ir):
    # Reuse Clash Meta renderer then strip Meta-only fields
    meta_path = Path(__file__).resolve().parents[2] / "clash-meta" / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location("cm_render", meta_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg = mod.render(ir)
    # Remove Meta-only keys if present
    cfg.pop("find-process-mode", None)
    # url-test groups are fine; include-all-providers may need providers section (user/Sub-Store)
    return cfg

#!/usr/bin/env python3
"""
Build Engine
Core → IR → Platform Renderers → build/
"""

import sys
import importlib.util
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ir import build_ir

def load_renderer(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(f"{platform}_render", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render

def main():
    print("=== Proxy-Config-Center Build ===")
    ir = build_ir()
    print(f"IR loaded: {len(ir.proxy_base)} base, {len(ir.proxy_service)} service, {len(ir.rules)} rules")

    build_dir = ROOT / "build"
    build_dir.mkdir(exist_ok=True)

    for platform in ("clash-meta", "egern"):
        render = load_renderer(platform)
        out_dir = build_dir / platform
        out_dir.mkdir(exist_ok=True)
        config = render(ir)
        out_path = out_dir / "config.yaml"
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"✅ Wrote {out_path}")

    print("Build finished.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

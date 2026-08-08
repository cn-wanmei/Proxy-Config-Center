#!/usr/bin/env python3
"""
Build Engine (P2-13)
Core → Resolved IR → Platform Renderers → build/
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

PLATFORMS = ("clash-meta", "egern")

def load_renderer(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(f"{platform}_render", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render

def main():
    print("=== Proxy-Config-Center Build ===")

    # Validate first
    try:
        from validate import main as validate_main
        rc = validate_main()
        if rc != 0:
            print("Validation failed, abort build")
            return rc
    except Exception as e:
        print(f"Validation warning: {e}")

    ir = build_ir()
    print(f"Resolved IR: {len(ir.base_groups)} base, {len(ir.services)} services, {len(ir.rules)} rules")
    print(f"DNS: {len(ir.resolvers)} resolvers, {len(ir.dns_policies)} policies")

    build_dir = ROOT / "build"
    build_dir.mkdir(exist_ok=True)

    for platform in PLATFORMS:
        render = load_renderer(platform)
        out_dir = build_dir / platform
        out_dir.mkdir(exist_ok=True)
        config = render(ir)
        out_path = out_dir / "config.yaml"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("# AUTO-GENERATED from Core — DO NOT EDIT MANUALLY\n")
            f.write("# Source: core/ | Build: scripts/build.py\n\n")
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"✅ Wrote {out_path}")

    print("Build finished.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

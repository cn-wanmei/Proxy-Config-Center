#!/usr/bin/env python3
"""
Build Engine — all platforms
Core → Resolved IR → Renderers → build/
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

# platform -> output relative path
PLATFORMS = {
    "clash-meta": "clash-meta/config.yaml",
    "clash": "clash/config.yaml",
    "egern": "egern/config.yaml",
    "stash": "stash/config.yaml",
    "loon": "loon/config.conf",
    "shadowrocket": "shadowrocket/config.conf",
}

def load_renderer(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(f"{platform}_render", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render

def write_config(out_path: Path, config):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# AUTO-GENERATED from Core — DO NOT EDIT MANUALLY\n"
        "# Source: core/ | Build: scripts/build.py\n\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        if isinstance(config, str):
            if not config.startswith("#"):
                f.write(header)
            f.write(config)
        else:
            f.write(header)
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def main():
    print("=== Proxy-Config-Center Build ===")

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

    build_dir = ROOT / "build"
    build_dir.mkdir(exist_ok=True)

    for platform, rel in PLATFORMS.items():
        try:
            render = load_renderer(platform)
            config = render(ir)
            out_path = build_dir / rel
            write_config(out_path, config)
            print(f"✅ Wrote {out_path}")
        except Exception as e:
            print(f"❌ {platform}: {e}")
            return 1

    print("Build finished.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

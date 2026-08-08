#!/usr/bin/env python3
"""
Build Engine — all platforms → build/ and final/
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

PLATFORMS = {
    "clash-meta": ("clash-meta/config.yaml", "yaml"),
    "clash": ("clash/config.yaml", "yaml"),
    "egern": ("egern/config.yaml", "yaml"),
    "stash": ("stash/config.yaml", "yaml"),
    "loon": ("loon/config.conf", "text"),
    "shadowrocket": ("shadowrocket/config.conf", "text"),
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
        "# Source: core/ | Build: scripts/build.py\n"
        "# 订阅/节点: 编辑 core/proxies/providers.yaml 后重新 build\n\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        if isinstance(config, str):
            if not config.lstrip().startswith("#"):
                f.write(header)
            f.write(config if config.endswith("\n") else config + "\n")
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

    for out_root_name in ("build", "final"):
        out_root = ROOT / out_root_name
        out_root.mkdir(exist_ok=True)

        for platform, (rel, _kind) in PLATFORMS.items():
            try:
                render = load_renderer(platform)
                config = render(ir)
                out_path = out_root / rel
                write_config(out_path, config)
                print(f"✅ Wrote {out_path}")
            except Exception as e:
                print(f"❌ {platform}: {e}")
                return 1

    # README in final/
    final_readme = ROOT / "final" / "README.md"
    final_readme.write_text(
        "# 最终配置 / Final Configs\n\n"
        "> 由 `python scripts/build.py` 自动生成，请勿手改。\n\n"
        "## 使用前\n\n"
        "1. 编辑 `core/proxies/providers.yaml`\n"
        "   - `subscriptions[].url` → 机场订阅链接\n"
        "   - `nodes[]` → 单节点/多节点（`enabled: true`）\n"
        "2. 重新执行 `python scripts/build.py`\n"
        "3. 从本目录复制对应客户端配置\n\n"
        "| 客户端 | 文件 |\n"
        "|--------|------|\n"
        "| Clash Meta | `clash-meta/config.yaml` |\n"
        "| Clash | `clash/config.yaml` |\n"
        "| Stash | `stash/config.yaml` |\n"
        "| Egern | `egern/config.yaml` |\n"
        "| Loon | `loon/config.conf` |\n"
        "| Shadowrocket | `shadowrocket/config.conf` |\n",
        encoding="utf-8",
    )
    print(f"✅ Wrote {final_readme}")

    print("Build finished.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

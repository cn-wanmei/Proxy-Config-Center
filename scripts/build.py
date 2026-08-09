#!/usr/bin/env python3
"""Build Engine — deterministic platform artifacts; final/ is opt-in only."""

import argparse
import importlib.util
import inspect
import json
import sys
from functools import lru_cache
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent

from ir import build_ir

PLATFORMS = {
    "clash-meta": ("clash-meta/config.yaml", "yaml"),
    "clash": ("clash/config.yaml", "yaml"),
    "stash": ("stash/config.yaml", "yaml"),
    "egern": ("egern/config.yaml", "yaml"),
    "loon": ("loon/config.conf", "text"),
    "shadowrocket": ("shadowrocket/config.conf", "text"),
    "sing-box": ("sing-box/config.json", "json"),
}


@lru_cache(maxsize=None)
def load_renderer(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    if not path.exists():
        raise FileNotFoundError(f"missing renderer: {path}")
    spec = importlib.util.spec_from_file_location(f"{platform.replace('-', '_')}_render", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load renderer: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render


def render_platform(platform: str, ir):
    render = load_renderer(platform)
    if "platform" in inspect.signature(render).parameters:
        return render(ir, platform=platform)
    return render(ir)


def write_config(out_path: Path, config, kind: str):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# AUTO-GENERATED from Core — DO NOT EDIT MANUALLY\n"
        "# Source: core/ | Build: scripts/build.py\n"
        "# 订阅/节点: 编辑 core/proxies/providers.yaml 后重新 build\n\n"
    )
    if kind == "json":
        out_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    with out_path.open("w", encoding="utf-8") as f:
        if isinstance(config, str):
            if not config.lstrip().startswith("#"):
                f.write(header)
            f.write(config if config.endswith("\n") else config + "\n")
        else:
            f.write(header)
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def build_root(root_name: str, ir) -> None:
    out_root = ROOT / root_name
    out_root.mkdir(exist_ok=True)
    for platform, (rel, kind) in PLATFORMS.items():
        config = render_platform(platform, ir)
        out_path = out_root / rel
        write_config(out_path, config, kind)
        print(f"✅ Wrote {out_path}")


def write_rule_audit_index() -> None:
    from rule_audit import audit, markdown

    index, _, _, _, _ = audit()
    audit_dir = ROOT / "build" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "rule-strategy-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (audit_dir / "rule-strategy-index.md").write_text(markdown(index), encoding="utf-8")
    print(f"✅ Wrote {audit_dir / 'rule-strategy-index.json'}")
    print(f"✅ Wrote {audit_dir / 'rule-strategy-index.md'}")


def write_intelligence_reports(ir) -> None:
    from rule_graph import build_graph
    from semantic_matrix import run as run_matrix
    from validate_remote_configs import validate as validate_remote
    from build_report import build_report
    from rewrite_release_urls import rewrite_root

    audit_dir = ROOT / "build" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    changed = rewrite_root(ROOT / "build", ir)
    print(f"✅ Normalized {changed} generated client assets to latest-rules/raw rule URLs")
    graph = build_graph()
    (audit_dir / "rule-graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    remote = validate_remote(ROOT / "build")
    (audit_dir / "remote-config-semantic.json").write_text(json.dumps(remote, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    matrix = run_matrix(ROOT / "build")
    (audit_dir / "domain-semantic-matrix.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = build_report(ROOT / "build")
    (audit_dir / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✅ Wrote intelligence reports to {audit_dir}")
    if graph["conflicts"] or graph["unreachable"] or graph["invalid_targets"]:
        raise RuntimeError("rule conflict/reachability audit failed")
    if not remote["ok"]:
        for error in remote["errors"]:
            print(f"❌ remote-config: {error}")
        raise RuntimeError("remote client semantic validation failed")
    if not matrix["ok"]:
        for error in matrix["errors"]:
            print(f"❌ semantic-matrix: {error}")
        raise RuntimeError("seven-platform semantic matrix failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-final", action="store_true")
    args = parser.parse_args()

    print("=== Proxy-Config-Center Build ===")
    from validate import main as validate_main
    rc = validate_main()
    if rc != 0:
        print("Validation failed, abort build")
        return rc

    ir = build_ir()
    print(f"Resolved IR: {len(ir.base_groups)} base, {len(ir.services)} services, {len(ir.rules)} rules")

    try:
        build_root("build", ir)
        write_rule_audit_index()
        write_intelligence_reports(ir)
        if args.include_final:
            build_root("final", ir)
            (ROOT / "final" / "README.md").write_text(
                "# 最终配置 / Final Configs\n\n> 由 `python scripts/build.py --include-final` 生成，请勿手改。\n",
                encoding="utf-8",
            )
            print(f"✅ Wrote {ROOT / 'final' / 'README.md'}")
    except Exception as exc:
        print(f"❌ Build failed: {type(exc).__name__}: {exc}")
        return 1

    print("Build finished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

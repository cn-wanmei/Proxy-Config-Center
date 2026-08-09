#!/usr/bin/env python3
"""Seven-platform semantic equivalence tests.

The test intentionally compares routing semantics, not serialized syntax. Each adapter
may express the same rule using a different native representation.
"""

import importlib.util
import inspect
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

from ir import build_ir

PLATFORMS = ["clash-meta", "clash", "stash", "egern", "loon", "shadowrocket", "sing-box"]


def load_renderer(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(f"semantic_{platform.replace('-', '_')}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render


def _targets_from_config(config: Any) -> list[str]:
    if isinstance(config, dict):
        rules = config.get("rules")
        if isinstance(rules, list):
            targets = []
            for rule in rules:
                if isinstance(rule, str):
                    if rule.startswith("MATCH,"):
                        targets.append(rule.split(",", 1)[1])
                    elif "," in rule:
                        targets.append(rule.rsplit(",", 1)[-1])
                elif isinstance(rule, dict):
                    for value in rule.values():
                        if isinstance(value, dict):
                            policy = value.get("policy") or value.get("outbound")
                            if policy:
                                targets.append(str(policy))
            return targets
        route = config.get("route") or {}
        if isinstance(route, dict):
            targets = []
            for rule in route.get("rules") or []:
                if isinstance(rule, dict) and rule.get("outbound"):
                    targets.append(str(rule["outbound"]))
            if route.get("final"):
                targets.append(str(route["final"]))
            return targets
    if isinstance(config, str):
        targets = []
        for line in config.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("FINAL,"):
                targets.append(line.split(",", 1)[1])
            elif line.startswith(("DOMAIN-", "RULE-SET,")) and "," in line:
                targets.append(line.rsplit(",", 1)[-1])
        return targets
    return []


def normalize_targets(targets: list[str], ir) -> set[str]:
    reverse = {str(v): k for k, v in ir.id_to_display.items()}
    result = {reverse.get(target, target) for target in targets}
    if "proxy-mode" in result and "final" in {s.id for s in ir.services}:
        result.add("final")
    return result


def main() -> int:
    ir = build_ir()
    expected = {source.target_service for source in ir.rule_sources if source.target_service}
    expected.add("final")
    results = {}
    for platform in PLATFORMS:
        renderer = load_renderer(platform)
        config = renderer(ir, platform=platform) if "platform" in inspect.signature(renderer).parameters else renderer(ir)
        actual = normalize_targets(_targets_from_config(config), ir)
        missing = sorted(expected - actual)
        if missing:
            raise AssertionError(f"{platform}: missing semantic targets: {missing}")
        results[platform] = len(actual)
    assert len(results) == 7
    print("Seven-platform semantic equivalence OK:", results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

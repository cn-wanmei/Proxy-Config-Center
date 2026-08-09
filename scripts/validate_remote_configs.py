#!/usr/bin/env python3
"""Validate the seven published client configs as executable semantic artifacts."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
CLIENTS = {
    "clash": ("clash.yaml", "yaml"),
    "clash-meta": ("clash-meta.yaml", "yaml"),
    "stash": ("stash.yaml", "yaml"),
    "egern": ("egern.yaml", "yaml"),
    "loon": ("loon.conf", "text"),
    "shadowrocket": ("shadowrocket.conf", "text"),
    "sing-box": ("sing-box.json", "json"),
}
RAW_RULE_PREFIX = "https://raw.githubusercontent.com/cn-wanmei/Proxy-Config-Center/latest-rules/rules/"


def _raw_urls(text: str) -> list[str]:
    return re.findall(r"https://raw\.githubusercontent\.com/cn-wanmei/Proxy-Config-Center/[^\s'\"`]+", text)


def _check_yaml(path: Path, platform: str) -> list[str]:
    errors: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ["root is not a mapping"]
    if platform in {"clash", "clash-meta", "stash"}:
        groups = data.get("proxy-groups") or []
        rules = data.get("rules") or []
        providers = data.get("rule-providers") or {}
        if not groups:
            errors.append("missing proxy-groups")
        if not rules:
            errors.append("missing rules")
        if not providers:
            errors.append("missing rule-providers")
        if rules and not any(str(x).startswith(("MATCH,", "FINAL,")) for x in rules[-2:]):
            errors.append("missing terminal MATCH/FINAL rule")
        group_names = {g.get("name") for g in groups if isinstance(g, dict)}
        for rule in rules:
            if str(rule).startswith("RULE-SET,"):
                parts = str(rule).split(",", 2)
                if len(parts) == 3 and parts[2] not in group_names:
                    errors.append(f"rule target group missing: {parts[2]}")
        for name, provider in providers.items():
            if not isinstance(provider, dict) or not provider.get("url"):
                errors.append(f"provider {name} missing url")
    elif platform == "egern":
        if not data.get("policy_groups"):
            errors.append("missing policy_groups")
        if not data.get("rules"):
            errors.append("missing rules")
    return errors


def _check_text(path: Path, platform: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if "[Proxy Group]" not in text and "[ProxyGroup]" not in text:
        errors.append("missing proxy group section")
    if "[Rule]" not in text:
        errors.append("missing rule section")
    if "FINAL," not in text and "MATCH," not in text:
        errors.append("missing terminal rule")
    if platform == "shadowrocket" and "RULE-SET" in text:
        errors.append("Shadowrocket contains unsupported RULE-SET")
    return errors


def _check_json(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ["root is not an object"]
    route = data.get("route") or {}
    outbounds = data.get("outbounds") or []
    tags = {x.get("tag") for x in outbounds if isinstance(x, dict)}
    if not outbounds:
        errors.append("missing outbounds")
    if not route.get("rules"):
        errors.append("missing route.rules")
    if not route.get("final"):
        errors.append("missing route.final")
    if route.get("final") and route["final"] not in tags:
        errors.append("route.final does not reference an outbound")
    return errors


def validate(root: Path) -> dict:
    result = {"version": 1, "clients": {}, "errors": []}
    for platform, (filename, kind) in CLIENTS.items():
        path = root / filename
        errors: list[str] = []
        if not path.exists():
            errors.append("missing file")
        else:
            try:
                if kind == "yaml":
                    errors.extend(_check_yaml(path, platform))
                elif kind == "json":
                    errors.extend(_check_json(path))
                else:
                    errors.extend(_check_text(path, platform))
                urls = _raw_urls(path.read_text(encoding="utf-8"))
                bad = [u for u in urls if not u.startswith(RAW_RULE_PREFIX)]
                if bad:
                    errors.append(f"non-latest-rules URL: {bad[0]}")
            except Exception as exc:
                errors.append(f"parse error: {type(exc).__name__}: {exc}")
        result["clients"][platform] = {"file": filename, "ok": not errors, "errors": errors}
        result["errors"].extend(f"{platform}: {e}" for e in errors)
    result["ok"] = not result["errors"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT / "build")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out", default="build/audit/remote-config-semantic.json")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else ROOT / args.root
    result = validate(root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.write:
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not result["ok"]:
        print("❌ remote config semantic validation failed", file=sys.stderr)
        return 1
    print("✅ seven remote client configs are semantically valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

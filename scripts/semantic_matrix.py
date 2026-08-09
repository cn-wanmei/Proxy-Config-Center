#!/usr/bin/env python3
"""Compare representative Core rule semantics across all seven rendered clients."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PLATFORMS = {
    "clash": "clash/config.yaml",
    "clash-meta": "clash-meta/config.yaml",
    "stash": "stash/config.yaml",
    "egern": "egern/config.yaml",
    "loon": "loon/config.conf",
    "shadowrocket": "shadowrocket/config.conf",
    "sing-box": "sing-box/config.json",
}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def service_domains() -> list[dict]:
    rows = []
    for path in sorted((ROOT / "core/rules/services").glob("*.yaml")):
        data = load(path)
        group = data.get("group") or str(data.get("id", "")).removeprefix("service-")
        for rule in data.get("rules") or []:
            values = rule.get("values") or []
            if values:
                rows.append({"group": group, "type": rule.get("type"), "value": str(values[0]), "source": path.name})
                break
    return rows


def names() -> dict[str, str]:
    groups = load(ROOT / "core/proxy-groups/service.yaml").get("groups") or []
    return {g["id"]: str((g.get("name") or {}).get("zh", g["id"])) for g in groups}


def platform_targets(path: Path, platform: str) -> set[str]:
    text = path.read_text(encoding="utf-8")
    result: set[str] = set()
    if platform in {"clash", "clash-meta", "stash"}:
        data = yaml.safe_load(text) or {}
        for rule in data.get("rules") or []:
            s = str(rule)
            if s.startswith("RULE-SET,"):
                parts = s.split(",", 2)
                if len(parts) == 3:
                    result.add(parts[2])
            elif s.startswith("DOMAIN-SUFFIX,"):
                parts = s.split(",", 2)
                if len(parts) == 3:
                    result.add(parts[2])
    elif platform == "egern":
        data = yaml.safe_load(text) or {}
        for rule in data.get("rules") or []:
            if isinstance(rule, dict) and isinstance(rule.get("rule_set"), dict):
                policy = rule.get("policy")
                if policy:
                    result.add(str(policy))
    elif platform == "sing-box":
        data = json.loads(text)
        for rule in (data.get("route") or {}).get("rules") or []:
            if isinstance(rule, dict):
                target = rule.get("outbound")
                if isinstance(target, str):
                    result.add(target)
    else:
        result.update(re.findall(r"(?:RULE-SET|DOMAIN-SUFFIX),[^,\n]+,([^,\n]+)", text))
    return {x for x in result if x}


def run(root: Path) -> dict:
    names_by_id = names()
    rows = service_domains()
    matrix = []
    errors = []
    for row in rows:
        expected_id = row["group"]
        expected_name = names_by_id.get(expected_id, expected_id)
        platforms = {}
        for platform, rel in PLATFORMS.items():
            path = root / rel
            targets = platform_targets(path, platform) if path.exists() else set()
            accepted = {expected_id, expected_name}
            matched = sorted(targets & accepted)
            ok = bool(matched)
            platforms[platform] = {"expected": accepted, "matched": matched, "ok": ok}
            if not ok:
                errors.append(f"{expected_id} representative {row['value']} missing on {platform}")
        matrix.append({**row, "platforms": platforms})
    return {"version": 1, "platforms": list(PLATFORMS), "rows": matrix, "errors": errors, "ok": not errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT / "build")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out", default="build/audit/domain-semantic-matrix.json")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else ROOT / args.root
    result = run(root.resolve())
    print(json.dumps({"rows": len(result["rows"]), "errors": len(result["errors"]), "ok": result["ok"]}, ensure_ascii=False))
    if args.write:
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for error in result["errors"]:
        print(f"❌ {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

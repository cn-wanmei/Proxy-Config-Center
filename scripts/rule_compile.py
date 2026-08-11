#!/usr/bin/env python3
"""Deterministic, client-agnostic rule compiler for 3.2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import yaml

ROOT = Path(__file__).resolve().parent.parent


def compile_rules(out: Path) -> Dict[str, object]:
    from engines.rule_pipeline import run_pipeline

    result = run_pipeline()
    if not result.ok:
        raise RuntimeError("audit gate failed; refusing to compile rules")

    rules = result.kept
    policies: Dict[str, List[dict]] = {}
    for rule in rules:
        policies.setdefault(rule["policy_id"], []).append(rule)

    out.mkdir(parents=True, exist_ok=True)
    rules_dir = out / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    emitted = []
    for policy_id in sorted(policies):
        items = sorted(
            policies[policy_id],
            key=lambda r: (int(r.get("priority", 500)), r["type"], r["value"], r["rule_id"]),
        )
        # A policy-scoped rule must be unique in the emitted artifact.
        unique = {}
        for item in items:
            unique[item["rule_id"]] = item
        items = list(unique.values())
        payload = {
            "schema_version": 1,
            "policy_id": policy_id,
            "rules": [
                {
                    "rule_id": r["rule_id"],
                    "global_rule_id": r["global_rule_id"],
                    "sha256": r["sha256"],
                    "type": r["type"],
                    "value": r["value"],
                    "priority": r["priority"],
                    "source_file": r.get("source_file", ""),
                    "provenance": r.get("provenance", ""),
                }
                for r in items
            ],
        }
        path = rules_dir / f"{policy_id}.yaml"
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        emitted.append({"policy_id": policy_id, "path": str(path.relative_to(ROOT)), "rule_count": len(items)})

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "0"
    manifest = {
        "schema_version": 1,
        "compiler": "rule-compiler-3.2",
        "version": version,
        "deterministic": True,
        "policy_count": len(emitted),
        "rule_count": len(rules),
        "policies": emitted,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="dist")
    args = parser.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    try:
        manifest = compile_rules(out)
    except Exception as exc:
        print(f"❌ rule compile FAILED: {exc}")
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    print("✅ rule compile OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

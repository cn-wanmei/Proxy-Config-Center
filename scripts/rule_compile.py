#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
POLICY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _safe_policy_id(policy_id: str) -> str:
    if not POLICY_RE.fullmatch(policy_id):
        raise ValueError(f"unsafe policy id: {policy_id!r}")
    return policy_id


def _canonical_rule(rule: dict) -> dict:
    # Keep RAW platform-agnostic and deterministic. Client-specific adapters are out of scope.
    return {
        "rule_id": rule["rule_id"],
        "global_rule_id": rule["global_rule_id"],
        "sha256": rule["sha256"],
        "type": rule["type"],
        "value": rule["value"],
        "priority": int(rule.get("priority", 500)),
        "source_file": rule.get("source_file", ""),
        "provenance": rule.get("provenance", ""),
    }


def compile_rules(out: Path):
    from engines.rule_pipeline import run_pipeline

    result = run_pipeline()
    if not result.ok:
        raise RuntimeError("audit gate failed; refusing to compile")

    rules_dir = out / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    policies: dict[str, list[dict]] = {}

    for rule in result.kept:
        policies.setdefault(_safe_policy_id(rule["policy_id"]), []).append(rule)

    emitted = []
    for policy_id in sorted(policies):
        items = sorted(
            {_canonical_rule(r)["rule_id"]: _canonical_rule(r) for r in policies[policy_id]}.values(),
            key=lambda r: (r["priority"], r["type"], r["value"], r["rule_id"]),
        )
        payload = {
            "schema_version": 4,
            "policy_id": policy_id,
            "rules": items,
        }
        path = rules_dir / f"{policy_id}.yaml"
        text = yaml.safe_dump(
            payload,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
        emitted.append({
            "policy_id": policy_id,
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "rule_count": len(items),
        })

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "schema_version": 4,
        "compiler": "rule-compiler-4.0",
        "version": version,
        "deterministic": True,
        "online_raw": True,
        "package_release": False,
        "policy_count": len(emitted),
        "rule_count": len(result.kept),
        "policies": emitted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile canonical rules into stable online RAW files")
    parser.add_argument("--out", default="dist", help="output root; use '.' to publish into repository rules/")
    args = parser.parse_args()
    out = Path(args.out)
    out = out if out.is_absolute() else ROOT / out

    try:
        manifest = compile_rules(out)
    except Exception as exc:
        print(f"❌ rule compile FAILED: {exc}")
        return 1

    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    print("✅ deterministic RAW compile OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

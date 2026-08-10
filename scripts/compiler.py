#!/usr/bin/env python3
"""Compiler Pipeline V2.1

CORE → Schema Validation → Canonical IR
    → Security Engine + Rule Engine → Optimizer
    → Capability Resolver → Platform IR
    → Platform emit → Reverse Validation → Release Artifact pins
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

PLATFORMS = [
    "clash-meta", "clash", "stash", "egern", "loon", "shadowrocket", "sing-box",
]


@dataclass
class CompileReport:
    version: str
    stages: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    platforms: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, str]] = field(default_factory=list)
    ok: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_schema_validation() -> List[str]:
    from engines.capability import validate_capabilities
    from engines.security_policy import load_security_policy
    errors: List[str] = []
    try:
        load_security_policy()
    except Exception as exc:
        errors.append(f"security policy load: {exc}")
    errors.extend(validate_capabilities())
    return errors


def stage_canonical_ir():
    from ir import build_ir
    return build_ir()


def stage_security(ir) -> List[str]:
    from engines.security_policy import load_security_policy
    from engines.security import run_core_security_invariants
    from engines.dns_engine import DNSEngine, build_clash_dns_config
    policy = load_security_policy()
    errors = run_core_security_invariants(ROOT / "core")
    errors.extend(DNSEngine().validate())
    dns = build_clash_dns_config(ipv6=True)
    errors.extend(policy.validate_dns_block(dns, platform="clash-meta"))
    return errors


def stage_rule_engine_normalize(ir) -> Dict[str, Any]:
    from engines.rule_normalize import normalize_rules
    from engines.rule_engine import load_ordered_rules
    ordered = load_ordered_rules()
    normalized = normalize_rules(ordered)
    return {"ordered": len(ordered), "normalized": len(normalized), "rules": normalized}


def stage_optimizer(norm: Dict[str, Any]) -> Dict[str, Any]:
    rules = list(norm.get("rules") or [])
    rules = [r for r in rules if r.get("values") or r.get("type") in ("match", "final")]
    rules.sort(key=lambda r: (str(r.get("type")), str(r.get("_group") or ""), str(r.get("values"))))
    return {"count": len(rules), "rules": rules}


def stage_capability_and_platform_ir(ir, platforms: List[str]) -> Dict[str, Any]:
    from platform_ir import build_platform_ir
    from engines.capability import assert_platform_compilable, validate_compile_capabilities
    errors = validate_compile_capabilities()
    out = {}
    for name in platforms:
        try:
            assert_platform_compilable(name)
            pir = build_platform_ir(ir, name)
            out[name] = pir.to_dict()
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    return {"platform_ir": out, "errors": errors}


def stage_emit(ir, platforms: List[str], out_root: Path) -> List[Dict[str, str]]:
    from build import render_platform, write_config, PLATFORMS as BUILD_PLATFORMS
    artifacts = []
    out_root.mkdir(parents=True, exist_ok=True)
    for name in platforms:
        if name not in BUILD_PLATFORMS:
            continue
        rel, kind = BUILD_PLATFORMS[name]
        config = render_platform(name, ir)
        path = out_root / rel
        write_config(path, config, kind)
        artifacts.append({"platform": name, "path": str(path.relative_to(ROOT)), "sha256": _sha256(path)})
    return artifacts


def stage_reverse_validation(artifacts: List[Dict[str, str]]) -> List[str]:
    from engines.security_policy import load_security_policy
    policy = load_security_policy()
    if not policy.reverse_validate_emit:
        return []
    errors: List[str] = []
    try:
        import yaml
    except ImportError:
        return ["reverse validation requires PyYAML"]
    for art in artifacts:
        path = ROOT / art["path"]
        if path.suffix not in (".yaml", ".yml", ".json"):
            continue
        try:
            if path.suffix == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
            else:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{art['path']}: parse failed: {exc}")
            continue
        if isinstance(data, dict) and isinstance(data.get("dns"), dict):
            plat = art["platform"]
            if plat in ("clash", "clash-meta", "stash"):
                errors.extend(f"{art['path']}: {e}" for e in policy.validate_dns_block(data["dns"], platform=plat))
    return errors


def stage_artifact_immutability(artifacts: List[Dict[str, str]], report_path: Path) -> Dict[str, Any]:
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH", ""),
        "artifacts": artifacts,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    pin_path = report_path.parent / "artifact-pins.json"
    pin_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"pin_path": str(pin_path.relative_to(ROOT))}


def run_pipeline(*, platforms: Optional[List[str]] = None, out: str = "build") -> CompileReport:
    platforms = platforms or PLATFORMS
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "0"
    report = CompileReport(version=version)

    report.stages.append("schema_validation")
    report.errors.extend(stage_schema_validation())

    report.stages.append("canonical_ir")
    try:
        ir = stage_canonical_ir()
    except Exception as exc:
        report.errors.append(f"canonical_ir: {exc}")
        return report

    report.stages.append("security_engine")
    report.errors.extend(stage_security(ir))

    report.stages.append("rule_engine")
    norm = stage_rule_engine_normalize(ir)
    report.stages.append("optimizer")
    stage_optimizer(norm)

    report.stages.append("capability_resolver")
    report.stages.append("platform_ir")
    cap = stage_capability_and_platform_ir(ir, platforms)
    report.errors.extend(cap.get("errors") or [])
    report.platforms = {
        k: {"routing_mode": v.get("routing_mode"), "features": v.get("features")}
        for k, v in (cap.get("platform_ir") or {}).items()
    }

    if report.errors:
        return report

    report.stages.append("emit")
    artifacts = stage_emit(ir, platforms, ROOT / out)
    report.artifacts = artifacts

    report.stages.append("reverse_validation")
    report.errors.extend(stage_reverse_validation(artifacts))

    report.stages.append("artifact_immutability")
    stage_artifact_immutability(artifacts, ROOT / "build" / "audit" / "compile-artifacts.json")

    pir_path = ROOT / "build" / "audit" / "platform-ir.json"
    pir_path.parent.mkdir(parents=True, exist_ok=True)
    pir_path.write_text(json.dumps(cap.get("platform_ir") or {}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report.ok = not report.errors
    (ROOT / "build" / "audit").mkdir(parents=True, exist_ok=True)
    (ROOT / "build" / "audit" / "compile-report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Proxy-Config-Center Compiler Pipeline 2.1")
    parser.add_argument("--platform", action="append", dest="platforms")
    parser.add_argument("--out", default="build")
    args = parser.parse_args()
    report = run_pipeline(platforms=args.platforms, out=args.out)
    print(json.dumps({"ok": report.ok, "stages": report.stages, "errors": report.errors, "artifacts": len(report.artifacts)}, ensure_ascii=False, indent=2))
    if not report.ok:
        for e in report.errors:
            print(" ", e)
        return 1
    print("\u2705 compile pipeline OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

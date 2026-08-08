#!/usr/bin/env python3
"""Platform capability engine — strict, data-driven feature gating."""

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required")

try:
    import jsonschema
except ImportError:
    raise SystemExit("jsonschema required")

ROOT = Path(__file__).resolve().parents[2]
PLATFORMS = ROOT / "platforms"
CAPABILITY_SCHEMA = ROOT / "common" / "schemas" / "capabilities.schema.json"

REQUIRED_PLATFORMS: List[str] = [
    "clash-meta", "clash", "stash", "egern", "loon", "shadowrocket",
]
REQUIRED_FEATURES = ("rule_provider", "rule_set", "domain_fallback")


def load_capabilities(platform: str) -> Dict[str, Any]:
    path = PLATFORMS / platform / "capabilities.yaml"
    if not path.exists():
        raise FileNotFoundError(f"missing capability profile: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level value must be a mapping")
    data.setdefault("platform", platform)
    data.setdefault("features", {})
    data.setdefault("limitations", {})
    return data


def feature_supported(features: Dict[str, Any], limitations: Dict[str, Any], feature: str) -> bool:
    """Resolve one feature: an explicit false limitation always wins."""
    if limitations.get(feature) is False:
        return False
    return features.get(feature) is True


def supports(platform: str, feature: str) -> bool:
    caps = load_capabilities(platform)
    return feature_supported(caps.get("features") or {}, caps.get("limitations") or {}, feature)


def supports_rule_set(platform: str) -> bool:
    return supports(platform, "rule_set")


def supports_rule_provider(platform: str) -> bool:
    return supports(platform, "rule_provider")


def supports_domain_fallback(platform: str) -> bool:
    return supports(platform, "domain_fallback")


def supports_remote_rules(platform: str) -> bool:
    return supports_rule_set(platform) or supports_rule_provider(platform)


def supports_proxy_provider(platform: str) -> bool:
    return supports(platform, "proxy_provider")


def platform_from_adapter_file(file: str) -> str:
    return Path(file).resolve().parents[1].name


def all_platforms() -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    if not PLATFORMS.exists():
        return result
    for d in sorted(PLATFORMS.iterdir()):
        if d.is_dir() and (d / "capabilities.yaml").exists():
            result[d.name] = load_capabilities(d.name)
    return result


def validate_capabilities() -> List[str]:
    errors: List[str] = []
    found = all_platforms()
    if not CAPABILITY_SCHEMA.exists():
        return [f"missing capability schema: {CAPABILITY_SCHEMA}"]
    with CAPABILITY_SCHEMA.open(encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    for name in REQUIRED_PLATFORMS:
        if name not in found:
            errors.append(f"missing platforms/{name}/capabilities.yaml")
            continue
        caps = found[name]
        for err in validator.iter_errors(caps):
            location = ".".join(str(x) for x in err.absolute_path)
            errors.append(f"{name}: {location}: {err.message}" if location else f"{name}: {err.message}")
        if caps.get("platform") != name:
            errors.append(f"{name}: platform field != directory name")
        features = caps.get("features") or {}
        for key in REQUIRED_FEATURES:
            if key not in features:
                errors.append(f"{name}: features.{key} must be explicit true/false")
            elif not isinstance(features[key], bool):
                errors.append(f"{name}: features.{key} must be boolean")
    return sorted(set(errors))


if __name__ == "__main__":
    errs = validate_capabilities()
    for name in REQUIRED_PLATFORMS:
        print(
            f"{name}: rule_set={supports_rule_set(name)} "
            f"rule_provider={supports_rule_provider(name)} "
            f"domain_fallback={supports_domain_fallback(name)}"
        )
    if errs:
        print("ERRORS:")
        for e in errs:
            print(" ", e)
        raise SystemExit(1)
    print("OK")

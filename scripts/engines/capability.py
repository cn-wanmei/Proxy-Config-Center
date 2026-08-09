#!/usr/bin/env python3
"""Platform capability engine — strict, data-driven feature gating."""

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml
import jsonschema

ROOT = Path(__file__).resolve().parents[2]
PLATFORMS = ROOT / "platforms"
CAPABILITY_SCHEMA = ROOT / "common" / "schemas" / "capabilities.schema.json"
PLATFORM_REGISTRY = ROOT / "common" / "platforms.yaml"
REQUIRED_FEATURES = ("rule_provider", "rule_set", "domain_fallback")


def required_platforms() -> List[str]:
    if not PLATFORM_REGISTRY.exists():
        raise FileNotFoundError(f"missing platform registry: {PLATFORM_REGISTRY}")
    with PLATFORM_REGISTRY.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    platforms = data.get("platforms") or []
    names = []
    for item in platforms:
        if isinstance(item, dict) and item.get("required", True):
            names.append(str(item["id"]))
    if not names:
        raise ValueError("platform registry contains no required platforms")
    return names


# Backward-compatible read-only alias for callers that still import the name.
REQUIRED_PLATFORMS: List[str] = required_platforms()


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
    for directory in sorted(PLATFORMS.iterdir()):
        if directory.is_dir() and (directory / "capabilities.yaml").exists():
            result[directory.name] = load_capabilities(directory.name)
    return result


def validate_capabilities() -> List[str]:
    errors: List[str] = []
    found = all_platforms()
    if not CAPABILITY_SCHEMA.exists():
        return [f"missing capability schema: {CAPABILITY_SCHEMA}"]
    with CAPABILITY_SCHEMA.open(encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    errors.extend(_validate_required_platforms(found, validator))
    return sorted(set(errors))


def _validate_required_platforms(found: Dict[str, dict], validator: Any) -> List[str]:
    errors: List[str] = []
    for name in required_platforms():
        if name not in found:
            errors.append(f"missing platforms/{name}/capabilities.yaml")
            continue
        caps = found[name]
        for err in validator.iter_errors(caps):
            location = ".".join(str(item) for item in err.absolute_path)
            if location:
                errors.append(f"{name}: {location}: {err.message}")
            else:
                errors.append(f"{name}: {err.message}")
        if caps.get("platform") != name:
            errors.append(f"{name}: platform field != directory name")
        features = caps.get("features") or {}
        for key in REQUIRED_FEATURES:
            if key not in features:
                errors.append(f"{name}: features.{key} must be explicit true/false")
            elif not isinstance(features[key], bool):
                errors.append(f"{name}: features.{key} must be boolean")
    return errors


if __name__ == "__main__":
    errs = validate_capabilities()
    for name in required_platforms():
        print(f"{name}: rule_set={supports_rule_set(name)} rule_provider={supports_rule_provider(name)} domain_fallback={supports_domain_fallback(name)}")
    if errs:
        print("ERRORS:")
        for error in errs:
            print(" ", error)
        raise SystemExit(1)
    print("OK")

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
RULES_ROOT = ROOT / "core" / "rules"
SERVICES_ROOT = RULES_ROOT / "services"
POLICIES_ROOT = RULES_ROOT / "policies"
COLLECTIONS_ROOT = RULES_ROOT / "collections"
CLIENTS_ROOT = ROOT / "core" / "clients"
POLICY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def safe_id(value: str) -> str:
    if not POLICY_RE.fullmatch(value):
        raise ValueError(f"unsafe identifier: {value!r}")
    return value


def normalize_type(value: str) -> str:
    return str(value).strip().lower().replace("-", "_")


def normalize_value(value: object) -> str:
    return str(value).strip()


def service_rules(service_id: str) -> list[tuple[str, str]]:
    path = SERVICES_ROOT / f"{service_id}.yaml"
    if not path.exists():
        raise ValueError(f"policy references missing service: {service_id}")
    data = load_yaml(path)
    out: list[tuple[str, str]] = []
    allowed = {"domain", "domain_suffix", "domain_keyword", "ip_cidr", "ip_cidr6", "user_agent"}
    for rule in data.get("rules") or []:
        if not isinstance(rule, dict):
            continue
        rtype = normalize_type(rule.get("type", ""))
        if rtype not in allowed:
            continue
        values = rule.get("values") if rule.get("values") is not None else rule.get("value")
        if values is None:
            continue
        if not isinstance(values, list):
            values = [values]
        for value in values:
            value = normalize_value(value)
            if value:
                out.append((rtype, value))
    return out


def dedupe_rules(rules: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    return sorted(set(rules), key=lambda item: (item[0], item[1]))


def load_policy_graph() -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    if POLICIES_ROOT.exists():
        for path in sorted(POLICIES_ROOT.glob("*.yaml")):
            data = load_yaml(path)
            pid = safe_id(str(data.get("id") or path.stem))
            children = [safe_id(str(x)) for x in (data.get("children") or [])]
            if not children:
                raise ValueError(f"policy has no children: {pid}")
            if pid in graph:
                raise ValueError(f"duplicate policy: {pid}")
            graph[pid] = children
    return graph


def load_collection(collection_id: str) -> list[str]:
    path = COLLECTIONS_ROOT / f"{collection_id}.yaml"
    data = load_yaml(path)
    return [safe_id(str(x)) for x in (data.get("policies") or [])]


def compile_client(client_id: str) -> dict:
    client_path = CLIENTS_ROOT / f"{client_id}.yaml"
    client = load_yaml(client_path)
    extension = str(client.get("extension") or ".list")
    root = ROOT / str(client.get("root") or f"rules/{client_id}")
    format_id = str(client.get("format") or client_id).lower()
    collection_id = safe_id(str(client.get("collection") or "global"))
    type_map = {str(k): str(v) for k, v in (client.get("rule_types") or {}).items()}

    if format_id != "loon":
        raise ValueError(f"unsupported 4.0 client format: {format_id}")

    policy_graph = load_policy_graph()
    collection_policies = load_collection(collection_id)
    policy_rules: dict[str, list[tuple[str, str]]] = {}

    for policy_id in collection_policies:
        children = policy_graph.get(policy_id, [policy_id])
        combined: list[tuple[str, str]] = []
        for child in children:
            combined.extend(service_rules(child))
        policy_rules[policy_id] = dedupe_rules(combined)

    emitted: list[dict] = []
    for policy_id in collection_policies:
        policy_dir = root / collection_id.capitalize() / policy_id.capitalize()
        policy_dir.mkdir(parents=True, exist_ok=True)

        total_path = policy_dir / f"{policy_id.capitalize()}{extension}"
        total_lines = [f"# {policy_id}", *[f"{type_map[t]},{v}" for t, v in policy_rules[policy_id]]]
        total_path.write_text("\n".join(total_lines).rstrip() + "\n", encoding="utf-8")
        emitted.append({"kind": "policy", "policy": policy_id, "path": str(total_path.relative_to(ROOT)), "count": len(policy_rules[policy_id])})

        for child in policy_graph.get(policy_id, [policy_id]):
            child_rules = dedupe_rules(service_rules(child))
            child_name = child.replace("-", "").title()
            child_path = policy_dir / f"{child_name}{extension}"
            child_lines = [f"# {child}", *[f"{type_map[t]},{v}" for t, v in child_rules]]
            child_path.write_text("\n".join(child_lines).rstrip() + "\n", encoding="utf-8")
            emitted.append({"kind": "child", "policy": policy_id, "service": child, "path": str(child_path.relative_to(ROOT)), "count": len(child_rules)})

    collection_dir = root / collection_id.capitalize()
    collection_dir.mkdir(parents=True, exist_ok=True)
    collection_path = collection_dir / f"{collection_id.capitalize()}{extension}"
    collection_rules: list[tuple[str, str]] = []
    for policy_id in collection_policies:
        collection_rules.extend(policy_rules[policy_id])
    collection_rules = dedupe_rules(collection_rules)
    collection_lines = [f"# {collection_id}", *[f"{type_map[t]},{v}" for t, v in collection_rules]]
    collection_path.write_text("\n".join(collection_lines).rstrip() + "\n", encoding="utf-8")
    emitted.append({"kind": "collection", "collection": collection_id, "path": str(collection_path.relative_to(ROOT)), "count": len(collection_rules)})

    return {"client": client_id, "collection": collection_id, "format": format_id, "files": emitted}


def compile_rules() -> dict:
    clients = sorted(p.stem for p in CLIENTS_ROOT.glob("*.yaml"))
    if not clients:
        raise ValueError("no client output definitions found")
    results = [compile_client(client_id) for client_id in clients]
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "schema_version": 4,
        "compiler": "rule-compiler-4.0",
        "version": version,
        "online_raw": True,
        "package_release": False,
        "clients": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile 4.0 hierarchical client-specific online RAW rules")
    parser.parse_args()
    try:
        manifest = compile_rules()
    except Exception as exc:
        print(f"❌ rule compile FAILED: {exc}")
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    print("✅ 4.0 hierarchical online RAW compile OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

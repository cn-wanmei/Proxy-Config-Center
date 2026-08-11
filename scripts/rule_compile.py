#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
RULES_ROOT = ROOT / "core" / "rules"
SERVICES_ROOT = RULES_ROOT / "services"
POLICIES_ROOT = RULES_ROOT / "policies"
COLLECTIONS_ROOT = RULES_ROOT / "collections"
CLIENTS_ROOT = ROOT / "core" / "clients"
IDENT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def safe_id(value: str) -> str:
    if not IDENT_RE.fullmatch(value):
        raise ValueError(f"unsafe identifier: {value!r}")
    return value


def display_name(value: str) -> str:
    return value.replace("-", " ").title().replace(" ", "")


def normalize_type(value: str) -> str:
    return str(value).strip().lower().replace("-", "_")


def normalize_value(value: object) -> str:
    return str(value).strip()


def service_rules(service_id: str) -> list[tuple[str, str]]:
    path = SERVICES_ROOT / f"{service_id}.yaml"
    if not path.exists():
        raise ValueError(f"missing service source: {service_id}")
    data = load_yaml(path)
    allowed = {"domain", "domain_suffix", "domain_keyword", "ip_cidr", "ip_cidr6", "user_agent"}
    out: list[tuple[str, str]] = []
    for rule in data.get("rules") or []:
        if not isinstance(rule, dict):
            raise ValueError(f"invalid rule object in {path}")
        rtype = normalize_type(rule.get("type", ""))
        if rtype not in allowed:
            raise ValueError(f"unsupported rule type {rtype!r} in {path}")
        values = rule.get("values") if rule.get("values") is not None else rule.get("value")
        if values is None:
            raise ValueError(f"rule has no value in {path}")
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
    for path in sorted(POLICIES_ROOT.glob("*.yaml")):
        data = load_yaml(path)
        pid = safe_id(str(data.get("id") or path.stem))
        children = [safe_id(str(x)) for x in (data.get("children") or [])]
        if pid in graph:
            raise ValueError(f"duplicate policy: {pid}")
        if children:
            graph[pid] = children
    return graph


def load_collection(collection_id: str) -> list[str]:
    path = COLLECTIONS_ROOT / f"{collection_id}.yaml"
    if not path.exists():
        raise ValueError(f"missing collection: {collection_id}")
    data = load_yaml(path)
    policies = [safe_id(str(x)) for x in (data.get("policies") or [])]
    if not policies:
        raise ValueError(f"collection has no policies: {collection_id}")
    return policies


def policy_children(policy_id: str, graph: dict[str, list[str]]) -> list[str]:
    return graph.get(policy_id, [policy_id])


def render_classical(name: str, rules: list[tuple[str, str]], type_map: dict[str, str]) -> str:
    lines = [f"# NAME: {name}", f"# TOTAL: {len(rules)}", ""]
    for rtype, value in rules:
        mapped = type_map.get(rtype)
        if not mapped:
            raise ValueError(f"client rule type is not mapped: {rtype}")
        lines.append(f"{mapped},{value}")
    return "\n".join(lines) + "\n"


def render_loon(name: str, rules: list[tuple[str, str]], type_map: dict[str, str]) -> str:
    return render_classical(name, rules, type_map)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_client(client_id: str, output_root: Path) -> dict:
    client_path = CLIENTS_ROOT / f"{client_id}.yaml"
    client = load_yaml(client_path)
    extension = str(client.get("extension") or ".list")
    relative_root = Path(str(client.get("root") or f"rules/{client_id}"))
    if relative_root.is_absolute() or ".." in relative_root.parts:
        raise ValueError(f"unsafe client output root: {relative_root}")
    root = output_root / relative_root
    format_id = str(client.get("format") or client_id).lower()
    collection_id = safe_id(str(client.get("collection") or "global"))
    type_map = {str(k): str(v) for k, v in (client.get("rule_types") or {}).items()}
    names = {str(k): str(v) for k, v in (client.get("names") or {}).items()}

    renderers = {
        "loon": render_loon,
        "classical": render_classical,
    }
    renderer = renderers.get(format_id)
    if renderer is None:
        raise ValueError(f"unsupported 4.0 client format: {format_id}")

    graph = load_policy_graph()
    collection_policies = load_collection(collection_id)
    policy_rules: dict[str, list[tuple[str, str]]] = {}

    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    for policy_id in collection_policies:
        combined: list[tuple[str, str]] = []
        for child in policy_children(policy_id, graph):
            combined.extend(service_rules(child))
        policy_rules[policy_id] = dedupe_rules(combined)

    emitted: list[dict] = []
    collection_dir = root / display_name(collection_id)
    collection_dir.mkdir(parents=True, exist_ok=True)

    collection_rules = dedupe_rules(rule for policy_id in collection_policies for rule in policy_rules[policy_id])
    collection_name = names.get(collection_id, display_name(collection_id))
    collection_path = collection_dir / f"{collection_name}{extension}"
    collection_path.write_text(renderer(collection_name, collection_rules, type_map), encoding="utf-8")
    emitted.append({"kind": "collection", "id": collection_id, "path": str(collection_path.relative_to(output_root)), "count": len(collection_rules), "sha256": file_sha256(collection_path)})

    for policy_id in collection_policies:
        policy_name = names.get(policy_id, display_name(policy_id))
        policy_dir = collection_dir / policy_name
        policy_dir.mkdir(parents=True, exist_ok=True)

        total_path = policy_dir / f"{policy_name}{extension}"
        total_path.write_text(renderer(policy_name, policy_rules[policy_id], type_map), encoding="utf-8")
        emitted.append({"kind": "policy", "id": policy_id, "path": str(total_path.relative_to(output_root)), "count": len(policy_rules[policy_id]), "sha256": file_sha256(total_path)})

        for child in policy_children(policy_id, graph):
            if child == policy_id:
                continue
            child_rules = dedupe_rules(service_rules(child))
            child_name = names.get(child, display_name(child))
            child_path = policy_dir / f"{child_name}{extension}"
            child_path.write_text(renderer(child_name, child_rules, type_map), encoding="utf-8")
            emitted.append({"kind": "child", "policy": policy_id, "id": child, "path": str(child_path.relative_to(output_root)), "count": len(child_rules), "sha256": file_sha256(child_path)})

    return {"client": client_id, "collection": collection_id, "format": format_id, "files": emitted}


def compile_rules(out: Path | None = None) -> dict:
    output_root = Path(out) if out is not None else ROOT
    clients = sorted(p.stem for p in CLIENTS_ROOT.glob("*.yaml"))
    if not clients:
        raise ValueError("no client output definitions found")
    results = [compile_client(client_id, output_root) for client_id in clients]
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
    parser = argparse.ArgumentParser(description="Compile 4.0 client -> collection -> policy -> child RAW hierarchy")
    parser.add_argument("--out", default=str(ROOT), help="repository root; generated RAW files go under rules/<client>/...")
    args = parser.parse_args()
    try:
        manifest = compile_rules(Path(args.out).resolve())
    except Exception as exc:
        print(f"❌ rule compile FAILED: {exc}")
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    print("✅ 4.0 hierarchical online RAW compile OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

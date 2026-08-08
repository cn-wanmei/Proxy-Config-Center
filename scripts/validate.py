#!/usr/bin/env python3
"""Core validation including Rule Source."""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "core"

def load_yaml(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def main() -> int:
    errors = []
    print("=== Core Validation ===")

    resolvers = (load_yaml(CORE / "dns" / "resolvers.yaml") or {}).get("resolvers") or {}
    groups = {g["id"]: g for g in ((load_yaml(CORE / "dns" / "groups.yaml") or {}).get("groups") or [])}
    policies = {p["id"]: p for p in ((load_yaml(CORE / "dns" / "policies.yaml") or {}).get("policies") or [])}

    for gid, g in groups.items():
        for rid in g.get("resolvers") or []:
            if rid not in resolvers:
                errors.append(f"dns group '{gid}' unknown resolver '{rid}'")
    for pid, p in policies.items():
        if p.get("group") not in groups:
            errors.append(f"dns policy '{pid}' unknown group")
        for opt in p.get("options") or []:
            if opt not in resolvers:
                errors.append(f"dns policy '{pid}' bad option '{opt}'")

    svc = load_yaml(CORE / "proxy-groups" / "service.yaml") or {}
    services = {g["id"]: g for g in (svc.get("groups") or [])}

    pri = load_yaml(CORE / "rules" / "priority.yaml") or {}
    priority_ids = {p["id"] for p in (pri.get("priority") or [])}

    src = load_yaml(CORE / "rules" / "sources.yaml") or {}
    sources = src.get("sources") or {}
    if not sources:
        errors.append("core/rules/sources.yaml is empty or missing")

    # Service ↔ Rule Source strong ref
    for sid in services:
        if sid not in sources and sid != "final":
            # final may only exist in sources
            if sid not in sources:
                errors.append(f"service '{sid}' has no rule source in sources.yaml")

    for sid in sources:
        if sid == "final":
            continue
        if sid not in services:
            errors.append(f"rule source '{sid}' has no matching service")

    for sid, meta in sources.items():
        if not any([
            meta.get("geosite"),
            meta.get("geoip"),
            meta.get("domain_suffix"),
            meta.get("blackmatrix7"),
            meta.get("match"),
        ]):
            errors.append(f"rule source '{sid}' has no geosite/geoip/domain/bm/match")

    print(f"Resolvers: {len(resolvers)} | Services: {len(services)} | Sources: {len(sources)} | Priority: {len(priority_ids)}")

    if errors:
        print("\n❌ Errors:")
        for e in errors:
            print(" ", e)
        return 1
    print("\n✅ All checks passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())

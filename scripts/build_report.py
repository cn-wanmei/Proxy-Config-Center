#!/usr/bin/env python3
"""Generate an auditable build report from the generated tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENT_FILES = {
    "clash": "clash/config.yaml", "clash-meta": "clash-meta/config.yaml", "stash": "stash/config.yaml",
    "egern": "egern/config.yaml", "loon": "loon/config.conf", "shadowrocket": "shadowrocket/config.conf",
    "sing-box": "sing-box/config.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report(root: Path) -> dict:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append({"path": str(path.relative_to(root)), "size": path.stat().st_size, "sha256": sha256(path)})
    clients = {}
    for name, rel in CLIENT_FILES.items():
        path = root / rel
        clients[name] = {"path": rel, "exists": path.exists(), "sha256": sha256(path) if path.exists() else None}
    audit_dir = root / "audit"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root.relative_to(ROOT) if root.is_relative_to(ROOT) else root),
        "clients": clients,
        "file_count": len(files),
        "files": files,
        "audits": {},
    }
    for name in ("rule-strategy-index.json", "rule-graph.json", "domain-semantic-matrix.json", "remote-config-semantic.json"):
        path = audit_dir / name
        if path.exists():
            report["audits"][name] = json.loads(path.read_text(encoding="utf-8"))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT / "build")
    parser.add_argument("--out", default="build/audit/build-report.json")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else ROOT / args.root
    report = build_report(root.resolve())
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✅ wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

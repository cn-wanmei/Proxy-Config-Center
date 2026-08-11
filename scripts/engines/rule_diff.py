#!/usr/bin/env python3
"""Rule diff & history (3.1 P2)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "dist" / "audit" / "history"


def snapshot_hash(atoms: List[dict]) -> str:
    lines = sorted(f"{a['rule_id']}|{a['content_hash']}" for a in atoms)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def write_snapshot(atoms: List[dict], *, version: str) -> Path:
    HISTORY.mkdir(parents=True, exist_ok=True)
    snap = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_hash": snapshot_hash(atoms),
        "count": len(atoms),
        "rule_ids": sorted(a["rule_id"] for a in atoms),
    }
    path = HISTORY / f"snapshot-{version}.json"
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HISTORY / "LATEST.json").write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def diff_snapshots(old: dict, new: dict) -> dict:
    old_ids = set(old.get("rule_ids") or [])
    new_ids = set(new.get("rule_ids") or [])
    return {
        "added": sorted(new_ids - old_ids),
        "removed": sorted(old_ids - new_ids),
        "unchanged": len(old_ids & new_ids),
        "old_hash": old.get("snapshot_hash"),
        "new_hash": new.get("snapshot_hash"),
    }


def change_report(diff: dict, version: str) -> str:
    lines = [
        f"# Rule change report — {version}",
        "",
        f"- added: {len(diff.get('added') or [])}",
        f"- removed: {len(diff.get('removed') or [])}",
        f"- unchanged: {diff.get('unchanged')}",
        f"- old_hash: `{diff.get('old_hash')}`",
        f"- new_hash: `{diff.get('new_hash')}`",
        "",
    ]
    if diff.get("added"):
        lines.append("## Added")
        lines.extend(f"- `{x}`" for x in diff["added"][:100])
        lines.append("")
    if diff.get("removed"):
        lines.append("## Removed")
        lines.extend(f"- `{x}`" for x in diff["removed"][:100])
        lines.append("")
    return "\n".join(lines)

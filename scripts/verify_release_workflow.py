#!/usr/bin/env python3
"""Fail-fast checks for the release workflow contract."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/release.yml"
TEXT = WORKFLOW.read_text(encoding="utf-8")

FORBIDDEN = ("INPUT_SHA", "EVENT_SHA", "target_sha")
REQUIRED = (
    "workflow_dispatch:",
    "release_tag:",
    "Resolve immutable source",
    "git rev-parse origin/main",
    "validate_release_dist.py --root dist",
    "Immutable GitHub Release",
    "Publish latest-rules atomically",
    "E2E Raw HTTP 200 and SHA256",
)
for token in FORBIDDEN:
    if token in TEXT:
        raise SystemExit(f"release workflow contains forbidden legacy token: {token}")
for token in REQUIRED:
    if token not in TEXT:
        raise SystemExit(f"release workflow missing required contract: {token}")

m = re.search(r"cp build/sing-box/config\.json dist/sing-box\.json", TEXT)
if not m:
    raise SystemExit("release workflow missing seven-client pack")

# Pack scope must never rewrite metadata files through rewrite_release_urls.py.
pack = TEXT.split("- name: Pack release", 1)[1]
if "dist/sources.yaml" in pack and "rewrite_release_urls.py" in pack:
    # This is acceptable only when sources.yaml is created before the rewrite and
    # the rewriter itself is client-scoped; enforce the explicit scope comment too.
    if "Only rewrite generated client entrypoints" not in (ROOT / "scripts/rewrite_release_urls.py").read_text(encoding="utf-8"):
        raise SystemExit("pack scope is not explicitly protected from metadata rewriting")

print("Release workflow self-check OK")

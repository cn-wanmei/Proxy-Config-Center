#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_gate_matches_version():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "release_tag_gate.py"), "--tag", version], cwd=ROOT, capture_output=True, text=True)
    assert "release tag gate" in (proc.stdout + proc.stderr)

def test_gate_rejects_mismatch():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "release_tag_gate.py"), "--tag", "v0.0.0"], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "does not match VERSION" in (proc.stdout + proc.stderr)

if __name__ == "__main__":
    test_gate_matches_version(); test_gate_rejects_mismatch(); print("OK release tag gate")

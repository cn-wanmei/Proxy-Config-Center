#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from engines.optimizer import optimize

def test_dedup_and_merge():
    rules = [
        {"type": "domain_suffix", "_group": "google", "values": ["google.com"]},
        {"type": "domain_suffix", "_group": "google", "values": ["youtube.com", "google.com"]},
        {"type": "domain_suffix", "_group": "google", "values": ["google.com"]},
    ]
    out, report = optimize(rules)
    assert report.input_count == 3
    ds = [r for r in out if r.get("type") == "domain_suffix" and r.get("_group") == "google"]
    assert len(ds) == 1
    assert "google.com" in ds[0]["values"] and "youtube.com" in ds[0]["values"]

def test_shadow_prune():
    rules = [{"type": "domain_suffix", "_group": "x", "values": ["a.example.com", "example.com"]}]
    out, _ = optimize(rules, strategies=("shadow_prune", "priority_sort"))
    assert "example.com" in out[0]["values"]

def test_drop_empty():
    rules = [{"type": "domain_suffix", "_group": "a", "values": []}, {"type": "final"}]
    out, report = optimize(rules, strategies=("drop_empty",))
    assert report.dropped_empty >= 1
    assert any(r.get("type") == "final" for r in out)

if __name__ == "__main__":
    test_dedup_and_merge(); test_shadow_prune(); test_drop_empty(); print("OK optimizer")

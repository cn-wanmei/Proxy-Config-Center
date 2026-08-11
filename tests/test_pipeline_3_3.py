#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from engines.rule_pipeline import run_pipeline
from engines.precedence import precedence_rank, compare_match_order
from engines.rule_id import content_hash, make_rule_id

def test_pipeline():
    r = run_pipeline()
    assert r.ok, [str(e) for e in r.errors]
    assert r.graph and r.graph["node_count"] > 0

def test_precedence():
    assert precedence_rank("ad-block") < precedence_rank("youtube")
    assert compare_match_order("ad-block", "youtube") < 0

def test_hash():
    assert len(content_hash("domain_suffix", "youtube.com")) == 64

if __name__ == "__main__":
    test_pipeline(); test_precedence(); test_hash(); print("OK pipeline 3.3")

#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import project_audit


def test_ai_registry():
    report = project_audit.ai_report()
    assert report["provider_count"] >= 10
    assert "claude.ai" in report["coverage"]
    assert "gemini.google.com" in report["coverage"]


def test_rule_graph_and_conflict_shapes():
    index = project_audit.rule_index()
    conflicts, unreachable, graph = project_audit.analyze(index)
    assert isinstance(index, list)
    assert isinstance(conflicts, list)
    assert isinstance(unreachable, list)
    assert set(graph) == {"nodes", "edges"}


def test_supply_chain_reports():
    report = project_audit.source_snapshot()
    assert report["snapshot_version"]
    assert "sources" in report
    sbom = project_audit.sbom()
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["components"]

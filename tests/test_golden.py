#!/usr/bin/env python3
"""
Golden Test
Compare key invariants of generated configs against expected snapshots.
Full file golden files can be added under tests/golden/ later.
"""

import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ir import build_ir

def load_renderer(platform: str):
    path = ROOT / "platforms" / platform / "adapter" / "render.py"
    spec = importlib.util.spec_from_file_location(f"{platform}_render", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render

def test_clash_meta_invariants():
    ir = build_ir()
    cfg = load_renderer("clash-meta")(ir)
    assert "proxy-groups" in cfg
    assert "rules" in cfg
    assert "dns" in cfg
    names = [g["name"] for g in cfg["proxy-groups"]]
    assert "代理模式" in names
    assert "中国连接" in names
    assert "苹果服务" in names
    assert "其它连接" in names
    assert any(str(r).startswith("MATCH,") or str(r).endswith("其它连接") for r in cfg["rules"])
    # China group should start with DIRECT
    china = next(g for g in cfg["proxy-groups"] if g["name"] == "中国连接")
    assert china["proxies"][0] == "DIRECT"
    apple = next(g for g in cfg["proxy-groups"] if g["name"] == "苹果服务")
    assert apple["proxies"][0] == "DIRECT"
    print("✅ golden: clash-meta invariants OK")

def test_egern_invariants():
    ir = build_ir()
    cfg = load_renderer("egern")(ir)
    assert "policy_groups" in cfg
    assert "rules" in cfg
    names = [g["select"]["name"] for g in cfg["policy_groups"]]
    assert "代理模式" in names
    assert "其它连接" in names
    print("✅ golden: egern invariants OK")

def test_loon_invariants():
    ir = build_ir()
    text = load_renderer("loon")(ir)
    assert "[Proxy Group]" in text
    assert "[Rule]" in text
    assert "FINAL," in text
    assert "中国连接" in text
    print("✅ golden: loon invariants OK")

if __name__ == "__main__":
    test_clash_meta_invariants()
    test_egern_invariants()
    test_loon_invariants()
    print("All golden tests passed")

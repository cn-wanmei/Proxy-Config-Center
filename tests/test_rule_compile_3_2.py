#!/usr/bin/env python3
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from rule_compile import compile_rules
def test_compile():
    with TemporaryDirectory() as tmp:
        m=compile_rules(Path(tmp)); assert m["deterministic"] is True; assert m["rule_count"]>0; assert list((Path(tmp)/"rules").glob("*.yaml"))
if __name__=="__main__": test_compile(); print("OK rule compile 3.2")

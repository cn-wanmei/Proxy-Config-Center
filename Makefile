PYTHONPATH := $(CURDIR)/scripts
export PYTHONPATH
PYTHON ?= python3
export SOURCE_DATE_EPOCH ?= 0

.PHONY: install audit_gate rule_compile compile test ci

install:
	$(PYTHON) -m pip install -r requirements.txt

audit_gate:
	$(PYTHON) scripts/rule_audit_gate.py --write --out dist

rule_compile:
	$(PYTHON) scripts/rule_compile.py --out dist

compile: audit_gate rule_compile

test:
	$(PYTHON) tests/test_pipeline_3_3.py
	$(PYTHON) tests/test_rule_only.py
	$(PYTHON) tests/test_rule_intelligence.py

ci: audit_gate rule_compile test

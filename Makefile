PYTHONPATH := $(CURDIR)/scripts
export PYTHONPATH
PYTHON ?= python3
export SOURCE_DATE_EPOCH ?= 0

.PHONY: install audit_gate rule_compile compile semantic_test compile_test test ci

install:
	$(PYTHON) -m pip install -r requirements.txt

audit_gate:
	$(PYTHON) scripts/rule_audit_gate.py --write --out dist

rule_compile:
	$(PYTHON) scripts/rule_compile.py --out dist

compile: audit_gate rule_compile

semantic_test:
	$(PYTHON) tests/test_semantic_3_2.py

compile_test:
	$(PYTHON) tests/test_rule_compile_3_2.py

test: semantic_test compile_test

ci: audit_gate rule_compile test

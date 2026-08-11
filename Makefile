PYTHONPATH := $(CURDIR)/scripts
export PYTHONPATH
PYTHON ?= python3
export SOURCE_DATE_EPOCH ?= 0
export RULE_AUDIT_STRICT ?= 1

.PHONY: install audit audit_gate rule_compile compile build clients_optional test ci

install:
	$(PYTHON) -m pip install -r requirements.txt

audit:
	$(PYTHON) scripts/rule_audit.py --write

audit_gate:
	$(PYTHON) scripts/rule_audit_gate.py --write

rule_compile:
	$(PYTHON) scripts/rule_compile.py --out dist

compile: audit_gate rule_compile

clients_optional:
	$(PYTHON) scripts/build.py --include-final

build: compile

test:
	$(PYTHON) tests/test_rule_only.py
	$(PYTHON) tests/test_rule_intelligence.py
	$(PYTHON) tests/test_rule_audit.py

ci: audit_gate rule_compile test

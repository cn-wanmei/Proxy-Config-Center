PYTHONPATH := $(CURDIR)/scripts
export PYTHONPATH
PYTHON ?= python3

.PHONY: install audit rule_compile compile build clients_optional test ci

install:
	$(PYTHON) -m pip install -r requirements.txt

audit:
	$(PYTHON) scripts/rule_audit.py --write

rule_compile:
	$(PYTHON) scripts/rule_compile.py --out dist

compile: rule_compile

clients_optional:
	$(PYTHON) scripts/build.py --include-final

build: rule_compile

test:
	$(PYTHON) tests/test_rule_only.py
	$(PYTHON) tests/test_rule_audit.py
	$(PYTHON) tests/test_rule_sources.py

ci: audit rule_compile test

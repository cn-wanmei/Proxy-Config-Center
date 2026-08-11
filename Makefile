PYTHONPATH := $(CURDIR)/scripts
export PYTHONPATH
PYTHON ?= python3

.PHONY: install audit audit_gate compile publish verify generate test ci clean

install:
	$(PYTHON) -m pip install -r requirements.txt

audit:
	$(PYTHON) scripts/rule_audit_gate.py --write --out .audit

audit_gate: audit

compile:
	rm -rf rules
	$(PYTHON) scripts/rule_compile.py --out .

publish:
	$(PYTHON) scripts/rule_audit_gate.py
	rm -rf rules
	$(PYTHON) scripts/rule_compile.py --out .

generate: publish

verify:
	$(PYTHON) scripts/rule_audit_gate.py
	rm -rf .audit/generated
	$(PYTHON) scripts/rule_compile.py --out .audit/generated
	diff -ru .audit/generated/rules rules

test:
	$(PYTHON) tests/test_semantic_4_0.py
	$(PYTHON) tests/test_rule_compile_4_0.py

ci: audit test verify

clean:
	rm -rf .audit dist rules

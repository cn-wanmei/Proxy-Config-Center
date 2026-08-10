PYTHONPATH := $(CURDIR)/scripts
export PYTHONPATH
PYTHON ?= python3

.PHONY: install validate security compile_gate audit build check verify_emit test doh_health golden ci

install:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	$(PYTHON) scripts/validate.py

security:
	$(PYTHON) scripts/security_check.py

compile_gate:
	$(PYTHON) scripts/compile_gate.py

doh_health:
	$(PYTHON) scripts/doh_health.py

audit:
	$(PYTHON) scripts/rule_audit.py --write

build:
	$(PYTHON) scripts/build.py --include-final

check: build
	$(PYTHON) scripts/check_config.py --root build
	$(PYTHON) scripts/check_config.py --root final

verify_emit: build
	$(PYTHON) scripts/verify_emit.py

test:
	$(PYTHON) tests/test_dns_leak.py
	$(PYTHON) tests/test_capability_matrix.py
	$(PYTHON) tests/test_capabilities.py
	$(PYTHON) tests/test_rule_audit.py
	$(PYTHON) tests/test_rule_sources.py
	$(PYTHON) tests/test_semantic.py
	$(PYTHON) tests/test_platform_semantics.py

golden: build
	$(PYTHON) tests/test_golden.py

ci: security compile_gate validate audit test golden check verify_emit

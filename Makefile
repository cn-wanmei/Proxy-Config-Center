PYTHONPATH := $(CURDIR)/scripts
export PYTHONPATH
PYTHON ?= python3

.PHONY: install validate security audit build check verify_emit test golden ci

install:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	$(PYTHON) scripts/validate.py

security:
	$(PYTHON) scripts/security_check.py

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
	$(PYTHON) tests/test_capabilities.py
	$(PYTHON) tests/test_rule_audit.py
	$(PYTHON) tests/test_rule_sources.py
	$(PYTHON) tests/test_semantic.py
	$(PYTHON) tests/test_platform_semantics.py

golden: build
	$(PYTHON) tests/test_golden.py

ci: security validate audit test golden check verify_emit

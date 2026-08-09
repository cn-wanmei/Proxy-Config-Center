PYTHONPATH := $(CURDIR)/scripts
export PYTHONPATH
PYTHON ?= python3

.PHONY: install validate audit trace build check test golden ci

install:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	$(PYTHON) scripts/validate.py

audit:
	$(PYTHON) scripts/rule_audit.py --write

trace:
	@test -n "$(DOMAIN)" || (echo "usage: make trace DOMAIN=chatgpt.com"; exit 2)
	$(PYTHON) scripts/rule_trace.py $(DOMAIN)

build:
	$(PYTHON) scripts/build.py --include-final

check: build
	$(PYTHON) scripts/check_config.py --root build
	$(PYTHON) scripts/check_config.py --root final

test:
	$(PYTHON) tests/test_ai_registry.py
	$(PYTHON) tests/test_capabilities.py
	$(PYTHON) tests/test_rule_audit.py
	$(PYTHON) tests/test_rule_sources.py
	$(PYTHON) tests/test_semantic.py
	$(PYTHON) tests/test_platform_semantics.py

golden: build
	$(PYTHON) tests/test_golden.py

ci: validate audit test golden check

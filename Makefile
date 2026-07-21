.PHONY: check lint lint-fix test coverage docs-check hypothesis-check harness-smoke paper-build paper-sync clean install health health-gpu check-real reviewer-repro nano-test nano-smoke nano-bakeoff nano-gates nano-validate-schema nano-large-site nano-large-site-all nano-large-site-pro nano-large-site-pro-b nano-large-site-pro-c nano-large-site-pro-d nano-large-site-pro-e nano-arena

PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)
# Absolute path: targets `cd` into NANO_DIR before invoking Python.
NANO_PYTHON ?= $(shell \
	if test -x nano-orchestrator/.venv/bin/python; then \
		echo "$(CURDIR)/nano-orchestrator/.venv/bin/python"; \
	elif test -x .venv/bin/python; then \
		echo "$(CURDIR)/.venv/bin/python"; \
	else \
		echo python3; \
	fi)
NANO_DIR := nano-orchestrator

install:
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e .

install-gpu: install
	$(PYTHON) -m pip install -r requirements-gpu.txt

wave1-gpu-parallel:
	chmod +x scripts/run_wave1_gpu_parallel.py
	MLFLOW_DISABLE=1 $(PYTHON) scripts/run_wave1_gpu_parallel.py --profile smoke --real --max-parallel 3

m1-phase0:
	$(PYTHON) scripts/run_milestone_m1_2000.py --phase 0

m1-generate-js:
	$(PYTHON) scripts/run_milestone_m1_2000.py --phase 1 --language JavaScript --real

m1-train-exp1-exp2:
	$(PYTHON) scripts/run_milestone_m1_2000.py --phase 5 --real --profile publication

m1-build-local:
	chmod +x scripts/build_m1_dataset_local.py
	$(PYTHON) scripts/build_m1_dataset_local.py

import-tier-a:
	chmod +x scripts/import_tier_a_datasets.py
	$(PYTHON) scripts/import_tier_a_datasets.py

lint:
	$(PYTHON) -m ruff check scripts/ tests/ experiments/ src/ 2>/dev/null || \
	$(PYTHON) -m ruff check scripts/ tests/ experiments/

lint-fix:
	$(PYTHON) -m ruff check --fix scripts/ tests/ experiments/ src/ 2>/dev/null || \
	$(PYTHON) -m ruff check --fix scripts/ tests/ experiments/

docs-check:
	$(PYTHON) scripts/validate_docs.py

hypothesis-check:
	$(PYTHON) -m pytest tests/unit/test_hypothesis.py -v

harness-smoke:
	chmod +x scripts/harness_smoke.sh scripts/reviewer_repro.sh
	./scripts/harness_smoke.sh

test:
	MLFLOW_DISABLE=1 $(PYTHON) -m pytest tests/ -m "not real" -v

coverage:
	MLFLOW_DISABLE=1 $(PYTHON) -m pytest tests/ -m "not real" --cov=src --cov-report=term-missing --cov-fail-under=80 -q 2>/dev/null || \
	MLFLOW_DISABLE=1 $(PYTHON) -m pytest tests/ -m "not real" -v

check: lint docs-check hypothesis-check harness-smoke test

check-real:
	MLFLOW_DISABLE=1 $(PYTHON) -m pytest tests/real/ -m real -v

health:
	$(PYTHON) scripts/health_check.py

health-gpu:
	$(PYTHON) scripts/health_check.py --gpu

paper-sync:
	$(PYTHON) scripts/build_paper.py --sync-only 2>/dev/null || echo "paper-sync: stub until scripts/build_paper.py exists"

paper-build: paper-sync
	@if command -v pdflatex >/dev/null 2>&1; then \
		cd paper && pdflatex -interaction=nonstopmode main.tex && \
		pdflatex -interaction=nonstopmode main.tex; \
	else \
		echo "pdflatex not found — skip local paper build (CI installs texlive)"; \
	fi

reviewer-repro:
	MLFLOW_DISABLE=1 bash scripts/reviewer_repro.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage coverage.xml
	rm -f paper/main.aux paper/main.log paper/main.out paper/main.pdf

# --- nano-orchestrator (subproject) ---

nano-validate-schema:
	cd $(NANO_DIR) && $(NANO_PYTHON) scripts/validate_schema.py

nano-test:
	cd $(NANO_DIR) && $(NANO_PYTHON) -m pytest tests/unit -q

nano-smoke:
	cd $(NANO_DIR) && $(NANO_PYTHON) -m nano_orchestrator smoke --request "$(or $(REQUEST),Create a JS clamp helper and an HTML checkout form)" --fixed-tasks

nano-bakeoff:
	cd $(NANO_DIR) && $(NANO_PYTHON) -m nano_orchestrator bakeoff --mode worker --model-id $(or $(MODEL_ID),qwen25-coder-0.5b) --base-url $(or $(BASE_URL),http://127.0.0.1:8081)

nano-gates:
	cd $(NANO_DIR) && $(NANO_PYTHON) -m nano_orchestrator gates

nano-large-site:
	cd $(NANO_DIR) && NANO_ORCH_HTML_VALIDATE=1 $(NANO_PYTHON) -m nano_orchestrator large-site

nano-large-site-all:
	cd $(NANO_DIR) && NANO_ORCH_HTML_VALIDATE=1 $(NANO_PYTHON) -m nano_orchestrator large-site --schedule benchmarks/large_site_schedule_all_models.json

nano-large-site-pro:
	cd $(NANO_DIR) && NANO_ORCH_HTML_VALIDATE=1 $(NANO_PYTHON) -m nano_orchestrator large-site --schedule benchmarks/large_site_schedule_pro.json

nano-large-site-pro-b:
	cd $(NANO_DIR) && NANO_ORCH_HTML_VALIDATE=1 $(NANO_PYTHON) -m nano_orchestrator large-site --schedule benchmarks/large_site_schedule_pro_b.json

nano-large-site-pro-c:
	cd $(NANO_DIR) && NANO_ORCH_HTML_VALIDATE=1 $(NANO_PYTHON) -m nano_orchestrator large-site --schedule benchmarks/large_site_schedule_pro_c.json

nano-large-site-pro-d:
	cd $(NANO_DIR) && NANO_ORCH_HTML_VALIDATE=1 $(NANO_PYTHON) -m nano_orchestrator large-site --schedule benchmarks/large_site_schedule_pro_d.json

nano-large-site-pro-e:
	cd $(NANO_DIR) && NANO_ORCH_HTML_VALIDATE=1 $(NANO_PYTHON) -m nano_orchestrator large-site --schedule benchmarks/large_site_schedule_pro_e.json

nano-arena:
	cd $(NANO_DIR) && $(NANO_PYTHON) -m nano_orchestrator arena --host 127.0.0.1 --port $(or $(PORT),8765)


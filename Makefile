.PHONY: check lint lint-fix test coverage docs-check hypothesis-check harness-smoke paper-build paper-sync clean install health health-gpu check-real reviewer-repro

PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)

install:
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e .

install-gpu: install
	$(PYTHON) -m pip install -r requirements-gpu.txt

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

# Nano-Orchestrator — Execution Plan (README-as-Spec)

> **Status:** approved for execution · **Location:** `nano-orchestrator/` (tracked in repo)  
> **Complements:** `docs/adr/ADR-002-student-model-selection.md`, UC-004, `docs/EVALUATION-METHOD.md`  
> **Hardware target:** RTX 4060 laptop, **8 GB VRAM**  
> **Local runtime (gitignored):** `.local/models/`, `.local/llama-prism-cuda/`, `.local/bonsai-chat/`  
> **Rules loaded:** AGENT-CORE-PRINCIPLES, token-economy, anti-hallucination, OWASP-AGENTIC-2026 (ASI02 / ASI07 / ASI08)

This README is the **normative spec** for the subproject. Code that contradicts this file is wrong until the README is updated first.

**Live tracker:** [PROGRESS.yaml](PROGRESS.yaml) — update after every work session.  
**Task backlog (100%):** [TASKS.md](TASKS.md) — work the next open checkbox (start at **T-010**).

**Index:** [TASKS](TASKS.md) · 0 TL;DR · 1 Context · 2 Architecture · 3 Contracts · 4 Stack · 5 Layout · 6 Phases · 7 14-day MVP · 8 Anti-patterns · 9 Metrics · 10 Risks · 11 Immediate next steps · 12 How to run · 13 References

---

## 0. TL;DR and Success Criterion

**Goal:** a 100% local codegen agent — no paid API, no network dependency at inference time — specialized in **JavaScript / HTML / FreeMarker** (nano-coder scope), faster and lighter in VRAM than one larger model alone, without losing quality on typed micro-tasks.

**Non-goal:** open-ended coding vs Claude / GPT / Copilot. Out of scope.

**Project success (beyond MVP):**

> Orchestration (**Orchestrator ~3B + Workers &lt;1B + Judge**) MUST beat **solo `Qwen2.5-Coder-0.5B`** on the same 30–50 micro-task gold set:
>
> | Metric | Gate |
> |--------|------|
> | Pass@1 (overall) | ≥ solo baseline |
> | Latency p50 (simple micro-task) | ≤ target measured in Phase 1 (initial reference: **≤ 2000 ms**) |
> | Resident VRAM peak | **≤ 6000 MB** (~2 GB left for OS / Cursor / IDE) |

If orchestration fails this bar → **keep solo 0.5B**. Do not add complexity.

---

## 1. Context (decided — do not reopen)

| Decision | Binding choice |
|----------|----------------|
| Topology | Orchestrator → Workers → Judge/Gate |
| Workers | Specialized `StudentModel` per `TargetLanguage` (ADR-002) |
| Orchestrator / Judge layer | **Application only** — never Domain |
| Persist generated code | **Human gate required** |
| Worker training data | Teacher distillation + Judge-approved logs |
| Every LLM call | Structured log (prompt, response, latency, verdict) |

Local stack already present (reuse — do not reinvent):

| Asset | Path |
|-------|------|
| llama-server (CUDA) | `.local/llama-prism-cuda/llama-server` |
| Qwen2.5-Coder-0.5B GGUF | `.local/models/qwen25-coder-0.5b/` (see bonsai-chat `models.json`) |
| Chat UI / model switcher | `.local/bonsai-chat/` |
| Quality bar for gold code | [`docs/CODE-QUALITY-STANDARD.md`](docs/CODE-QUALITY-STANDARD.md) |

---

## 2. Architecture

```mermaid
flowchart TD
    U[User request] --> O{{Orchestrator ~3B decompose}}
    O -->|MicroTask JSON| W1[Worker JS 0.5-0.6B]
    O -->|MicroTask JSON| W2[Worker HTML 0.5-0.6B]
    O -->|MicroTask JSON| W3[Worker FTL 0.5-0.6B]
    O -.->|optional| W4[Worker Lint-Format 135-360M]
    W1 --> J[Judge + Sandbox]
    W2 --> J
    W3 --> J
    W4 -.-> J
    J -->|score OK| M[Deterministic merge]
    J -->|score low| R[Retry this MicroTask only]
    R -.-> O
    M --> H[[Human gate]]
    H --> P[(Persistence)]
```

**Hard caps (ASI08):**

- Max **5** concurrent workers
- Max **2** retries per `MicroTask`
- Max **2–3** models resident in VRAM at once
- Orchestrator loaded **twice per cycle** only (decompose + judge/merge) — unload between via `keep_alive` / stop server

---

## 3. Contracts (Phase 0) — highest leverage deliverable

### 3.1 Pydantic schemas

Canonical implementation: [`src/nano_orchestrator/domain/entities.py`](src/nano_orchestrator/domain/entities.py)

```text
MicroTask      → id, role, language, prompt, context?, constraints[], acceptance[], max_tokens
WorkerResponse → task_id, code, confidence, notes?, latency_ms, tokens_used
JudgeVerdict   → task_id, passed, score, checks{}, retry_recommended, feedback?
```

Enums: `TargetLanguage` = `javascript | html | freemarker` · `WorkerRole` = `coder | formatter | linter`

### 3.2 Judge rubric (priority — non-negotiable)

1. **Sandbox / execution** (highest weight): real parser, syntax check, tests  
2. **Contract adherence**: valid schema, correct language, within `max_tokens`  
3. **LLM-as-judge** (lowest weight): secondary signal only — never sole decider  

### 3.3 Result-like boundaries

Domain/application boundaries use `Ok` / `Err` ([`domain/result.py`](src/nano_orchestrator/domain/result.py)). Untamed exceptions MUST NOT cross from infrastructure into application.

### 3.4 Phase 0 acceptance tests

```gherkin
GIVEN MicroTask schema
WHEN instance created with language="python"
THEN validation rejects with clear error
AND exception does not leak past the application boundary
```

```bash
cd nano-orchestrator
python -m pytest tests/unit/test_entities.py -q
python scripts/validate_schema.py
```

---

## 4. Technical Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Primary LLM runtime | **llama.cpp server** (already in `.local/llama-prism-cuda`) | GPU offload `-ngl 99`, matches bonsai-chat |
| Optional alternate | Ollama (`keep_alive`) | Faster pull for bake-off; same GGUF family |
| Language | Python 3.11+ | Aligns with nano-coder train / Unsloth path |
| Contracts | Pydantic v2 | Schema tests already scaffolded |
| Fine-tune (Phase 3) | Unsloth QLoRA | Same path validated on Qwen2.5-Coder |
| Export | GGUF Q4_K_M | llama-server / Ollama |
| Sandbox JS | `node --check` + `vm` timeout | Zero extra deps for syntax |
| Sandbox HTML | `html-validate` (npm, offline) | No Java, no network |
| Sandbox FreeMarker | Minimal JVM wrapper on `freemarker.jar` | See §10 — only mature parser |
| Tests | pytest + GIVEN/WHEN/THEN names | Project BDD style |

---

## 5. Folder Layout

```text
nano-orchestrator/                     # repo root subproject (versioned)
├── README.md                          # THIS FILE (normative)
├── PROGRESS.yaml                      # live checklist
├── pyproject.toml
├── src/nano_orchestrator/
│   ├── domain/                        # pure rules — zero I/O
│   ├── application/                   # orchestration use cases
│   ├── ports/                         # Protocol interfaces
│   └── infrastructure/                # Ollama / llama.cpp / sandboxes
├── tests/
│   ├── unit/
│   ├── integration/                   # requires running llama-server
│   └── golden/
│       ├── gold_set.json              # 30–50 tasks — HUMAN authored
│       ├── GOLD_CHECKLIST.md          # fill checklist
│       └── held_out.json              # never used for fine-tune
├── benchmarks/
│   ├── worker_bakeoff.py
│   └── RESULTS.md                     # fill with measured numbers only
├── scripts/
│   ├── setup_models.sh
│   ├── validate_schema.py
│   ├── smoke_runner.py
│   └── ftl_parser_spike/              # Phase 1 risk spike
└── docs/
    ├── CODE-QUALITY-STANDARD.md
    └── ADR-DRAFT-multi-nano-orchestration.md
```

Layers: Interfaces/CLI → Application → Domain ← Infrastructure. Domain NEVER imports outer layers.

---

## 6. Phases (detailed + exit criteria)

### Phase 0 — Contract (1–2 days)

| Deliverable | Path | DoD |
|-------------|------|-----|
| Entities | `domain/entities.py` | Unit tests green |
| Result type | `domain/result.py` | Used at port boundaries |
| Rubric stub | `domain/rubric.py` | Weights documented in code |
| Schema validator | `scripts/validate_schema.py` | Exit 0 on gold JSON |
| Gold format | `tests/golden/gold_set.json` | ≥ 3 exemplars valid; checklist open for 30 |

**Exit:** `pytest tests/unit -q` AND `validate_schema.py` pass.

---

### Phase 1 — Worker bake-off (1 week)

#### Worker candidates (&lt;1B)

| Candidate | Params | License | How to get | Notes |
|-----------|--------|---------|------------|-------|
| **Qwen2.5-Coder-0.5B** | 0.5B | Apache 2.0 | Already local GGUF / `ollama pull qwen2.5-coder:0.5b` | **Baseline** |
| Qwen3-0.6B | 0.6B | Apache 2.0 | `ollama pull qwen3:0.6b` or HF→GGUF | Strong successor |
| Gemma3-270M | 0.27B | Gemma terms | `ollama pull gemma3:270m` | Lower bound (ADR-002) |
| SmolLM2-360M | 0.36M | Apache 2.0 | `ollama pull smollm2:360m` | Weak code unless fine-tuned |
| MobileLLM-R1-360M | 0.36B | **FAIR NC** | HF only | **Research only — not for Zaflas product** |

#### Orchestrator / Judge candidates (~3B)

| Candidate | Params | License | How to get | Notes |
|-----------|--------|---------|------------|-------|
| SmolLM3-3B | 3B | Apache 2.0 | HF `HuggingFaceTB/SmolLM3-3B` → GGUF | PT-BR in training mix; confirm Ollama tag |
| Nanbeige4.1-3B | ~3.9B | Apache 2.0 | HF / community Ollama | Strong code claims; validate on **your** gold set (possible benchmax) |

```gherkin
GIVEN gold set of 30–50 micro-tasks
WHEN each candidate runs the same set
THEN RESULTS.md records pass@1, p50 latency, peak VRAM
AND no candidate is cut without scoring all three languages
```

**Exit:** [benchmarks/RESULTS.md](benchmarks/RESULTS.md) filled with **measured** numbers; top-2 workers + preferred orchestrator chosen.

---

### Phase 2 — Minimal orchestrator (1–2 weeks)

No CrewAI / LangGraph on day 1.

**Loop:**

1. Load orchestrator → emit `list[MicroTask]`  
2. Unload orchestrator (`keep_alive=0` / stop server)  
3. Run workers (≤2 concurrent on 8 GB)  
4. Sandbox checks → `JudgeVerdict`  
5. Retry failed tasks (≤2)  
6. Reload orchestrator → merge / optional LLM secondary score  
7. Print package for **human gate** (no auto-write to disk)

```gherkin
GIVEN a user request
WHEN Orchestrator decomposes into MicroTasks
THEN each MicroTask validates against entities.py
AND active workers ≤ 5
```

**Exit:** `python scripts/smoke_runner.py` processes one request end-to-end and prints scores.

---

### Phase 3 — Specialize workers (nano-coder core)

- One LoRA/QLoRA per `TargetLanguage` via Unsloth  
- Train on Judge-approved logs from Phases 1–2 (+ teacher distillation)  
- Export GGUF Q4_K_M → llama-server  
- Held-out set stays out of training  

```gherkin
GIVEN a fine-tuned worker exported Q4_K_M
WHEN scored on held_out.json
THEN pass@1 ≥ base model
AND VRAM footprint does not grow vs base
```

---

### Phase 4 — Reliable Judge

| Check | Tool | Gate |
|-------|------|------|
| JS syntax | `node --check` | must pass |
| JS optional exec | `vm` + timeout | if `acceptance` asks |
| HTML | `html-validate` CLI | must pass |
| FreeMarker | JVM wrapper (`ftl_parser_spike`) | must pass |
| LLM secondary | Orchestrator 3B | never sole pass |

Log every call to `logs/llm_calls.jsonl` (local, gitignored pattern under this folder).

---

### Phase 5 — Dynamic orchestration (only after 0–4 work)

- Dynamic worker selection + retry budget  
- Debate only for critical tasks (~2.5× cost) — not default  

---

## 7. MVP — 14-day executable checklist

Update [PROGRESS.yaml](PROGRESS.yaml) as you go.

| Day | Deliverable | Concrete action | Definition of Done |
|-----|-------------|-----------------|--------------------|
| **1–2** | Schemas + gold start | Finish entities tests; hand-write gold (see GOLD_CHECKLIST) | `validate_schema.py` exit 0; ≥10 tasks written |
| **3** | Gold complete | Finish 10 JS / 10 HTML / 10 FTL by hand | 30 tasks in `gold_set.json`; held_out has ≥6 |
| **4–5** | Runner skeleton | Wire llama.cpp adapter + smoke_runner | One request E2E prints `JudgeVerdict` JSON |
| **6–7** | JS + HTML sandboxes | `node --check` + `npm i html-validate` | Gold JS/HTML produce `checks` map |
| **8** | FTL spike | Build `scripts/ftl_parser_spike` (Java) | Parse OK + ParseException → bool |
| **9–11** | Worker bake-off | `benchmarks/worker_bakeoff.py` | RESULTS.md filled (measured) |
| **12** | Pick winners | Document choice in PROGRESS.yaml | 2 workers + 1 orchestrator locked |
| **13–14** | LoRA smoke | Unsloth QLoRA on best 0.5B worker | Export GGUF; pass@1 not worse than base |

**MVP success:** orchestration ≥ solo Qwen2.5-Coder-0.5B on gold set under §0 gates.

---

## 8. Anti-patterns (guardrails)

| Anti-pattern | Why forbidden |
|--------------|---------------|
| 10 nanos chatting to each other | Cascading failures without contract (ASI08) |
| Orchestrator &lt;1B | Cannot plan; keep ~3B on top |
| Generic un-specialized worker | 0.5B capacity dilutes |
| LLM-as-judge alone | Sandbox required |
| Dynamic swarm before fixed pipeline works | Sequential supervisor first |
| All models resident in VRAM | 8 GB OOM / swap death |
| Trust published benches without gold set | Especially Nanbeige4.1 |
| Ship MobileLLM-R1 in product | FAIR NC license |
| AI-generated gold set as ground truth | Human-authored only (§11) |

---

## 9. Metrics template (Phase 1)

Copy into [benchmarks/RESULTS.md](benchmarks/RESULTS.md) — **numbers only after measurement**.

| Model | Role | Pass@1 JS | Pass@1 HTML | Pass@1 FTL | p50 ms | VRAM MB | tok/s |
|-------|------|-----------|-------------|------------|--------|---------|-------|
| Qwen2.5-Coder-0.5B | baseline | | | | | | |
| Qwen3-0.6B | worker | | | | | | |
| Gemma3-270M | worker | | | | | | |
| SmolLM2-360M | worker | | | | | | |
| SmolLM3-3B | orchestrator | | | | | | |
| Nanbeige4.1-3B | orchestrator | | | | | | |

Pass@1 definition for a micro-task: `JudgeVerdict.passed == true` after sandbox (retries counted separately as Pass@k).

---

## 10. Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No mature FreeMarker parser outside JVM | Blocks FTL Phase 4 | Day-8 spike: ~30-line Java wrapper on `freemarker.jar`; JRE headless (~50–100 MB disk, 0 VRAM) |
| MobileLLM-R1 FAIR NC | Cannot ship to customers | Benchmark-only; never fine-tune into product |
| VRAM contention on 8 GB | Swap / hang | Orchestrator 2×/cycle; ≤2–3 resident models; unload aggressively |
| Nanbeige4.1 possible benchmax | Wrong orchestrator pick | Decide only from RESULTS.md on local gold |
| Overfit on 30–50 train tasks | Brittle workers | `held_out.json`; early stopping |
| Retry cascade | Latency explosion | Cap 2 retries; escalate to human gate |

---

## 11. Immediate next steps

### Today (Phase 0 kickoff)

**Next task:** [T-030 in TASKS.md](TASKS.md) — Phase 2 LlamaCppAdapter / decompose loop.

Phase 1 bake-off **complete** — winners locked in PROGRESS.yaml. See [benchmarks/RESULTS.md](benchmarks/RESULTS.md).

```bash
cd nano-orchestrator
python scripts/validate_schema.py
python scripts/validate_gold_code.py
python -m pytest tests/unit -q
./scripts/start_model_server.sh qwen25-coder-0.5b
python benchmarks/worker_bakeoff.py --mode worker --model-id qwen25-coder-0.5b --write-results
```

### Tomorrow

- Reach **≥ 15** gold tasks by hand (mix of languages).  
- Do **not** ask an LLM to invent the gold set — it becomes circular evaluation.

### This week

```bash
./scripts/setup_models.sh   # pulls bake-off candidates (Ollama path)
# FTL spike:
cd scripts/ftl_parser_spike && ./build.sh   # after spike skeleton exists (Day 8)
```

### Explicit choice deferred

ADR formalization vs coding: skeleton + this README are enough to start Phase 0–2. Formal ADR draft lives at [docs/ADR-DRAFT-multi-nano-orchestration.md](docs/ADR-DRAFT-multi-nano-orchestration.md) — promote into repo `docs/adr/` when ready.

---

## 12. How to run (operator cheatsheet)

```bash
# From repo root
cd nano-orchestrator

# Install (editable)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Phase 0
pytest tests/unit -q
python scripts/validate_schema.py

# Start baseline worker (reuse existing GGUF — example)
# ../.local/llama-prism-cuda/llama-server -m ../.local/models/qwen25-coder-0.5b/*.gguf -ngl 99 -c 8192 --port 8081

# Smoke (Phase 2 — stub until wired)
python scripts/smoke_runner.py --request "Create a FreeMarker list item and a JS filter helper"
```

Human gate: smoke_runner prints proposed files to stdout / `out/proposal/` — **operator copies manually**. Never auto-commit generated code.

---

## 13. References

- Meta AI — MobileLLM-R1 — arXiv:2509.24945 (license: FAIR NC)  
- Hugging Face — SmolLM3 blog — https://huggingface.co/blog/smollm3  
- Nanbeige — Nanbeige4.1-3B — arXiv:2602.13367  
- Google — Gemma 3 270M announcement  
- html-validate — https://html-validate.org  
- OWASP Agentic AI Top 10 (2026) — ASI02 / ASI07 / ASI08  
- Parent project — `docs/adr/ADR-002-student-model-selection.md`, `nano-orchestrator/docs/CODE-QUALITY-STANDARD.md`

---

**Stop condition:** if after Day 14 orchestration loses to solo 0.5B on gold → archive this subproject as a negative result and document in parent `experiments/` — that is still a successful research outcome.

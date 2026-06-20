# AGENTS.md — nano-coder

> **Read this first** in any new agent session (Cursor, Claude Code, Codex, Windsurf, etc.).

**Language:** 100% English — code, comments, docs, commits, and all agent output.

---

## What this repo is

| Is | Is not |
|----|--------|
| SLM fine-tuning benchmark pipeline (JS/HTML/FreeMarker) | A hosted coding API product |
| Synthetic data via teacher LLM distillation | Ready-to-run without completing docs checklist |
| OWASP 2025 + Agentic 2026 aligned | Free to skip rules without user override |

**Project docs:** [docs/README.md](docs/README.md) — start with [docs/GLOSSARY.md](docs/GLOSSARY.md) and [docs/PHASES.md](docs/PHASES.md).

When rules conflict with existing code, **rules prevail** — unless the user explicitly overrides for a task.

---

## Rules path (resolve first)

```bash
pip install -r agent-harness/requirements.txt   # once per machine
./agent-harness/rules-path.sh
```

| Config file | `rules_dir` |
|-------------|-------------|
| `agent-harness/harness.config.yaml` | `agent-rules/` |

Paths are relative to **project root**. Use output from `rules-path.sh`; do not hardcode paths.

---

## Always load (base context)

Read these at session start or before non-trivial work:

1. `agent-rules/AGENT-CORE-PRINCIPLES.md` — architecture contract
2. `agent-rules/09-ai-agent-specific/token-economy.md` — load less, execute better
3. `agent-rules/09-ai-agent-specific/anti-hallucination.md` — verify before assert

Cursor users: `.cursor/rules/*.mdc` applies automatically (`alwaysApply`). Regenerate after clone:

```bash
./agent-harness/install.sh . --cursor-only
```

---

## Conditional load (task-specific)

Load **2–6 files only** — not the entire rule tree.

```bash
./agent-harness/resolve-rules.sh <keywords from task>
```

| Task | Example keywords |
|------|------------------|
| API endpoint | `api endpoint auth validation contract` |
| Security review | `owasp security authz bola agentic` |
| Domain feature | `domain layer state event` |
| Bug fix | `bugfix regression error` |
| Performance | `query cache n+1` |

### Cursor: task-scoped rule file (optional)

```bash
./agent-harness/generate-task-rules.sh api endpoint auth
./agent-harness/generate-task-rules.sh --clean   # when task done
```

Creates `.cursor/rules/_task-active.mdc`. Delete when the task is finished.

**Index:** `agent-rules/STRUCTURE.md`  
**Manifest:** `agent-rules/manifest.yaml`  
**Security map:** `agent-rules/03-security/README.md`

---

## Agent protocol

1. Run `./agent-harness/rules-path.sh` → confirm `agent-rules/`.
2. Identify task keywords → run `./agent-harness/resolve-rules.sh`.
3. State which rule files you loaded (brief list).
4. **ASK** if [docs/NEW-PROJECT-CHECKLIST.md](docs/NEW-PROJECT-CHECKLIST.md) items are blank — never assume business rules.
5. Smallest diff; one logical change per commit.
6. Verify after each edit — do not claim tests passed without running them.
7. English only in all artifacts.

---

## Key references

| Document | Purpose |
|----------|---------|
| [agent-rules/AGENT-CORE-PRINCIPLES.md](agent-rules/AGENT-CORE-PRINCIPLES.md) | Domain architecture contract |
| [agent-rules/STRUCTURE.md](agent-rules/STRUCTURE.md) | Full rule tree + task mapping |
| [agent-rules/03-security/OWASP-TOP10-2025.md](agent-rules/03-security/OWASP-TOP10-2025.md) | Web/API security (A01–A10) |
| [agent-rules/03-security/OWASP-AGENTIC-2026.md](agent-rules/03-security/OWASP-AGENTIC-2026.md) | Agentic AI security (ASI01–ASI10) |
| [agent-harness/README.md](agent-harness/README.md) | Install, resolve, maintenance |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Domain ubiquitous language |
| [README.md](README.md) | Human-oriented project overview |

---

## Optional local overrides

Project-specific rules not in harness: `.local/overrides/` (gitignored). Harness rules still apply unless user explicitly waives.

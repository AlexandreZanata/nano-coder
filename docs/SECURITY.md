# Security — nano-coder

> OWASP Top 10:2025 and Agentic 2026 mapping for this project. Phase 1 is local CLI — several items are preparatory for future API.

---

## Threat model summary

| Asset | Risk |
|-------|------|
| `TEACHER_API_KEY`, `HF_TOKEN` | Secret leakage → financial abuse |
| Teacher-generated code | Malicious code execution on operator machine (ASI05) |
| Synthetic dataset files | Poisoned training data (ASI06) |
| Agent rule packs / skills | Supply chain tampering (ASI04) |
| LLM prompts with seeds | Accidental PII in API calls |

---

## OWASP Top 10:2025 mapping

| ID | Risk | nano-coder control |
|----|------|-------------------|
| A01 Broken Access Control | Future API roles | RBAC in [ARCHITECTURE.md](ARCHITECTURE.md); phase 1 local only |
| A02 Security Misconfiguration | Debug flags, open CORS | No debug endpoints; config validated at CLI start |
| A03 Supply Chain | HF models, npm linters | Pin versions; verify checksums; ADR-003 documents sources |
| A04 Cryptographic Failures | Secrets in repo | `.env` gitignored; BR-006 budget limits API blast radius |
| A05 Injection | Eval of generated JS | BR-009 sandbox; no `eval` in pipeline |
| A06 Insecure Design | Auto-run without review | BR-007 human confirm before train; manual seed review |
| A07 Authentication Failures | N/A phase 1 | Required if HTTP dashboard added |
| A08 Software/Data Integrity | Dataset tampering | Immutable `DatasetVersion`; event log append-only |
| A09 Logging Failures | No audit of LLM calls | Log teacher calls: model, timestamp, token count (no secrets) |
| A10 SSRF | Teacher fetching URLs | Teacher API only; no user-supplied URLs in pipeline v1 |

Full rules: `agent-rules/03-security/`

---

## OWASP Agentic 2026 (ASI01–ASI10)

| ID | Control in nano-coder |
|----|----------------------|
| ASI01 Goal hijack | Seeds and prompts in version-controlled files; not from untrusted web in v1 |
| ASI02 Tool misuse | CLI allow-list only; agents use documented commands |
| ASI03 Identity abuse | Separate env keys per operator machine; no shared prod credentials |
| ASI04 Supply chain | Pin `agent-rules` / harness version; verify submodule if used |
| ASI05 Unexpected code execution | BR-009 sandbox for ExecutionCheck |
| ASI06 Memory poisoning | Agents must not write to `agent-rules/` without human review |
| ASI07 Inter-agent comms | N/A single pipeline |
| ASI08 Cascading failures | BR-006 budget cap; cancel long runs |
| ASI09 Human trust exploitation | Manual review sample before publish; confirm before train |
| ASI10 Rogue agents | Kill switch: cancel run; no auto-publish |

Full index: `agent-rules/03-security/OWASP-AGENTIC-2026.md`

---

## Agent integration (AGENT-CORE-PRINCIPLES §13)

- AI agents operate in **Application layer** orchestration only
- **Read-only** on published datasets and checkpoints unless operator confirms write
- **Log** all teacher LLM calls (input hash, output hash, model id)
- **Never** send secrets or PII in prompts — seeds must be synthetic scenarios
- Generated code is **suggestion** until gates pass

---

## Data retention

| Data | Retention |
|------|-----------|
| Event log | Project lifetime |
| API logs | 90 days local |
| Draft failed generations | 30 days then purge |
| Published datasets | Permanent for reproducibility |

---

## Checklist (security)

- [x] Secrets in `.env` only — `.env.example` documents vars
- [x] ASI05 sandbox required before ExecutionCheck
- [x] Human confirm gates for publish and train
- [ ] Dependency lockfile when stack chosen (Python `requirements.txt` pending)
- [ ] CI secret scanning when repo pushed to remote

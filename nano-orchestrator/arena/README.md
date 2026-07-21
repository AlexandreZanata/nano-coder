# Nano-Orchestrator Arena

Local playground to inspect orchestrator outputs (human gate).

## Run

```bash
make nano-arena
# or: cd nano-orchestrator && python -m nano_orchestrator arena
```

Open **http://127.0.0.1:8765**

## What you see

| Pane | Source |
|------|--------|
| Proposal files | `out/proposal/*` |
| Verdicts / scores | `out/proposal/package.json` |
| HTML preview | sandboxed iframe |
| Schedule runs | `benchmarks/runs/*.json` |

Auto-refresh every 3s while a schedule is running (`make nano-large-site-all`).

**Never auto-persists** — review only.

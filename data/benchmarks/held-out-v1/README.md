# Held-out test set — `held-out-v1`

Immutable benchmark tasks (BR-004, BR-008). **Never** use in training or synthetic generation.

| File | Purpose |
|------|---------|
| `manifest.json` | Version metadata and task counts |
| `js.jsonl` | 50 JavaScript held-out tasks |
| `html.jsonl` | 50 HTML held-out tasks |
| `fmt.jsonl` | 50 FreeMarker held-out tasks |

**Regenerate** (only before v1 is frozen in production runs):

```bash
python scripts/bootstrap_held_out_tasks.py
```

**Schema:** `config/held-out-v1/task.schema.json`  
**Scope source:** `config/scope-boundary.yaml`

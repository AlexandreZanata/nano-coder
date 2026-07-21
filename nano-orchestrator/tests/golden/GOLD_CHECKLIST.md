# Gold set checklist — v1 FROZEN (2026-07-21)

Target: **10 JavaScript + 10 HTML + 10 FreeMarker** = 30 tasks in `gold_set.json`.  
Held-out: **≥2 per language** in `held_out.json` (never used for fine-tune).

Quality bar: [`docs/CODE-QUALITY-STANDARD.md`](../../docs/CODE-QUALITY-STANDARD.md)  
Backlog: **T-010…T-014** marked done in [TASKS.md](../../TASKS.md).

## Rules

- Gold v1 is **frozen** (`"frozen": true`). Prefer additive v2 file over silent edits.
- Held-out IDs must stay out of fine-tune datasets.
- Re-validate after any change:

```bash
python scripts/validate_schema.py
python scripts/validate_gold_code.py
```

## JavaScript (10) — T-010 done

| ID | Written? | Prompt summary |
|----|----------|----------------|
| js-001 | yes | filterValues pure function |
| js-002 | yes | parsePositiveInt |
| js-003 | yes | uniqueSorted |
| js-004 | yes | groupBy |
| js-005 | yes | safeJsonParse Result-like |
| js-006 | yes | debounce + cancel |
| js-007 | yes | clamp |
| js-008 | yes | toQueryString |
| js-009 | yes | deepFreeze |
| js-010 | yes | assertNever |

## HTML (10) — T-011 done

| ID | Written? | Prompt summary |
|----|----------|----------------|
| html-001 | yes | accessible submit form |
| html-002 | yes | skip link + main |
| html-003 | yes | definition list |
| html-004 | yes | table with caption + scope |
| html-005 | yes | figure + figcaption |
| html-006 | yes | nav aria-current |
| html-007 | yes | fieldset radios |
| html-008 | yes | article + h1 |
| html-009 | yes | dialog method=dialog |
| html-010 | yes | breadcrumb ol |

## FreeMarker (10) — T-012 done

| ID | Written? | Prompt summary |
|----|----------|----------------|
| ftl-001 | yes | product list ?html |
| ftl-002 | yes | admin/member #if |
| ftl-003 | yes | #list + #sep |
| ftl-004 | yes | price ?string |
| ftl-005 | yes | default ! |
| ftl-006 | yes | #macro pageTitle |
| ftl-007 | yes | #switch status |
| ftl-008 | yes | ?url path segment |
| ftl-009 | yes | empty list message |
| ftl-010 | yes | #assign fullName |

## Held-out (6) — T-013 done

| ID | Language | Written? | Prompt summary |
|----|----------|----------|----------------|
| ho-js-001 | javascript | yes | isBlank |
| ho-js-002 | javascript | yes | chunk |
| ho-html-001 | html | yes | email label |
| ho-html-002 | html | yes | ul three items |
| ho-ftl-001 | freemarker | yes | #list 1..3 |
| ho-ftl-002 | freemarker | yes | yes/no flag |

## Progress

| Block | Done count | Target |
|-------|------------|--------|
| JS | 10 | 10 |
| HTML | 10 | 10 |
| FTL | 10 | 10 |
| Held-out | 6 | 6 |
| **Freeze T-014** | **yes** | yes |

# Code Quality Standard — Training Data (Enterprise Bar)

> Every `GoldSeedExample` and accepted `SyntheticExample` MUST meet this bar.
> Training on mediocre code teaches the student model to reproduce mediocrity.

**Applies to:** JavaScript, HTML, FreeMarker (and instruction text paired with them).

---

## 1. Universal rules (all languages)

| Rule | Requirement |
|------|-------------|
| **Single responsibility** | One clear task per example — no kitchen-sink snippets |
| **No secrets** | No API keys, tokens, real URLs with credentials, PII |
| **No placeholders** | No `TODO`, `FIXME`, `...`, `your code here`, lorem ipsum logic |
| **Deterministic** | Same instruction → same structural pattern (no random naming per run) |
| **Readable** | Names reveal intent; no `x`, `tmp`, `data1` unless teaching naming anti-patterns (tag explicitly) |
| **Minimal but complete** | Shortest code that fully satisfies the instruction — no dead code |
| **English only** | Identifiers, comments, instructions in English |
| **Consistent style** | One style guide per language file — see §2–§4 |

---

## 2. JavaScript — enterprise bar

### Must have

- `"use strict"` or ES module (`export`/`import`) — pick one style per seed batch
- `const` / `let` only — no `var`
- Explicit error handling where I/O or parsing occurs (`try/catch` or Result pattern)
- Pure functions preferred; side effects isolated and named
- JSDoc on exported/public functions (`@param`, `@returns`, `@throws` when relevant)

### Must NOT have

- `eval`, `Function()`, dynamic `import()` from user strings
- Implicit globals
- Console.log as “implementation” (only in examples tagged `debugging`)
- Libraries unless instruction explicitly requires one (and version noted)

### Lint target (when gate implemented)

- ESLint recommended + `eslint:recommended`
- Max function length: **30 lines** (aligns with agent-rules)
- Max cyclomatic complexity: **10** per function

### Good example shape

```javascript
/**
 * Returns elements matching predicate — does not mutate input.
 * @param {number[]} values
 * @param {(n: number) => boolean} predicate
 * @returns {number[]}
 */
export function filterValues(values, predicate) {
  if (!Array.isArray(values)) {
    throw new TypeError("values must be an array");
  }
  return values.filter(predicate);
}
```

---

## 3. HTML — enterprise bar

### Must have

- `<!DOCTYPE html>` when full document; or valid fragment when instruction says “snippet”
- Semantic tags (`header`, `main`, `nav`, `section`, `article`, `footer`) when structure warrants
- `lang` attribute on `<html>` for full documents
- Accessible basics: `alt` on images, `<label for>` on form fields, button `type`
- Indentation: 2 spaces, consistent

### Must NOT have

- Inline event handlers (`onclick=`) — use `addEventListener` in paired JS examples instead
- Deprecated tags for new examples (`<center>`, `<font>`) unless tagged `legacy-html`
- Empty `alt=""` on informative images

### Validation target

- HTML5 parser pass
- Optional: subset of axe rules (labels, landmarks)

---

## 4. FreeMarker — enterprise bar

### Must have

- Explicit data model documented in instruction (what variables exist and types)
- `<#-- comment -->>` for non-obvious macro behavior
- Macros with clear parameter list; avoid deep nesting (>3 levels)
- Safe output: `${var?html}` or `?no_esc` only when instruction requires raw HTML and is tagged `trusted-html`

### Must NOT have

- Arbitrary `?eval` or executing user-controlled strings
- Includes from dynamic paths without allow-list
- Macro names that collide with built-ins

### Validation target

- FreeMarker syntax parser
- Fixture JSON + render smoke when macro generates markup

---

## 5. Instruction text quality (paired with code)

Each example is `{ instruction, code, tags }`.

| Field | Standard |
|-------|----------|
| **instruction** | Imperative, specific, testable (“Write a function that…”, not “help me with arrays”) |
| **code** | Complete answer — not a partial diff |
| **tags** | At least one: domain tag + difficulty tag (see playbook taxonomy) |

Bad instruction: *“Make some HTML”*  
Good instruction: *“Write a semantic HTML5 contact form with name, email, and message fields. Labels must be associated with inputs. Submit button type=submit.”*

---

## 6. Anti-patterns — auto-reject for gold seeds

- [ ] Copied from Stack Overflow without rewriting to standard
- [ ] Teacher hallucinated API (method that does not exist)
- [ ] Inconsistent naming within same file (`userName` vs `user_name`)
- [ ] Commented-out code blocks
- [ ] Giant monolithic functions (>30 lines) without decomposition tag
- [ ] Mixed languages in one file (unless tagged `polyglot-example`)

---

## 7. Difficulty taxonomy (required tag)

| Tag | Meaning |
|-----|---------|
| `L1-trivial` | Single concept (one loop, one tag) |
| `L2-standard` | Typical enterprise task (form, utility, template macro) |
| `L3-composite` | Multi-step (JS module + HTML fragment + FMT macro) |
| `L4-edge-case` | Error paths, empty input, boundary values |

Target mix per language in published dataset:

- L1: 15% · L2: 50% · L3: 25% · L4: 10%

---

## 8. Domain taxonomy (required tag)

**JavaScript:** `array`, `object`, `async`, `dom`, `validation`, `module`, `class`, `functional`, `error-handling`

**HTML:** `forms`, `semantic`, `accessibility`, `layout`, `metadata`, `tables`, `media`

**FreeMarker:** `macro`, `include`, `list`, `condition`, `formatting`, `nested`, `custom-directive`

---

## 9. Self-review before promoting seed to `data/seeds/`

Answer **yes** to all:

1. Would I approve this in a production PR?
2. Does the code run/parse without modification?
3. Is the instruction unambiguous?
4. Is there exactly one primary learning objective?
5. Are tags and difficulty set?
6. Is it isolated from held-out test topics? (see playbook Stage 0)

If any **no** → revise in `.local/seeds/draft/` before promotion.

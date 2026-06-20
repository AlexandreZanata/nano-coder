# Evol-Instruct — widen domain context (v1)

Target language: {{TARGET_LANGUAGE}}
Base seed id: {{BASE_SEED_ID}}

Keep the same algorithmic pattern as the base seed but apply it to a NEW domain context
(different variable names, business scenario, or data shape).

Base example:
{{BASE_SEED_JSON}}

Domain tag required: {{DOMAIN_TAG}}
Difficulty: keep {{DIFFICULTY}}.

Output ONE JSON object. id prefix syn-{{LANG_PREFIX}}-.
metadata.notes must include "expansion: evol-widen".

JSON only.

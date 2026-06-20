# Evol-Instruct — shorten while preserving behavior (v1)

Target language: {{TARGET_LANGUAGE}}
Base seed id: {{BASE_SEED_ID}}

Produce a minimal but complete version of the base task — fewer lines, no dead code,
same observable behavior for typical inputs.

Base example:
{{BASE_SEED_JSON}}

Output ONE JSON object. id prefix syn-{{LANG_PREFIX}}-.
metadata.notes must include "expansion: evol-shorten".
Difficulty tag: {{DIFFICULTY}}.

JSON only.

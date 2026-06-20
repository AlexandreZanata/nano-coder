# Evol-Instruct — deepen difficulty (v1)

Target language: {{TARGET_LANGUAGE}}
Base seed id: {{BASE_SEED_ID}}

Increase complexity from L{{FROM_LEVEL}} to L{{TO_LEVEL}} while keeping the same core pattern.

Base example:
{{BASE_SEED_JSON}}

Add: error paths, edge cases, or multi-step logic appropriate for {{TO_LEVEL}}.
Do not introduce frameworks or held-out topics.

Output ONE JSON object (same schema as self-instruct). id prefix syn-{{LANG_PREFIX}}-.
metadata.notes must include "expansion: evol-deepen".

JSON only.

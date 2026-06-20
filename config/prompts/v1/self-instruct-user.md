# Self-Instruct user prompt — Stage 4 (v1)

Target language: {{TARGET_LANGUAGE}}
Expansion method: self-instruct
Difficulty target: {{DIFFICULTY_TARGET}}
Domain tag required: {{DOMAIN_TAG}}

Generate a NEW example inspired by but not copying these gold seeds:

{{FEW_SHOT_SEEDS}}

Requirements:
- Different instruction wording and code structure from all few-shots.
- Include tag {{DOMAIN_TAG}} and difficulty {{DIFFICULTY_TARGET}}.
- id must use prefix syn-{{LANG_PREFIX}}- and a new unused number.

Output JSON only.

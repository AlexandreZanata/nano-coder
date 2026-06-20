# Gold seeds — promoted `GoldSeedExample` records

Manual seeds promoted from `.local/seeds/draft/` after validation (Stage 3).

## Layout

```
data/seeds/
├── reference/          # Quality anchors (few-shot templates) — do not delete
│   ├── REF-js-enterprise-utility.json
│   ├── REF-html-a11y-form.json
│   └── REF-fmt-macro-list.json
├── javascript/         # Promoted JS seeds (seed-js-NNN.json)
├── html/               # Promoted HTML seeds (seed-html-NNN.json)
└── freemarker/         # Promoted FMT seeds (seed-fmt-NNN.json)
```

## Schema and taxonomy

| Artifact | Path |
|----------|------|
| JSON Schema | `config/seeds-v1/seed.schema.json` |
| Tag taxonomy | `config/seeds-v1/taxonomy.yaml` |
| Quality bar | `.local/CODE-QUALITY-STANDARD.md` |

## Validate before promotion

```bash
python scripts/bootstrap_gold_seeds.py   # regenerate from catalog
python scripts/validate_seed.py data/seeds/javascript/ --require-metadata
python scripts/validate_seed.py data/seeds/html/ --require-metadata
python scripts/validate_seed.py data/seeds/freemarker/ --require-metadata
```

BR-001 requires ≥50 promoted seeds per `TargetLanguage` before synthetic expansion.

## Promotion (Stage 3)

```bash
python scripts/promote_seeds.py --verify data/seeds --skip-lint
python scripts/promote_seeds.py --draft .local/seeds/draft   # promote draft → data/seeds/
```

Manifest: `data/seeds/manifest.json` · ESLint config: `config/eslint/eslint.config.js`

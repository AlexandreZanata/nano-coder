# Paper draft

LaTeX skeleton for workshop or arXiv submission. Structure modeled after [quantun-ia/paper](https://github.com/AlexandreZanata/quantun-ia/tree/main/paper).

## Build

```bash
make paper-build
# or:
cd paper && pdflatex main.tex && pdflatex main.tex
```

## Structure

| Path | Purpose |
|------|---------|
| `main.tex` | Document entry |
| `sections/` | Introduction, methods, experiments, results, limitations |
| `tables/` | Auto-generated LaTeX (future: `make latex-tables`) |
| `figures/` | Pass@k and χ heatmaps (future: `make figures`) |
| `references.bib` | Bibliography |
| `arxiv_metadata.yaml` | arXiv upload metadata |

Narrative scope: [docs/PAPER-NARRATIVE.md](../docs/PAPER-NARRATIVE.md).

## Submission checklist

- [ ] `make check` green on main
- [ ] Publication-profile runs on RTX 4060 (`make check-real`)
- [ ] All in-scope `results.md` filled
- [ ] `make paper-build` produces `main.pdf`
- [ ] CITATION.cff + Zenodo DOI (optional)
- [ ] arXiv upload — set `arxiv_id` in `arxiv_metadata.yaml`

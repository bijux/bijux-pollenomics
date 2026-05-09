# Repository docs scope validation

- Rule: no docs rewrite may destroy breadth in 01, 02, or 03 unless an equally informative replacement is already present and linked
- Overall ok: `false`

| Section | Landing | Required pages | Missing pages | Missing links |
| --- | --- | ---: | --- | --- |
| Runtime handbook | `docs/public/pollenomics/index.md` | 12 | `none` | `interfaces/entrypoints-and-examples/`, `operations/common-workflows/`, `quality/change-validation.md` |
| Data handbook | `docs/public/pollenomics-data/index.md` | 15 | `none` | `none` |
| Maintainer handbook | `docs/internal/maintain/index.md` | 5 | `none` | `none` |

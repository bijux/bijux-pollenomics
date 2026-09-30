# Why we separated research reports from governed results

## Our decision

We made root `reports/` the reader's entry point for scientific arguments,
source decisions, results and limits. We kept numeric products, source
receipts, producer scripts and verification fixtures at their governed
destinations until each producer and citation can move with them. We publish
selected rights-safe explanations through `docs/public/` and source-locked
PDF briefings through `presentation/`. We keep local runs under `artifacts/`.

We made this decision because `docs/report/` serves several incompatible
roles. Our 29 September 2026 inventory counted **1,819 files and
346,859,031 bytes** there: scientific rows, source receipts, generated
website assets, tests, scripts and human reports. Eight major areas account
for **1,606 files**:

| Governed area | Files | Approximate MiB | Responsibility we retained there |
| --- | ---: | ---: | --- |
| `regions/` | 454 | 212.49 | Nordic generated maps, browser assets, source and score products. |
| `source-relations/` | 121 | 43.57 | Source correspondence and custody. |
| `atlas/` | 116 | 16.76 | Browser checks and assets used by the website build. |
| `world/` | 172 | 12.51 | World products and assets used by the publisher. |
| `pollen-reconstruction/` | 123 | 10.51 | Study products, scores and the scientific verifier. |
| `publication-replay/` | 53 | 6.80 | Paper/archive correspondence rows and source receipts. |
| `method-certification/` | 461 | 4.40 | R oracle cases, reference bundles and fixtures. |
| `countries/` | 106 | 3.52 | Country source and field products. |

Across the full tree we counted 439 JSON, 431 CSV, 404 JavaScript and 268
Markdown files. We do not assign ownership from extensions: each move needs
its producer, source rights and citation role identified.

## What we changed

We created [the research index](../README.md) and a
[claim-to-evidence index](../evidence-index.md) so a reader can go from a
scientific question to an exact numeric row and its source. Our root
science reports now own the human interpretation for the following work;
the linked governed products retain the numeric and producer ownership.

| Research question now owned in `reports/` | Governed result or source boundary |
| --- | --- |
| [Publication and archive correspondence](../science/publication-correspondence.md) | [Paper correspondence ledger](../../docs/report/pollen-reconstruction/paper-correspondence.csv) and [PFT crosswalk](../../docs/report/publication-replay/landclim-pft-crosswalk/README.md). |
| [Nordic pollen synthesis](../science/nordic-pollen-study.md), [country results](../science/denmark-finland-norway-author-pollen.md) and [Swedish holdout](../science/sweden-author-pollen.md) | [Country score products](../../docs/report/regions/nordic/author-target-pollen/report.json) and [Swedish score products](../../docs/report/regions/nordic/swedish-author-target-pollen/report.json). |
| [Nordic training selection](../science/nordic-observed-pollen-selection.md) and [matched transfer](../science/nordic-observed-pollen-transfer.md) | [Search trial ledger](../../docs/report/regions/nordic/pollen-development/report.json) and [transfer freeze](../../docs/report/regions/nordic/selected-pollen-transfer/freeze.json). |
| [English LOVE and forward pollen](../science/english-lra-pollen-prediction.md) | [Fold/score products](../../docs/report/pollen-reconstruction/author-lra-constrained/report.json) and [basin-radius sensitivity](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/README.md). |
| [HYDE modeled context](../science/hyde-cropland-source-account.md) | [Country totals](../../docs/report/regions/nordic/hyde-country-cropland/report.json) and [native grid check](../../docs/report/regions/nordic/hyde-country-cropland/grid-conservation/README.md). |
| [Swedish training scope](../science/sweden-training-scope.md) and [age/distance sensitivity](../science/sweden-spatiotemporal-sensitivity.md) | [Frozen scope products](../../docs/report/regions/nordic/swedish-training-scope/report.json) and [support sensitivity](../../docs/report/regions/nordic/swedish-support-sensitivity/report.json). |
| [Bjäresjö archaeology context](../science/bjaresjo-context.md) | [Country source screen](../../docs/report/countries/sweden/bjaresjo-context-screen/report.json). |

We left earlier `docs/report/` narrative URLs as short citation pages where
readers or the website still use them. We did not create a second editable
scientific interpretation at those paths. We locked the new root reports and
their cited source identities with the
[research verifier](../verify.py), the [scientific verifier](../../docs/report/pollen-reconstruction/verify_report.py)
and the [presentation source lock](../../presentation/source-lock.json).

## Why migration remains selective

Our inventory found **224 files outside `docs/report/`** with text references
to `docs/report` or `report/`: 166 under `packages/`, 50 under `docs/`, four
under `configs/`, two under `makes/`, one in `mkdocs.yml` and one under
`.github/`. This is a broad text count, not a count of distinct path
dependencies. Still, `make reports` publishes into `docs/report`,
`configs/ci/reproducible-report-build.json` names that tracked root, and
MkDocs builds those files. A wholesale move would break named producers,
manifests, public links and tests.

We therefore move or regenerate one owned domain at a time and update its
producer, config, tests, manifests, website links and citation paths in the
same checked unit. We retain a compatibility citation only where an existing
reader needs it. The remaining `docs/report/` tree is an active governed
product surface, not a completed migration or a second canonical library.

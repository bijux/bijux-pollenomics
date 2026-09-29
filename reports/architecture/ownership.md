# Report ownership and migration map

The current detailed report tree is `docs/report/`: 1,819 files occupying
346,859,031 bytes at the 29 September 2026 inventory. It combines scientific
rows, source receipts, generated website products, test inputs, scripts and
human narratives. A reader should start at [the root research index](../README.md)
while the existing governed result locations remain live.

| Current area | Files | Approximate MiB | Main content and destination |
| --- | ---: | ---: | --- |
| `regions/` | 454 | 212.49 | Nordic generated maps, browser assets, source and score products; keep machine and website assets in governed publishing locations. |
| `source-relations/` | 121 | 43.57 | Source correspondence and custody; move reader narratives by source domain only after producer and receipt paths are mapped. |
| `atlas/` | 116 | 16.76 | Interactive/browser verification and assets; retain with website build until an owned publication boundary is defined. |
| `world/` | 172 | 12.51 | World products and assets; retain with current publisher. |
| `pollen-reconstruction/` | 123 | 10.51 | Scientific studies, scores and report verifier; migrate human narrative with its manifest and all inbound links. |
| `publication-replay/` | 53 | 6.80 | Paper and archive correspondence; reader narrative belongs in root `reports/science/`, source-bound tables need an explicit governed owner. |
| `method-certification/` | 461 | 4.40 | R oracle cases, reference bundles and certification narratives; keep exact test fixtures and source rights distinct from public explanation. |
| `countries/` | 106 | 3.52 | Country source/field results; report narratives belong under named country questions when producer ownership is mapped. |

These eight areas account for 1,606 files and most bytes. The remaining
top-level reports include validation, synthetic checks, propagation, animal
reviews and root generated audits. Extension counts across the whole tree are
439 JSON, 431 CSV, 404 JavaScript and 268 Markdown files; extension alone does
not say whether a file is public, private or generated. Classify each selected
file by producer, source rights and citation role before moving it.

## Current incoming dependencies

An exact text search for `docs/report` or `report/` finds 224 referencing files
outside that tree: 166 under `packages/`, 50 under `docs/`, four under
`configs/`, two under `makes/`, and one each under `mkdocs.yml` and `.github/`.
This is a broad text count, not a count of distinct path semantics. In
particular, `make reports` calls `publish-reports` with `docs/report` as the
output root, `configs/ci/reproducible-report-build.json` declares that tracked
root, and MkDocs builds report files as non-navigation pages. The scientific
[report verifier](../../docs/report/pollen-reconstruction/verify_report.py)
checks retained file identities. Existing links from public pages, root
reports and the [presentation source lock](../../presentation/source-lock.json)
also depend on exact scientific report paths.

## Ownership target

| Kind of material | Long-term owner |
| --- | --- |
| Human scientific argument, source/cohort and method interpretation | Root `reports/`, grouped by enduring research question. |
| Reproducible numeric tables, manifests and private-use receipts | The owning producer's governed result destination, linked from the root narrative. |
| Curated rights-safe explanation for broad readers | `docs/public/`, linked to the exact report and result. |
| Presentation slide and final PDF | `presentation/`, with a checked source lock. |
| Local run logs and scratch computation | Root `artifacts/`. |

The first migrated narrative is [publication correspondence](../science/publication-correspondence.md).
Its previous website path is a short citation page. The scope record and
result ledger name the root narrative; the numeric CSV and source-specific
tables retain their governed producer paths. Both citation page and root
narrative are pinned by the scientific manifest. Future domains need the same
producer, manifest, link and website review, without two editable narratives.

The [Swedish and Nordic pollen study](../science/nordic-pollen-study.md) is the
second migrated narrative. Its former `docs/report/pollen-reconstruction/README.md`
website path is a citation page; the result table, scientific scope, manifest,
scripts and numeric products still have their governed owner. Both narrative
locations and the three presentation citations were checked together.

The [Denmark/Finland/Norway author-target pollen report](../science/denmark-finland-norway-author-pollen.md)
is root-owned on the same terms. Its score, coverage, input manifest, sealed
outcomes and predictions remain with the scientific producer. The prior
website path is a citation page, and the master result ledger names the root
narrative.

The [Swedish author-target country holdout](../science/sweden-author-pollen.md)
completes the four-country reader set. Its website citation page and master
ledger point to the root narrative, while the 51 scored and three refused
bins remain in the producer-owned numeric outputs.

The [Nordic observed-pollen selection](../science/nordic-observed-pollen-selection.md)
and [matched transfer](../science/nordic-observed-pollen-transfer.md) accounts
are separately root-owned. The search's trial ledger and the transfer's
frozen predictions and paired scores remain with their respective producers;
the old website pages preserve citations to both methods.

The [English constrained LOVE study](../science/english-lra-pollen-prediction.md)
is now root-owned. Its 15-site source and method account links the governed
fold, frozen-prediction, score and paired-comparison outputs; the old website
path stays as a citation page, while numeric and producer files remain put.

The [four-country HYDE cropland account](../science/hyde-cropland-source-account.md)
is root-owned. Its 84 source totals and native-grid reconciliations stay in
the producer tree; the old website path remains a citation page. The
scientific result and paper correspondence ledgers now name the root account.

The [Swedish training-scope comparison](../science/sweden-training-scope.md)
uses the same boundary: interpretation and limits live in the root report;
the six fold inputs, frozen predictions, coverage, scores and machine report
stay in the governed producer tree. Its former website path is a citation
page, and the master result ledger cites the root narrative.

We placed the [Swedish age and distance sensitivity](../science/sweden-spatiotemporal-sensitivity.md)
in the same research library. Its root report owns the question, matched
interpretation and limits; the governed `swedish-support-sensitivity/` result
path owns the frozen predictions, coverage, scores and machine report. The
website keeps a short citation page, and the result ledger names the root
report.

We placed the [Bjäresjö context decision](../science/bjaresjo-context.md)
in the root research library. Its governed country result retains the
source-bound nearby SEAD rows, 25-window overlap check and machine receipt;
the root report explains the physical-core and ecological join refusals.

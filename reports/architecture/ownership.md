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
most linked governed products retain the numeric and producer ownership. The Bjäresjösjön context screen is the first numerical slice now owned beside its root report.

| Research question now owned in `reports/` | Governed result or source boundary |
| --- | --- |
| [Publication and archive correspondence](../science/publication-correspondence.md) | [Paper correspondence ledger](../../docs/report/pollen-reconstruction/paper-correspondence.csv) and [PFT crosswalk](../science/publication-correspondence/pft-crosswalk/README.md). |
| [Nordic pollen synthesis](../science/nordic-pollen-study.md), [country results](../science/denmark-finland-norway-author-pollen.md) and [Swedish holdout](../science/sweden-author-pollen.md) | [Country score products](../../docs/report/regions/nordic/author-target-pollen/report.json) and [Swedish score products](../../docs/report/regions/nordic/swedish-author-target-pollen/report.json). |
| [Nordic training selection](../science/nordic-observed-pollen-selection.md) and [matched transfer](../science/nordic-observed-pollen-transfer.md) | [Search trial ledger](../../docs/report/regions/nordic/pollen-development/report.json) and [transfer freeze](../../docs/report/regions/nordic/selected-pollen-transfer/freeze.json). |
| [English LOVE and forward pollen](../science/english-lra-pollen-prediction.md) | [Fold/score products](../../docs/report/pollen-reconstruction/author-lra-constrained/report.json) and [basin-radius sensitivity](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/README.md). |
| [HYDE modeled context](../science/hyde-cropland-source-account.md) | [Country totals](../../docs/report/regions/nordic/hyde-country-cropland/report.json) and [native grid check](../../docs/report/regions/nordic/hyde-country-cropland/grid-conservation/README.md). |
| [Published reindeer appendix correspondence](../science/reindeer-appendix-correspondence.md) | [DNA scope result](../../docs/report/source-relations/dna-scope/report.json) and a retained website citation page; original source bytes stay in their governed source library. |
| [Swedish training scope](../science/sweden-training-scope.md) and [age/distance sensitivity](../science/sweden-spatiotemporal-sensitivity.md) | [Frozen scope products](../../docs/report/regions/nordic/swedish-training-scope/report.json) and [support sensitivity](../../docs/report/regions/nordic/swedish-support-sensitivity/report.json). |
| [Bjäresjö archaeology context](../science/bjaresjo-context.md) | [Country source screen](../science/bjaresjo-context/report.json). |

We left earlier `docs/report/` narrative URLs as short citation pages where
readers or the website still use them. We did not create a second editable
scientific interpretation at those paths. We locked the new root reports and
their cited source identities with the
[research verifier](../verify.py), the [scientific verifier](../../docs/report/pollen-reconstruction/verify_report.py)
and the [presentation source lock](../../presentation/source-lock.json).

For the Bjäresjösjön context screen, we moved the three byte-identical numeric
products beside [our lake decision](../science/bjaresjo-context.md). Its producer
accepts an explicit output directory; we changed the replay test, scientific
scope and manifest, claim index and source locks to use the root result path.
The old `docs/report/` page remains a citation to that one owner. We regenerated
the report portal inventory so it lists that citation without pointing to the
removed numeric files. This refresh also records report surfaces added since
the portal's earlier snapshot; those inventory changes are not new scientific
results.

We next moved the publication PFT/LCT crosswalk as one owned domain. Its
source-bound CSV and JSON products and paper/source notes now live beside the
[publication correspondence report](../science/publication-correspondence.md).
We kept its earlier website page as a citation, retargeted the exact scientific
reader and replay tests, and regenerated the portal inventory. The numeric and
source notes moved byte for byte. The paper/archive `ISTS` classification and
unreplayed standard-error covariance remain unresolved.

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

## What we learned from the clean report build

We ran the governed [`verify-rebuild` target](../../makes/pollenomics-verification.mk)
against clean commit `4e429452b` on 30 September 2026. Its two isolated
`publish-reports` runs completed and produced identical files. The comparison
with the tracked `docs/report/` tree failed, so we did not certify a clean
build/no-diff result.

| Comparison | Observed result |
| --- | ---: |
| Files emitted by each isolated `publish-reports` run | 709 |
| Files in tracked `docs/report/` | 1,860 |
| Tracked files absent from that producer's output | 1,151 |
| Shared paths with different content | 19 |
| Differences between the two isolated runs | 0 |

The absent files cluster in method certification (461), regional research
(142), pollen reconstruction (132), source relations (121) and atlas evidence
(116), with smaller groups elsewhere. We keep these governed outputs and
their distinct producers; copying them into an isolated build would not prove
that `publish-reports` generated them. The 19 shared-path differences include
portal inventories computed over different trees and animal review pages
with different source or enrichment states. We reviewed the animal differences
against the current source rows: the tracked exclusion report still listed two
camel samples after their mapping posture changed to ambiguous. We regenerated
that report from the source-backed producer, bringing its excluded count from
1,139 to 1,137, equal to the output-honesty blocked count. We also refreshed
the readiness country-locality counts and made the publisher use the canonical
honesty renderer, which retains source-native taxon mismatches. These
corrections resolve specific stale tracked pages; they do not establish
whole-tree reproducibility or authorize replacing separately governed files.

We inspected the publication path as well: `make reports` calls
`publish-reports` on tracked `docs/report/`, and its staging helper swaps the
new tree into place. With the current producer scope, that operation would
remove the 1,151 files it does not generate. We therefore did not run that
target on the tracked report root. We added a preflight to the full report
publisher: it refuses to replace a tree containing the scientific manifest,
method-certification reference or Neotoma source-relation marker. The tracked
root has those markers, so the command now fails before staging or deleting
its separately governed outputs. Isolated complete publisher trees still use
the atomic replacement path. The ownership repair must make publication
preserve each separately governed report domain before the tracked target can
successfully refresh.

We decided to define producer ownership before changing the
[`rebuild policy`](../../configs/ci/reproducible-report-build.json) or
regenerating tracked pages. The next clean-build proof must bind each
producer-owned output to its actual inputs, regenerate the dependent portal
over the complete governed tree, and compare the resulting tracked files.
Until then, the two-run repeatability result is valid, but the tracked-tree
no-diff gate remains failed. The full local diagnostic is retained under
`artifacts/execution-control/reproducible-report-build.nVLYdW/evidence/`;
the decision and counts above remain in this report if local artifacts are
purged.

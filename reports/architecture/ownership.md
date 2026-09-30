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
| [English analytical LOVE refusal](../science/english-analytical-love/README.md) and [constrained forward pollen](../science/english-lra-pollen-prediction.md) | Root [analytical fold/cover ledgers](../science/english-analytical-love/README.md), [constrained fold/score products](../../docs/report/pollen-reconstruction/author-lra-constrained/report.json) and [basin-radius sensitivity](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/README.md). |
| [HYDE modeled context](../science/hyde-cropland-source-account.md) | [Country totals](../../docs/report/regions/nordic/hyde-country-cropland/report.json) and [native grid check](../../docs/report/regions/nordic/hyde-country-cropland/grid-conservation/README.md). |
| [Published reindeer appendix correspondence](../science/reindeer-appendix-correspondence.md) | [DNA scope result](../../docs/report/source-relations/dna-scope/report.json) and a retained website citation page; original source bytes stay in their governed source library. |
| [Swedish training scope](../science/sweden-training-scope.md) and [age/distance sensitivity](../science/sweden-spatiotemporal-sensitivity.md) | [Frozen scope products](../../docs/report/regions/nordic/swedish-training-scope/report.json) and [support sensitivity](../../docs/report/regions/nordic/swedish-support-sensitivity/report.json). |
| [Further Swedish lake transfer](../science/sweden-lake-transfer.md) | [Frozen predictions and 189 scores](../../docs/report/regions/nordic/swedish-lake-transfer/README.md) remain with their governed producer. |
| [Vegetation-reference decision](../science/vegetation-reference.md) | [Zero-pair screen](../../docs/report/validation/empd2-nfi-pairing/report.json), [Färskesjön plot](../../docs/report/vegetation-reference/farskesjon/report.json), [historical-map support](../../docs/report/vegetation-reference/smaland-historical-maps/coverage.json) and [published figure](../../docs/report/vegetation-reference/southern-sweden-figure/report.json) keep their source-bound producers. |
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
new tree into place. Its former complete-tree swap would have removed the
1,151 files it does not generate. We changed the mixed-tree path to assemble
the publisher output first, retain files absent from that output, recompute
the sustainability count and portal over the complete staged tree, then swap
it atomically. A symlink or file-directory collision refuses the swap. The
ordinary isolated complete-tree path still drops stale publisher directories.

We ran `make reports` on the tracked root after a small mixed-tree test. It
finished with **1,860 files**, including the scientific manifest,
method-certification reference and Neotoma source relation, with no deleted
paths. Thirty-two tracked changes were generated-date updates only; we kept
their prior dates rather than commit a date-only refresh. The substantive
remaining change corrects the sustainability review's report-file count from
1,803 to 1,860. This proves preservation for the current tree. It does not
prove that the 1,151 retained files can be regenerated from their separate
producers; the clean full-tree no-diff gate remains open.

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

We checked one separately governed numerical owner as a bounded rebuild
probe. The [analytical LOVE ring sensitivity producer](../science/analytical-love-ring-sensitivity/replay.py)
ran from current source into an absent `artifacts/jobs/report-owner-proof/`
destination. Its `report.json` and `ring-cover.csv` matched the two tracked
files byte for byte, with SHA-256
`bd43a66757c4124a4df714a480675368de62d16505c9d43982a609039aba5848`
and `714fdd94f40ca8c4b90f23b290190754bc5f2d82ede22395b871f2384910442e`.
We moved that producer and its two byte-identical results into the
[root science report](../science/analytical-love-ring-sensitivity/README.md).
The earlier `docs/report/` page is now a citation to this single owner. This
reduces the mixed-tree ownership surface, but the local replay does not
rebuild the other separately governed files or close the full-tree gate.

We also moved the English author-prepared analytical LOVE refusal as one
scientific result: its report, 15-fold refusal ledger and 54-ring cover
diagnostic are now owned beside our [source decision](../science/english-analytical-love/README.md).
The original `docs/report/` page remains a citation. We updated the scientific
scope, result table and byte manifest to name the root files; their numerical
bytes did not change. The existing source producer and reader still govern
reproduction, while the independent complete-tree rebuild remains open.

Our [artifact custody decision](artifact-custody.md) records a separate
bounded checkout retirement and its recoverable source identity. It does not
alter the report producer ownership or the failed independent rebuild gate.

We made the two-grid author R/native execution a readable
[root scientific decision](../science/publication-correspondence/author-example-reexecution.md).
The existing machine receipt retains its governed path and exact execution
identity; its earlier website page now directs readers to the single research
account. We did not rerun the numerical calculation solely for this report
move or treat the two released grids as the historical 1,128-record study.
We used the same boundary for the adjacent
[author method and input profile](../science/publication-correspondence/author-method-profile.md):
the human decision and source limitations are rooted here, while its
crosswalk, input ledger, machine report and hashed comparison receipts remain
at their governed producer path. Its source-backed replay also exposed an
older author-custody hash in the machine report; we refreshed that identity
without changing the crosswalk or example input rows.

We also rooted the [exact published-window interpretation](../science/publication-correspondence/published-window-provenance.md)
and left the 124-row ledger, generated calculation detail, machine summary
and producer manifest at their governed path. The old page now directs a
reader to the research decision. This keeps the archive discrepancy
discoverable without claiming the two source versions share historical
input rows.

We replayed the adjacent 62-row mean/standard-error envelope producer from
its exact governed correspondence inputs. Its JSON summary and Markdown
report matched their retained files byte for byte; the parsed CSV rows also
matched, but the producer used CRLF where the governed CSV used LF. We made
the producer write LF and checked all three outputs byte for byte against
the retained [uncertainty result](../../docs/report/publication-replay/landclim-published-window-uncertainty/README.md).
The historical manifest still describes the earlier producer source; this
current replay proves the present output bytes for this one owner. It does
not close the other separately governed outputs or the full-tree no-diff gate.

The independent report-build diagnostic also lists the Småland historical-map
coverage result among files that `publish-reports` never emits. We ran its
[source-bound producer](../../docs/report/vegetation-reference/smaland-historical-maps/coverage.py)
against the three exact private article and appendix bytes into an absent
`artifacts/jobs/report-owner-proof/` destination. The produced JSON matched
the [tracked coverage result](../../docs/report/vegetation-reference/smaland-historical-maps/coverage.json)
byte for byte, SHA-256
`f13f1e5ece6e4060b98036d7bdca42b4ff2c47ca8dc118931d2b43c074519012`.
This establishes a current owner for that one numerical source-support file.
It does not make the article's unpublished vegetation fractions available or
turn the 1,151-file clean-build gap into a pass.

We checked the other two vegetation-reference owners from their pinned private
sources as well. The [Färskesjön plot producer](../../docs/report/vegetation-reference/farskesjon/plot_support.py)
reproduced its [refusal and measured-plot report](../../docs/report/vegetation-reference/farskesjon/report.json)
byte for byte, SHA-256
`c2a21045859c27672a310fc1faf6b6651ee8320320c56764ccecc5639540b855`.
The [published-figure producer](../../docs/report/vegetation-reference/southern-sweden-figure/compare.py)
reproduced both the [nine-label CSV](../../docs/report/vegetation-reference/southern-sweden-figure/printed-labels.csv)
and [machine comparison](../../docs/report/vegetation-reference/southern-sweden-figure/report.json)
byte for byte, SHA-256
`e7e6f04e4711690421ca4c84af9e1237cbdb3b95554d63a6d81e2a61ff2a3f54`
and `7205071dc7bd4b7bdf99c77788583bfbb1ab8699546c9f5acd3e6566da4e7e57`.
These four files now have checked current producers. Their distinct evidence
limits and the zero-pair decision remain as stated in our
[vegetation-reference account](../science/vegetation-reference.md).

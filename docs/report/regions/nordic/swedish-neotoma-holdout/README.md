# Storasjö observed-pollen holdout

The [locked protocol](protocol.json) selected Neotoma site 28874, collection
unit 39243, using source metadata before the target pollen counts were read.
Storasjö has two EPD pollen datasets, 54004 and 54005, from the same bog core.
Each has 77 samples at the same 77 depths and with the same default calibrated
ages. The [independent parallel-dataset review](parallel-dataset-review.json)
finds identical source-name pollen NISP vectors at **77/77** matching depths:
35,767 native pollen counts and 60 distinct source names in each dataset.
Dataset 54004 supplies the one physical-core target; counting both would double
the response without adding a separate core. The parallel dataset remains
identified in the source audit.

The [input manifest](input-manifest.json) binds the exact Neotoma relational
snapshot, author taxonomy lookup and previously retained 81-site DK/FI/NO
training profiles. The 77 target samples have selected source-default calibrated
ages from 65 to 10,874 BP. Their 500 BP bins yield **22 target site bins**.
The 31-target mapping retains **35,505 assigned NISP**, 253 author-excluded
NISP and 9 unmapped NISP out of 35,767 native pollen NISP. The [prepared
metadata](inputs/metadata-SE.json.gz) contains sample IDs, age-bin membership
and site location, while [sealed outcomes](sealed-outcomes/outcomes-SE.json.gz)
retain target counts separately. This is a direct observed-pollen
subcomposition; no LRA reconstruction or measured vegetation is involved.

The [prediction freeze](prediction-freeze.json) and [committed prediction
file](predictions/predictions-SE.json.gz) were committed before scoring. All
three fixed methods predicted all 22 bins; target counts were absent from the
predictor inputs. Scoring used that committed prediction file. The [score
table](scores.csv), [coverage](coverage.csv), [site summary](site-scores.csv)
and [taxon diagnostics](taxon-diagnostics.csv) preserve the matched denominator.
The [producer used at the freeze](reference/prediction-producer.py.txt) is
retained at its exact commit `a5e42998d` source hash. Later edits to the live
command do not change that historical prediction identity. The
[parallel-dataset review producer](reference/parallel-dataset-review-producer.py.txt)
is likewise retained at its exact commit `955730853` source hash.

| Fixed method | Scored bins | Site mean absolute fraction error | Site Hellinger distance |
| --- | ---: | ---: | ---: |
| nearest site | 22 | 0.015389 | 0.243786 |
| inverse distance squared | 22 | 0.016881 | 0.285723 |
| training mean | 22 | 0.019351 | 0.327260 |

Nearest site has the lowest error for this **one target core** on the fixed
31-target axis. Storasjö is a bog, so its pollen source support need not match
the lake sites in the earlier Swedish study. Prior Nordic outcomes informed the
fixed methods and source records were available before this protocol; this is
an additional development transfer result, not independent confirmation of
model superiority or country-wide performance. The target has no admitted
independent landscape vegetation label.

## Reproduce

From the repository root, with the retained external author-reference capsule:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_neotoma_holdout prepare \
  --repository . --author-source-root /path/to/landclim/author-reference \
  --output artifacts/jobs/swedish-neotoma-holdout/replay-prepared
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_neotoma_holdout predict \
  --prepared artifacts/jobs/swedish-neotoma-holdout/replay-prepared \
  --output artifacts/jobs/swedish-neotoma-holdout/replay-predictions
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_neotoma_holdout score \
  --prepared artifacts/jobs/swedish-neotoma-holdout/replay-prepared \
  --predictions docs/report/regions/nordic/swedish-neotoma-holdout/predictions \
  --output artifacts/jobs/swedish-neotoma-holdout/replay-scored
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_neotoma_duplicate_review \
  --repository . --output artifacts/jobs/swedish-neotoma-holdout/replay-duplicates
```

The [report manifest](manifest.json) lists all retained file digests. Compare
each replay product byte-for-byte with its retained counterpart; the scorer
must use the committed frozen prediction file. The private author lookup is
authenticated by SHA-256 and is not copied into this report.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained Storasjö development result counts one physical core once after matching both parallel datasets at all77depths and freezes three observed-pollen predictors before scoring.

**Unsupported claim.** Two duplicate datasets are not two independent cores; this exposed-design bog result does not establish confirmatory method superiority, country-wide performance, LRA or vegetation accuracy.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer. A separate replay at commit 65d4752111915e1157315004d59603469af2d644 completed six maintained prepare, predict and score commands and two independent observers, all with exit 0. Common, inner and outer run results were 0. All ten native products per study family matched the retained bytes exactly. Only four preparation files per family receive retained source admission. Nine protocol, historical freeze, reference-text and verification files remain unresolved under their original study owners; no historical production or freeze certificate is inferred. Both protocols used the exact training-SE input. The original owner recipes incorrectly declared training-DK; those recipes and this correction remain explicit in the capsule and witness. The authored capsule preserves the original public source and controls and all 66,481 input identities. Runtime, private taxonomy lookup, relational inputs and 4,356 bytecode payloads remain omitted. The original generic outer receipt mentions EMPD2; its text is preserved, and the actual Swedish plan and eight command receipts establish the execution scope. These previously exposed direct-pollen development results do not establish untouched confirmation, ecological or field accuracy, vegetation truth, acquisition or reuse rights, human acceptance or LRA admission. Authoring the capsule is not a new native retention execution.

**Remaining input or review.** A genuinely independent target and qualified source/physical/ecological evidence are required for stronger claims; the historical predictor/review bytes remain explicit custody.

**Cause category.** Single-core development transfer with parallel-dataset deduplication.

**Consequence.** An additional repository dataset cannot double the response mass or provide replication when its source count vectors are identical.

**Precise next acceptance route.** Replay the parallel-dataset review and maintained study consumers, retain dataset54004as the single target and score committed predictions before evaluating independent confirmation separately.

**Negative or refused result.** Dataset54005remains identified but excluded as duplicate support; prior Nordic outcomes informed the design and the core has no admitted vegetation label.

**Matched denominator.** One core with two77sample datasets matching77/77depths;one target contributes35,767native NISP=35,505assigned+253excluded+9unmapped,22bins/66method rows/31taxa.

Qualified authored reader SHA-256: `9986695a9a4d784d36a043528ef076414d508447553b3f4d31b485764a04d3ed`.

- [Retained qualification evidence: docs/report/regions/nordic/swedish-neotoma-holdout/report.json](report.json) (SHA-256 `4e208e1016cbc14544ebb45be11f5feffa2c5497b8c50c326d37643419638aab`).

- [Retained qualification evidence: reports/science/source-lineage/swedish-direct-pollen-preparation.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/swedish-direct-pollen-preparation.json) (SHA-256 `a64dfad19cfc41eae4d4e6c810b2078076a2b3d3c2088fbe11dff6a024d095aa`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

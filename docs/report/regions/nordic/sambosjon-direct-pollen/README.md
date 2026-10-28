# Sämbosjön direct observed-pollen evaluation

The [protocol](protocol.json) fixed a new Swedish physical-site target, the
existing 16 exact-label closed pollen response, 500-cal-BP bins, 84 prior
training sites and three fixed predictors. The [prepared input receipt](inputs/input-manifest.json),
[deterministic gzip training profile](inputs/training.json.gz),
[prediction freeze](frozen/freeze.json), [predictions](frozen/predictions.json),
[scores](scores.csv), [coverage](coverage.csv) and [machine report](report.json)
preserve the separate preparation, prediction and scoring reads. The shared
source screen parsed the raw observation partition, including Sämbosjön taxon
rows, for validation during preparation; it discarded those rows before
writing prepared training or prediction inputs. Target composition was
interpreted and aggregated for scoring only after a prediction freeze. The
retained freeze SHA-256 is
`8337d7b6316295b2506dd2efff73d2c3e08a2ecd35d3690a5b2047280c3337ec`.
Before opening target outcomes, scoring verifies the prepared Neotoma manifest
and all 13 recorded relational source-part hashes, including the sample,
age-claim and observation parts. A source-part mutation is refused before the
target outcome reader runs.

| Fixed method | Scored bins | Equal-bin MAE | Equal-bin Hellinger |
| --- | ---: | ---: | ---: |
| Inverse distance squared, primary | 22 | 0.022991 | 0.184176 |
| Nearest site | 22 | 0.026202 | 0.233673 |
| Training mean | 22 | 0.037466 | 0.283108 |

All **22 candidate bins** had two or more positive-count training physical
sites, were predicted, and were scored. There were **zero refused or failed
bins**. The 111 distinct source samples contribute 393,822 native NISP pollen
counts: 224,291 on the declared 16-label axis and 169,531 outside it. The
closed response is **56.95%** of native pollen mass. Missing exact labels are
zero cells only within this observed source subcomposition; outside labels are
not interpreted as absent vegetation.

The target is Neotoma/EPD site `3398`, its single `SAMBOTOT` core `4262`, and
its single pollen dataset `4403` ([dataset DOI](https://doi.org/10.21233/53ys-nt12)).
The source records a core collection date of `1977-01-01`; that recorded date
is not evidence for a verified sampling day. Its 111 unique depths are
2.5–552.5 cm. One source-default MADCAP/IntCal09 calibrated chronology
(`neotoma:chronology:4262:30017`) assigns one comparable sample age to each
depth, 964–11,285 cal BP, with younger and older bounds. A separate
radiocarbon chronology supplies 111 context-only claims. The 15 retained
chronology controls were not used to infer a new age model; age uncertainty was
not propagated through the fixed 500-year bins. The source site is a WGS84
point at 12.41426° E, 57.16313° N. Spatial predictors use site-center
distance. The nearby LandClim `SAM` point is 3.316459 km away and the
[source review](../../../source-relations/neotoma/landclim-site-identity/site-comparison.csv)
refuses a same-core identity. It is not a target alias or another observation.

The dataset names Gunnar Digerfeldt as investigator. The retained Neotoma
provider publication response identifies one primary source: **Digerfeldt,
G. (1982), *The Holocene development of Lake Sämbosjön. 1. The regional
vegetation history*, Lundqua report 23, Lund University, pp. 1–24**. The
response is retained at
`bijux-pollenomics-data/neotoma/publication-links/2026-09-29/responses/dataset-4403-publications.json`.
[Neotoma's 2025 Data Use and Embargo Policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
permits available data under CC BY 4.0 with Neotoma, the European Pollen
Database, original-investigator, primary-publication and dataset-DOI
attribution. The Neotoma/EPD source transport used here is
`data/neotoma/raw/neotoma_pollen_dataset_downloads/part-003.json` at row 14,
SHA-256 `d7b9f9e0616b71ab74be03e15ae3f81fa856582463d51e0c1559d763bb3552af`.
The relational manifest SHA-256 is
`6f6777a40b67bd0704eb1a982f19e6d451cad0d6e4a41dfebf5e3f28be33105b`.

Aggregate native and 16-label count mass and positive-bin support were
inspected before the first prediction freeze. An initial scoring process
completed under freeze
`f30cec9b3a9aec925b4b92beadc8eb33cc5fca69336aabb98362dcfdcb7e671a`,
but its metrics and compositions were not opened. Review corrected the nearby
`SAM` identity annotation, then froze the same prediction bytes under
`6f0682edf83c8b8575a5a0c45e5f9c4294de61261a15055a0ddc42cb04ab636a`.
Aggregate scores were inspected after that freeze. The final annotation now
states the preparation read boundary explicitly; its predictions remain
byte-identical (prediction file SHA-256
`97a2b45ce51e2e42c851e64ba5b91ea721e887fac6c1e92e16f3938b428f4e65`).
After aggregate-score exposure, the same 5,145,874 training JSON bytes were
stored as deterministic gzip with `mtime=0` (121,413 bytes). The input and
freeze hashes changed from the prior uncompressed freeze
`c70fd1b6c87f4ab0ad86855f6e092980cf159319978b08b2f42a0f956f7fd0bc`;
decompression restores the original training bytes exactly, and the fixed
prediction, score and coverage files remain byte-identical.
This is descriptive development evidence for one newly
evaluated physical site. It has prior aggregate-count and later aggregate-score
exposure, so it is not an independent confirmation or untouched lockbox. One
site cannot support between-site uncertainty or a broad Swedish claim. It is
neither LRA nor measured-vegetation validation.

The separate [source age-bound screen](age-bounds/README.md) finds that 58 of
111 selected sample intervals span a nominal 500-cal-BP boundary. It leaves
this point-age score and its prediction freeze unchanged. The
[contained-age sensitivity](interval-support/README.md) keeps 53 samples and
21 bins on those identical predictions. Primary equal-bin MAE is 0.023054
versus 0.022881 for original counts on the same bins. The unsupported first
bin is explicitly refused; this marginal-support comparison is no age
posterior or independent confirmation.

To replay into absent directories under `artifacts/`, run the three stages in
order and pass the actual freeze digest to scoring:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.sambosjon_direct_pollen prepare \
  --repository . --output artifacts/jobs/sambosjon-replay/prepared
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.sambosjon_direct_pollen predict \
  --repository . --prepared artifacts/jobs/sambosjon-replay/prepared \
  --output artifacts/jobs/sambosjon-replay/frozen
freeze_sha=$(shasum -a 256 artifacts/jobs/sambosjon-replay/frozen/freeze.json | cut -d ' ' -f 1)
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.sambosjon_direct_pollen score \
  --repository . --prepared artifacts/jobs/sambosjon-replay/prepared \
  --frozen artifacts/jobs/sambosjon-replay/frozen \
  --freeze-sha256 "$freeze_sha" \
  --output artifacts/jobs/sambosjon-replay/scored
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained one-core16-label development study freezes66predictions before separate scoring, preserves all22positive bins and documents preparation/aggregate-count and later aggregate-score exposure.

**Unsupported claim.** It is not untouched confirmation, between-site Swedish skill, LRA, measured vegetation validation or evidence that the nearby LandClimSAMpoint is the same core.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer.

**Remaining input or review.** Chronology bounds and source identity need their declared scope; correlated age uncertainty and independent ecological truth are not supplied.

**Cause category.** Single-core exposed development result with explicit historical freeze lineage.

**Consequence.** Corrected annotations and deterministic gzip preserve prediction bytes but cannot erase the prior exposure history or create another observation.

**Precise next acceptance route.** Replay the separate source-bound preparation/prediction/scoring stages, retain historical prediction identity and compare any age sensitivity on matched bins with no refit.

**Negative or refused result.** The nearbySAMjoin is refused and outside-axis pollen is not absent vegetation; zero failed bins does not mean independent scientific acceptance.

**Matched denominator.** One site3398/core4262/dataset4403;111samples,22bins,three methods/66predictions;393,822native NISP=224,291closed16-label+169,531outside; primaryMAE0.022991.

- [Retained qualification evidence: docs/report/regions/nordic/sambosjon-direct-pollen/report.json](report.json) (SHA-256 `410db1760454c74809fb3c60811db159c90e5e35c8bbdd1fb770c8435ff7f4c1`).

- [Canonical scientific account: reports/science/sambosjon-direct-pollen.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sambosjon-direct-pollen.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

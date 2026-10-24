# Tagged Petr Kuneš LRA comparison

The [bounded comparison](summary.csv) executes two pinned R sources against
the same LandClim II author example counts and parameters: the author's 30
October 2016 `LRA-REVEALS-release.R` and Petr Kuneš's [LRA v0.1.2 source](https://github.com/petrkunes/LRA/tree/d29075692ed730e3934bc461eb9081c404aef59b)
at commit `d29075692ed730e3934bc461eb9081c404aef59b`. The tagged source
tarball is retained outside the product repository with SHA-256
`3292d4726e3cb0204d6f8326c5ce9208aecf3e064c180846adab3be7fa03a353`.
The selected v0.1.2 commit is a version comparison target. It has not been authenticated as the executable version used in the 2022 analysis; that publication-specific version remains uncertain.
Its `REVEALS.R`, `KPf.R` and `DESCRIPTION` SHA-256 values are respectively
`50353523cd1e1cb85b3fc572d55320771bdc4bf6b03b7b98ba7fa6c3b321d72d`,
`bebe75561016cfe12138d9bf49326da760d475afa762e3c15ad7150d51938247`,
and `7828cfa0220637cabb029b93d447da41cbf6215327088179569e7b157d38ee90`.
The author source SHA-256 is
`7675b6e615cddba328bad506692b3a6a31e00d9273cef5ad4641a1737fddfd87`.
The pinned zipfR 0.6-70 source tarball is retained privately with SHA-256
`0c318569cf5dd13ab5ea22f7cf797a2daeda09d8332d89ba54fd2d7c643ecf96`.
The tagged package's `DESCRIPTION` says GPL-2 while the GitHub root shows an
MIT license; its source is not copied into this product repository.

The [taxon comparison](taxa.csv) has all 31 cover and 31 standard-error
values for each of four cases at the author **225 BP midpoint** window:
one 150 m lake, a 150/10 m lake pair, all six sites with positive source
counts, and the full nine-site grid 512 input (six active, three absent at
this window). Both functions use the same author 31-taxon PPE/covariance and
GPM-neutral parameters, wind 3 m/s and region 100,000 m. The same R seed is
set before each call. All **124 matched cover pairs** and **124 matched SE
pairs** have zero difference at the CSV's retained precision; source site
counts also agree. The tagged `KPf` function body is identical to the 2016
author body's parsed R expression; the `REVEALS` bodies differ. This is a
version comparison within a shared code lineage, not an independent model
derivation or a corrected uncertainty certification.

The R replay also retains the full grid's [1,000 original-site bootstrap
indices](bootstrap-full-grid.csv) (SHA-256
`1515f0b680e066bfc1810b0ce691e70dea56856076bf9a149c70d00f4efb9a45`)
and verifies that both R versions sampled identical indices. The
[direct native comparison](native-report.json) feeds those exact zero-based
indices and the same full nine-site, 31-taxon, 100–350 BP input into the
historical native profile. Against the tagged R output, all 31 cover values
pass the predeclared `1e-11` absolute/`1e-10` relative tolerance (maximum
residual `1.21958e-13`); all 31 SE values pass `5e-8` absolute/`1e-9`
relative tolerance (maximum residual `2.86438e-14`). Six sites have
source support in that window. The native report SHA-256 is
`273c1b129551e6392ca926988bf594a66c7de9f435b299832e24b771731d8995`.

The isolated one-window calculation does not replay the full 25-window R
random-number stream from the [two-grid author/native result](../../publication-replay/landclim-example-reexecution/README.md).
That prior result's 225 BP values must not be compared to these outputs as if
their bootstrap draws had the same history. The current comparison also does
not test the LSM transport branch, chronological or basin uncertainty, source
missing-taxon semantics, or Nordic empirical reconstruction. The
[reviewed conditional draw profile](../author-site-uncertainty/README.md) is a
different method with a restricted positive-count subcomposition.

The maintained [replay script](replay.R) parses only the author's `KPf` and
`REVEALS` function definitions, avoiding the archived script's old
installation side effects. It loads the tagged functions from their pinned
source files and requires the literal DESCRIPTION versions zipfR `0.6-70`
and LRA `0.1.2`. Reproduce into an absent `artifacts/` directory using the
existing authenticated source store and shared R library. This command runs
only the four source-R comparisons; it does not rerun the Python model:

```sh
SOURCE_STORE=/path/to/existing/source-store
ZIPFR_LIBRARY="$PWD/artifacts/qualification/native-reference/library"
OUTPUT="$PWD/artifacts/science/petrkunes-r-reference"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 Rscript --vanilla \
  docs/report/method-certification/petrkunes-r-comparison/replay.R \
  "$SOURCE_STORE/landclim/author-reference" \
  "$SOURCE_STORE/lra/petrkunes-v0.1.2/LRA-d29075692ed730e3934bc461eb9081c404aef59b" \
  "$ZIPFR_LIBRARY" "$OUTPUT"
cmp docs/report/method-certification/petrkunes-r-comparison/summary.csv \
  "$OUTPUT/summary.csv"
cmp docs/report/method-certification/petrkunes-r-comparison/taxa.csv \
  "$OUTPUT/taxa.csv"
cmp docs/report/method-certification/petrkunes-r-comparison/bootstrap-full-grid.csv \
  "$OUTPUT/bootstrap-full-grid.csv"
```

The independent Python procedure is optional, separate numerical work. It is
not part of this source-R execution protocol and has not been launched for it.
The retained `native-report.json` describes its historical source epoch,
inputs and supplied draws; a new Python run must retain its own observed
source identity and cannot acquire the old execution identity through a
matching value. If that separate calculation is required, its entry point is:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 .venv/bin/python -B \
  docs/report/method-certification/petrkunes-r-comparison/native_comparison.py \
  --repository . --private-root "$SOURCE_STORE/landclim/author-reference" \
  --output "$PWD/artifacts/science/petrkunes-native-reference"
```

The governed summary SHA-256 is
`5f7957d2d318518e96959a286b74a9a183a9b23655aef3216d61dfd38137541a`;
the taxon comparison SHA-256 is
`b37211fda3a692d1b903501a14323ab14820950d434f8a2953b9ea25a269b915`.

## Source-R reference execution protocol

The retained three R CSVs do not currently have an admitted source-R execution
authority. The separately authenticated native comparison establishes a Python
calculation against those reference bytes; it does not establish the missing
R execution. A new calculation will address this narrow source-reference gap,
without relabelling historical execution custody or rerunning Python.

Before new outcomes, the calculation fixes the same four cases, their order,
31-taxon axis, 225 BP source column, original site inputs, shared PPE/covariance,
3 m/s wind, 100,000 m extent, neutral GPM and seed 750225. The two R functions
retain their different bodies and source-compatible uncertainty formulas.
The three absent full-grid sites remain absent; they do not become observed
zero-count sites. At each multisite case, both R versions must sample exactly
the same original-site indices. The full-grid index output remains 1,000 rows
by six sampled entries. Each entry is a zero-based position on the original
nine-site axis, drawn from the active positions `{0, 2, 3, 4, 7, 8}`; the
entries are not indices on a compact six-site axis. The active positions are
derived from the original site list and nine prepared inputs.

Use R 4.6.0 and the one shared installation of authenticated zipfR 0.6-70.
The literal installed DESCRIPTION version is `0.6-70`, not its normalized
`packageVersion` display. The maintained replay records `sessionInfo()`,
RNG kind and the actually loaded zipfR namespace before and after source calls
in one process. It refuses an existing output directory or a different
dependency/source version. All original author and tagged source files are
read in place. Neither source package is copied or installed for this replay.

Use the single source-R invocation above, without the optional Python
procedure. The already provisioned shared library is reused in place.

The existing reproduction criteria remain byte-for-byte equality of
`summary.csv`, `taxa.csv` and `bootstrap-full-grid.csv` against their retained
counterparts. A separate standard-library observer will inspect all 124 cover
and 124 SE pairs, exact labels/order, finite masks, site-count populations,
recorded differences and all 6,000 full-grid index entries. This is independent
inspection of saved outputs, not another R execution or independent physical
model. Any mismatch, warning, refusal or nonzero process exit remains evidence;
there is no retry, changed seed, tolerance relaxation or automatic replacement
of the original references. The retained Python comparison remains bound to
its original inputs and draws.

The prospective execution limit is 120 seconds, with 512 MiB peak RSS and
50 MiB additional storage including the shared dependency. These are bounds
to measure, not historical performance claims. The intended result is a
qualified current source-R reference calculation on four already exposed
cases. It cannot identify the 2022 executable, resolve source licensing,
validate the source uncertainty model or supply historical, Nordic, field,
human-review or hosted-release acceptance.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** The retained Petr/Kuneš author-R correspondence matches selected mean and SE outputs and a same-index bootstrap on shared prepared author data, keeping code/data lineage explicit.

**Unsupported claim.** Agreement on these shared inputs is not independent empirical derivation, full 25-window random-stream reproduction, scientific source admission or measured vegetation accuracy.

**Actual verification performed.** Reviewed the retained native report and mean/SE summary, case support and numerical tolerances and bound their public bytes. This qualification ran no author-R program, bootstrap or native Python model.

**Remaining input or review.** Original source geometry, chronology, measured-taxon interpretation and source-use rights remain scientific inputs; GPL-2 DESCRIPTION and MIT GitHub labels require a real rights decision rather than inference from numerical agreement. The selected tagged v0.1.2 source is not authenticated as the exact executable used in 2022; that historical version identity remains uncertain.

**Cause category.** Author-code arithmetic correspondence on shared prepared input lineage.

**Consequence.** The comparison qualifies a named computational route and selected population; it does not independently validate the historical observations or all author scenarios.

**Precise next acceptance route.** Replay the maintained selected-case owner with exact author inputs and indices, preserve its tolerance and scope, and resolve the named source/rights questions before any scientific or redistribution admission.

**Negative or refused result.** Unreproduced windows and unresolved source/use rights stay open. Shared code lineage and 124 zero retained CSV differences do not become independent evidence.

**Matched denominator.** Four selected site cases by 31 taxa at 225 BP give 124 mean and 124 SE pairs; one full grid has nine sites, six active and 1,000 shared indices. Native residual maxima are 1.21958e-13 for 31 means and 2.86438e-14 for 31 SEs.

- [Retained qualification evidence: docs/report/method-certification/petrkunes-r-comparison/native-report.json](native-report.json) (SHA-256 `273c1b129551e6392ca926988bf594a66c7de9f435b299832e24b771731d8995`).

- [Retained qualification evidence: docs/report/method-certification/petrkunes-r-comparison/summary.csv](summary.csv) (SHA-256 `5f7957d2d318518e96959a286b74a9a183a9b23655aef3216d61dfd38137541a`).

- [Retained qualification evidence: docs/report/method-certification/petrkunes-r-comparison/taxa.csv](taxa.csv) (SHA-256 `b37211fda3a692d1b903501a14323ab14820950d434f8a2953b9ea25a269b915`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

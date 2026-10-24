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

## Current source-R reference execution

At committed source `14a3cec7ac1b0a05f122411d4fde9bb5b397280e`, the
single R invocation above exited zero in 28.307267125 seconds. It reproduced
`summary.csv`, `taxa.csv` and `bootstrap-full-grid.csv` byte for byte; the
three retained numerical files were not replaced. Peak child RSS was
103,841,792 bytes on macOS, and additional outputs occupied 25,810 bytes.
There was no R stderr. These measurements satisfy the predeclared 120-second,
512 MiB and 50 MiB execution budget. The committed source and Git identity,
13 raw R inputs, three tagged source files and all 38 installed package
DESCRIPTION files (36 existing dependency packages, the DISQOVER 0.9.14
reference and zipfR) remained unchanged.

A separate saved-output observer verified all 124 cover and 124 SE pairs as
finite with exact zero differences, the 124 case/taxon labels and all 6,000
original-site bootstrap positions. Its first attempt stopped before numeric
comparison because it incorrectly equated raw source labels with prepared
labels. The existing authenticated 31-row crosswalk corrected that observer
assertion, adding one observer-only input to the 13 R inputs. The qualified
observer exited zero; neither R nor Python reconstruction was relaunched,
and no numerical criterion or output was changed. The failed observer
remains evidence of that initial label error.

This qualifies a **current three-CSV source-R replay**, not original R
execution custody. The linked `native-report.json` remains a separately
qualified historical Python calculation: no Python model ran in this replay.
The exact 2022 executable, source rights, uncertainty validity, field accuracy,
human review and release acceptance remain unresolved.

Before the new outcomes, the committed protocol fixed the same four cases,
their order, 31-taxon axis, 225 BP source column, original site inputs, shared PPE/covariance,
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
counterparts. The separate standard-library observer checked all 124 cover
and 124 SE pairs, exact labels/order, finite masks, site-count populations,
recorded differences and all 6,000 full-grid index entries. This is independent
inspection of saved outputs, not another R execution or independent physical
model. Any mismatch, warning, refusal or nonzero process exit remains evidence;
there is no retry, changed seed, tolerance relaxation or automatic replacement
of the original references. The retained Python comparison remains bound to
its original inputs and draws.

The same-process before/after runtime records report R 4.6.0 (2026-04-24),
`aarch64-apple-darwin23` on macOS Tahoe 26.6.2, the R.framework
`libRblas.0.dylib` and `libRlapack.dylib`, and LAPACK 3.12.1. The RNG kind
was Mersenne-Twister / Inversion / Rejection. Only zipfR was attached beyond
the base packages; compiler and parallel 4.6.0 were loaded namespaces. The
full before/after sessions remain in the bounded execution artifacts rather
than a duplicate runtime file. This is a current calculation on four already
exposed cases. It cannot identify the 2022 executable, resolve source licensing,
validate the source uncertainty model or supply historical, Nordic, field,
human-review or hosted-release acceptance.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** A current four-case source-R replay reproduces the three retained R CSVs byte for byte: 124 cover and 124 SE pairs agree exactly, with identical original-site bootstrap indices. The separately retained historical Python comparison remains distinct.

**Unsupported claim.** Agreement on these shared inputs is not independent empirical derivation, full 25-window random-stream reproduction, scientific source admission or measured vegetation accuracy.

**Actual verification performed.** At committed source 14a3cec7ac1b0a05f122411d4fde9bb5b397280e, the R-only replay exited zero in 28.307267125 seconds, peak child RSS 103,841,792 bytes and output 25,810 bytes, with no R stderr. All three CSVs reproduce exactly; a separate saved-output observer verified 248 finite pairs, 124 labels and 6,000 indices. Its first label assertion failed before numeric comparison and was corrected with the existing authenticated crosswalk; R was not relaunched. Source, raw inputs and dependency metadata stayed unchanged. No Python model ran.

**Remaining input or review.** Original source geometry, chronology, measured-taxon interpretation and source-use rights remain scientific inputs; GPL-2 DESCRIPTION and MIT GitHub labels require a real rights decision rather than inference from numerical agreement. The selected tagged v0.1.2 source is not authenticated as the exact executable used in 2022; that historical version identity remains uncertain.

**Cause category.** Author-code arithmetic correspondence on shared prepared input lineage.

**Consequence.** The comparison qualifies a named computational route and selected population; it does not independently validate the historical observations or all author scenarios.

**Precise next acceptance route.** Retain this current source-R calculation separately from historical execution custody and the retained Python report. Resolve the exact 2022 executable, source-use rights and independent uncertainty/field evidence before broader scientific or redistribution admission.

**Negative or refused result.** The first observer failed an incorrect raw-versus-prepared label assertion; the existing crosswalk corrected it without changing results or tolerances. Unreproduced windows, historical R custody, the exact publication executable and unresolved source/use rights remain open; shared code lineage and exact CSV agreement are not independent field evidence.

**Matched denominator.** Current R-only: four cases by 31 taxa, 124 finite cover plus 124 finite SE pairs, exact zero differences; full nine-site grid with six active positions and 1,000 rows by six sampled original-site indices. Separately retained Python: 31 means and 31 SEs within declared tolerances, not rerun here.

- [Retained qualification evidence: docs/report/method-certification/petrkunes-r-comparison/native-report.json](native-report.json) (SHA-256 `273c1b129551e6392ca926988bf594a66c7de9f435b299832e24b771731d8995`).

- [Retained qualification evidence: docs/report/method-certification/petrkunes-r-comparison/summary.csv](summary.csv) (SHA-256 `5f7957d2d318518e96959a286b74a9a183a9b23655aef3216d61dfd38137541a`).

- [Retained qualification evidence: docs/report/method-certification/petrkunes-r-comparison/taxa.csv](taxa.csv) (SHA-256 `b37211fda3a692d1b903501a14323ab14820950d434f8a2953b9ea25a269b915`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

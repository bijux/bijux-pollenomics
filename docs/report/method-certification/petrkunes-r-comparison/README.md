# Tagged Petr Kuneš LRA comparison

The [bounded comparison](summary.csv) executes two pinned R sources against
the same LandClim II author example counts and parameters: the author's 30
October 2016 `LRA-REVEALS-release.R` and Petr Kuneš's [LRA v0.1.2 source](https://github.com/petrkunes/LRA/tree/d29075692ed730e3934bc461eb9081c404aef59b)
at commit `d29075692ed730e3934bc461eb9081c404aef59b`. The tagged source
tarball is retained outside the product repository with SHA-256
`3292d4726e3cb0204d6f8326c5ce9208aecf3e064c180846adab3be7fa03a353`.
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

The isolated one-window calculation does not replay the full 25-window R
random-number stream from the [two-grid author/native result](../../publication-replay/landclim-example-reexecution/README.md).
That prior result's 225 BP values must not be compared to these outputs as if
their bootstrap draws had the same history. The current comparison also does
not test the LSM transport branch, chronological or basin uncertainty, source
missing-taxon semantics, or Nordic empirical reconstruction. The
[reviewed conditional draw profile](../author-site-uncertainty/README.md) is a
different method with a restricted positive-count subcomposition.

The source [replay script](replay.R) parses only the author's `KPf` and
`REVEALS` function definitions, avoiding the archived script's old
installation side effects. It loads the tagged functions from their pinned
source files and requires zipfR 0.6.70 and LRA 0.1.2. Reproduce into
`artifacts/` using the private source roots:

```sh
mkdir -p artifacts/jobs/petrkunes-r-comparison/r-library
R CMD INSTALL --library=artifacts/jobs/petrkunes-r-comparison/r-library \
  /path/to/bijux-pollenomics-data/lra/dependencies/zipfR_0.6-70.tar.gz
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 Rscript \
  docs/report/method-certification/petrkunes-r-comparison/replay.R \
  /path/to/landclim/author-reference \
  /path/to/bijux-pollenomics-data/lra/petrkunes-v0.1.2/LRA-d29075692ed730e3934bc461eb9081c404aef59b \
  artifacts/jobs/petrkunes-r-comparison/r-library \
  artifacts/jobs/petrkunes-r-comparison/replay
cmp docs/report/method-certification/petrkunes-r-comparison/summary.csv \
  artifacts/jobs/petrkunes-r-comparison/replay/summary.csv
cmp docs/report/method-certification/petrkunes-r-comparison/taxa.csv \
  artifacts/jobs/petrkunes-r-comparison/replay/taxa.csv
```

The governed summary SHA-256 is
`5f7957d2d318518e96959a286b74a9a183a9b23655aef3216d61dfd38137541a`;
the taxon comparison SHA-256 is
`b37211fda3a692d1b903501a14323ab14820950d434f8a2953b9ea25a269b915`.

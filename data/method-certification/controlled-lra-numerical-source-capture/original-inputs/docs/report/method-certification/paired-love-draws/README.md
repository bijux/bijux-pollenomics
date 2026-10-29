# Paired local stochastic LOVE draws

The [source-bound report](report.json) compares the installed DISQOVER 0.9.14
`LOVEr` and `lov` functions with the current Python analytical LOVE engine.
Both consume the exact [same pollen, parameter and ring rows](setup.json),
two copies of one [regional cover vector and explicit local PPE/count draws](draws.json).
The regional vector is the source-compatible deterministic Python REVEALS
output; its corresponding R behavior is certified separately by the original
oracle's deterministic REVEALS cases. Its source three-decimal percentage
rounding leaves the fractional vector summing to 0.99999, which both LOVE
implementations preserve.

The R replay only substitutes supplied stochastic samplers and the supplied
regional-cover return at the function boundaries. It executes the installed
source's ring deposition and local equation. Six paired local PPE/count
realizations cover two repeats and the three eligible rings; the other seven
rings remain source-invalid. Across Mean, Q10, Q90 and SD, all **120 finite**
R/Python cells agree within the declared `3e-10` absolute tolerance (largest
difference `6.93e-14`); all **280 missing** cells occupy the same positions.
The full [R values](r-values.csv), [Python values](python-values.csv) and
[R session](r-session.txt) are retained. Counts and PPE draws vary by repeat
and ring, so this checks more than a deterministic wrapper call.

This is exact-draw numerical parity for one bounded ten-taxon source fixture.
It does not imply that R and NumPy produce the same random stream from equal
seeds, that the source's historical uncertainty is calibrated, or that the
unbounded local estimates are valid vegetation compositions. The separate
[optimizer comparison](../optimizer-solution-quality/README.md) evaluates
solution quality and achieved objectives without claiming equal search paths.

First build the source-locked R library with the [current R reference
producer](../current-r-oracle/README.md#reproduction). Replay into a new absent
output below `artifacts/` with that library and Rscript:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python docs/report/method-certification/paired-love-draws/replay.py \
  --repository . \
  --library artifacts/jobs/native-r-reproduction/library \
  --rscript /usr/local/bin/Rscript \
  --output artifacts/jobs/paired-love-draws/reproduction
```

The generated library path is a local run product, not a portable dependency.
The producer verifies the exact source archive and installed marker, hashes its
input closure and outputs, retains failures under the artifact run, and only
writes a passed report after every numeric and missing-position comparison.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** The retained analytical LOVE comparison uses the exact same two explicit draw realizations and setup in Python and DISQOVER 0.9.14, preserving invalid cases and the rounded regional-vector sum.

**Unsupported claim.** Matched explicit draws do not establish R/NumPy seed trajectory equivalence, calibrated interval coverage, physically valid vegetation compositions, relevant source area or measured ecological accuracy.

**Actual verification performed.** Reviewed the retained setup, draw and report accounts and their exact public identities, including finite/missing partitions and comparison tolerance. No R execution, draw generation or analytical model was rerun for this reader qualification.

**Remaining input or review.** A current-source owner replay must preserve the same setup and arrays; scientific application needs physical and observational source support and independent interpretation of invalid and negative cases.

**Cause category.** Conditional cross-language arithmetic correspondence with fixed shared draws.

**Consequence.** The small finite-cell differences support the declared calculation only; matching missing cells and inadmissible estimates remain part of the result.

**Precise next acceptance route.** Replay the paired-LOVE owner using the exact committed draw arrays and nonfinite mask, retain the regional total 0.99999 and all invalid cases, then separately review any physically justified scientific case.

**Negative or refused result.** Seven of ten cases are invalid. The 280 matched missing cells remain missing; neither the comparison nor renormalization silently converts them into valid predictions.

**Matched denominator.** Ten taxa by ten rings, two explicit repeats, six local PPE/count realizations, three eligible cases;120 finite Mean/Q10/Q90/SD cells agree within 3e-10, maximum 6.927791673660977e-14, with 280 matched missing cells.

Qualified authored reader SHA-256: `fa77174bea370dd5e4e8ff24c3cb0aff5109dc75dcebd559aadd30ed36ce59a0`.

- [Retained qualification evidence: docs/report/method-certification/paired-love-draws/report.json](report.json) (SHA-256 `bdb5984e4e37cfca64ba6ebc766db421c80c13570b67dabbd4d1239baf2650e0`).

- [Retained qualification evidence: docs/report/method-certification/paired-love-draws/draws.json](draws.json) (SHA-256 `904a7833ab0396e4a44f6bb8501a7b1180c48cdadb4714189aa2b41abd3d0351`).

- [Retained qualification evidence: docs/report/method-certification/paired-love-draws/setup.json](setup.json) (SHA-256 `9ac28398214f733ea6b193a78a4da570b654806945703be7c2238a4021c8029b`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

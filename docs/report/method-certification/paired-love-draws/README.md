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

Replay into a new absent output below `artifacts/` with the exact installed
source library and Rscript:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python docs/report/method-certification/paired-love-draws/replay.py \
  --repository . \
  --library artifacts/jobs/live-original-r-certified/library \
  --rscript /usr/local/bin/Rscript \
  --output artifacts/jobs/paired-love-draws/reproduction
```

The private library path is local custody, not a portable dependency. The
producer verifies the exact source archive and installed marker, hashes its
input closure and outputs, retains failures under the artifact run, and only
writes a passed report after every numeric and missing-position comparison.

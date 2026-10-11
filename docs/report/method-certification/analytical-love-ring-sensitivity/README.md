# Analytical LOVE ring sensitivity

The [report](report.json) and [100-cell ring table](ring-cover.csv) replay the
bundled ten-taxon LOVE example with its recorded local and regional pollen,
parameters, and first ten ring boundaries. The source-compatible analytical
method uses two identical deterministic draws. Original DISQOVER 0.9.14 R
[case C0023](../original-r-reference/README.md) checks the same full wrapper
output under the declared numerical tolerance.

Only three of the first ten rings satisfy the source's strict local-basin
boundary. Their example mean-radius coordinates are 9, 12.65, and 17.75 in
the bundled ring table's native units. Across those 30 taxon/ring values,
16 are negative and six exceed one. The range is -7.6443 to 8.4990; the
largest within-taxon change across eligible rings is 6.2606. Invalid rings
remain missing. The raw analytical outputs are deliberately retained rather
than clipped or closed. The result shows strong sensitivity to the selected
ring and an inadmissible vegetation composition for this example; it supplies
no empirical vegetation validation or recommended RSAP.

To regenerate from the repository root into a new absent directory under
`artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python docs/report/method-certification/analytical-love-ring-sensitivity/replay.py \
  --repository . --output artifacts/jobs/analytical-love-ring-sensitivity/reproduction
```

The report records the hashes of the three packaged example inputs and the
owning analytical, input, and dispersal code. It checks invalid-ring masking,
finite valid-ring outputs, and identical deterministic draws before writing
the table. It does not infer historical basin geometry or a fit to an observed
landscape.

# What the analytical LOVE ring example tells us

We replayed the bundled ten-taxon LOVE example with its recorded local and
regional pollen, parameters and first ten ring boundaries. The
[producer](replay.py) used the source-compatible analytical method and two
identical deterministic draws. Original DISQOVER 0.9.14 R
[case C0023](../../../docs/report/method-certification/original-r-reference/README.md)
checks the same full wrapper output under its declared numerical tolerance.

We kept the [exact report](report.json) and [100-cell ring table](ring-cover.csv)
beside this account. Only three of the first ten rings satisfy the source's
strict local-basin boundary. Their mean-radius coordinates are 9, 12.65 and
17.75 in the example's native units. Across those 30 valid taxon/ring cells,
16 estimates are negative and six exceed one. The range is -7.6443 to
8.4990; the largest within-taxon change across valid rings is 6.2606.
Invalid rings remain missing. We retained the raw analytical estimates
because clipping or closing them would conceal the method's behavior.

We conclude that this example is sensitive to ring choice and produces an
inadmissible vegetation composition. It does not validate vegetation against
an observed landscape, establish a historical basin geometry or recommend
an RSAP radius.

We independently reran the producer from current source into an absent
output directory and matched both retained numeric products byte for byte.
The report pins the three packaged example inputs and the analytical, input
and dispersal code hashes. To rerun it from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python reports/science/analytical-love-ring-sensitivity/replay.py \
  --repository . --output artifacts/jobs/analytical-love-ring-sensitivity/reproduction
```

Use a new absent output directory for each run. The producer checks invalid
ring masking, finite valid-ring outputs and identical deterministic draws
before writing the table.

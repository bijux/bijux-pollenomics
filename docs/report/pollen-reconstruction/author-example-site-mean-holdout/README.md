# Author example site-mean pollen holdout

The [source-pinned result](report.json) withholds each of 17 author site IDs
within its grid, then predicts each available 31-taxon pollen composition from
the equal-site mean at the same time bin. It scores 177 of 184 observed site-bin
targets and refuses seven bins without another training site. Site-macro mean
absolute error is 0.018949 in fraction units; site-macro total variation is
0.293703. The [score ledger](scores.csv) retains each scored or refused bin,
and the [prediction ledger](predictions.csv) retains taxon predictions.

This is an untuned, previously exposed development baseline. It is separate
from the later model search, which compares candidates on 174 common bins.
The different scored support prevents a direct improvement claim. Site IDs
lack reviewed aliases across databases; the prepared 31-taxon axis is not a
closed raw-core denominator. No LRA skill, Swedish transfer or measured
vegetation accuracy follows from this result. Original author inputs and the
independent R reference remain in private source custody with redistribution
unresolved.

The [result](report.json) binds the author source revision and private reference
receipt to the scored denominators and method. The [prediction](predictions.csv)
and [score](scores.csv) ledgers are the retained numeric outputs. The
[family replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/pollen-reconstruction/author-example-site-mean-holdout/replay.py) checks the private source identity, runs the existing
producer, normalizes its two CSV line endings and verifies all four tracked
outputs. From the repository root, use an absent output directory under
`artifacts/`:

```sh
.venv/bin/python docs/report/pollen-reconstruction/author-example-site-mean-holdout/replay.py \
  --source-root ../bijux-pollenomics-data/landclim/author-reference \
  --output artifacts/author-example-site-mean-holdout/replay
```

The governed [report](report.json) and [generated summary](REPORT.md) retain
the current result. The producer emits CRLF CSV while these retained ledgers
use LF; the replay changes only those line endings before the byte comparison.

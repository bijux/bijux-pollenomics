# Initial-point sensitivity of constrained LOVE

The [saved analytic-gradient diagnostic](../optimizer-gradient/README.md) recovered
HANGINGS but left CUTHILL2 and LONGBREACH unconverged in both local rings of the
BECKHAM development fold. This comparison changes the initial cover composition
for those four training objectives. It uses the same physical author pollen,
30-taxon closed subcomposition, author PPE and fall speeds, BROADOWN regional
handoff, ring geometry, exact derivative and SLSQP constraints.

For each objective, the protocol declares 32 positive starts before fitting:
half uniform plus half observed training pollen; half uniform plus half the
normalized direction of the coupled regional cover; and half uniform plus half
each of the 30 ordered taxon unit vectors. Each attempt retains the original 300-iteration cap, 16,000-search-
evaluation cap and `ftol=1e-8`. The maintained optimizer independently certifies
the final objective with one additional evaluation. All attempts run serially
with one numerical thread, within a 600-second native stage. Memory and output
limits are checked afterward; no operating-system memory or storage quota is
claimed.

REVEALS returns cover percentages rounded to three decimal places. Their sum
need not equal exactly 100. For the regional initial-point mixture only, the
rounded fractional vector is divided by its sum. The original rounded fractions
remain unchanged in the regional deposition and LOVE objective. The two
`regional_handoffs` records preserve the native percentages, source precision,
fractional mass and normalized start direction on the ordered taxon axis.

The objective remains the Euclidean distance between `log(predicted pollen)`
and `log(observed training pollen + 0.001)`. LOVE normalizes
the nonnegative candidate cover by its sum before computing local deposition.
A selected candidate must pass the original host checks and solver convergence,
be finite, lie in `[0,1]` and sum to one within `1e-6`. Within each ring, selection
minimizes the certified original objective among accepted candidates, breaking
ties by declared start identifier. A refused candidate cannot win selection.

The completed comparison retained all **128 attempts: 84 accepted and 44
refused**. Every ring has at least one candidate that passes the unchanged
convergence and host gates.

| Training site | Ring outer radius | Accepted / 32 | Refused / 32 | Selected objective | Selected start |
| --- | ---: | ---: | ---: | ---: | --- |
| CUTHILL2 | 500 m | 23 | 9 | 0.8230886739145842 | `taxon-01-half-uniform` |
| CUTHILL2 | 1,000 m | 23 | 9 | 0.8230886739145842 | `taxon-01-half-uniform` |
| LONGBREACH | 500 m | 19 | 13 | 0.587410752957418 | `regional-cover-half-uniform` |
| LONGBREACH | 1,000 m | 19 | 13 | 0.587410752957418 | `regional-cover-half-uniform` |

The CUTHILL2 selected start emphasizes `Alnus.glutinosa`, the second taxon in
the ordered source axis. Its accepted result takes 104 iterations and 276 search
evaluations per ring. The LONGBREACH selected start uses the normalized regional
direction and takes 134 iterations and 388 search evaluations per ring. Each
selected result has one additional independent objective-certification call.
All 44 refusals retain “Positive directional derivative for linesearch”.

Both regional handoffs retain a native percentage sum of
`99.99899999999998` and an original fractional sum of `0.99999`. The separately
recorded start direction is closed to one. These are source rounding and start
construction facts; the objective still uses the original `0.99999` mass.

The native comparison completed in **10.868 seconds**. The complete runtime and
source-custody wrapper completed in **35.419 seconds**, with native and wrapper
exits both zero and no before/after source-input mismatch. Completed-child peak
RSS was **385,318,912 bytes**. The declared 2 GiB memory and 64 MiB logical-output
postchecks passed; these measurements do not enforce aggregate process or
operating-system quotas.

The saved uniform-start analytic objectives are `0.8230886817938257` for
CUTHILL2 and `0.587410833421881` for LONGBREACH in each ring. All four saved
analytic fits refused with “Positive directional derivative for linesearch”.
The selected objectives differ from those refused uniform results by
`-7.879241481489885e-9` and `-8.04644630925111e-8`, respectively. Changing the
initial point yields accepted solutions close to the earlier refused objective
values. Those earlier records, HANGINGS and the finite-difference and gradient
checks are reused without rerunning or replacing them.

[report.json](report.json) retains every start, candidate or refusal, objective,
stop message, iteration/evaluation diagnostics and elapsed time.
[trials.jsonl](trials.jsonl) retains the start and completion events for every
attempt. The [execution receipt](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/author-love-start-diagnostic.json)
binds their exact bytes, inputs, source candidate, command, terminal and runtime.
[replay.py](https://github.com/bijux/bijux-pollenomics/blob/main/docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/replay.py) implements this comparison without changing the original
[gradient consumer](https://github.com/bijux/bijux-pollenomics/blob/main/docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/replay.py). Reproduction requires the
source-qualified prepared inputs and matching selection manifest. The public
protocol preserves the executed scientific settings with portable input names;
the receipt retains the original execution-selection identity. This page adds
no new pollen acquisition.

The source execution uses a compact distribution-metadata projection for engine
discovery. Installed wheel and sdist qualification remains separate.

Reproduce the declared comparison with the matching source checkout and qualified
engine/runtime environment. Reuse the 13 original source-qualified prepared
files listed in [protocol.json](protocol.json); their identities, the three
previous witnesses and the unchanged source reference are checked before and
after the calculation. Choose an absent output directory.

```sh
set -eu
repository="$(pwd)"
prepared="/path/to/source-qualified/prepared-inputs"
job="artifacts/science/author-love-start-replay"
python="${PYTHON:-python3}"
protocol="$repository/docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/protocol.json"
selection_sha256="$("$python" -c \
  'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' \
  "$protocol")"
test ! -e "$job"
mkdir -p "$job"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  "$python" \
  docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/replay.py \
  --repository "$repository" --prepared "$prepared" \
  --selection "$protocol" --selection-sha256 "$selection_sha256" \
  --output "$job/report.json" --trials "$job/trials.jsonl"
```

The registered execution receipt supplies the actual resource checks and source
metadata derivation. The command above is a consumer invocation; its runtime and
prepared-input qualification remain prerequisites.

These are 128 optimizer attempts on four existing training objectives, not 128
independent samples or uncertainty draws. Convergence from several starts does
not calibrate an uncertainty interval. The numerical comparison does not decode or score BECKHAM target counts.
Byte authentication of the original source snapshot establishes custody only.
The original fold, published predictions and scores remain unchanged. These
accepted training fits establish numerical convergence under the declared source
assumptions. Global optimality and measured vegetation accuracy remain untested. The broader result and its physical assumptions remain in the
[English LRA scientific account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md).


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound fixed-start convergence diagnostic on exposed English training objectives. Preserve the exact128attempts/84accepted/44refused denominator, raw rounded regional mass, original unchanged outer-fold outcome and every numerical, ecological, uncertainty and source-rights limit.

**Supported claim.** The fixed initial-point comparison yields 84 accepted constrained LOVE fits across the four CUTHILL2/LONGBREACH ring objectives, while retaining 44 line-search refusals. Every ring has an accepted candidate under the original objective, source assumptions and per-attempt bounds.

**Unsupported claim.** Global optimality, original R optimizer parity, a completed BECKHAM prediction or score, an untouched cohort, measured vegetation accuracy, Nordic source admission, rights admission or release approval.

**Actual verification performed.** The registered numerical comparison ran on clean source candidate `64685821de6216983c629df167abe0c16caa57ec` with the separately pinned diagnostic source. All 128 outcomes and 256 start/completion ledger events were retained. The original 13 prepared input files, three baseline witnesses, source references, package trees and qualified runtime passed before/after custody. Native and runtime-wrapper exits were zero; the declared resource postchecks passed. The earlier uniform and HANGINGS fits were not rerun.

**Remaining input or review.** This diagnostic does not run the complete outer fold or resolve its physical geometry, transport interpretation, independent vegetation measurements or qualified ecological review.

**Cause category.** algorithm/numerical | assumption | comparability | qualified review

**Consequence.** Keep convergence and host objective certification mandatory. Report every refusal; retain the original fold outcome and all earlier reports.

**Precise next acceptance route.** Use the admitted fixed-start comparison to decide whether another explicitly declared numerical evaluation is justified. Any complete-fold prediction or ecological claim needs its own source-qualified consumer and evidence.

**Negative or refused result.** Forty-four of 128 attempts retain the original line-search refusal: nine per CUTHILL2 ring and thirteen per LONGBREACH ring. The four earlier uniform analytic fits remain refused. No complete-fold BECKHAM reconstruction or score was produced by this diagnostic.

**Matched denominator.** Two existing English training sites × two local rings × 32 predeclared positive starts = 128 attempts on four objectives, all on the same 30-taxon axis. No new site, sample, held-out observation or scored fold is added.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/report.json](report.json) (SHA-256 `29386982ad042292b918d25ac5891760c045b83a7edeebaf08b256e571719ddd`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/trials.jsonl](trials.jsonl) (SHA-256 `fe7b2734419a7c98cbfc6215ac83950887111acda629ef75586ae294c8050f75`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/protocol.json](protocol.json) (SHA-256 `d257517c80ea407de3c186a8fa611d3a68ef95aae2ee706173849148fe6a37d8`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/replay.py](https://github.com/bijux/bijux-pollenomics/blob/main/docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/replay.py).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/report.json](../optimizer-gradient/report.json) (SHA-256 `8ce87d7083b0dde01d9030bb82bbd6ea9d3193dc4c52fc0ad7c9346894d8774d`).

- [Retained qualification evidence: reports/science/source-cohorts/author-love-start-diagnostic.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/author-love-start-diagnostic.json) (SHA-256 `e5d7966db299a0ab24eb9a035c2a159dbeb8afc2b6045de5b1430aa7d08b132e`).

- [Canonical scientific account: reports/science/english-lra-pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

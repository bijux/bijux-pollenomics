# Installed LRA batch cache and recovery

The [receipt](report.json) records a bounded installed-host workload on macOS
arm64 with CPython 3.11.13. The host and numerical extension were installed
from the separately checked wheels identified in the receipt. Its SHA-256 is
`9ca39ea4568c844ef9fb3454bde2d3438f168b89bf6a8009bb1095df2c8d5ac5`.
Three requests
use the repository's [synthetic fixture producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics/tests/unit/analysis/lra/support.py):
REVEALS, analytical LOVE and paired LRA, each with two taxa and one declared
regional/local sample as applicable. A single shared seven-file evidence
directory backs all requests. The batch limit is three items and two spawned
workers, with each numerical thread control set to one.

| Attempt | Exit | Completed / refused | Cache hits | Elapsed seconds | Maximum resident set size reported by `/usr/bin/time -l` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Invalid paired PPE | 2 | 2 / 1 | 0 | 3.48 | 201,637,888 bytes |
| Corrected rerun | 0 | 3 / 0 | 2 | 3.20 | 205,815,808 bytes |
| Warm rerun | 0 | 3 / 0 | 3 | 3.13 | 204,406,784 bytes |
| REVEALS PPE changed | 0 | 3 / 0 | 2 | 3.13 | 206,749,696 bytes |

The first attempt set paired Alnus PPE to −1, which produced a structured
`invalid_lra_schema` refusal. The corrected request computed that item while
reusing the two completed products. The warm rerun reused all three. Each
reused item has the same cache key and scientific content SHA-256 as its cold
calculation. Changing REVEALS Alnus PPE from 4 to 5 missed the cache, changed
the cache key from `9dddfce2…` to `b69d6976…`, and changed the scientific
content SHA-256 from `7629d257…` to `29da0325…`; the other two products
remained hits. Full keys and identities are in the receipt.

These are whole-command measurements, including Python and spawned-worker
startup. They do not estimate peak memory of each worker separately or show
a useful speedup at this small workload. Cache hits are verified product reads,
and the failed request never becomes a hit. All outputs remain
`scientific_acceptance: not_evaluated`; this checks operational recovery on
synthetic inputs, not ecological accuracy or a Nordic sample admission.

To rebuild the three batch requests in a new `artifacts/` directory, run this
from the repository root. The installed CLI's `run-lra-batch` command then
accepts each JSON file with the generated directory as `--input-root`, a
shared `--cache-root`, a fresh `--report-root` per attempt, and
`--max-workers 2 --max-items 3`. Run `failure.json`, `resume.json`,
`resume.json` again, then `parameter-change.json` in that order.

```sh
python3 - <<'PY'
import copy
import json
import runpy
from pathlib import Path

root = Path("artifacts/jobs/lra-batch-execution/replay-input")
root.mkdir(parents=True, exist_ok=False)
fixture = runpy.run_path(
    "packages/bijux-pollenomics/tests/unit/analysis/lra/support.py"
)["request_fixture"]
items = [
    {
        "item_id": name,
        "request": json.loads(json.dumps(fixture(root, operation), sort_keys=True)),
    }
    for name, operation in (
        ("reveals", "reveals"),
        ("analytical", "love"),
        ("paired", "lra"),
    )
]
requests = {
    "resume": items,
    "failure": copy.deepcopy(items),
    "parameter-change": copy.deepcopy(items),
}
requests["failure"][2]["request"]["parameters"][0]["ppe"] = -1
requests["parameter-change"][0]["request"]["parameters"][0]["ppe"] = 5
for name, selected in requests.items():
    (root / f"{name}.json").write_text(
        json.dumps({"schema_version": "lra-batch-request.v1", "items": selected}, indent=2)
        + "\n"
    )
PY
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** The retained installed macOS batch diagnostic exercises three synthetic routes, cache identity and an exact invalid-PPE refusal with two workers and one numerical thread per worker.

**Unsupported claim.** The batch timings establish neither speedup, per-worker memory, scientific source admission, field accuracy, a current wheel build nor official release certification.

**Actual verification performed.** Reviewed the retained installed-run account, attempt/refusal/cache transitions and actual whole-command timing scope and bound its report bytes. No installation, CLI batch or model execution was repeated for this reader qualification.

**Remaining input or review.** A current-candidate installed diagnostic must retain its own archive/import identity; scientific use additionally needs admitted observations and justified parameters, while release requires its hosted admission evidence.

**Cause category.** Installed execution/cache contract on synthetic inputs.

**Consequence.** The account demonstrates bounded installed behavior for its recorded wheels and inputs; a cache hit cannot independently validate the scientific result.

**Precise next acceptance route.** Use the maintained installed distribution and batch consumers at the intended source candidate, preserve the invalid-PPE case and independently qualify any scientific inputs before release admission.

**Negative or refused result.** The initial invalid PPE attempt has two passes, one refusal and exit 2. Corrected, warm and changed-PPE attempts retain their distinct hit/miss patterns rather than converting the failed attempt to a pass.

**Matched denominator.** Three synthetic routes, two taxa, seven evidence files and four batch attempts; corrected three-route execution has two hits, warm execution three, changed PPE two; observed whole-command times are about 3.13–3.48 seconds.

- [Retained qualification evidence: docs/report/method-certification/lra-batch-execution/report.json](report.json) (SHA-256 `9ca39ea4568c844ef9fb3454bde2d3438f168b89bf6a8009bb1095df2c8d5ac5`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

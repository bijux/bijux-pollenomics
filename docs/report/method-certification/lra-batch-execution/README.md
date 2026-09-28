# Installed LRA batch cache and recovery

The [receipt](report.json) records a bounded installed-host workload on macOS
arm64 with CPython 3.11.13. The host and numerical extension were installed
from the separately checked wheels identified in the receipt. Its SHA-256 is
`9ca39ea4568c844ef9fb3454bde2d3438f168b89bf6a8009bb1095df2c8d5ac5`.
Three requests
use the repository's [synthetic fixture producer](../../../../packages/bijux-pollenomics/tests/unit/analysis/lra/support.py):
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

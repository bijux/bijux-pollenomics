# Neotoma acquisition scope

The [source-bound receipt](report.json) verifies that all 206 retained inventory
JSON rows are ordered, unchanged objects from the stored 387 queried rows. Their
209 dataset IDs equal both the request and download ID lists in the nine-part
archive manifest. The receipt pins the inventory, manifest and four current
country boundary files by SHA-256. The nine archive parts and relational
preservation have their own validated reader and [native round trip](../native-roundtrip/README.md).

Replaying the current country selector against those same queried rows selects
200 rows and 203 dataset IDs. Six retained source rows are now excluded: site
700/dataset 720, 3025/3941, 3138/4082, 3221/4181, 3311/4298 and
13395/20058. The receipt records their exact queried-row indexes. This is a
current selection difference; the retained files do not say which original
boundary capture or decision authorized those six rows.

The stored inventory and archive are producer-serialized JSON. They do not
contain original HTTP request/response bytes, per-page limit/offset/status,
termination evidence or 209 original download response digests. The April 2026
`generated_on` field does not establish a request timestamp. A source custodian
must provide those original acquisition records, or a new separately identified
capture must write each exact request URL and parameters, status, timestamp,
response-body bytes and digest, page count and termination evidence, then bind
parsed rows to those bytes and each download response to its dataset ID. A new
capture can verify its own scope but cannot retroactively certify the April
capture. Neither this receipt nor the manifest establishes source rights, age
choice, count denominator or LRA admission.

Replay from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.neotoma_acquisition_scope \
  --repository "$PWD" \
  --output artifacts/jobs/neotoma-acquisition-scope/replay/report.json
```

Compare the replayed JSON with the retained receipt before using its conclusions.

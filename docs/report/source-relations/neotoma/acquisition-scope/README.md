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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The retained inventory objects and 209 dataset IDs reconcile to the nine-part serialized download manifest.

**Unsupported claim.** Serialization equality cannot recover original HTTP response bytes, pagination termination, request times or original boundary-selection authority.

**Actual verification performed.** Read the acquisition receipt and six exact current-selector differences; no network acquisition or historical receipt reconstruction.

**Remaining input or review.** Original request/response/page/download identities or a separately identified new capture are required.

**Cause category.** Missing original HTTP authority and changed country selection.

**Consequence.** A new capture could qualify itself but cannot certify the April capture retroactively.

**Precise next acceptance route.** Recover original URLs/parameters, statuses, timestamps, response digests and termination evidence, or capture a distinct source revision honestly.

**Negative or refused result.** Six retained rows are outside the current selector; original HTTP receipts are unavailable.

**Matched denominator.** 387 queried rows→206 retained rows/209 datasets; current selector 200 rows/203 datasets; 6 retained-only rows, 0 current-only rows.

Qualified authored reader SHA-256: `30a1b159e3b0643e50473eebed06648dc48141095292e8d67d04da8f1c5dac50`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/acquisition-scope/report.json](report.json) (SHA-256 `0468b53b29c5892151c1533d487994f63617c7df7c40e6b167637d1657e2f5fd`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

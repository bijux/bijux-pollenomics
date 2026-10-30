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

## Distinct current Abborrtjärnen capture

A separate capture now binds current official Neotoma responses for dataset
**19913**, site **13338**, collection unit **14910**, handle **ABBO**. Its
[comparison result](current-abbo-comparison.json) establishes source preservation
for this one core. The April inventory, nine-part archive, historical receipt
above and six retained-only country decisions remain unchanged.

The canonical source identity is
`neotoma/dataset-19913/2026-10-26T185139Z`. The folder label was assigned during
planning; the four actual requests ran from **2026-10-26T18:54:13.050022Z** to
**18:54:19.449560Z**. All four returned HTTP 200: the dataset download, its
dataset metadata, the current Neotoma policy and the EPD policy. The capture
manifest retains each exact GET URL/target and request headers, duplicate-preserving
response headers, status, start/end times, complete response entity bytes,
byte count and digest. Transfer framing was removed by the HTTP client; the
entity bytes were not content-decoded or JSON-reserialized.

The download from
[`/v2.0/data/downloads/19913`](https://api.neotomadb.org/v2.0/data/downloads/19913)
contains **632,600 bytes**, SHA-256
`1317496c2e1d04c7f69a2048ee49647350f5abfc0f8e23360211e01f5eb5dd8a`.
The completed `capture-manifest.json` has SHA-256
`906f7e38d5c32d03f00094136ee89213ea39ea99eb422db233e723b8f4e79269`.
Metadata creation dates, HTTP dates, request times and the capture identity
are distinct. The API route version does not establish a database revision or
transactional snapshot across the four requests. No Nordic inventory search or
pagination completeness is claimed by this dataset-ID capture.

### Source preservation and comparison

At committed consumer source
`dad49494903831173661f0629d4e8b0d793b2a86`, session **51050** terminated with
exit zero in **0.875201792 seconds**, with peak resident memory **184,795,136
bytes**. The existing `build_neotoma_relational_snapshot` projected the newly
captured row and the retained dataset-19913 row separately, with distinct source
identities. The existing native hierarchy reconciliation checked every
parent-scoped payload and occurrence on its eight surfaces for each projection.

| Surface or source quantity | Retained row | Current response |
| --- | ---: | ---: |
| Sites / collection units / datasets / chronologies | 1 / 1 / 1 / 1 | 1 / 1 / 1 / 1 |
| Chronology control rows, including the core top | 7 | 7 |
| Samples | 107 | 107 |
| Sample-owned age claims | 107 | 107 |
| Observations, source unit NISP | 2,892 | 2,892 |
| Normalized source variables | 94 | 94 |
| Missing/unexpected native payloads, conflicts, orphans, unregistered occurrences | 0 | 0 |

The nested dataset-row comparison found **zero changed paths**. It compares exact
decoded JSON numeric values, integer-versus-decimal kind, strings, booleans,
nulls, missing fields and literal array order. It does not assert equality of
JSON numeric spellings, whitespace, object-key order or HTTP bytes: `1.00` and
`1.0` have equal decimal values. A fixture distinguishes
`1.000000000000000001` from `1.0` even when both become the same binary64 value.
Changed decimals are serialized as explicitly tagged exact strings without
rounding. The native projector continues to use its existing Python JSON
binary64 semantics; that projection and the exact source-value comparison are
separate checks. Full source bytes remain inspectable in the canonical capture.

The standalone projections deliberately supply no new country decision. Their
raw country is Sweden, but their governed country remains `UNASSIGNED` and
propagation remains blocked. Existing temporal handling retains **106 comparable
age claims and one negative-BP refusal**. These are the unchanged software
postures, not selected ages or scientific admission. NISP observation counts
do not establish a qualified terrestrial denominator, taxon mapping or PPE.

The native report is **24,550 bytes** and the complete changes file is
**3 bytes** (`[]` followed by a newline), within the predeclared 100,000-byte
report and 2,000,000-byte changes bounds. Runtime and memory were below the
120-second and 512-MiB bounds. No full relational snapshot or duplicate source
archive was written. Exact command/status/resources are retained locally in
`artifacts/neotoma-capture-comparison/execution.json`; the full changes file is
under its `current-abbo/` directory.

Reproduce the maintained comparison with the canonical capture available,
using a new artifact destination:

```sh
source_store="/path/to/bijux-pollenomics-data"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.source_completion.neotoma.capture_comparison \
  --repository "$PWD" \
  --capture "$source_store/neotoma/dataset-19913/2026-10-26T185139Z" \
  --capture-manifest-sha256 906f7e38d5c32d03f00094136ee89213ea39ea99eb422db233e723b8f4e79269 \
  --output "$PWD/artifacts/neotoma-capture-comparison/abbo-replay"
```

Seventeen focused fixtures, configured Ruff formatting/lint and two-path strict
types passed before commit. The fixtures preserve changed counts, ages,
unknown fields, missing/null/zero/type distinctions, duplicate observations,
HTTP failures and input drift. A duplicate sample identity produces a failed
native comparison, retains its report and changes, and exits nonzero. An
initial strict-type test import was corrected. Pre-run review also identified
the binary64 comparison limit; separate exact numeric parsing and its
false-equivalence fixture resolved that claim before any actual comparison.
Neither was a failed native source result.

An independent observer subsequently ran at committed checker source
`cc19f699e014d6adf1a2d43d369e66a2f342ec2a`, against the saved producer result
above. It imports neither the comparison producer nor its Decimal helpers.
Its JSON number hooks retain integer kinds and exact `Fraction` values, and
its separate traversal counts source entities and occurrences directly.
It confirms equality of the two raw dataset-row value trees, all eight native
surface counts, 94 source taxon IDs, 2,892 NISP observations, the three input
byte identities and the reported zero changes/nonadmission. This is a distinct
numeric decoder and raw-count check, not another production run.

Session **72878** terminated with exit zero: **two tests passed in 0.29 s**,
with **0.624543250 s** process wall time and peak resident memory
**150,323,200 bytes**. One test controls sub-binary64 differences and number
kinds; the other actually reads the raw sources and saved result, with no skip.
Configured Ruff and strict types also passed for the observer. Its recorded
command was:

```sh
PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -l .venv/bin/python -B -m pytest \
  -c configs/pytest.ini \
  packages/bijux-pollenomics-dev/tests/source_completion/neotoma/test_capture_comparison_result.py \
  --basetemp=artifacts/neotoma-capture-comparison/committed-rational-observer -q
```

### Attribution and use limits

Attribute the **Neotoma Paleoecology Database**, its constituent **European
Pollen Database**, original investigator **Thomas Giesecke**, and dataset
DOI [`10.21233/2vzb-bg61`](https://doi.org/10.21233/2vzb-bg61). The retained
provider publication record identifies Giesecke's 2005 study as primary:
[*Holocene forest development in the central Scandes Mountains, Sweden*](https://doi.org/10.1007/s00334-005-0070-2),
*Vegetation History and Archaeobotany* **14**, 133–147. The publisher verifies
that DOI and volume; the provider record itself has a null publication DOI and
prints volume 13. Those source fields were not silently corrected. The
[existing core-method account](../../../../../reports/science/abborrtjarnen-source-method.md)
retains the publication-to-core interpretation and its remaining limits.

The captured policy requests the Neotoma reference **Williams, Grimm et al.
(2018), Quaternary Research 89, 156–177**, together with the database's
permanent identifier [`10.17616/R3PD38`](https://doi.org/10.17616/R3PD38).
Its EPD section requests **Fyfe et al. (2009), Vegetation History and
Archaeobotany 18, 417–424**. These database references accompany the
dataset-specific investigator, DOI and original publication above.

The captured [Neotoma policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
and [EPD policy](https://epdweblog.org/epd_data_home/epd_policy/) support public
Neotoma/EPD data use with attribution under **CC BY 4.0**. This is a permitted
current source-preparation route, not a new blanket permission requirement.
It supplies no Rootsi workbook or PANGAEA permission. Current value equality
does not recover the April requests, their boundaries or HTTP bodies, and does
not identify the ages or revision selected by the original paper or LandClim.
Basin history, denominator, taxonomy/parameters and scientific admission remain
separate; no existing source, country ledger, map or model input was replaced.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The retained inventory objects and 209 dataset IDs reconcile to the nine-part serialized download manifest. Separately, one current official ABBO response has complete HTTP custody, equal exact decoded values/kinds to its retained row, and complete native preservation across eight surfaces.

**Unsupported claim.** Serialization equality cannot recover original HTTP response bytes, pagination termination, request times or original boundary-selection authority.

**Actual verification performed.** Historical acquisition receipt and six current-selector differences reused. The distinct four-request current capture and committed single-core native comparison terminated successfully at dad49494903831173661f0629d4e8b0d793b2a86. The separate exact-rational/raw-count observer passed both tests at cc19f699e014d6adf1a2d43d369e66a2f342ec2a. No historical HTTP reconstruction, full Nordic recapture or new model run.

**Remaining input or review.** Original request/response/page/download identities remain missing for the April Nordic capture. Current ABBO source custody is now separately established; its scientific age, denominator, basin and taxon decisions remain outside this result.

**Cause category.** Missing original HTTP authority and changed country selection.

**Consequence.** A new capture could qualify itself but cannot certify the April capture retroactively.

**Precise next acceptance route.** Recover original URLs/parameters, statuses, timestamps, response digests and termination evidence for the April scope. Use the separately qualified current ABBO capture under its own identity for an eligible core consumer; selected age, basin, denominator and taxon/parameter decisions still require their own evidence.

**Negative or refused result.** Six retained rows are outside the current selector; original HTTP receipts are unavailable.

**Matched denominator.** Historical scope: 387 queried rows→206 retained rows/209 datasets; current selector 200 rows/203 datasets; 6 retained-only rows, 0 current-only rows. Distinct current scope: one ABBO dataset, 107 samples, 107 age claims, 7 controls, 2,892 observations and 94 source variables.

- [Retained qualification evidence: docs/report/source-relations/neotoma/acquisition-scope/report.json](report.json) (SHA-256 `0468b53b29c5892151c1533d487994f63617c7df7c40e6b167637d1657e2f5fd`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

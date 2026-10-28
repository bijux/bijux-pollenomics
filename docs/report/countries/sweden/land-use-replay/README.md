# Southern Sweden land-use product replay

The [receipt](receipt.json) records one fresh execution of the existing Sweden
country-report consumer against the current repository inputs. It compares the
published six-target, 150-window LandClim/SEAD/aDNA synthesis with the rebuilt
JSON, CSV and Markdown. All three output files and all three checked upstream
country products match byte-for-byte. The six semantic change categories each
have zero entries. The receipt SHA-256 is
`f6fcc69f04872d7ef65ed3ac19f2168e2f4b27b2ed2e073730f66de905b253a0`.

The receipt pins seven direct source files, including AADR v66, the LandClim
grid, SEAD record intervals and the governed SVAR review. It also pins eleven
land-use policy source files and the published/replayed hashes of the AADR
locality, animal locality and lake-decision products consumed along the country
report path. The source files are the current repository bytes; this replay
does not reconstruct an earlier historical source revision.

The [historical comparison](historical-comparison.json) reads the earlier
committed product at `0a3a42ade39112b256faa527b898fb98df2c57cf` without
switching branches. Its seven direct source files are unchanged in the current
worktree. Four land-use producer paths changed. The previous product contained
two wetland targets and 50 windows; the current one contains those wetlands
plus four governed named lakes and 150 windows. The diff records 106 product
membership entries: four target decisions, 100 target-window rows and two
derived count fields. It records one policy-rule change and one coverage/admission
count change. Existing wetland scientific values did not change. This narrows
the product revision to target selection and presentation policy; it is not a
claim that land cover changed in the past. The historical comparison SHA-256 is
`e1332c72d19be249be19099cfadade66817c1f59425677391f8b0564f42e6d41`.

The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sweden_land_use_replay.py)
classifies target or source-window membership, normalized identity/value,
policy or weighting, admission/exclusion, scientific-result and presentation
differences separately. It refuses a new unclassified product field or a
duplicate target/window key. A changed source hash is a provenance lead; the
field-level diff identifies what changed in the governed product, without
claiming that one source caused a historical landscape change.

Reproduce from the repository root into a new directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.sweden_land_use_replay \
  --repository . --output artifacts/semantic-replay/sweden-reproduction \
  --historical-revision 0a3a42ad
```

Compare both resulting JSON files with the governed receipts. The replay
answers product reproducibility and semantic-diff questions. It does not turn
modeled LandClim cover, dated SEAD context or spatial overlap into independent
vegetation truth or a multi-evidence causal trajectory.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Swedish observed pollen/modeled land use/archaeological context has separate provenance and no causal or ecological validation.

**Supported claim.** The retained native replay receipt reports byte-identical six-target 150-window country products and a field-classified comparison with the earlier two-target 50-window product.

**Unsupported claim.** A historical product diff or current output equality does not establish past land-cover change, independent vegetation truth or a multi-evidence causal trajectory.

**Actual verification performed.** Read the retained replay/historical receipts and source-policy bindings; checked native status identical,three outputs and three upstream products,plus reported change categories. No fresh country-report execution was run for this reader.

**Remaining input or review.** A current candidate needs its own source-bound execution before a current reproducibility claim; ecological claims additionally need admitted independent observations and chronology.

**Cause category.** Retained product reproduction and semantic change accounting, separate from historical causation.

**Consequence.** The historical expansion is governed target-selection/presentation: four named lakes added to two wetland contexts. Existing wetland values are retained,not inferred past landscape change.

**Precise next acceptance route.** Execute the maintained semantic replay against a frozen coherent candidate and compare all source/policy/output identities; retain separate membership,policy,admission and scientific-result differences.

**Negative or refused result.** Retained replay reports zero changes in six categories; historical 106 membership entries plus policy/admission changes remain visible. Historical receipts are not relabelled as current execution.

**Matched denominator.** Current retained 6 targets×25 windows=150 rows versus historical 2×25=50;three output files/three upstream products;7 direct source and 11 policy files are custody counts,not scientific sample support.

- [Retained qualification evidence: docs/report/countries/sweden/land-use-replay/receipt.json](receipt.json) (SHA-256 `f6fcc69f04872d7ef65ed3ac19f2168e2f4b27b2ed2e073730f66de905b253a0`).

- [Retained qualification evidence: docs/report/countries/sweden/land-use-replay/historical-comparison.json](historical-comparison.json) (SHA-256 `e1332c72d19be249be19099cfadade66817c1f59425677391f8b0564f42e6d41`).

- [Retained qualification evidence: docs/report/countries/sweden/sweden_land_use_synthesis_v66.json](../sweden_land_use_synthesis_v66.json) (SHA-256 `c9aa7a1a57aabd0673c4411677da29b8add4a8d604c5db30aab6003a2a4d0380`).

- [Canonical scientific account: reports/science/sweden-lake-trajectory.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sweden-lake-trajectory.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

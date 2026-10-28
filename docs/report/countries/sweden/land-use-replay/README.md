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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/sweden-lake-trajectory.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sweden-lake-trajectory.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

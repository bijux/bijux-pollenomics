# SEAD built map candidate

The published Nordic atlas build `atlas-e50f85d0eaf103404801f4b4c4a9f3a6377db546ea4c20f4293c72dd461a9fc6` and the browser candidate `atlas-ee0c85dd860bce72123c877990bc3bf54a39795dfa77735379ffe5b6350de6ee` agree on the retained four-country SEAD source details. The browser replay checked 16 chronology tables at two widths with 0 runtime errors. The public SEAD evidence blocks and map layer prose/counts match the governed sources. The [machine report](report.json) binds the checked source and map bytes.

The built site layer contains 2,069 context points, including 1,219 without numeric site envelopes. The Swedish discovery layer contains 8,799 features: 7,244 numeric record intervals and 1,555 unresolved context records. A live run of the map's time-filter functions excluded every site 3840 record from the 84–104 BP gap and admitted the two 82 BP records at 82 BP; a source-backed 0 BP site envelope remained numeric while an unresolved site remained outside the test time window. The optional site inventory ignores the time filter because its envelopes are display context.

The source review contains 25,109 typed chronology claims and zero eligible ecological events across Denmark, Finland, Norway and Sweden. The built atlas contains zero accepted propagation edges. Cross-border candidate materialization is therefore refused for lack of admissible event endpoints; a national border is not a rejection rule. The pinned acquisition release status is `refused`. Site envelopes do not establish occupation, arrival or propagation.

## Reproduce

From the repository root, run the existing retained-source candidate and browser verifier, then this audit with their output paths:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.nordic_source_candidate --repository . --destination artifacts/sead-map-candidate/source-display
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic-country.mjs artifacts/sead-map-candidate/source-display artifacts/sead-map-candidate/browser '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.source_completion.sead_map_candidate --repository . --candidate artifacts/sead-map-candidate/source-display --browser-receipt artifacts/sead-map-candidate/browser/receipt.json
```

Use absent artifact destinations for a replay. The browser result is a bounded retained-source detail check; it does not certify event-level ecology, source release, hosted deployment or all browser engines.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The retained historical map candidate verified bounded SEAD details and gap-aware time filtering for its exact atlas/browser builds.

**Unsupported claim.** Its historical PASS/current-sync fields do not certify the changed current renderer, browser engine, hosted release or ecological events.

**Actual verification performed.** The maintained map audit ran on the current selected source context after its chronology-country parent was regenerated. All 76 dependencies of the retained browser candidate and all 19 actually served payload hashes match current source bytes. The browser receipt records 16 chronology-table checks and zero runtime errors. The map time-filter JavaScript was executed again. No new browser session, source capture or model run occurred.

**Remaining input or review.** Source classifications and event and propagation eligibility remain unaccepted. The browser evidence covers eight retained source details in four countries at two widths. It does not certify all source records, hosted deployment, other engines, chronology accuracy or source release rights.

**Cause category.** Historical presentation qualification and refused scientific endpoints.

**Consequence.** Old browser success remains retained evidence only for its pinned candidate, not current browser adoption.

**Precise next acceptance route.** Use the maintained chronology-country producer before the map audit when its custody parent changes. Reuse a browser capture only after every declared candidate dependency and served byte is verified unchanged; recapture when that exact footprint changes. Source classification and ecological event admission require separate qualified evidence.

**Negative or refused result.** All 25,109 typed source chronology claims retain their display, context or refusal roles. There are zero eligible ecological events and zero accepted propagation edges. The 84–104 BP gap admits no record for site 3840; the 82 BP test admits two. A numeric 0 BP envelope remains numeric, and unresolved support remains outside the test window. The current account audit supplies no new browser execution.

**Matched denominator.** Historical 2,069 context sites/1,219 untimed; 8,799 discovery records=7,244 numeric+1,555 unresolved; 16 chronology tables/two widths/0 recorded runtime errors.

- [Retained qualification evidence: docs/report/source-relations/sead/map-candidate/report.json](report.json) (SHA-256 `20d564598838620c15405a16b36ad4885a8c85a4f919fa21f888904795a8242f`).

- [Retained qualification evidence: docs/report/source-relations/sead/interval-sets/report.json](../interval-sets/report.json) (SHA-256 `b2c7fe1f2e4ab7b1d331031abcc4fac9bd484d81345f463df5d3f08085a0735c`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

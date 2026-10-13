# SEAD built map candidate

The published Nordic atlas build `atlas-77be437a84bc823b81933728de0fa81a5da6f7d1a38683ec361d7a3c49a65897` and the browser candidate `atlas-ee0c85dd860bce72123c877990bc3bf54a39795dfa77735379ffe5b6350de6ee` agree on the retained four-country SEAD source details. The browser replay checked 16 chronology tables at two widths with 0 runtime errors. The public SEAD evidence blocks and map layer prose/counts match the governed sources. The [machine report](report.json) binds the checked source and map bytes.

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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

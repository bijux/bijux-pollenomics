# Governed Nordic propagation edge ledger

The [16-row edge ledger](edge-ledger.csv) retains every ordered source and target country bin for Denmark, Finland, Norway and Sweden. The [report](report.json) binds the current Neotoma source snapshot, concept review, original propagation evidence and output hash. Its [retained evidence](evidence/manifest.json) contains the original zero-event release bundle with all seven payload hashes. The [classification decision receipt](classification-evidence/manifest.json) and its accepted queue, release decision and observation denominator are retained separately.

The source-first screen consumed two real Neotoma sites, 128 variables and 256 chronology/profile attempts. It admitted **zero events**. The four-country Neotoma concept file has 1,351 rows: 1,298 unmapped and 53 not applicable, with no accepted mapping. The propagation release consequently has zero input events, zero evaluated pairs and zero directed candidates in each of the 16 country bins. All 16 declared sensitivity scenarios retain the same empty bins. The release metadata explicitly forbids public release of ecological propagation claims.

These country pairs are **reporting bins**, not 16 observed source-to-target routes. The two-site event screen is not a census of event-ready sites in four countries. The compact classification receipt retains the decision and 370,936-observation denominator, while its large per-observation membership product remains outside this report; this is not a full classification audit replay. Empty bins cannot estimate a propagation rate, validate a distance threshold or prove an ecological absence. A future admitted concept, comparable age series and source event would require rebuilding this ledger and rerunning its consumers.

Recompute and verify the retained ledger and source/evidence identities from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/report/propagation/governed-edge-ledger/replay.py
```

The same checked producer can write the CSV and JSON into a fresh artifact
directory for an independent byte comparison:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/report/propagation/governed-edge-ledger/replay.py \
  --output-dir artifacts/jobs/governed-edge-ledger/reproduction
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The retained ledger accounts for all ordered four-country reporting bins under the actual zero-event Neotoma release and explicitly prohibits ecological propagation publication.

**Unsupported claim.** Empty reporting bins establish no observed route, rate, distance threshold, ecological absence or full replay of the external per-observation classification membership.

**Actual verification performed.** Read the ledger narrative and physical report including concept-status and observation denominators; no ledger producer, classification capture or propagation estimator was rerun.

**Remaining input or review.** Accepted taxon mapping, comparable reviewed sample ages and at least one admitted source event are missing before real route evaluation can begin.

**Cause category.** Source and classification admission refusal with an empty derived event population.

**Consequence.** All country bins remain inspectable without manufacturing sixteen biological routes or interpreting zero candidates as evidence of absence.

**Precise next acceptance route.** Admit exact concepts and chronology against the native source, rerun the source-first screen, and rebuild the ledger and actual public propagation consumers if an event becomes admissible.

**Negative or refused result.** All 1351 concept rows are unaccepted (1298 unmapped, 53 not applicable); public_release_allowed remains false and all sixteen scenarios contain zero events, pairs and candidates.

**Matched denominator.** Two screened sites, 128 variables, 256 profile attempts; 16 ordered source/target country bins per scenario across 16 scenarios. Classification denominator 370936 source observations is distinct from zero admitted events.

- [Retained qualification evidence: docs/report/propagation/governed-edge-ledger/report.json](report.json) (SHA-256 `a72a95f33a0213f61df572e19301788946809ecb7651cd27df28e4eb226c8b29`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

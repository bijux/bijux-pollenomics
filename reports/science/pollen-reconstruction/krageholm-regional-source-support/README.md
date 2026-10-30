# Krageholm support for a Betula–Ulmus regional source

All six predeclared 500-year windows have complete literal Betula and Ulmus count support in the retained Krageholm record. Their nineteen source samples supply a potential input to a separately declared regional-source experiment. This result establishes source and age accounting, with no reconstruction, prediction, geometry qualification or field admission.

The [protocol](protocol.json) and independent reader were committed before opening the source part. The [compact result](result.json) keeps the complete population and six-window accounting; the detailed local result retains every original owner, observation disposition and age claim. The original Krageholm Betula–Poaceae geometry, wind, covariance and counting studies remain unchanged.

## Native identity and chronology

The retained Neotoma/European Pollen Database record is dataset **23013**, site **3204**, collection unit **16622**, handle **KRAGMJNY**, with **96** unique ordered sample owners. The source is `data/neotoma/raw/neotoma_pollen_dataset_downloads/part-005.json`, 23,953,555 bytes, SHA-256 `93a673c6fa66522667be2292cda076489330cbe1b5da8cea6b000d9c124c10cc`. This authenticates the retained source bytes, not missing original HTTP custody or a new current capture. Attribute dataset [10.21233/d642-mk20](https://doi.org/10.21233/d642-mk20) to its contributor Marie-José Gaillard-Lemdahl, and the selected chronology separately to Giesecke et al. (2014). Existing local analytical-use scope and historical metadata restrictions remain; this account grants no new reuse rights.

The analysis explicitly selects calibrated MADCAP chronology **13366**, named `Giesecke et al. 2014 (MADCAP)`, with native type `Calibrated radiocarbon years BP` and the inherited Neotoma AD 1950 reference. It is not the unique native default: the collection-unit reference is **13365**, a separate radiocarbon profile, while both chronology declarations have `isdefault=true`. All those declarations and all source ages, signed/null bounds, depths and sample identities remain inspectable. The selected point/name/type are valid on all 96 owners. There is no calibration, interpolation, age repair or propagated chronology law. Noninteger age fields retain the existing reader’s binary64 interpretation; original byte identity preserves their source spellings.

## Complete source and window accounting

A supported panel requires one literal **Betula / native taxon 29** and one literal **Ulmus / native taxon 310**, with uncontextualized pollen/pollen, NISP, and nonnegative integer JSON values. Reported zero, absent label, duplicate, wrong identity, incompatible metadata, null, missing value and invalid numeric type remain different states. There is no synonym mapping, fractional rounding or absent-to-zero rule. The full denominator is the sum of literal source pollen NISP rows; it is not a qualified terrestrial-pollen universe or independent-grain count. Any invalid or duplicate pollen row would suppress that denominator.

Across the full record, **91/96** panels are complete: **187** measured cells and **five missing Ulmus literals** in the 192 requested slots. The missing entries occur at selected ages 10,029, 11,144, 11,330, 11,515 and 11,701 BP, all outside the frozen six-window domain. They remain missing and make the all-96 Betula–Ulmus aggregate unavailable. All **2,803** source pollen NISP cells pass their declared typing/identity checks, summing to **87,713**; **622** non-pollen rows remain outside that sum. Source-wide count availability does not fill the five panel cells.

The half-open windows below retain all their source members. No incomplete sample was dropped to obtain a complete bin. Nineteen owners fall inside these six windows and seventy-seven outside. The protocol would withhold window aggregates if any owner had an unassignable selected age; none does here.

| Selected calibrated-BP window | Owners | Betula | Ulmus | Two-axis N | Full source pollen NISP | Outside two-axis N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [2700, 3200) | 4 | 506 | 36 | 542 | 3973 | 3431 |
| [3200, 3700) | 4 | 408 | 68 | 476 | 3955 | 3479 |
| [3700, 4200) | 3 | 204 | 81 | 285 | 2976 | 2691 |
| [4200, 4700) | 2 | 135 | 35 | 170 | 2097 | 1927 |
| [4700, 5200) | 3 | 160 | 65 | 225 | 2654 | 2429 |
| [5200, 5700) | 3 | 225 | 87 | 312 | 2732 | 2420 |

These bins contain **2,010** two-axis counts (1,638 Betula and 372 Ulmus), **18,387** literal source pollen NISP and **16,377** counts outside the two-axis panel. All six requested outcomes remain supported, without changing the source-wide incomplete-panel disposition.

## Actual execution and independent check

Both actual jobs used frozen committed HEAD `bb7ea494d38cba97a7f5c40909ae7d127c100d58`, with stable index, consumed code/protocol and original source bytes. The producer ran once, terminal **28435f**, exit zero, `/usr/bin/time -l` **0.35 s**, peak RSS **137,560,064 bytes**. Its 274,758-byte result has SHA-256 `7d19b911ffe54c0fe97b2de973bc85b7150ded6e37550d571ff838b108353c30` and remains under `artifacts/physical-core/krageholm-regional-source-support/native-run/`; exact invocation, environment and terminal facts are adjacent under `native-execution/`.

The independent standard-library JSON/Decimal traversal imports no producer and compares every ordered owner, native count type, literal support disposition, age/chronology declaration, full/excluded mass, population total and all six windows. Terminal **731057** exited zero in **0.295 s**, peak RSS **134,660,096 bytes**. Its 1,275-byte check, SHA-256 `710a9747a3d4c29971bf95ae8711610f61a01068a31047d943e64af527ef5623`, and execution facts remain under `artifacts/wetland-source-review/krageholm-regional-source-support/`. Both jobs fit 120 seconds, 512 MiB posthoc RSS and 2 MiB output, with five numeric thread settings at one and bytecode disabled. Neither actual job needed a retry.

Before execution, **90** combined producer/independent synthetic controls passed, with configured Ruff/format and strict types. Earlier test-only parent-directory/import assumptions remain recorded; the first root combined collection lacked the required test-package `PYTHONPATH`, and the corrected invocation passed without changing source or scientific criteria.

From the repository root, the maintained producer can reproduce the audit with an absent output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.essd_reproduction.nordic_coupled.regional_source_support \
  --repository "$PWD" --output "$PWD/artifacts/krageholm-regional-source-support"
```

The separately declared [fixed regional-source study](../krageholm-regional-coupled/README.md) has now consumed this exact nineteen-owner panel. It keeps Krageholm regional-only while excluding complete transitive families of held-out small sites. All eighteen target folds and fifty-four method dispositions remain visible: nine method slots score in 2700–3200 cal BP and forty-five refuse because required local compositions fail. Its independent check qualifies the declared calculation conditional on saved kernels and distances; this source-support audit itself remains unchanged.

No measured vegetation, historical shoreline, basin/core equivalence or regional representativeness has been established. The study's 837 m static-circle profile remains a declared hypothesis. Counts and source ages do not supply missing geometry, rights or qualified field decisions; the completed calculation must not be repeated merely because this source account previously described it as prospective.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** All 96 Krageholm owners and source chronology distinctions are reconciled; nineteen owners provide complete literal Betula29/Ulmus310 support on all six fixed windows, with five out-of-domain missing Ulmus cells preserved.

**Unsupported claim.** An all-96 complete panel, source-absent zeros, unique native default chronology, historical basin or regional representativeness, physical reconstruction, predictions, vegetation accuracy or field admission.

**Actual verification performed.** Producer and independent observer at frozen bb7ea494d both exited zero: all 96 owners, 192 panel slots, 2803 valid pollen cells, 622 non-pollen rows and six windows reconciled. Ninety controlled checks, configured lint/format and strict types pass. Producer .35s/RSS137560064B; observer .295s/RSS134660096B.

**Remaining input or review.** The full 96-owner two-axis aggregate remains unavailable because five older Ulmus literals are missing. The six-window source panel has now been consumed by the separately qualified fixed-regional study; static basin geometry, regional representativeness, physical/parameter applicability and field admission remain separate. Resolver: Source and field experts for historical geometry, rights, parameter applicability or ecological interpretation Reopen when: New source-owned geometry, parameter or independent measured evidence permits a prospectively justified analysis; unchanged source support and the completed fixed-regional study need no rerun.

**Cause category.** data|assumption|comparability

**Consequence.** Complete source-count support permits assessment of a distinct conditional regional-source profile; it supplies no historical geometry, independent observations or field acceptance.

**Precise next acceptance route.** Reuse the independently qualified fixed-regional calculation in reports/science/pollen-reconstruction/krageholm-regional-coupled/README.md, preserving all eighteen folds and fifty-four method dispositions. Qualify physical/parameter assumptions and obtain matched measured vegetation or genuinely untouched evidence for broader acceptance.

**Negative or refused result.** The all-96 Betula/Ulmus aggregate is suppressed for five missing Ulmus entries outside the requested windows. Both source default flags and the different native collection reference remain explicit; no data, age or geometry was repaired.

**Matched denominator.** 96 owners=19 in six windows+77 outside;192 requested panel slots=187 measured+5 missing;91 complete panels. Six-window totals:2010 two-axis counts,18387 full source pollen NISP and16377 excluded counts.

Retained evidence: [reports/science/pollen-reconstruction/krageholm-regional-source-support/protocol.json](protocol.json), [reports/science/pollen-reconstruction/krageholm-regional-source-support/result.json](result.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

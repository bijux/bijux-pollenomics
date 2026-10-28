# SEAD categorical component lineage

This account follows categorical source items into their exact staged parent
observations. A linked category item, the component's nullable fields and the
parent display text are separate source facts. The [compact report](report.json)
keeps all three, together with their source class and type identities.

The governed acquisition is `sead-full-evidence-39bfff6a-ce80714e`. Its build is
`sha256:ce80714e4c9e9974b24913e5da50f49854670ed642879c1ca5076499e1d56725`.
The producer binds 35 source files: admission and acquisition manifests, the
materialization manifest and observation header, six raw relational tables,
and all 25 observation partitions. It checks every parent analysis observation;
it does not repeat provider acquisition or original materialization.

## Source populations and interpretation

| Population | Rows |
| --- | ---: |
| All staged observations scanned | 177,763 |
| All parent analysis values reconciled | 68,705 |
| Categorical components and distinct categorical parents | 4,800 |
| Null component `value` and `is_variant` fields | 4,800 |
| Parent display equals the linked item name | 1,979 |
| Parent display differs from the linked item name | 2,821 |
| Categorical parents with analysis-entity chronology context only | 25 |
| Categorical parents without analysis-entity chronology | 4,775 |
| Eligible events admitted | 0 |

All linked items share the category type declared by their parent value class.
Null component fields do not erase that linked item identity. Conversely, the
item name does not replace the parent display string. For example, source item
`-lw` has parent displays `-LW`, `-lw` and `-lw?`; their distinction survives.
The producer records 15 exact class/item/value/variant/display groups.

The source classes describe 4,695 waney-edge components, 80 earlywood/latewood
components and 25 components concerning SNP capture, damage treatment, library
preparation and molecular sex. Identical item names such as `NO` can occur under
different source types. These counts describe analysis components; they are
not counts of physical specimens, libraries, sequencing assays or people.
No category is translated into an ecological presence/absence observation.

No unit is exposed by the linked source type for these 4,800 components. The
25 chronology-context links provide neither an eligible chronology claim nor
an ecological event. All 68,705 parent observations preserve refused event
eligibility and `source_classification_not_accepted`.

## Reproduce

From the repository root, with an absent artifact destination:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --frozen python -m \
  bijux_pollenomics_dev.source_completion.sead.categorical_values \
  --repository "$PWD" \
  --output "$PWD/artifacts/sead-categorical-lineage/report.json"
```

Compare the output bytes with the governed report. The producer refuses changed
source hashes, missing or repeated parent keys, altered categorical components,
item/class type mismatches, changed units or chronology support, promoted event
eligibility, unsafe destinations and existing outputs. It checks all consumed
source hashes again before publication; it does not lock external source files
against concurrent writes. Source continuity supplies no new rights grant,
biological interpretation, specimen identity or independent scientific decision.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** Categorical item identities, nullable component fields and parent displays survive as distinct source values and types.

**Unsupported claim.** Category components are not specimens, libraries, assays, people, presence/absence or eligible dated events.

**Actual verification performed.** Read the 4,800-component report, 15 groups, display differences and context-only chronology links; no source component consumer rerun.

**Remaining input or review.** Source class/entity interpretation, units, taxonomy and chronology/event admission require qualified review.

**Cause category.** Categorical source semantics cannot be inferred from label resemblance.

**Consequence.** The 2,821 display/item differences and null component fields must remain intact.

**Precise next acceptance route.** Review each source type/class/entity and obtain qualified chronology/ecological meaning before any event mapping.

**Negative or refused result.** 25 chronology links are context only; 4,775 lack entity chronology; all event eligibility refused.

**Matched denominator.** 4,800 distinct component parents of 68,705 analysis values; 1,979 display matches/2,821 differences; 4,800 unexposed units; 0 events.

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-categorical-values/report.json](report.json) (SHA-256 `8ada887dccab478198935df6aa273f96d7422eb73f062be582bb5b121db7131e`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

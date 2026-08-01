# Repository SEAD legibility review

This report-root packet explains what the repository can currently claim about SEAD and what still depends on thinner source capture or upstream inspection.

- Source family: `SEAD archaeology context`
- Current posture: `contextual_archaeology_layer_with_explicit_temporal_and_access_limits`
- Reviewed rows: `2195`

## Normalization Risk

- medium access constrained: `1448`
- medium contextual numeric mix: `735`
- medium period label interpretation: `12`

## Access Visibility

- site page only: `2192`
- site page with reference links: `3`

## Temporal Postures

- contextual label only: `12`
- mixed interval and context: `497`
- numeric interval: `154`
- numeric interval with caveat: `238`
- unresolved: `1294`

## Direct Links

- source_page: `docs/public/pollenomics-data/sources/sead.md`
- handbook_page: `docs/public/pollenomics-data/sources/sead-handbook.md`
- normalized_output_page: `docs/public/pollenomics-data/publications/sead-exports.md`
- access_model: `data/sead/review/access_model.json`
- evidence_review: `data/sead/review/evidence_legibility_review.json`
- recovery_requirements: `data/sead/review/recovery_requirements.json`

## Recovery Requirements

| Requirement | Required evidence | Satisfaction signal |
| --- | --- | --- |
| linked_temporal_promotion | Promote captured SEAD dating-range, calendar-era, and relative-period rows into normalized BP intervals wherever the linked inventory supports it, while keeping unresolved rows explicit. | SEAD temporal review shows numeric intervals for chronology-bearing rows and leaves unresolved site inventory rows visibly unresolved instead of implying uniform time support. |
| reference_visibility_promotion | Promote preserved bibliography or DOI links wherever checked-in SEAD linked records expose them, and keep site-page-only rows explicit where upstream link visibility remains thin. | The access review distinguishes bibliography-backed rows from site-page-only rows without hiding the remaining upstream access constraint. |
| context_layer_republication | Republish the normalized SEAD context layer with explicit temporal semantics, access posture, and context-only caveats on every feature. | Normalized and published SEAD GeoJSON no longer trigger missing-temporal-semantics findings in report review surfaces. |
| published_scope_refresh | Refresh published world, Europe-plus, and Nordic report bundles so SEAD appears as a bounded archaeology context layer rather than a generic environmental blob. | Published map and review bundles expose SEAD with stable caveats, access wording, and bounded contextual role labels. |

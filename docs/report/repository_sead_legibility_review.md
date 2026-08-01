# Repository SEAD legibility review

This report-root packet explains what the repository can currently claim about SEAD and what still depends on thinner source capture or upstream inspection.

- Source family: `SEAD archaeology context`
- Current posture: `contextual_archaeology_layer_with_explicit_temporal_and_access_limits`
- Reviewed rows: `2195`

## Normalization Risk

- medium access constrained: `1447`
- medium contextual numeric mix: `748`

## Access Visibility

- site page only: `2192`
- site page with reference links: `3`

## Temporal Postures

- mixed interval and context: `509`
- numeric interval: `157`
- numeric interval with caveat: `239`
- unresolved: `1290`

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
| unresolved_chronology_boundary | Retain sites without captured upstream chronology as an explicit spatial-only population; add dates only when a linked SEAD chronology record supplies defensible bounds. | Every captured chronology row has normalized BP bounds, the temporal-evidence layer is fully time-filterable, and upstream-undated sites remain visibly unresolved. |
| unreferenced_site_boundary | Retain site-page-only access where captured bibliography rows expose no directly followable DOI or URL; add links only from identified SEAD bibliography values. | All captured bibliography relations preserve their source relation and sites without directly followable upstream links remain explicit instead of receiving inferred URLs. |
| context_layer_republication | Republish the normalized SEAD context layer with explicit temporal semantics, access posture, and context-only caveats on every feature. | Normalized and published SEAD GeoJSON no longer trigger missing-temporal-semantics findings in report review surfaces. |
| published_scope_refresh | Refresh published world, Europe-plus, and Nordic report bundles so SEAD appears as a bounded archaeology context layer rather than a generic environmental blob. | Published map and review bundles expose SEAD with stable caveats, access wording, and bounded contextual role labels. |

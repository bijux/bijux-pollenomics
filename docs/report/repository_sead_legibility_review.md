# Repository SEAD legibility review

This report-root packet explains what the repository can currently claim about SEAD and what still depends on thinner source capture or upstream inspection.

- Source family: `SEAD archaeology context`
- Current posture: `contextual_archaeology_layer_with_explicit_temporal_and_access_limits`
- Reviewed rows: `2195`

## Normalization Risk

- high thin site inventory: `2195`

## Access Visibility

- site page only: `2195`

## Temporal Postures

- unresolved: `2195`

## Direct Links

- source_page: `docs/02-bijux-pollenomics-data/sources/sead.md`
- handbook_page: `docs/02-bijux-pollenomics-data/sources/sead-handbook.md`
- normalized_output_page: `docs/public/pollenomics-data/publications/sead-exports.md`
- access_model: `data/sead/review/access_model.json`
- evidence_review: `data/sead/review/evidence_legibility_review.json`
- recovery_roadmap: `data/sead/review/recovery_roadmap.json`

## Recovery Roadmap

| Deliverable | Goal | Completion signal |
| --- | --- | --- |
| linked_temporal_capture | Capture linked dating-range, relative-period, and uncertainty tables into checked-in raw SEAD inventory refreshes. | Checked-in raw SEAD rows carry temporal linked tables often enough that the thin-site-inventory risk no longer dominates the review packet. |
| reference_link_capture | Preserve stable bibliography or DOI links wherever SEAD linked records expose them, so readers do not have to begin every review from the generic site page. | The access review shows a meaningful shift away from site-page-only visibility. |
| context_layer_republication | Republish the normalized SEAD context layer with explicit temporal semantics, access posture, and context-only caveats on every feature. | Normalized and published SEAD GeoJSON no longer trigger missing-temporal-semantics findings in report review surfaces. |
| published_scope_refresh | Refresh published world, Europe-plus, and Nordic report bundles so SEAD appears as a bounded archaeology context layer rather than a generic environmental blob. | Published map and review bundles expose SEAD with stable caveats, access wording, and bounded contextual role labels. |

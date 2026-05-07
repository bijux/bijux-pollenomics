# Animal sample aggregation warnings

- Project accession anchors: `36`
- Accession-range anchors: `2`
- Sample accession anchors: `2`
- Project-locality summaries: `10`
- Projects with project-level sample anchors: `38`
- Projects with locality count drift: `0`
- Species with summary count drift: `0`

- `project_level_sample_anchors`: `38`. Projects whose current sample rows are still anchored at project or accession-range level rather than true per-sample identifiers.
- `project_locality_summary_rows`: `10`. Locality rows that are still summarized at project-locality level rather than explicit per-sample site rows.
- `locality_count_drift`: `0`. Projects where project-level locality summaries disagree with sample-backed site counts.
- `species_summary_count_drift`: `0`. Species summaries that disagree with the current sample-master counts.

# Context occurrence chronology

A numeric site span does not establish an occurrence inside that span. Analytical
ranking, evidence richness and scientific-review overlap use the shared
`collection.contracts.occurrence_chronology` contract. It requires explicit numeric
comparability with no refusal and consistent declared bounds. LandClim sequence
coverage, SEAD site envelopes, Neotoma site extrema and nearby navigation summaries
remain spatial and source-availability context. Individual SEAD dating and dendro
records and explicitly declared model windows retain their own eligible supports.
This classification does not infer an epoch, calibration or source authentication.

A `ContextPointRecord` remains one spatial record. Its optional
`occurrence_supports` retain individually validated component identifiers, bounds
and source semantics; `source_record` retains the literal input metadata at that boundary and the
native identifiers it declared. The atlas adapter populates these only after the existing
source-schema reader validates membership. Missing or refused members remain in
the source record. A whole-record contextual or refused declaration constrains all
members. An explicitly empty component collection cannot fall back to its coverage
hull.

Overlap tests use the union of admitted members. They preserve gaps and count one
point per query even when several members overlap. Nearby context summaries count
each point once per navigation window. Their displayed summary window remains
navigation context and does not become a lake-owned or sample-owned date.

Spatial-only input omits `temporal_semantics`; consumers use optional access.
Explicit empty, contextual and refused declarations retain their separate meanings.
The fieldwork documentation layer therefore remains visible without inventing ages.

Context CSV and GeoJSON keep their existing output when optional source data is
absent. Where present, CSV adds JSON-valued `occurrence_supports_json` and
`source_record_json` cells, requiring explicit JSON decoding. GeoJSON preserves
the original named source schema, owned sample components and native metadata,
with independently retained source provenance. Re-reading validates the current
source fields rather than trusting nested provenance as permission. Each boundary
retains its literal input; repeated transport can retain earlier provenance inside
that input. Physical source attachment identity remains in its separate
traceability receipt.

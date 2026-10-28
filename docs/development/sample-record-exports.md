# Sample record exports

Standalone sample JSON, CSV and GeoJSON use the version 2 sample contract by
default. Existing flat identifiers and date columns keep their values. Two
additional fields preserve the information required to interpret those values:

- `sample_chronology` contains the exact source chronology, dating basis,
  uncertainty text, evidence class, precision, refusal, source release and
  chronology provenance. Reference epoch, age type, calibration and model remain
  `not_separately_declared` when the normalized sample does not declare them.
- `sample_identity` retains the stable namespace/token, source-native sample and
  experiment identifiers, publication/table labels and their identity lineage.

JSON and GeoJSON carry these fields as objects. CSV carries each object as a JSON
cell; parse it with a JSON reader after reading the CSV. JSON `null` endpoints
remain distinct from genuine numeric zero. Refused, negative, reversed and
context-only source values are preserved as source assertions. Exporting a value
does not admit it as comparable chronology or approve a date transformation.

The default schema identifiers are `adna-sample-record-export.v2`,
`adna-sample-geojson.v2` and `adna-sample-geojson-collection.v2`. A GeoJSON
collection uses matching feature and property versions. Locality exports retain
their separate version 2 contract and display-only coverage hull.

Consumers that require the previous flat projection may explicitly request
`schema_version="adna-sample-record-export.v1"` from `serialize_sample_record` or
`write_samples_csv`. The GeoJSON builders and writer accept their corresponding
version 1 schema identifiers. These legacy projections omit the added metadata;
use version 2 for source chronology interpretation and round trips. Unsupported
versions fail before an export writer creates its file.

## Reading exported chronology

The generic atlas and external point readers recognize the named sample export
schemas. Preferred sample v2 validates the singular `sample_chronology` support,
its original precision and refusal, and the agreement of flat dates and native
identity with `sample_identity`. A conflicting projection or unsupported schema
is refused. An explicit v1 projection is contextual: its missing fields were not
carried by that projection, which does not establish that the original source
lacked them. Numeric use requires the complete v2 record or a separately qualified
source reconstruction.

External point views retain the literal latest input properties in `source_record`,
along with owned chronology, native identities, and declared envelope versions.
Refused or contextual numeric views have null BP fields while the original source
values remain intact. `feature_has_time` follows eligibility rather than the
presence of a number. Declared sample `political_entity` also supplies the country
filter label when no country is declared; conflicting declared labels are refused,
and unavailable geography remains unavailable. Source epoch, calibration, model and method are never
invented by an adapter.

Declared sample GeoJSON collection, feature and property versions must agree.
Ordinary unversioned GeoJSON envelopes may contain an explicitly versioned record;
ordinary layer labels are still required by the external point API. CSV JSON
cells require their explicit source decoder and are not coerced by GeoJSON input.

Locality v2 uses plural `sample_chronologies` and explicit native `sample_ids`.
Standalone records also retain `locality_identity`, including the native locality
namespace/token, source anchor tokens and declared `political_entity`. The latter
also remains a flat geographic display field. Maintained wrapper rows retain
their existing `identity` object. External readers preserve these source objects
and project declared geography into the country filter; conflicting duplicate
identities or nonempty geographic labels are refused. Locality CSV carries
`locality_identity` as a JSON-valued cell. Its flat nullable geographic text has
the ordinary one-way CSV null-to-empty projection, while the nested JSON identity
retains null; an empty text cell never restores an inferred source null.
`locality_export_records` reads the maintained `localities` wrapper and propagates
its version to record views. The browser equivalent is `localityExportRecords`.
A wrapper is not a single observation. Admitted member supports retain their gaps;
the locality coverage hull remains a display extent. Legacy locality v1 remains
contextual even when its flat display bounds are populated.

Schema-less numeric fields without a comparison posture are contextual. Zero
remains a retained source assertion and is distinct from missing chronology;
it does not establish numeric eligibility. Declaring empty `temporal_semantics`
also grants no permission. Only an explicitly eligible numeric posture, a
validated owned support, or an independently authorized typed calendar contract
can admit numeric use. The separate `source-pollen-record-export.v1`
chronology-claim format keeps its own contract.

Preferred named source identities also supply operational map row IDs, encoded as
a JSON pair of the exact native namespace and stable token. This preserves distinct
co-located records with the same display name through atlas extraction and temporal
summary references. Display names remain source labels. Generic external point
identity behavior is unchanged; a legacy locality projection without native identity
cannot reconstruct it from names or coordinates.

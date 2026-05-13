# Animal sample product contract

- Primary durable unit: `sample_record`

## Required fields

| Field | Meaning |
| --- | --- |
| identity.stable_token | stable sample identifier inside the repository |
| species_latin_name | species assignment carried by the sample row |
| project_accession | archive project or accession family anchor for the sample |
| paper_doi_or_paper_url | primary publication anchor for the sample claim |
| supplementary_source_or_supporting_source_url | supporting file or source artifact behind location or sample detail |
| locality_identity.locality_text | site or locality label attached to the sample |
| chronology.original_text | raw chronology claim kept before normalization |
| chronology.time_start_bp | older bound of the normalized BP interval when defensible |
| chronology.time_end_bp | younger bound of the normalized BP interval when defensible |
| coordinates.latitude_text | latitude text retained from direct coordinates or later resolution |
| coordinates.longitude_text | longitude text retained from direct coordinates or later resolution |
| coordinate_basis | how the repository derived or withheld coordinates for the sample |
| coordinates.confidence | confidence class carried by the coordinate claim |
| inclusion_status | current publication posture or blocking state for the sample row |

## Reader questions answered

- which sample exists
- which species it belongs to
- which project and paper describe it
- which supporting source anchors its site claim
- what chronology claim the repository keeps
- what coordinate basis and confidence the repository keeps
- whether the row is publishable, blocked, or still weak

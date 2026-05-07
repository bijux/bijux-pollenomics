# Animal aDNA Layout

`data/adna/` is the checked animal aDNA evidence root. It keeps three owned
entrypoints:

- `species/` holds species-owned evidence chains, one root per Latin-name slug
- `governance/` holds cross-species audits, source registries, caveat ledgers,
  and publication contracts
- `final/` holds shared downstream atlas-ready and country-ready animal outputs

## Entry Points

- [`species/equus_caballus/README.md`](species/equus_caballus/README.md)
- [`species/ovis_aries/README.md`](species/ovis_aries/README.md)
- [`governance/source_library/project_registry.json`](governance/source_library/project_registry.json)
- [`governance/animal_sample_product_contract.json`](governance/animal_sample_product_contract.json)
- [`governance/path_ownership_map.md`](governance/path_ownership_map.md)
- [`final/atlas/animal_atlas_point_candidates.json`](final/atlas/animal_atlas_point_candidates.json)
- [`final/countries/country_publication_index.json`](final/countries/country_publication_index.json)

## Meaning

The durable unit is the sample-backed evidence chain, not the project and not
the map point.

- `species/` answers what sample, site, chronology, and coordinate evidence the
  repository actually owns
- `governance/` answers whether that evidence is coherent, traceable, and safe
  to publish
- `final/` answers which shared downstream outputs were derived from that
  evidence

If a file does not fit one of those three roles, it is in the wrong place.

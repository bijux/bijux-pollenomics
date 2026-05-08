# Repository atlas input audit

- Atlas input rows: `6`

| Atlas input | Domain role | Refresh anchor | Tracked metrics | Note |
| --- | --- | --- | --- | --- |
| LandClim pollen context | `primary_domain` | `data/landclim/normalized/landclim_summary.json` | `site_count` 492, `grid_cell_count` 88 | LandClim is a first-class pollen context family, not generic map decoration. |
| Neotoma pollen context | `primary_domain` | `data/neotoma/raw/neotoma_pollen_sites.json` | `site_count` 200 | Neotoma broadens the pollen story with its own site inventory and should remain distinct from LandClim. |
| SEAD archaeology context | `contextual_domain` | `data/sead/raw/nordic_sites.json` | `site_count` 2195 | SEAD is broader environmental archaeology context and should stay visible as its own source family. |
| RAÄ archaeology context | `contextual_domain` | `data/raa/normalized/sweden_archaeology_layer.json` | `published_site_count` 761917, `density_cell_count` 106 | RAÄ is explicitly Sweden-scoped and should never be mistaken for Nordic-wide archaeology coverage. |
| Nordic boundary framing | `framing_domain` | `data/boundaries/normalized/nordic_country_boundaries.geojson` | `country_feature_count` 4 | Boundary geometry is framing, not scientific evidence, but it still changes how every mapped layer is interpreted. |
| Animal aDNA publication surface | `contextual_domain` | `docs/report/animal_sample_database_review.json` | `published_point_count` 234, `unresolved_row_count` 21 | Animal aDNA is still a partial recovery program whose public map surface depends on sample-owned support packets and release gates. |

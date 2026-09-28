# Swedish native pollen against the LandClim II author lookup

The [39-bin result](bins.csv) applies the authors' published
[LandClim II taxonomy lookup](https://github.com/rmfyfe/landclimII/blob/57ead2e2fcc493d099be4e5a3092fc396e1c3d3a/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv)
to the same three native `NISP` datasets used in the
[held-out Swedish direct-pollen study](../../../pollen-reconstruction/swedish-direct-pollen/REPORT.md).
The lookup is already held in the external LandClim author-reference bundle;
its SHA-256 is
`3a745f9b7606e5d0b59feaba2683b930c8d3990e4810f8217b69160a29a1b507`.
The [authors' preparation-code description](https://github.com/rmfyfe/landclimII/blob/57ead2e2fcc493d099be4e5a3092fc396e1c3d3a/README.md)
calls this the synonym table for harmonizing taxonomy. The
[method paper](https://essd.copernicus.org/articles/14/1581/2022/), Sect. 2.2,
states that pollen morphological types were harmonized into 31 RPP taxa.

| Site | Native NISP | Author-assigned | Author-excluded | Unmapped | Assigned fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Abborrtjärnen | 88,004 | 86,691 | 1,311 | 2 | 98.5080% |
| Bussjösjön | 56,450 | 40,915 | 9,277 | 6,258 | 72.4801% |
| Bökesjön | 42,548 | 41,407 | 1,110 | 31 | 97.3183% |

The lookup has 10,788 rows, 9,731 distinct source strings and 31 assigned
targets in addition to `zz.do not use` and an age-field target. Duplicate
source strings agree on their target. Exact source strings map `Alnus` to
`Alnus glutinosa`, `Corylus` to `Corylus avellana`, `Quercus` to
`Quercus deciduous`, and `Poaceae` to `Poaceae`. Those assignments recover
large counts that the separate [literal parameter-name screen](../parameter-coverage/README.md)
could only mark unmatched. The lookup also explicitly excludes names such as
`Humulus/Cannabis` (4,647 BUS counts). Its listed `Poaceae undiff.` string
does **not** cover BUS `Poaceae undiff. (<40 µm)` (6,096 counts) or
`Poaceae undiff. (>40 µm)` (158 counts); those remain unmapped without a
source-backed, size-specific decision.

The author lookup does explicitly assign its separate spellings
`Poaceae undiff. <40um` to `Poaceae` and `Poaceae undiff. >40um` to
`Cerealia-t`. These are source-witnessed candidates for the two BUS labels,
which differ in punctuation and the micrometre symbol. If those two name
variants were accepted, **6,254** BUS counts would move from unmapped mass:
6,096 to `Poaceae` and 158 to `Cerealia-t`. The BUS author-assigned fraction
would rise from **72.4801%** to **83.5589%**. The governed bin and site
results retain that scenario in separate candidate fields; the actual author
lookup counts and the **6,258** unmapped BUS counts remain unchanged. No
other name is normalized by this rule.

The exclusion is especially consequential in BUS bin **500–1000 cal BP**:
`Humulus/Cannabis` contributes **3,369 of 7,175** native NISP counts
(**46.9547%**) there. In bin **0–500 cal BP** it contributes **1,254 of
9,341** counts (**13.4247%**). These are direct native source counts in the
enumerated [exclusions](../../../pollen-reconstruction/swedish-direct-pollen/exclusions.csv),
not vegetation percentages. A 31-target reconstruction would address the
author-selected pollen subcomposition, with markedly different retained mass
across these two bins; the excluded taxon must remain visible in any score or
interpretation.

These are **author lookup assignments**, not an independently reviewed
biological identification or a numerical reconstruction. The lookup target
names are not identical to every published PPE/FSP parameter label; for
example it emits `Quercus deciduous` and `Picea`, while the parameter table
uses `Quercus deciduous t.` and `Picea abies`. The separate
[author parameter binding](../author-parameter-binding/README.md) resolves
the exact target-to-RPP/FSP correspondence in the retained author code
profile. Applying it to Neotoma still requires a complete counting-denominator
decision and sample-time basin geometry. In particular the
[Bussjösjön basin review](../bussjosjon-basin/README.md) records a material
coordinate conflict. **No Swedish LRA sample is admitted.**

The [report](report.json) retains the 31 target count totals, leading excluded
and unmapped source names for each site, source identities and exact output
CSV hash. Replay from the repository root with the already retained external
author-reference bundle:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass \
  --repository . \
  --author-source-root ../bijux-pollenomics-data/landclim/author-reference \
  --output artifacts/jobs/landclim-taxonomy-mass/replay
```

Compare the replayed `bins.csv` and `report.json` byte-for-byte with this
directory. The producer refuses changed lookup bytes, conflicting duplicate
names, changed Swedish source scope and any native count that fails to close.

# Solsø 1981 core area and radiocarbon lineage

The [primary EPD/PANGAEA age dataset](https://doi.pangaea.de/10.1594/PANGAEA.740759)
explicitly identifies event `SOLSOE81`, a central 1981 Livingstone core, and
reports **Area: 2.5 ha**. This is the same numeric area and unit as the
[LandClim I Solsø site row](../README.md). The source describes the lake as
strongly drained and now mostly fen. Its area is a source-reported core-site
attribute, not a dated historical lake shoreline.

The [source-bound control join](report.json) compares all **34** primary
radiocarbon rows with the retained Neotoma controls for collection unit 4303.
It matches **30** distinct primary lab controls exactly on lab number, depth
(metres to centimetres), uncalibrated radiocarbon age and both errors (ka to
years BP), and δ13C. Those controls occupy **54** Neotoma control rows because
24 recur in both Neotoma chronologies. The primary labels `K-3970`, `K-4012`,
`K-4016` and `K-5634` have no retained Neotoma control; there are no conflicting
values for primary labels that are present. The two remaining Neotoma control
rows are not counted as primary radiocarbon matches.

This establishes a strong 1981 core and age-control relationship. The
LandClim II 79-sample sequence still lacks an authenticated sample/core join
to either of the two Neotoma cores and uses an author chronology. A 2.5 ha
site area cannot supply an age-specific basin radius or correct historical
water-level change. **Zero Solsø samples are admitted to LRA** from this join.

The 3,574-byte primary text source (SHA-256
`9934dd802fa7b7094c2a6cc08fff90ef29c1c630a092787c4f4a3aac96be6be0`)
is retained under `landclim/pangaea/solsoe/` in the external source store.
PANGAEA attributes the dataset to Bent V. Odgaard and the European Pollen
Database under CC BY-NC 3.0; the raw source is not redistributed in this
repository. The governed report pins both that source and the Neotoma
relational control part.

Reproduce from the repository root into an absent artifacts directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.solsoe_core_age_lineage \
  --repository . \
  --source-root /Users/bijan/bijux/bijux-pollenomics-data \
  --output artifacts/jobs/solsoe-primary-core-age-replay
```

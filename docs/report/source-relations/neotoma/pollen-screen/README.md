# Neotoma pollen prerequisite screen

The [summary](summary.json) and [sample decisions](report.json) preserve the
source-bound screen for the corrected relational snapshot. It reads the
authenticated raw Neotoma/EPD capture and the governed relational materialization.
The source snapshot and build IDs are unchanged; the relational manifest is
`6f6777a40b67bd0704eb1a982f19e6d451cad0d6e4a41dfebf5e3f28be33105b`.

The screen requires an agreeing pair of source `pollen` element labels, a finite
integer count and a sample-owned comparable typed age. It finds 10,637 necessary
candidate samples: Denmark 91, Finland 1,797, Norway 3,544, Sweden 5,011 and
unassigned 194. The five partitions sum to 12,388 captured samples, with 1,751
distinct refusals. The complete report retains source row locators and reasoned
sample decisions, including alternatives rather than silently choosing an age.

The chronology projection now follows [Neotoma's rule](https://open.neotomadb.org/manual/chronology-age-related-tables-1.html)
of one default chronology per age type. The previous cross-age-type conflict
classification suppressed valid count observations; the corrected materialization
retains 32 chronology-control payload conflicts and one genuine same-age-type
default conflict. This screen is a prerequisite, not an LRA input or an accepted
taxon/PPE/basin/denominator decision. No LRA or measured-vegetation result is
claimed.

## Reproduce

Run the installed `inspect_neotoma_lra_pollen_screen` consumer against
`data/neotoma/raw/neotoma_pollen_dataset_downloads` and
`data/neotoma/relational`. The retained summary binds both exact manifests;
compare those identities and the candidate sample ID digest before reusing a
rerun. The [Nordic direct-pollen result](../../../regions/nordic/direct-pollen/RESULTS.md)
is a separate observed-pollen study with its own age selection and held-out
country procedure.

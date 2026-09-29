# Reindeer published Appendix S1 specimen correspondence

The [Molecular Ecology article](https://doi.org/10.1111/mec.17274) lists
`mec17274-sup-0001-Appendix S1.zip` as its supporting information and names
Table S3 as the sample metadata source for ENA project `PRJEB60484`.
A user-supplied archive with that filename was retained in the governed
[source library](../../../../data/adna/governance/source_library/papers/10.1111-mec.17274/supplementary/mec17274-sup-0001-Appendix%20S1.zip).
Its SHA-256 is
`179ce63b79122e62017c8df8433379929f8c160f399ff44969ef05917ad734c9`.
All four loose files supplied with the archive match the ZIP members byte for
byte. Wiley's direct ZIP request returned HTTP 403, so matching the listing
does **not** independently establish publisher byte parity. The source receipt
records this limit.

The extracted `mec17274-sup-0003-Table S3.xlsx` is SHA-256
`81cc00377f5898004b8f4f724c0aa1b787fdb30d7df9874b31f1a27241268462`.
Its populated rows contain 110 specimens: 90 modern and 20 ancient.
Eighteen ancient Svalbard rows occur at Excel rows 3–20; two Franz Josef Land
specimens, FJL1a and FJL3, occur at rows 111–112. All 20 ancient rows name
`PRJEB60484` in column O and join one-to-one to the retained ENA BioSample
aliases. The governed sample-master outputs now preserve each published row
alongside earlier evidence; the chronology selection for R20 retains the
primary 0–450 BP interval and records the later narrower reanalysis separately.

The previously retained [author preprint Table S3](reindeer-preprint-supplement.md)
has 108 populated rows (90 modern, 18 ancient). The published table adds
FJL1a and FJL3. Among 108 shared specimen IDs, 90 changes in column N add
the citation year, all 108 column O values add the project accession, and
two column M sequencing labels differ. The published table does not add an
independent vegetation or pollen observation; it strengthens specimen-level
source attribution for the aDNA comparator.

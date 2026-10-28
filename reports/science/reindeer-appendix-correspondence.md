# Why we use the published reindeer appendix for specimen identity

## Our source decision

The [Molecular Ecology article](https://doi.org/10.1111/mec.17274) lists
`mec17274-sup-0001-Appendix S1.zip` as its supporting information and names
Table S3 as the sample metadata source for ENA project `PRJEB60484`.
We retained a user-supplied archive with that filename in the governed
source library at
`data/adna/governance/source_library/papers/10.1111-mec.17274/supplementary/mec17274-sup-0001-Appendix S1.zip`.
Its SHA-256 is
`179ce63b79122e62017c8df8433379929f8c160f399ff44969ef05917ad734c9`.
We found that all four loose files supplied with the archive match the ZIP
members byte for byte. Wiley's direct ZIP request returned HTTP 403, so matching the listing
does **not** independently establish publisher byte parity. The source receipt
records this limit.

We identified the extracted `mec17274-sup-0003-Table S3.xlsx` by SHA-256
`81cc00377f5898004b8f4f724c0aa1b787fdb30d7df9874b31f1a27241268462`.
Its populated rows contain 110 specimens: 90 modern and 20 ancient.
Eighteen ancient Svalbard rows occur at Excel rows 3–20; two Franz Josef Land
specimens, FJL1a and FJL3, occur at rows 111–112. All 20 ancient rows name
`PRJEB60484` in column O and join one-to-one to the retained ENA BioSample
aliases. We preserve each published row in the governed sample master
alongside earlier evidence; the chronology selection for R20 retains the
primary 0–450 BP interval and records the later narrower reanalysis separately.

## What we found across versions

The [author preprint Table S3](../../docs/report/source-relations/dna-scope/reindeer-preprint-supplement.md)
has 108 populated rows (90 modern, 18 ancient). We compared it with the
published table, which adds
FJL1a and FJL3. Among 108 shared specimen IDs, 90 changes in column N add
the citation year, all 108 column O values add the project accession, and
two column M sequencing labels differ. The published table does not add an
independent vegetation or pollen observation; it strengthens specimen-level
source attribution for the aDNA comparator.

We also retained an alternate article PDF (SHA-256
`cf4a27fb5c32fef13b024b43145e9fe7e2975c02acf2ffae3b754c2f77d8cd84`)
and a mitogenome FASTA (SHA-256
`fae6416e162e3fc66f552b3cb49803f2b4050006bd8c55785fe9544ccdd424da`).
The PDF embeds the article DOI. The FASTA has 112 records, each 16,362 bases;
the [Dryad record](https://doi.org/10.5061/dryad.tht76hf5n) lists its exact
filename as the study's final mitogenome alignment. Both user-supplied files
and a custody manifest are retained under
`bijux-pollenomics-data/adna/prjeb60484/published-article-and-alignment/`.
Direct publisher and Dryad byte parity remain unverified. These two files are
not consumed by the sample-master join or treated as new specimens.

## What remains limited

We matched FASTA headers to all **110** published Table S3 specimen labels:
49 match exactly, 60 match after removing one or more leading `Svalbard_`
prefixes, and `T11` corresponds to the table's `T-11` spelling. All 20
ancient Table S3 labels match FASTA headers exactly. Two additional FASTA
headers, `B16` and `Svalbard_B-64`, have no separate published Table S3 row;
`B16` must not be silently merged with the distinct `B-16` header. These
are header-level correspondences only. They do not establish the origin of
the two additional sequences, sequence quality, or independent biological
specimens. We used the retained Table S3 and FASTA bytes with the hashes
above, counting populated Table S3 rows and FASTA `>` headers.
The `B16` and `B-16` alignment strings differ at 2,863 of 16,362 positions;
neither extra header duplicates another complete sequence in this file.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Published reindeer appendix Table S3 can be joined to retained ENA BioSamples for named specimens.

**Unsupported claim.** Unqualified specimen history or ecological movement from header-level correspondences.

**Actual verification performed.** Retained appendix/version comparison and BioSample one-to-one join are reported; index did not reacquire ZIP.

**Remaining input or review.** Appendix version comparison supports specimen IDs but selected header correspondences do not prove every sample-to-source provenance or independent ecological interpretation. Resolver: Reindeer study data custodian and qualified specimen reviewer Reopen when: Versioned row-level specimen and accession authority resolves ambiguous source associations before propagation.

**Cause category.** data|qualified review

**Consequence.** Use the appendix for specimen identity only until provenance and scientific interpretation are reviewed.

**Precise next acceptance route.** Versioned row-level specimen and accession authority resolves ambiguous source associations before propagation. Then update reports/science/source-cohorts.md.

**Negative or refused result.** Wiley direct ZIP HTTP 403; no claim that all header correspondences establish sample origin.

**Matched denominator.** 110 populated rows: 90 modern and 20 ancient; 20 ancient rows join one-to-one to retained ENA BioSamples.

Retained evidence: [docs/report/source-relations/dna-scope/reindeer-preprint-supplement.md](../../docs/report/source-relations/dna-scope/reindeer-preprint-supplement.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

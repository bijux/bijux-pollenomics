"""Source-defined project populations and unresolved denominator boundaries."""

from __future__ import annotations

from bijux_pollenomics.adna.workflow.paths import ADNA_SOURCE_LIBRARY_DIR

from ..models import _ProjectIntakeExpectation


def population_expectation(project_accession: str) -> _ProjectIntakeExpectation | None:
    """Keep source-population authority separate from archive capture counts."""
    if project_accession == "PRJEB31613":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The retained Cell article Results and Table S1 describe 278 "
                "ancient equids: 245 horses, 27 mules, three asses and three "
                "hemiones. The 87 new high-coverage horse genomes are an "
                "analysis subset. Data Availability assigns aligned sequencing "
                "data to PRJEB31613 without equating the project to that subset "
                "or the horse-only master. The archive capture contains 440 "
                "runs across 223 BioSamples: 190 Equus caballus, 27 hybrids, "
                "three asses and three hemiones. These distinct populations "
                "do not close a project-wide specimen denominator or establish "
                "that 55 horses are missing from the archive."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.cell.2019.03.049/"
                "supplementary/1-s2.0-S0092867419303848-mmc1.xlsx"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Preserve all 245 horse master rows and the full mixed-equid "
                "source population. Resolve specimen-owned author/native "
                "accession correspondence and the new/reused/deposited scope "
                "without counting hybrids as horses, selecting the 87-genome "
                "analysis subset as the project, or inferring biological gaps."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJEB22390":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The retained Science supplement p.2 selects 42 ancient horse "
                "samples from 17 sites for deeper sequencing after low-depth "
                "screening, without enumerating all screened remains. Page 13 "
                "assigns alignments to PRJEB22390 and describes 156 libraries "
                "(one to seven per sample), including 154 USER-treated libraries. "
                "Forty-two selected genomes, 156 technical libraries and the "
                "captured 42 runs/BioSamples are separate populations; they "
                "do not establish the initial screening denominator or an "
                "exhaustive project deposition roster."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aao3297/"
                "supplementary/aao3297_gaunitz_sm.pdf"
            ),
            sample_identifier_status="manual_curation_required",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Preserve all 42 recovered sample rows and their independent "
                "dating evidence. Recover source-owned screening and deposition "
                "scope before defining a project expectation; do not count "
                "libraries as animals or infer failed and missing specimens "
                "from technical library counts."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJEB19970":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The retained 2017 primary supplement Table S12 lists fourteen "
                "new ancient genomes, separately from thirty-eight comparators; "
                "p.2 assigns shotgun reads to PRJEB19970. The retained archive "
                "contains 241 run records and fourteen BioSamples. The later "
                "2019 comparative workbook labels fifteen rows with this project: "
                "thirteen ancient horses and two modern outgroups. Its omission "
                "of BER11_L is resolved by the primary table and thirteen native "
                "run filenames joining SAMEA103910520, making sixteen curated "
                "source records without establishing sixteen independent animals "
                "or a closed project denominator."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aam5298/"
                "supplementary/aam5298_librado.sm.pdf"
            ),
            sample_identifier_status="manual_curation_required",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Preserve all fifteen later-workbook rows and the separate "
                "primary BER11_L-to-BioSample join. Resolve the remaining "
                "author-registration/native-accession correspondence and modern "
                "outgroup deposition scope before defining a project denominator. "
                "Do not infer CGG aliases, remove comparators, count files as "
                "animals, or turn the Table S12 date label into a precise date."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJNA1328209":
        return _ProjectIntakeExpectation(
            expected_sample_count=5,
            expected_sample_count_status="known_from_source_table",
            expected_sample_count_provenance=(
                "The retained primary article reports genomic data generated "
                "from five Lake Qinghai Basin goat remains, with three retained "
                "after authentication and filtering for population analysis. "
                "Supplementary Table S2 lists all five source sample labels. "
                "This generated-source population is not the three-genome "
                "analysis subset or an authenticated native-accession crosswalk."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.24272-j.issn.2095-8137.2025.080/"
                "supplementary/Supplementary_tables.xlsx"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Preserve the five Table S2 source labels, three-genome analysis "
                "subset and four marked archaeological-context dates. Recover "
                "explicit archive-to-specimen bindings before filling native IDs; "
                "administrative recovery does not establish independent animals."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJNA705960":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The retained primary article DOI 10.1371/journal.pone.0249537 "
                "assigns original Illumina reads to PRJNA705960. Eighteen bone "
                "samples were processed; eleven yielded consensus sequences "
                "and seven failed mapping or quality criteria. Nine consensus "
                "sequences met GenBank submission criteria. The eleven reviewed "
                "ENA BioSample aliases do not establish whether unsuccessful "
                "libraries were deposited or close the project specimen roster."
            ),
            expected_sample_count_artifact_path=(
                "data/adna/review/galician_cattle/article.html"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Bind the primary paper and retained S1/S2 tables without "
                "reacquisition. Preserve eighteen processed specimens, eleven "
                "consensus sequences, seven quality failures and nine GenBank "
                "submissions as separate stages. Recover a closed deposition "
                "roster; do not infer seven missing BioSamples or independent "
                "animals, or replace sample-owned aurochs taxonomy."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJEB41594":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The retained Reporting Summary p. 2 selects six specimens for "
                "genomic sequencing; p. 3 describes six extracted teeth and five "
                "samples advanced to deep shotgun sequencing. The final article "
                "assigns shotgun files to PRJEB41594 without a closed project "
                "count. Five retained ENA sample aliases, including one Capra "
                "record, do not resolve that source-stage population boundary."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41562-021-01083-y/"
                "supplementary/41562_2021_1083_MOESM2_ESM.pdf"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Recover the source-owned six-to-five specimen/analysis-stage "
                "crosswalk and closed project submission roster. Preserve all "
                "five archive identities and the Capra taxonomic mismatch; "
                "do not infer an expected count or independent individuals."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJEB31621":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The retained Science Supplementary Table S1 lists 66 ancient "
                "sample IDs; Table S6 separates nine new modern genomes from "
                "reused comparators. The project capture has 77 BioSample "
                "owners across 364 runs, while the 78-row master additionally "
                "retains provisional Men1. These populations do not establish "
                "a closed project specimen denominator or an MV013-to-Men1 join."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aav1002/"
                "supplementary/aav1002_verdugo_sm.pdf"
            ),
            sample_identifier_status="manual_curation_required",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Recover explicit Men1/MV013 specimen correspondence and the "
                "modern ERS-to-SAMEA crosswalk with project/reused-data scope. "
                "Keep the 66 ancient source IDs, 77 captured archive owners "
                "and 78-row curated union distinct."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJEB75467":
        return _ProjectIntakeExpectation(
            expected_sample_count=50,
            expected_sample_count_status="known_from_source_table",
            expected_sample_count_provenance=(
                "The retained Nature supplement physical p. 3 identifies 50 "
                "new samples, listed as 50 unique Analysis IDs in Supplementary "
                "Data 1!A2:AB51. Final Data Availability assigns new reads and "
                "alignments to PRJEB75467, separately from reused data. This "
                "mixed-taxon source-sample denominator does not imply 50 "
                "independent individuals or complete archive identity recovery."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41586-024-08112-6/"
                "supplementary/41586_2024_8112_MOESM3_ESM.xlsx"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Reconcile all 50 source Analysis IDs with captured BioSamples "
                "and submitted filenames. Preserve provisional Fre1, the six "
                "unmatched source IDs, Borly4a/Borlya alias ambiguity, literal "
                "taxa and sample-specific source-use restrictions."
            ),
        )

    if project_accession == "PRJEB59481":
        return _ProjectIntakeExpectation(
            expected_sample_count=5,
            expected_sample_count_status="known_from_source_table",
            expected_sample_count_provenance=(
                "The retained Genome Biology and Evolution article Data Availability "
                "explicitly assigns five new ancient individuals to PRJEB59481. "
                "All five Table 1 sample labels join distinct official ENA BioSamples; "
                "reused comparison genomes are outside this project-owned population."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1093-gbe-evae114/"
                "article_full_text.xml"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Preserve the five Table 1 to ENA identity bindings and keep "
                "material disagreements and chronology evidence separate."
            ),
        )

    if project_accession == "PRJEB60484":
        return _ProjectIntakeExpectation(
            expected_sample_count=20,
            expected_sample_count_status="known_from_source_table",
            expected_sample_count_provenance=(
                "The retained Molecular Ecology Appendix S1 Table S3 lists 20 "
                "ancient specimens with PRJEB60484 in the project column; all "
                "20 join distinct ENA BioSample aliases."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1111-mec.17274/"
                "supplementary/mec17274-sup-0003-Table S3.xlsx"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Preserve the exact Table S3 to ENA alias join and source-specific "
                "chronology alternatives in the generated sample master."
            ),
        )

    if project_accession == "PRJEB81815":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The published genome cohort contains 70 ancient and 17 "
                "present-day/museum samples, with resequencing rows kept "
                "separate. The study also processed 225 ancient remains and "
                "generated shallow data before deep selection. Data Availability "
                "does not restrict the project submission to those 87 genomes; "
                "matching captured counts cannot establish that boundary."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.adt2642/"
                "supplementary/science.adt2642_tables s1_to_s8.zip"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Recover the shallow/deep submission inventory and preserve "
                "the 778_Fss/778_Fsl, 779_Fss/779_Fsl and BG05/BG5 conflicts. "
                "Keep the published 87-genome cohort distinct from processed "
                "remains, technical rows and independent specimens."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJNA1178732":
        return _ProjectIntakeExpectation(
            expected_sample_count=22,
            expected_sample_count_status="known_from_source_table",
            expected_sample_count_provenance=(
                "The retained full primary article, mmc8.pdf physical p. 15, "
                "describes 22 collected ancient felid bones producing seven "
                "nuclear and 22 mitochondrial genomes. Physical p. 9 assigns "
                "generated FASTQ data to PRJNA1178732. Workbook mmc3 sheet A "
                "rows 4-25 lists exactly those 22 new FS sample IDs; comparative "
                "datasets and resequencing do not enlarge this population."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.xgen.2025.101099/"
                "supplementary/1-s2.0-S2666979X25003556-mmc3.xlsx"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Preserve all 22 source-table labels, mixed felid taxa and "
                "the unresolved ornata/bieti interpretation. Recover explicit "
                "accession-to-FS bindings before filling blank native IDs; "
                "do not treat the redirected article HTML as full text."
            ),
        )

    if project_accession == "PRJEB30282":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The retained project contains 632 runs and 343 BioSamples: "
                "320 archive-selected Dataset S1 lab codes plus 23 Dataset S2 "
                "modern this-study accessions. Article footnote fn8 binds "
                "ancient and modern reads to the project without an independent "
                "project roster. The broader 2099-sample analysis and 557 new "
                "mtDNA datasets are different assay and reuse populations."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1073-pnas.1901169116/"
                "article.html.gz"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Recover a source-defined ancient deposition roster and "
                "specimen-to-extraction correspondence. Keep the closed "
                "23-modern subgroup separate from the archive-selected 320 "
                "lab-code rows and the broader screened or reused register."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "PRJEB36540":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "The retained article HTML, stored as article.pdf, distinguishes "
                "180 archaeological samples, 29 ancient Illumina sample owners "
                "plus controls, four selected nuclear genomes and 91 mtDNA "
                "assignments. FASTQ and Sanger depositions differ. The master "
                "combines 180 Data 1 records with ten Data 2-only labels; neither "
                "that 190-row union nor five captured BioSamples closes a "
                "project-specific specimen population."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s42003-021-02794-8/"
                "article.pdf"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Reconcile assay/deposition scope and the ten cross-table "
                "labels using explicit specimen evidence. Do not collapse "
                "TEP5/TEP05 by zero stripping. Keep controls and Sanger results "
                "separate, and preserve Turkish specimen-use restrictions."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    if project_accession == "SRP073444":
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="source_population_unresolved",
            expected_sample_count_provenance=(
                "Original Table S3 and the full ENA report agree on 107 "
                "deposited technical representations across 63 author labels, "
                "separate from 77 sampled Table S1 IDs. The 20-row master uses "
                "the first NCBI results-page bridge, not the whole archive. "
                "Capture, touchdown and shotgun representations do not define "
                "interchangeable independent biological specimens."
            ),
            expected_sample_count_artifact_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1111-1755-0998.12551/"
                "article.html.gz"
            ),
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Define the deposited-treatment, author-label and specimen "
                "denominators and their selected-page correspondence. Preserve "
                "Palm143 accession-to-extraction-to-bone ambiguity; neither "
                "collapse nor independent biological counting is inferred."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    return None

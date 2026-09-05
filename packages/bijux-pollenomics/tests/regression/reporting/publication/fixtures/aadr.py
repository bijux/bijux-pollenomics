from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.reporting.models import SampleRecord
AADR_HEADER = "\t".join(
    [
        "Genetic ID",
        "Master ID",
        "Group ID",
        "Locality",
        "Political Entity",
        "Lat.",
        "Long.",
        "Publication abbreviation",
        "Year first published",
        "Full Date",
        "Date mean in BP",
        "Data type",
        "Molecular Sex",
    ]
)

def write_anno(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(AADR_HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def sample_record(
    genetic_id: str,
    locality: str,
    political_entity: str,
    datasets: tuple[str, ...],
) -> SampleRecord:
    from bijux_pollenomics.adna import (
        AdnaChronology,
        AdnaCoordinate,
        AdnaLocalityIdentity,
        AdnaSampleIdentity,
    )
    from bijux_pollenomics.reporting.models import SampleRecord

    return SampleRecord(
        identity=AdnaSampleIdentity(
            namespace="homo_sapiens:aadr_genetic_id",
            stable_token=genetic_id,
            accession_lineage=(
                "species:Homo sapiens",
                "source:AADR",
                f"dataset:{datasets[0]}",
                f"genetic_id:{genetic_id}",
            ),
        ),
        locality_identity=AdnaLocalityIdentity(
            namespace="homo_sapiens:locality",
            stable_token=(
                f"homo_sapiens:aadr:{political_entity.casefold()}:{locality.casefold()}:"
                "59-8586-17-6389"
            ),
            locality_text=locality,
            political_entity=political_entity,
            source_anchor_tokens=("AADR", "59.8586", "17.6389"),
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family="AADR",
        source_release="v62.0",
        record_modality="metadata_only",
        review_strength="curated_release_metadata",
        provenance_quality="release_manifest_pinned",
        master_id=genetic_id,
        group_id=f"{political_entity}_Group",
        locality=locality,
        political_entity=political_entity,
        coordinates=AdnaCoordinate(
            latitude=59.8586,
            longitude=17.6389,
            latitude_text="59.8586",
            longitude_text="17.6389",
            confidence="unknown",
        ),
        publication="PaperA",
        year_first_published="2022",
        full_date="500 BCE",
        chronology=AdnaChronology(
            original_text="2200-2700 BP",
            time_start_bp=2200,
            time_end_bp=2700,
            time_mean_bp=2450,
            dating_basis="bp_mean_and_stddev",
        ),
        data_type="AG",
        molecular_sex="F",
        datasets=datasets,
    )

"""Canonical record fixtures for Homo sapiens runtime tests."""

from collections.abc import Callable

import pytest
from bijux_pollenomics.adna.domain.models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)


@pytest.fixture
def human_sample() -> Callable[..., AdnaSampleRecord]:
    """Build a minimal canonical human record with explicit chronology semantics."""

    def build(
        *,
        dataset: str = "ho",
        younger_bp: int | None = None,
        older_bp: int | None = None,
        mean_bp: int | None = None,
        label: str = "",
        full_date: str = "",
    ) -> AdnaSampleRecord:
        return AdnaSampleRecord(
            identity=AdnaSampleIdentity(
                namespace="homo_sapiens:aadr_genetic_id",
                stable_token="SE1",
                accession_lineage=(f"dataset:{dataset}",),
            ),
            locality_identity=AdnaLocalityIdentity(
                namespace="homo_sapiens:locality",
                stable_token="uppsala",
                locality_text="Uppsala",
                political_entity="Sweden",
                source_anchor_tokens=("uppsala",),
            ),
            species_latin_name="Homo sapiens",
            species_common_name="human",
            source_family="AADR",
            source_release="v66",
            record_modality="metadata_only",
            review_strength="curated_release_metadata",
            provenance_quality="release_manifest_pinned",
            master_id="M1",
            group_id="G1",
            locality="Uppsala",
            political_entity="Sweden",
            coordinates=AdnaCoordinate(
                latitude=59.8,
                longitude=17.6,
                latitude_text="59.8",
                longitude_text="17.6",
                confidence="unknown",
            ),
            publication="Paper",
            year_first_published="2022",
            full_date=full_date,
            chronology=AdnaChronology(
                original_text=label,
                time_start_bp=younger_bp,
                time_end_bp=older_bp,
                time_mean_bp=mean_bp,
                dating_basis="unknown",
            ),
            data_type="AG",
            molecular_sex="F",
            datasets=(dataset,),
        )

    return build

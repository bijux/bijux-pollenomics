"""Project, paper, supplement, and intake registry behavior."""

from pathlib import Path

from bijux_pollenomics.adna.sources.library import (
    build_paper_registry,
    build_project_registry,
    build_source_intake_audit,
    build_source_intake_release_guard,
    build_supplement_registry,
    build_supplement_zip_member_registry,
)


def test_project_and_paper_registries_preserve_recovery_statuses(
    materialized_output_root: Path,
) -> None:
    sheep_project = next(
        item
        for item in build_project_registry(materialized_output_root)
        if item.project_accession == "PRJEB36540"
    )
    assert sheep_project.paper_download_status == "archived"
    assert sheep_project.supplement_download_status == "archived"
    assert sheep_project.expected_sample_count_status == "not_yet_curated"
    assert (
        sheep_project.sample_identifier_status == "paper_or_supplement_targets_curated"
    )

    sheep_paper = next(
        item
        for item in build_paper_registry(materialized_output_root)
        if item.paper_doi == "10.1038/s42003-021-02794-8"
    )
    assert sheep_paper.supplementary_count == 5
    assert sheep_paper.article_download_status == "archived"
    assert sheep_paper.sample_extractability == "supplement_extractable"
    assert sheep_paper.sample_table_extraction_status == "published_empty"
    assert any(
        path.endswith("42003_2021_2794_MOESM4_ESM.zip")
        for path in sheep_paper.expected_supplementary_artifacts
    )


def test_supplement_registries_preserve_archive_member_lineage(
    materialized_output_root: Path,
) -> None:
    assert any(
        item.paper_doi == "10.1038/s42003-021-02794-8"
        and item.artifact_kind == "supplementary_zip"
        for item in build_supplement_registry(materialized_output_root)
    )
    assert any(
        item["paper_doi"] == "10.1038/s42003-021-02794-8"
        and item["member_name"] == "TableS1.csv"
        for item in build_supplement_zip_member_registry(materialized_output_root)
    )


def test_intake_audit_and_release_guard_accept_the_fixture(
    materialized_output_root: Path,
) -> None:
    assert (
        build_source_intake_audit(materialized_output_root)[
            "sample_extractable_violations"
        ]
        == []
    )
    assert build_source_intake_release_guard(materialized_output_root)["passing"]

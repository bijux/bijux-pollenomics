"""Official-source contracts for the Baltic ancient-sheep samples."""

from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

import pytest
from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_project_sample_chronology_rows,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.projects.sample_master.tables.baltic_sheep import (
    ARTICLE_SOURCE_PATH,
    ENA_SAMPLE_SOURCE_DIRECTORY,
    build_baltic_sheep_material_conflicts,
    load_baltic_sheep_official_evidence,
    materialize_baltic_sheep_material_conflicts,
    parse_baltic_sheep_article_chronology,
    parse_baltic_sheep_ena_sample,
    reconcile_baltic_sheep_official_evidence,
)
from bijux_pollenomics.adna.sources.library import (
    build_project_source_bundles,
    build_source_artifact_index,
)
from bijux_pollenomics.adna.sources.recovery import build_project_recovery_dossier
from bijux_pollenomics.adna.workflow.source_artifacts import (
    resolve_source_artifact_path,
)

from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts

DATA_ROOT = REPOSITORY_ROOT / "data"
WORKBOOK_SOURCE_PATH = (
    "data/adna/governance/source_library/papers/10.1093-gbe-evae114/"
    "supplementary/SupplementaryTables_Revision2.xlsx"
)
ARCHIVE_SOURCE_PATH = (
    "data/adna/governance/source_library/projects/PRJEB59481/archive_metadata.html"
)


def _article_payload() -> bytes:
    return (DATA_ROOT / ARTICLE_SOURCE_PATH.removeprefix("data/")).read_bytes()


def _ena_payload(accession: str) -> bytes:
    return (
        DATA_ROOT
        / ENA_SAMPLE_SOURCE_DIRECTORY.removeprefix("data/")
        / f"{accession}.xml"
    ).read_bytes()


def _copy_source_artifact(output_root: Path, repository_path: str) -> None:
    destination = output_root / repository_path.removeprefix("data/")
    destination.parent.mkdir(parents=True, exist_ok=True)
    logical_source = DATA_ROOT / repository_path.removeprefix("data/")
    storage_source = resolve_source_artifact_path(logical_source)
    storage_destination = (
        destination.with_suffix(destination.suffix + ".gz")
        if storage_source.suffix == ".gz"
        else destination
    )
    shutil.copy2(storage_source, storage_destination)
    receipt_source = logical_source.with_suffix(
        logical_source.suffix + ".metadata.json"
    )
    if receipt_source.is_file():
        receipt_destination = destination.with_suffix(
            destination.suffix + ".metadata.json"
        )
        shutil.copy2(receipt_source, receipt_destination)


def _copy_official_source_bundle(output_root: Path) -> None:
    _copy_source_artifact(output_root, ARTICLE_SOURCE_PATH)
    for suffix in range(1, 6):
        _copy_source_artifact(
            output_root,
            f"{ENA_SAMPLE_SOURCE_DIRECTORY}/SAMEA11296029{suffix}.xml",
        )


def test_official_sources_join_all_five_samples_with_explicit_denominators() -> None:
    bundle = load_baltic_sheep_official_evidence(DATA_ROOT)

    assert bundle.denominator.expected_sample_count == 5
    assert bundle.denominator.ena_sample_count == 5
    assert bundle.denominator.article_sample_count == 5
    assert bundle.denominator.joined_sample_count == 5
    assert set(bundle.by_accession()) == {
        f"SAMEA11296029{suffix}" for suffix in range(1, 6)
    }


def test_official_sources_preserve_coordinates_jurisdictions_and_chronology() -> None:
    samples = {
        row.archive.sample_label: row
        for row in load_baltic_sheep_official_evidence(DATA_ROOT).samples
    }

    assert {
        label: (
            row.archive.latitude_text,
            row.archive.longitude_text,
            row.region_name,
            row.country_name,
        )
        for label, row in samples.items()
    } == {
        "AKAS001": ("60.23", "20.08", "Åland", "Finland"),
        "AKAS002": ("60.23", "20.08", "Åland", "Finland"),
        "ASTF001": ("57.29", "17.97", "Gotland", "Sweden"),
        "ASTF002": ("57.29", "17.97", "Gotland", "Sweden"),
        "ASTF003": ("57.29", "17.97", "Gotland", "Sweden"),
    }
    assert {
        label: (
            row.chronology.source_text,
            row.chronology.younger_bp,
            row.chronology.older_bp,
        )
        for label, row in samples.items()
    } == {
        "AKAS001": ("527 to 340 cal BP (Ua-71141)", 340, 527),
        "AKAS002": ("CE 1500 to 1550", 400, 450),
        "ASTF001": ("3957 to 3699 cal BP (Ua-71140)", 3699, 3957),
        "ASTF002": ("4151 to 3936 cal BP (Ua-71139)", 3936, 4151),
        "ASTF003": ("Late Neolithic", None, None),
    }
    assert samples["AKAS002"].chronology.contextual is True
    assert samples["ASTF003"].chronology.precision_posture == "broad_period_only"
    assert all(
        row.jurisdiction_basis == "governed_region_to_country_assignment"
        for row in samples.values()
    )
    assert all(
        row.jurisdiction_registry_id == "baltic-sheep-region-country.v1"
        and row.jurisdiction_registry_version == "1.0.0"
        and row.jurisdiction_registry_path.endswith("official_evidence.py")
        and row.jurisdiction_registry_locator.endswith(f"[{row.region_name!r}]")
        for row in samples.values()
    )
    article_root = ElementTree.fromstring(_article_payload())
    assert all(
        len(article_root.findall(row.chronology.source_locator)) == 1
        for row in samples.values()
    )
    for row in samples.values():
        ena_root = ElementTree.fromstring(_ena_payload(row.archive.accession))
        assert len(ena_root.findall(row.archive.source_locator)) == 1
        assert len(ena_root.findall(row.archive.description_source_locator)) == 1


def test_generators_use_official_claims_with_separate_source_provenance() -> None:
    master_rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB59481")
    chronology_rows = build_project_sample_chronology_rows(DATA_ROOT, "PRJEB59481")

    assert len(master_rows) == len(chronology_rows) == 5
    assert {
        (row.political_entity, row.latitude_text, row.longitude_text)
        for row in master_rows
    } == {
        ("Finland", "60.23", "20.08"),
        ("Sweden", "57.29", "17.97"),
    }
    assert all(row.sample_lineage_path == WORKBOOK_SOURCE_PATH for row in master_rows)
    by_label = {row.preferred_sample_label: row for row in chronology_rows}
    assert (by_label["AKAS002"].time_start_bp, by_label["AKAS002"].time_end_bp) == (
        400,
        450,
    )
    assert by_label["AKAS002"].chronology_precision_posture == "contextual_interval"
    assert by_label["ASTF003"].chronology_text == "Late Neolithic"
    assert by_label["ASTF003"].time_start_bp is None
    assert by_label["ASTF003"].time_end_bp is None
    assert all(
        row.chronology_provenance_path == ARTICLE_SOURCE_PATH for row in chronology_rows
    )
    assert all(
        "evae114-T1" in row.chronology_provenance_locator for row in chronology_rows
    )


def test_material_conflicts_retain_both_exact_source_claims() -> None:
    conflicts = build_baltic_sheep_material_conflicts(DATA_ROOT)

    assert len(conflicts) == 5
    assert all(row.status == "source_disagreement_unresolved" for row in conflicts)
    assert all(row.archive_claim == "humerus" for row in conflicts)
    assert all("right radius" in row.supplement_claim.casefold() for row in conflicts)
    assert all(
        row.archive_source_path.endswith(f"{row.accession}.xml") for row in conflicts
    )
    assert all("Ancient remains" in row.supplement_source_locator for row in conflicts)


def test_material_conflicts_round_trip_as_a_governed_ledger(tmp_path: Path) -> None:
    required_paths = (
        Path(WORKBOOK_SOURCE_PATH),
        Path(ARCHIVE_SOURCE_PATH),
        Path(ARTICLE_SOURCE_PATH),
        *(
            Path(ENA_SAMPLE_SOURCE_DIRECTORY) / f"SAMEA11296029{suffix}.xml"
            for suffix in range(1, 6)
        ),
    )
    for relative_path in required_paths:
        _copy_source_artifact(tmp_path, str(relative_path))

    materialize_baltic_sheep_material_conflicts(tmp_path)
    ledger_path = (
        tmp_path / "adna/governance/source_library/projects/PRJEB59481/"
        "material_evidence_conflicts.json"
    )
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    assert ledger["expected_sample_count"] == 5
    assert ledger["conflict_count"] == 5
    assert len(ledger["rows"]) == 5
    assert all(
        row["status"] == "source_disagreement_unresolved" for row in ledger["rows"]
    )
    assert all(row["archive_claim"] == "humerus" for row in ledger["rows"])
    assert all(
        "right radius" in row["supplement_claim"].casefold() for row in ledger["rows"]
    )
    indexed = {row.local_path: row for row in build_source_artifact_index(tmp_path)}
    conflict_paths = {
        "adna/governance/source_library/projects/PRJEB59481/"
        "material_evidence_conflicts.json",
        "adna/governance/source_library/projects/PRJEB59481/"
        "material_evidence_conflicts.csv",
    }
    assert conflict_paths <= indexed.keys()
    assert all(indexed[path].fetch_status == "archived" for path in conflict_paths)
    bundle = next(
        row
        for row in build_project_source_bundles(tmp_path)
        if row.project_accession == "PRJEB59481"
    )
    assert conflict_paths <= set(bundle.local_artifact_paths)


def test_recovery_dossier_counts_every_unresolved_material_pair() -> None:
    dossier = build_project_recovery_dossier(DATA_ROOT, "PRJEB59481")

    assert dossier["material_evidence_expected_count"] == 5
    assert dossier["material_evidence_conflict_count"] == 5
    assert any(
        "5 of 5 material claim pairs" in note
        for note in dossier["contradictory_evidence"]
    )


def test_official_xml_sources_are_discoverable_in_project_inventory() -> None:
    indexed = {
        row.local_path: row
        for row in build_source_artifact_index(DATA_ROOT)
        if "PRJEB59481" in row.project_accessions
    }
    expected_paths = {
        ARTICLE_SOURCE_PATH.removeprefix("data/"),
        f"{ARTICLE_SOURCE_PATH.removeprefix('data/')}.metadata.json",
        *{
            f"{ENA_SAMPLE_SOURCE_DIRECTORY.removeprefix('data/')}/"
            f"SAMEA11296029{suffix}.xml"
            for suffix in range(1, 6)
        },
        *{
            f"{ENA_SAMPLE_SOURCE_DIRECTORY.removeprefix('data/')}/"
            f"SAMEA11296029{suffix}.xml.metadata.json"
            for suffix in range(1, 6)
        },
    }
    assert expected_paths <= indexed.keys()
    assert all(indexed[path].fetch_status == "archived" for path in expected_paths)
    bundle = next(
        row
        for row in build_project_source_bundles(DATA_ROOT)
        if row.project_accession == "PRJEB59481"
    )
    assert expected_paths <= set(bundle.local_artifact_paths)


def test_ena_identity_coordinate_and_locality_drift_fail_closed() -> None:
    payload = _ena_payload("SAMEA112960291")
    with pytest.raises(ValueError, match="identity drift"):
        parse_baltic_sheep_ena_sample(
            payload.replace(b'alias="AKAS001"', b'alias="ASTF001"'),
            source_path="mutated.xml",
            expected_accession="SAMEA112960291",
        )
    with pytest.raises(ValueError, match="lat_lon must occur exactly once"):
        parse_baltic_sheep_ena_sample(
            payload.replace(
                b"</SAMPLE_ATTRIBUTES>",
                b"<SAMPLE_ATTRIBUTE><TAG>lat_lon</TAG><VALUE>0, 0</VALUE>"
                b"</SAMPLE_ATTRIBUTE></SAMPLE_ATTRIBUTES>",
            ),
            source_path="mutated.xml",
            expected_accession="SAMEA112960291",
        )
    with pytest.raises(ValueError, match="locality drift"):
        parse_baltic_sheep_ena_sample(
            payload.replace(b"Kastelholm", b"Stora Forvar"),
            source_path="mutated.xml",
            expected_accession="SAMEA112960291",
        )
    with pytest.raises(ValueError, match="coordinate drift"):
        parse_baltic_sheep_ena_sample(
            payload.replace(b"60.23", b"60.24"),
            source_path="mutated.xml",
            expected_accession="SAMEA112960291",
        )
    with pytest.raises(ValueError, match="description drift"):
        parse_baltic_sheep_ena_sample(
            payload.replace(b"Sheep humerus", b"Sheep femur"),
            source_path="mutated.xml",
            expected_accession="SAMEA112960291",
        )


def test_official_source_load_reconciles_payload_bytes_and_receipt(
    tmp_path: Path,
) -> None:
    _copy_official_source_bundle(tmp_path)
    mutated_path = (
        tmp_path
        / ENA_SAMPLE_SOURCE_DIRECTORY.removeprefix("data/")
        / "SAMEA112960291.xml"
    )
    mutated_path.write_bytes(mutated_path.read_bytes().replace(b"60.23", b"60.24"))

    with pytest.raises(ValueError, match="receipt does not reconcile.*content_sha256"):
        load_baltic_sheep_official_evidence(tmp_path)


@pytest.mark.parametrize(
    ("repository_path", "field", "invalid_value"),
    (
        (
            f"{ENA_SAMPLE_SOURCE_DIRECTORY}/SAMEA112960291.xml",
            "source_url",
            "https://example.invalid/sample.xml",
        ),
        (
            f"{ENA_SAMPLE_SOURCE_DIRECTORY}/SAMEA112960291.xml",
            "license_name",
            "Creative Commons Attribution 4.0 International",
        ),
        (ARTICLE_SOURCE_PATH, "license_name", "EMBL-EBI Terms of Use"),
        (ARTICLE_SOURCE_PATH, "pmcid", "PMC00000000"),
        (ARTICLE_SOURCE_PATH, "storage_byte_size", 1),
    ),
)
def test_official_source_load_refuses_receipt_identity_license_and_storage_drift(
    tmp_path: Path,
    repository_path: str,
    field: str,
    invalid_value: object,
) -> None:
    _copy_official_source_bundle(tmp_path)
    logical_path = tmp_path / repository_path.removeprefix("data/")
    receipt_path = logical_path.with_suffix(logical_path.suffix + ".metadata.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt[field] = invalid_value
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(ValueError, match=f"receipt does not reconcile.*{field}"):
        load_baltic_sheep_official_evidence(tmp_path)


def test_article_context_epoch_identity_and_denominator_drift_fail_closed() -> None:
    payload = _article_payload()
    with pytest.raises(ValueError, match="reference epoch"):
        parse_baltic_sheep_article_chronology(
            payload.replace(b"1950 CE", b"2000 CE"), source_path="mutated.xml"
        )
    with pytest.raises(ValueError, match="not bound to AKAS002 context"):
        parse_baltic_sheep_article_chronology(
            payload.replace(
                b'CE 1500 to 1550<sup><xref rid="tblfn2" ref-type="table-fn">a</xref></sup>',
                b"CE 1500 to 1550",
            ),
            source_path="mutated.xml",
        )
    with pytest.raises(ValueError, match="locality drift"):
        parse_baltic_sheep_article_chronology(
            payload.replace(b"Kastelholm, ", b"Stora F\xc3\xb6rvar, ", 1),
            source_path="mutated.xml",
        )
    with pytest.raises(ValueError, match="article identity drift"):
        parse_baltic_sheep_article_chronology(
            payload.replace(b"PMC11162877", b"PMC00000000", 1),
            source_path="mutated.xml",
        )
    with pytest.raises(ValueError, match="CC BY 4.0 license drift"):
        parse_baltic_sheep_article_chronology(
            payload.replace(
                b"https://creativecommons.org/licenses/by/4.0/",
                b"https://creativecommons.org/licenses/by/3.0/",
                1,
            ),
            source_path="mutated.xml",
        )

    root = ElementTree.fromstring(payload)
    table_body = root.find(".//table-wrap[@id='evae114-T1']/table/tbody")
    assert table_body is not None
    table_body.remove(list(table_body)[-1])
    with pytest.raises(ValueError, match="identities must occur exactly once"):
        parse_baltic_sheep_article_chronology(
            ElementTree.tostring(root), source_path="mutated.xml"
        )


def test_reconciliation_refuses_missing_and_cross_contaminated_rows() -> None:
    bundle = load_baltic_sheep_official_evidence(DATA_ROOT)
    with pytest.raises(ValueError, match="ENA evidence denominator drift"):
        reconcile_baltic_sheep_official_evidence(
            tuple(row.archive for row in bundle.samples[:-1]),
            tuple(row.chronology for row in bundle.samples),
        )

    archive_rows = [row.archive for row in bundle.samples]
    archive_rows[0] = replace(archive_rows[0], site_name="Stora Förvar")
    with pytest.raises(ValueError, match="source locality conflict"):
        reconcile_baltic_sheep_official_evidence(
            tuple(archive_rows), tuple(row.chronology for row in bundle.samples)
        )

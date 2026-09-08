"""Independent exact-denominator tests over checked-in governed source data."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from bijux_pollenomics.reporting.adna.sample_chronology_context.repository import (
    load_animal_sample_chronology_corpus,
)


def _data_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data"
        if (candidate / "adna" / "governance").is_dir():
            return candidate
    raise AssertionError("repository data root is unavailable")


def test_real_governed_source_denominators_and_exclusive_waterfall() -> None:
    corpus = load_animal_sample_chronology_corpus(_data_root())

    assert dict(corpus.source_counts) == {
        "project_count": 40,
        "sample_master_row_count": 1475,
        "sample_chronology_row_count": 1455,
        "sample_site_row_count": 1455,
        "admitted_node_count": 557,
        "refused_master_row_count": 918,
    }
    assert dict(corpus.refusal_counts) == {
        "sequencing_experiment_identity": 20,
        "sample_identity_not_final": 5,
        "source_chronology_not_comparable": 558,
        "source_coordinate_not_mappable": 335,
        "sample_provenance_unavailable": 0,
        "chronology_provenance_unavailable": 0,
        "site_provenance_unavailable": 0,
    }
    assert Counter(node.project_species_latin_name for node in corpus.nodes) == {
        "Bos taurus": 31,
        "Capra hircus": 9,
        "Equus caballus": 476,
        "Felis catus": 35,
        "Ovis aries": 4,
        "Sus scrofa domesticus": 2,
    }
    assert Counter(node.project_accession for node in corpus.nodes) == {
        "PRJEB30282": 2,
        "PRJEB31613": 234,
        "PRJEB44430": 242,
        "PRJEB59481": 4,
        "PRJEB75467": 31,
        "PRJEB81815": 35,
        "PRJEB90141": 4,
        "PRJNA1328209": 5,
    }
    assert (
        min(node.younger_bp for node in corpus.nodes),
        max(node.older_bp for node in corpus.nodes),
    ) == (17, 68764)
    assert Counter(node.chronology_precision_posture for node in corpus.nodes) == {
        "contextual_interval": 5,
        "sample_approximate_or_modeled": 39,
        "sample_precise_interval": 127,
        "sample_precise_point": 386,
    }
    assert Counter(node.coordinate_basis for node in corpus.nodes) == {
        "archive_coordinates": 4,
        "named_site_geocoding": 2,
        "supplementary_proximal_site_coordinates": 31,
        "supplementary_table_coordinates": 520,
    }
    assert Counter(node.coordinate_confidence for node in corpus.nodes) == {
        "approximate": 33,
        "exact": 520,
        "source_reported_two_decimal_degrees": 4,
    }
    assert Counter(node.source_native_taxonomy_status for node in corpus.nodes) == {
        "available": 72,
        "unavailable": 485,
    }


def test_real_admitted_identity_set_equals_curated_fully_grounded_set() -> None:
    data_root = _data_root()
    source = load_animal_sample_chronology_corpus(data_root)
    source_ids = {
        (node.project_accession, node.repo_stable_sample_id) for node in source.nodes
    }
    curated_ids: set[tuple[str, str]] = set()
    for path in sorted(
        (data_root / "adna" / "species").glob("*/normalized/sample_records.json")
    ):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload["samples"]:
            linkage = any(
                str(row.get(field, "")).strip()
                for field in ("paper_doi", "paper_url", "supplementary_source")
            )
            chronology = row.get("chronology", {})
            coordinates = row.get("coordinates", {})
            fully_grounded = (
                linkage
                and row.get("inclusion_status") != "sample_context_blocked"
                and isinstance(chronology, dict)
                and chronology.get("time_start_bp") is not None
                and chronology.get("time_end_bp") is not None
                and isinstance(coordinates, dict)
                and bool(str(coordinates.get("latitude_text", "")).strip())
                and bool(str(coordinates.get("longitude_text", "")).strip())
                and str(coordinates.get("confidence", "")).strip() != "withheld"
            )
            if fully_grounded:
                curated_ids.add((row["project_accession"], row["master_id"]))

    assert len(curated_ids) == 557
    assert source_ids == curated_ids


def test_real_input_identity_recomputes_from_exact_paths_and_bytes() -> None:
    data_root = _data_root()
    identity = load_animal_sample_chronology_corpus(data_root).input_identity
    observed_paths = [artifact.logical_path for artifact in identity.artifacts]
    expected_paths = [
        "adna/governance/source_library/project_registry.json",
        *[
            f"adna/governance/source_library/projects/{project}/{filename}"
            for project in sorted(
                path.name
                for path in (
                    data_root / "adna" / "governance" / "source_library" / "projects"
                ).iterdir()
                if path.is_dir()
            )
            for filename in (
                "sample_chronology.json",
                "sample_master.json",
                "sample_sites.json",
            )
        ],
    ]
    assert observed_paths == sorted(expected_paths)
    assert len(observed_paths) == len(set(observed_paths)) == 121

    members: list[tuple[str, bytes]] = []
    families: dict[str, list[tuple[str, bytes]]] = {}
    for artifact in identity.artifacts:
        content = (data_root / artifact.logical_path).read_bytes()
        assert artifact.byte_count == len(content)
        assert artifact.sha256 == sha256(content).hexdigest()
        member = (artifact.logical_path, content)
        members.append(member)
        families.setdefault(Path(artifact.logical_path).name, []).append(member)

    assert identity.combined_sha256 == _framed_digest(members)
    assert dict(identity.family_sha256) == {
        name: _framed_digest(family_members)
        for name, family_members in sorted(families.items())
    }


def _framed_digest(members: list[tuple[str, bytes]]) -> str:
    digest = sha256()
    for logical_path, content in sorted(members):
        path_bytes = logical_path.encode("utf-8")
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()

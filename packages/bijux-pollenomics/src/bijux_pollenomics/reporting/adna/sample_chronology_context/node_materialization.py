"""Materialize admitted animal chronology nodes and their input identity."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path

from .contracts import (
    AnimalChronologyInputIdentity,
    AnimalSampleChronologyNode,
    InputArtifactIdentity,
)

_SampleKey = tuple[str, str]


def build_node(
    master: Mapping[str, object],
    chronology: Mapping[str, object],
    site: Mapping[str, object],
    *,
    registry_row: Mapping[str, object],
) -> AnimalSampleChronologyNode:
    """Build one admitted node from reconciled governed surfaces."""
    project = _required_text(master, "project_accession")
    sample_id = _required_text(master, "repo_stable_sample_id")
    return AnimalSampleChronologyNode(
        feature_id=f"animal-source-chronology:{project}:{sample_id}",
        project_accession=project,
        repo_stable_sample_id=sample_id,
        preferred_sample_label=_required_text(master, "preferred_sample_label"),
        project_species_latin_name=_required_text(master, "species_latin_name"),
        project_species_common_name=_required_text(master, "species_common_name"),
        source_native_identity_kind=_optional_text(
            master.get("source_native_identity_kind")
        ),
        source_native_tax_id=_optional_text(master.get("source_native_tax_id")),
        source_native_scientific_name=_optional_text(
            master.get("source_native_scientific_name")
        ),
        locality_text=_required_text(site, "locality_text"),
        site_name=_required_text(site, "site_name"),
        country_name=_optional_text(site.get("country_name")),
        broader_geography=_optional_text(site.get("broader_geography")),
        latitude=_coordinate(
            master.get("latitude_text"), -90.0, 90.0, (project, sample_id), "latitude"
        ),
        longitude=_coordinate(
            master.get("longitude_text"),
            -180.0,
            180.0,
            (project, sample_id),
            "longitude",
        ),
        latitude_text=_required_text(master, "latitude_text"),
        longitude_text=_required_text(master, "longitude_text"),
        coordinate_basis=_required_text(site, "coordinate_basis"),
        coordinate_confidence=_required_text(site, "coordinate_confidence"),
        chronology_text=_required_text(chronology, "chronology_text"),
        chronology_strength=_required_text(chronology, "chronology_strength"),
        chronology_evidence_class=_required_text(
            chronology, "chronology_evidence_class"
        ),
        chronology_precision_posture=_required_text(
            chronology, "chronology_precision_posture"
        ),
        chronology_normalization_status=_required_text(
            chronology, "chronology_normalization_status"
        ),
        younger_bp=_required_int(chronology, "time_start_bp"),
        older_bp=_required_int(chronology, "time_end_bp"),
        mean_bp=_required_int(chronology, "time_mean_bp"),
        dating_basis=_required_text(chronology, "dating_basis"),
        sample_lineage_path=_required_text(master, "sample_lineage_path"),
        sample_lineage_locator=_required_text(master, "sample_lineage_locator"),
        sample_lineage_excerpt=_required_text(master, "sample_lineage_excerpt"),
        chronology_provenance_path=_required_text(
            chronology, "chronology_provenance_path"
        ),
        chronology_provenance_kind=_required_text(
            chronology, "chronology_provenance_kind"
        ),
        chronology_provenance_locator=_required_text(
            chronology, "chronology_provenance_locator"
        ),
        chronology_provenance_text=_required_text(
            chronology, "chronology_provenance_text"
        ),
        location_evidence_artifact_path=_required_text(
            site, "location_evidence_artifact_path"
        ),
        location_evidence_artifact_kind=_required_text(
            site, "location_evidence_artifact_kind"
        ),
        location_evidence_locator=_required_text(site, "location_evidence_locator"),
        location_evidence_text=_required_text(site, "location_evidence_text"),
        source_url=(
            _optional_text(registry_row.get("primary_paper_url"))
            or _optional_text(registry_row.get("project_url"))
            or ""
        ),
    )


def build_input_identity(
    data_root: Path, captured_inputs: Mapping[Path, bytes]
) -> AnimalChronologyInputIdentity:
    """Bind the corpus to every captured governed input byte."""
    identities: list[InputArtifactIdentity] = []
    family_members: dict[str, list[tuple[str, bytes]]] = {}
    all_members: list[tuple[str, bytes]] = []
    for path in sorted(
        captured_inputs, key=lambda item: item.relative_to(data_root).as_posix()
    ):
        logical_path = path.relative_to(data_root).as_posix()
        content = captured_inputs[path]
        identities.append(
            InputArtifactIdentity(
                logical_path=logical_path,
                byte_count=len(content),
                sha256=sha256(content).hexdigest(),
            )
        )
        member = (logical_path, content)
        all_members.append(member)
        family_members.setdefault(path.name, []).append(member)
    families = tuple(
        (name, _framed_digest(members))
        for name, members in sorted(family_members.items())
    )
    return AnimalChronologyInputIdentity(
        combined_sha256=_framed_digest(all_members),
        family_sha256=families,
        artifacts=tuple(identities),
    )


def _framed_digest(members: list[tuple[str, bytes]]) -> str:
    digest = sha256()
    for logical_path, content in sorted(members):
        path_bytes = logical_path.encode("utf-8")
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _required_text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value.strip()


def _optional_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _required_int(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _coordinate(
    value: object, lower: float, upper: float, key: _SampleKey, label: str
) -> float:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"mappable {label} is unavailable for {key!r}")
    try:
        coordinate = float(value)
    except ValueError as exc:
        raise ValueError(f"mappable {label} is invalid for {key!r}") from exc
    if not lower <= coordinate <= upper:
        raise ValueError(f"mappable {label} is outside WGS84 bounds for {key!r}")
    return coordinate

"""Strict readers and joins for governed animal sample chronology artifacts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from hashlib import sha256
import json
from pathlib import Path
from typing import cast

from ....adna.domain.models.vocabularies import (
    ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
    ADNA_CHRONOLOGY_PRECISION_POSTURES,
    ADNA_COORDINATE_CONFIDENCE,
    ADNA_COORDINATE_PROVENANCE_CLASSES,
    ADNA_DATING_BASES,
)
from ....adna.projects.evidence.chronology.constants import (
    ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
    ADNA_CHRONOLOGY_STRENGTHS,
)
from ....adna.projects.registry.sites.records import (
    ADNA_LOCALITY_RESOLUTION_STATUSES,
)
from ....adna.projects.sample_master.models import (
    ADNA_SAMPLE_EVIDENCE_STATUSES,
    ADNA_SAMPLE_IDENTITY_RESOLUTIONS,
    ADNA_SOURCE_NATIVE_IDENTITY_KINDS,
)
from .contracts import (
    AnimalChronologyInputIdentity,
    AnimalSampleChronologyCorpus,
    AnimalSampleChronologyNode,
    AnimalSampleChronologyRefusal,
    InputArtifactIdentity,
)

_REGISTRY_SCHEMA = "adna-source-library.v1"
_SURFACE_SCHEMAS = {
    "sample_master.json": "animal-project-sample-master.v1",
    "sample_chronology.json": "animal-project-sample-chronology.v1",
    "sample_sites.json": "animal-project-sample-sites.v1",
}
_CHRONOLOGY_STATUSES = set(ADNA_CHRONOLOGY_NORMALIZATION_STATUSES)
_IDENTITY_STATUSES = set(ADNA_SAMPLE_IDENTITY_RESOLUTIONS)
_MAPPABLE_POSTURE = "mappable_point"
_MAPPABLE_COORDINATE_BASES = {
    "archive_coordinates",
    "direct_published_coordinates",
    "named_site_geocoding",
    "supplementary_proximal_site_coordinates",
    "supplementary_table_coordinates",
}
_MAPPABLE_COORDINATE_CONFIDENCE = {
    "approximate",
    "exact",
    "inferred",
    "source_reported_two_decimal_degrees",
}
_NUMERIC_CHRONOLOGY_PRECISION_POSTURES = {
    "contextual_interval",
    "sample_approximate_or_modeled",
    "sample_precise_interval",
    "sample_precise_point",
}
_REFUSAL_ORDER = (
    "sequencing_experiment_identity",
    "sample_identity_not_final",
    "source_chronology_not_comparable",
    "source_coordinate_not_mappable",
    "sample_provenance_unavailable",
    "chronology_provenance_unavailable",
    "site_provenance_unavailable",
)

_Row = dict[str, object]
_SampleKey = tuple[str, str]


def load_animal_sample_chronology_corpus(
    data_root: Path,
) -> AnimalSampleChronologyCorpus:
    """Read, validate, and exclusively classify every governed master identity."""
    data_root = Path(data_root)
    source_root = data_root / "adna" / "governance" / "source_library"
    registry_path = source_root / "project_registry.json"
    captured_inputs: dict[Path, bytes] = {}
    registry = _read_object(registry_path, captured_inputs=captured_inputs)
    _require_equal(registry.get("schema_version"), _REGISTRY_SCHEMA, "registry schema")
    registry_rows = _rows(registry, "registry")
    projects = _project_inventory(registry_rows)
    project_root = source_root / "projects"
    _validate_project_directories(project_root, set(projects))

    surfaces: dict[str, dict[_SampleKey, _Row]] = {
        filename: {} for filename in _SURFACE_SCHEMAS
    }
    for accession, registry_row in sorted(projects.items()):
        for filename, schema in _SURFACE_SCHEMAS.items():
            path = project_root / accession / filename
            payload = _read_object(path, captured_inputs=captured_inputs)
            _validate_surface_root(
                payload,
                filename=filename,
                schema=schema,
                accession=accession,
                species=_required_text(registry_row, "species_latin_name"),
            )
            project_rows = _rows(payload, f"{accession}/{filename}")
            _validate_declared_counts(payload, filename, project_rows)
            for row in project_rows:
                key = _validate_row_identity(
                    row,
                    accession=accession,
                    species=_required_text(registry_row, "species_latin_name"),
                    filename=filename,
                )
                if key in surfaces[filename]:
                    raise ValueError(f"duplicate {filename} sample identity: {key!r}")
                surfaces[filename][key] = row

    masters = surfaces["sample_master.json"]
    chronologies = surfaces["sample_chronology.json"]
    sites = surfaces["sample_sites.json"]
    _validate_join_sets(masters, chronologies, sites)

    nodes: list[AnimalSampleChronologyNode] = []
    refusals: list[AnimalSampleChronologyRefusal] = []
    refusal_counts = Counter({reason: 0 for reason in _REFUSAL_ORDER})
    for key in sorted(masters):
        master = masters[key]
        reason: str | None
        if (
            master.get("source_native_identity_kind")
            == "sequencing_experiment_accession"
        ):
            reason = "sequencing_experiment_identity"
        else:
            chronology = chronologies[key]
            site = sites[key]
            _validate_cross_surface_identity(master, chronology, site, key=key)
            _validate_chronology_shape(chronology, key=key)
            _validate_coordinate_claim(master, site, key=key)
            reason = _refusal_reason(master, chronology, site)
            if reason is None:
                nodes.append(
                    _build_node(
                        master,
                        chronology,
                        site,
                        registry_row=projects[key[0]],
                    )
                )
                continue
        refusal_counts[reason] += 1
        refusals.append(
            AnimalSampleChronologyRefusal(
                project_accession=key[0],
                repo_stable_sample_id=key[1],
                reason_code=reason,
            )
        )

    if len(nodes) + len(refusals) != len(masters):
        raise ValueError("animal sample chronology dispositions do not reconcile")
    return AnimalSampleChronologyCorpus(
        nodes=tuple(nodes),
        refusals=tuple(refusals),
        input_identity=_build_input_identity(data_root, captured_inputs),
        source_counts=(
            ("project_count", len(projects)),
            ("sample_master_row_count", len(masters)),
            ("sample_chronology_row_count", len(chronologies)),
            ("sample_site_row_count", len(sites)),
            ("admitted_node_count", len(nodes)),
            ("refused_master_row_count", len(refusals)),
        ),
        refusal_counts=tuple(
            (reason, refusal_counts[reason]) for reason in _REFUSAL_ORDER
        ),
    )


def _read_object(path: Path, *, captured_inputs: dict[Path, bytes]) -> _Row:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"governed animal chronology input is unavailable: {path}")
    try:
        content = path.read_bytes()
        value = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid governed animal chronology JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"governed animal chronology root must be an object: {path}")
    captured_inputs[path] = content
    return cast(_Row, value)


def _rows(payload: Mapping[str, object], label: str) -> list[_Row]:
    value = payload.get("rows")
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} rows must be a list of objects")
    return cast(list[_Row], value)


def _project_inventory(rows: list[_Row]) -> dict[str, _Row]:
    projects: dict[str, _Row] = {}
    for row in rows:
        accession = _required_text(row, "project_accession")
        _required_text(row, "species_latin_name")
        if accession in projects:
            raise ValueError(f"duplicate governed project accession: {accession}")
        projects[accession] = row
    if not projects:
        raise ValueError("governed animal project registry is empty")
    return projects


def _validate_project_directories(project_root: Path, expected: set[str]) -> None:
    if not project_root.is_dir() or project_root.is_symlink():
        raise ValueError("governed animal project directory is unavailable")
    children = tuple(project_root.iterdir())
    observed = {
        path.name for path in children if path.is_dir() and not path.is_symlink()
    }
    invalid = {path.name for path in children if not path.is_dir() or path.is_symlink()}
    if observed != expected or invalid:
        raise ValueError(
            "governed animal project inventory does not reconcile; "
            f"missing={sorted(expected - observed)}, "
            f"extra={sorted(observed - expected)}, invalid={sorted(invalid)}"
        )


def _validate_surface_root(
    payload: Mapping[str, object],
    *,
    filename: str,
    schema: str,
    accession: str,
    species: str,
) -> None:
    _require_equal(payload.get("schema_version"), schema, f"{filename} schema")
    _require_equal(payload.get("project_accession"), accession, f"{filename} project")
    _require_equal(payload.get("species_latin_name"), species, f"{filename} species")


def _validate_declared_counts(
    payload: Mapping[str, object], filename: str, rows: list[_Row]
) -> None:
    if filename != "sample_master.json":
        _require_count(payload.get("row_count"), len(rows), f"{filename} row_count")
        return
    biological = sum(
        row.get("source_native_identity_kind") != "sequencing_experiment_accession"
        for row in rows
    )
    final = sum(row.get("sample_identity_resolution") == "final" for row in rows)
    ambiguous = sum(
        row.get("sample_identity_resolution") == "ambiguous" for row in rows
    )
    _require_count(
        payload.get("recovered_sample_count"), biological, "master recovered"
    )
    _require_count(payload.get("final_sample_count"), final, "master final")
    _require_count(payload.get("ambiguity_row_count"), ambiguous, "master ambiguity")


def _validate_row_identity(
    row: Mapping[str, object], *, accession: str, species: str, filename: str
) -> _SampleKey:
    _require_equal(row.get("project_accession"), accession, f"{filename} row project")
    _require_equal(row.get("species_latin_name"), species, f"{filename} row species")
    sample_id = _required_text(row, "repo_stable_sample_id")
    status = _required_text(row, "sample_identity_resolution")
    if status not in _IDENTITY_STATUSES:
        raise ValueError(
            f"unsupported sample identity status for {(accession, sample_id)!r}"
        )
    _required_vocabulary(
        row,
        "sample_evidence_status",
        ADNA_SAMPLE_EVIDENCE_STATUSES,
        key=(accession, sample_id),
    )
    if filename == "sample_master.json":
        _required_vocabulary(
            row,
            "source_native_identity_kind",
            ADNA_SOURCE_NATIVE_IDENTITY_KINDS,
            key=(accession, sample_id),
        )
    elif filename == "sample_chronology.json":
        for field, allowed in (
            ("chronology_strength", ADNA_CHRONOLOGY_STRENGTHS),
            ("chronology_evidence_class", ADNA_CHRONOLOGY_EVIDENCE_CLASSES),
            ("chronology_precision_posture", ADNA_CHRONOLOGY_PRECISION_POSTURES),
            (
                "chronology_normalization_status",
                ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
            ),
            ("dating_basis", ADNA_DATING_BASES),
        ):
            _required_vocabulary(row, field, allowed, key=(accession, sample_id))
    elif filename == "sample_sites.json":
        _required_vocabulary(
            row,
            "locality_resolution_status",
            ADNA_LOCALITY_RESOLUTION_STATUSES,
            key=(accession, sample_id),
        )
        _optional_vocabulary(
            row,
            "coordinate_basis",
            ADNA_COORDINATE_PROVENANCE_CLASSES,
            key=(accession, sample_id),
        )
        _optional_vocabulary(
            row,
            "coordinate_confidence",
            ADNA_COORDINATE_CONFIDENCE,
            key=(accession, sample_id),
        )
    return accession, sample_id


def _required_vocabulary(
    row: Mapping[str, object],
    field: str,
    allowed: tuple[str, ...] | set[str],
    *,
    key: _SampleKey,
) -> None:
    value = _required_text(row, field)
    if value not in allowed:
        raise ValueError(f"unsupported {field} for {key!r}: {value!r}")


def _optional_vocabulary(
    row: Mapping[str, object],
    field: str,
    allowed: tuple[str, ...] | set[str],
    *,
    key: _SampleKey,
) -> None:
    value = _optional_text(row.get(field))
    if value is not None and value not in allowed:
        raise ValueError(f"unsupported {field} for {key!r}: {value!r}")


def _validate_join_sets(
    masters: Mapping[_SampleKey, _Row],
    chronologies: Mapping[_SampleKey, _Row],
    sites: Mapping[_SampleKey, _Row],
) -> None:
    if set(chronologies) != set(sites):
        raise ValueError(
            "animal sample chronology and site identities do not reconcile"
        )
    biological = {
        key
        for key, row in masters.items()
        if row.get("source_native_identity_kind") != "sequencing_experiment_accession"
    }
    if set(chronologies) != biological:
        raise ValueError(
            "animal biological sample master identities do not reconcile to companions"
        )


def _validate_cross_surface_identity(
    master: Mapping[str, object],
    chronology: Mapping[str, object],
    site: Mapping[str, object],
    *,
    key: _SampleKey,
) -> None:
    for field in (
        "species_latin_name",
        "species_common_name",
        "project_accession",
        "repo_stable_sample_id",
        "preferred_sample_label",
        "sample_basis",
        "sample_evidence_status",
        "sample_identity_resolution",
        "sample_ambiguity_note",
    ):
        values = (master.get(field), chronology.get(field), site.get(field))
        if values[0] != values[1] or values[0] != values[2]:
            raise ValueError(f"cross-surface {field} mismatch for {key!r}")


def _validate_chronology_shape(row: Mapping[str, object], *, key: _SampleKey) -> None:
    status = _required_text(row, "chronology_normalization_status")
    if status not in _CHRONOLOGY_STATUSES:
        raise ValueError(f"unsupported chronology normalization for {key!r}")
    values = tuple(
        row.get(field) for field in ("time_start_bp", "time_end_bp", "time_mean_bp")
    )
    if status in {"text_only_unparsed", "unresolved"}:
        if any(value is not None for value in values):
            raise ValueError(f"noncomparable chronology exposes numeric BP for {key!r}")
        return
    precision = _required_text(row, "chronology_precision_posture")
    if precision not in _NUMERIC_CHRONOLOGY_PRECISION_POSTURES:
        raise ValueError(f"numeric chronology has incompatible precision for {key!r}")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise ValueError(f"normalized chronology requires integer BP for {key!r}")
    younger, older, mean = cast(tuple[int, int, int], values)
    if younger < 0 or younger > mean or mean > older:
        raise ValueError(f"invalid canonical BP interval for {key!r}")
    if status == "normalized_point" and not younger == mean == older:
        raise ValueError(f"normalized point chronology is not a point for {key!r}")
    if status == "normalized_interval" and younger == older:
        raise ValueError(f"normalized interval chronology is a point for {key!r}")
    if status == "normalized_point" and precision == "sample_precise_interval":
        raise ValueError(f"normalized point has interval precision for {key!r}")
    if status == "normalized_interval" and precision == "sample_precise_point":
        raise ValueError(f"normalized interval has point precision for {key!r}")


def _validate_coordinate_claim(
    master: Mapping[str, object], site: Mapping[str, object], *, key: _SampleKey
) -> None:
    posture = site.get("coordinate_mapping_posture")
    if posture not in {"", _MAPPABLE_POSTURE}:
        raise ValueError(f"unsupported coordinate mapping posture for {key!r}")
    if posture != _MAPPABLE_POSTURE:
        return
    basis = _required_text(site, "coordinate_basis")
    confidence = _required_text(site, "coordinate_confidence")
    if basis not in _MAPPABLE_COORDINATE_BASES:
        raise ValueError(f"mappable coordinate has incompatible basis for {key!r}")
    if confidence not in _MAPPABLE_COORDINATE_CONFIDENCE:
        raise ValueError(
            f"mappable coordinate has incompatible confidence for {key!r}"
        )
    _coordinate(master.get("latitude_text"), -90.0, 90.0, key, "latitude")
    _coordinate(master.get("longitude_text"), -180.0, 180.0, key, "longitude")


def _refusal_reason(
    master: Mapping[str, object],
    chronology: Mapping[str, object],
    site: Mapping[str, object],
) -> str | None:
    if master.get("sample_identity_resolution") != "final":
        return "sample_identity_not_final"
    if chronology.get("chronology_normalization_status") not in {
        "normalized_interval",
        "normalized_point",
    }:
        return "source_chronology_not_comparable"
    if site.get("coordinate_mapping_posture") != _MAPPABLE_POSTURE:
        return "source_coordinate_not_mappable"
    if not _has_text(master, _SAMPLE_PROVENANCE_FIELDS):
        return "sample_provenance_unavailable"
    if not _has_text(chronology, _CHRONOLOGY_PROVENANCE_FIELDS):
        return "chronology_provenance_unavailable"
    if not _has_text(site, _SITE_PROVENANCE_FIELDS):
        return "site_provenance_unavailable"
    return None


_SAMPLE_PROVENANCE_FIELDS = (
    "sample_lineage_path",
    "sample_lineage_locator",
    "sample_lineage_excerpt",
)
_CHRONOLOGY_PROVENANCE_FIELDS = (
    "chronology_provenance_path",
    "chronology_provenance_kind",
    "chronology_provenance_locator",
    "chronology_provenance_text",
)
_SITE_PROVENANCE_FIELDS = (
    "location_evidence_artifact_path",
    "location_evidence_artifact_kind",
    "location_evidence_locator",
    "location_evidence_text",
)


def _build_node(
    master: Mapping[str, object],
    chronology: Mapping[str, object],
    site: Mapping[str, object],
    *,
    registry_row: Mapping[str, object],
) -> AnimalSampleChronologyNode:
    project = _required_text(master, "project_accession")
    sample_id = _required_text(master, "repo_stable_sample_id")
    younger = _required_int(chronology, "time_start_bp")
    older = _required_int(chronology, "time_end_bp")
    mean = _required_int(chronology, "time_mean_bp")
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
        younger_bp=younger,
        older_bp=older,
        mean_bp=mean,
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


def _build_input_identity(
    data_root: Path, captured_inputs: Mapping[Path, bytes]
) -> AnimalChronologyInputIdentity:
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
    combined = _framed_digest(all_members)
    return AnimalChronologyInputIdentity(
        combined_sha256=combined,
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


def _has_text(row: Mapping[str, object], fields: tuple[str, ...]) -> bool:
    return all(
        isinstance(row.get(field), str) and str(row[field]).strip() for field in fields
    )


def _require_equal(observed: object, expected: object, label: str) -> None:
    if observed != expected:
        raise ValueError(
            f"{label} mismatch: expected {expected!r}, observed {observed!r}"
        )


def _require_count(observed: object, expected: int, label: str) -> None:
    if (
        isinstance(observed, bool)
        or not isinstance(observed, int)
        or observed != expected
    ):
        raise ValueError(
            f"{label} mismatch: expected {expected}, observed {observed!r}"
        )


__all__ = ["load_animal_sample_chronology_corpus"]

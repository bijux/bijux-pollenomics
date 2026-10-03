"""Authenticate one retained Neotoma publication response against its capture."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .contracts import ReportRebuildError, require_relative_path
from .qualified_sources import (
    QualifiedReportSources,
    _checked_file,
    _file_spec,
    _object,
    _regular_path,
)

SCHEMA = "qualified-neotoma-publication-link.v1"
FIELDS = frozenset(
    {
        "schema_version",
        "source_id",
        "capture_manifest",
        "response",
        "dataset_id",
        "publication_id",
        "source_api",
        "response_count",
    }
)
SOURCE_ID = "neotoma/publication-links/2026-09-29"
RESPONSE = "responses/dataset-4200-publications.json"
SOURCE_API = "https://api.neotomadb.org/v2.0/data/datasets/"


def validated_neotoma_publication_link(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Bind the one response and its authenticated capture manifest in place."""
    repository = _regular_path(repository, directory=True)
    relative = require_relative_path(descriptor_path.as_posix(), "source descriptor")
    descriptor_file = _regular_path(repository / relative)
    payload = descriptor_file.read_bytes()
    descriptor = _object(payload)
    if frozenset(descriptor) != FIELDS or descriptor["schema_version"] != SCHEMA:
        raise ReportRebuildError("Neotoma publication descriptor differs")
    if (
        descriptor["source_id"] != SOURCE_ID
        or type(descriptor["dataset_id"]) is not int
        or descriptor["dataset_id"] != 4200
        or type(descriptor["publication_id"]) is not int
        or descriptor["publication_id"] != 16060
        or descriptor["source_api"] != SOURCE_API
        or type(descriptor["response_count"]) is not int
        or descriptor["response_count"] != 169
    ):
        raise ReportRebuildError("Neotoma publication source identity differs")
    manifest_spec = _file_spec(descriptor["capture_manifest"])
    response_spec = _file_spec(descriptor["response"])
    if (
        manifest_spec["path"] != "capture-manifest.json"
        or response_spec["path"] != RESPONSE
    ):
        raise ReportRebuildError("Neotoma publication source filenames differ")
    root = _regular_path(source_root, directory=True)
    if root.is_relative_to(repository) or repository.is_relative_to(root):
        raise ReportRebuildError("Neotoma publication source must be external")
    directory = _regular_path(root / SOURCE_ID, directory=True)
    manifest_file = _checked_file(directory, manifest_spec)
    response_file = _checked_file(directory, response_spec)
    manifest = _object(manifest_file.read_bytes())
    responses = manifest.get("responses")
    if (
        manifest.get("schema_version") != "neotoma-candidate-publication-capture.v1"
        or manifest.get("source_api") != SOURCE_API
        or type(manifest.get("response_count")) is not int
        or manifest["response_count"] != 169
        or not isinstance(responses, list)
        or len(responses) != 169
        or any(not isinstance(row, dict) for row in responses)
    ):
        raise ReportRebuildError("Neotoma publication capture contract differs")
    paths = [row.get("path") for row in responses]
    if any(not isinstance(path, str) for path in paths) or len(set(paths)) != len(
        paths
    ):
        raise ReportRebuildError("Neotoma publication capture has duplicate paths")
    chosen: list[dict[str, Any]] = [
        row for row in responses if row.get("path") == RESPONSE
    ]
    if len(chosen) != 1:
        raise ReportRebuildError("Neotoma publication response absent from capture")
    row = chosen[0]
    if (
        row.get("dataset_id") != 4200
        or row.get("http_status") != 200
        or row.get("sha256") != response_spec["sha256"]
        or row.get("bytes") != response_spec["size"]
        or row.get("url") != f"{SOURCE_API}4200/publications"
    ):
        raise ReportRebuildError("Neotoma publication response capture differs")
    response = _object(response_file.read_bytes())
    data = response.get("data")
    if not isinstance(data, list):
        raise ReportRebuildError("Neotoma publication response data differs")
    primary = [
        publication
        for item in data
        if isinstance(item, dict)
        for publication in [item.get("publication")]
        if isinstance(publication, dict)
        and isinstance(publication.get("datasets"), list)
        and any(
            isinstance(dataset, dict)
            and dataset.get("siteid") == 3234
            and dataset.get("datasetid") == 4200
            and dataset.get("primary") is True
            for dataset in publication["datasets"]
        )
    ]
    if len(primary) != 1 or primary[0].get("publicationid") != 16060:
        raise ReportRebuildError("Neotoma publication primary link differs")
    if (
        descriptor_file.read_bytes() != payload
        or hashlib.sha256(manifest_file.read_bytes()).hexdigest()
        != manifest_spec["sha256"]
        or hashlib.sha256(response_file.read_bytes()).hexdigest()
        != response_spec["sha256"]
    ):
        raise ReportRebuildError("Neotoma publication inputs changed during check")
    return QualifiedReportSources(
        directory=directory,
        inputs={
            relative: descriptor_file,
            f"external/{SOURCE_ID}/{manifest_spec['path']}": manifest_file,
            f"external/{SOURCE_ID}/{response_spec['path']}": response_file,
        },
        descriptor_sha256=hashlib.sha256(payload).hexdigest(),
    )

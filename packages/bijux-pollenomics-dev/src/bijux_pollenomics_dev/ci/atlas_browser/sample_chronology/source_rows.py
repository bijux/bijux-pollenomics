"""Exact published sample identities and chronology for bounded browser verification."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
from typing import Any

from bijux_pollenomics.adna.domain.models import AdnaChronology
from bijux_pollenomics.adna.domain.models.localities import AdnaSampleChronologySupport
from bijux_pollenomics.adna.species.homo_sapiens.records import _parse_sample_row

from ..candidate_files import regular_bytes

SWEDISH_SOURCE = "docs/report/countries/sweden/sweden_aadr_v66_samples.csv"
DANISH_SOURCE = "docs/report/countries/denmark/denmark_aadr_v66_samples.csv"
SWEDISH_LOCALITY = "Frälsegården (Västra Götalands län, Falköping, Falbygden)"
DANISH_UNDATED_SAMPLE = "CGG_2_105338.SG"
GAP_BP = 4141


def normalized_chronology_from_published_row(row: dict[str, str]) -> AdnaChronology:
    """Reconstruct the existing AADR source normalization and verify its export.

    The retained CSV is a published export, not a newly authenticated raw source.
    Only the canonical constructor's chronology is used. Its evidence class,
    precision and refusal are preserved; no source dating metadata is invented.
    """
    schema = {key: key for key in row}
    release = next(
        (
            part.removeprefix("release:")
            for part in row["accession_lineage"].split(";")
            if part.startswith("release:")
        ),
        "not_declared_in_export",
    )
    normalized = _parse_sample_row(
        row,
        schema=schema,
        dataset_name="retained_published_export",
        source_release=release,
        source_family=row["source_family"],
        record_modality="published_source_export",
        review_strength="not_a_new_source_review",
        provenance_quality="exact_published_export",
    )
    if normalized is None:
        raise ValueError(
            "Published sample cannot be reconstructed by its canonical AADR source parser"
        )
    chronology = normalized.chronology
    expected = tuple(
        int(row[field]) if row.get(field) else None
        for field in ("time_start_bp", "time_end_bp", "time_mean_bp")
    )
    if (
        chronology.time_start_bp,
        chronology.time_end_bp,
        chronology.time_mean_bp,
    ) != expected:
        raise ValueError(
            "Canonical AADR chronology disagrees with published source endpoints"
        )
    if (
        chronology.dating_basis != row["dating_basis"]
        or chronology.original_text != row["time_label"]
    ):
        raise ValueError(
            "Canonical AADR chronology disagrees with published date basis or original label"
        )
    return chronology


def feature_from_rows(
    rows: list[dict[str, str]], *, source_path: str
) -> dict[str, Any]:
    """Retain exact source fields; missing epoch/type/calibration stays undeclared."""
    if not rows or len(rows) > 100:
        raise ValueError("Browser sample support requires one bounded source locality")
    identities = [row["genetic_id"] for row in rows]
    if len(set(identities)) != len(identities) or any(
        not value for value in identities
    ):
        raise ValueError("Browser source genetic identities must be unique")
    if (
        len(
            {
                (
                    row["locality"],
                    row["political_entity"],
                    row["latitude"],
                    row["longitude"],
                )
                for row in rows
            }
        )
        != 1
    ):
        raise ValueError(
            "Browser sample support cannot merge distinct source localities"
        )
    supports = []
    for row in rows:
        if (
            row["schema_version"] != "adna-sample-record-export.v1"
            or row["source_family"] != "AADR"
        ):
            raise ValueError(
                "Browser source requires the maintained published AADR sample export"
            )
        chronology = normalized_chronology_from_published_row(row)
        release = next(
            (
                item.removeprefix("release:")
                for item in row["accession_lineage"].split(";")
                if item.startswith("release:")
            ),
            "not_declared_in_export",
        )
        support = AdnaSampleChronologySupport(
            row["genetic_id"],
            chronology,
            source_release=release,
            provenance_path=source_path,
            provenance_locator="genetic_id=" + row["genetic_id"],
            provenance_excerpt=row["time_label"],
            provenance_kind="published_source_export",
        )
        # The strict maintained decoder rejects malformed/nonintegral support rather than inventing a date.
        supports.append(
            AdnaSampleChronologySupport.from_dict(support.as_dict()).as_dict()
        )
    valid = [
        (int(row["time_start_bp"]), int(row["time_end_bp"]))
        for row in rows
        if row["time_start_bp"]
        and row["time_end_bp"]
        and 0 <= int(row["time_start_bp"]) <= int(row["time_end_bp"])
    ]
    first = rows[0]
    return {
        "record_id": "aadr:v66:published-locality:" + first["genetic_id"],
        "title": first["locality"],
        "country": first["political_entity"],
        "latitude": float(first["latitude"]),
        "longitude": float(first["longitude"]),
        "sample_ids": identities,
        "source_family": first["source_family"],
        "raw_master_ids": [row["master_id"] for row in rows],
        "sample_count": len(rows),
        "sample_chronologies": supports,
        "chronology_role": "locality_sample_coverage_hull",
        "time_start_bp": min((pair[0] for pair in valid), default=None),
        "time_end_bp": max((pair[1] for pair in valid), default=None),
        "source_name": "Published AADR v66 sample export",
        "source_path": source_path,
        "description": "Exact published sample supports. Locality coverage is a display hull; no new source review, calibration or ecological event admission.",
    }


def load_source_features(
    repository: Path,
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]]]:
    """Select a real disconnected Swedish locality and one real undated Danish sample."""
    features, source_records, inputs = [], [], {}
    for path, selector in (
        (SWEDISH_SOURCE, SWEDISH_LOCALITY),
        (DANISH_SOURCE, DANISH_UNDATED_SAMPLE),
    ):
        raw = regular_bytes(repository / path)
        inputs[path] = hashlib.sha256(raw).hexdigest()
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
        if len(rows) > 1000:
            raise ValueError(
                "Browser published sample source exceeds the declared bound"
            )
        chosen = [
            row
            for row in rows
            if (
                row["locality"] == selector
                if path == SWEDISH_SOURCE
                else row["genetic_id"] == selector
            )
        ]
        feature = feature_from_rows(chosen, source_path=path)
        if path == DANISH_SOURCE and (
            len(chosen) != 1
            or feature["time_start_bp"] is not None
            or feature["time_end_bp"] is not None
        ):
            raise ValueError(
                "Frozen Danish source control must remain genuinely undated"
            )
        features.append(feature)
        source_records.append(
            {
                "source_path": path,
                "source_sha256": inputs[path],
                "source_row_count": len(rows),
                "selected_rows": chosen,
                "feature": feature,
            }
        )
    return features, inputs, source_records

"""Source partition, vocabulary, and digest identity refusal tests."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import cast

import pytest

from ..fixtures import (
    _READ_BYTES,
    _REPOSITORY_ROOT,
    _build,
    _replace_input_document,
    _set_nested,
)


def test_duplicate_source_stage_identity_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def duplicate(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows.append(deepcopy(rows[0]))

    _replace_input_document(
        monkeypatch, "data/source_family_evidence_stage_matrix.json", duplicate
    )

    with pytest.raises(ValueError, match="duplicate source keys"):
        _build()


def test_duplicate_json_object_key_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = (_REPOSITORY_ROOT / "data/collection_summary.json").resolve()
    document = cast(dict[str, object], json.loads(_READ_BYTES(target)))
    replacement = (
        b'{"source_hashes":{},"source_hashes":'
        + json.dumps(document["source_hashes"]).encode("utf-8")
        + b"}"
    )

    def read_bytes(path: Path) -> bytes:
        return replacement if path.resolve() == target else _READ_BYTES(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)

    with pytest.raises(ValueError, match="duplicate JSON key: source_hashes"):
        _build()


def test_duplicate_landclim_reported_country_label_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def duplicate_label(document: dict[str, object]) -> None:
        features = cast(list[dict[str, object]], document["features"])
        for feature in features:
            properties = cast(dict[str, object], feature["properties"])
            popup_rows = cast(list[dict[str, object]], properties["popup_rows"])
            reported = next(
                (row for row in popup_rows if row.get("label") == "Reported country"),
                None,
            )
            if reported is not None:
                popup_rows.append(deepcopy(reported))
                return
        raise AssertionError("fixture has no Reported country row")

    _replace_input_document(
        monkeypatch,
        "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
        duplicate_label,
    )

    with pytest.raises(ValueError, match="duplicate Reported country labels"):
        _build()


def test_unknown_neotoma_country_partition_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def add_unknown_country(document: dict[str, object]) -> None:
        reconciliation = cast(dict[str, object], document["reconciliation"])
        attribution = cast(
            dict[str, object], reconciliation["country_attribution_counts"]
        )
        counts = cast(dict[str, object], attribution["raw_country_codes"])
        counts["XX"] = 17

    _replace_input_document(
        monkeypatch, "data/neotoma/relational/reconciliation.json", add_unknown_country
    )

    with pytest.raises(ValueError, match="unsupported country partitions"):
        _build()


def test_aadr_summary_country_must_match_its_partition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def change_country(document: dict[str, object]) -> None:
        document["country"] = "Denmark"

    _replace_input_document(
        monkeypatch,
        "docs/report/countries/sweden/sweden_aadr_v66_summary.json",
        change_country,
    )

    with pytest.raises(ValueError, match="does not match partition: SE"):
        _build()


@pytest.mark.parametrize(
    ("relative_path", "field_path"),
    (
        (
            "data/collection_summary.json",
            ("source_hashes", "landclim", "snapshot_sha256"),
        ),
        ("data/boundaries/raw/source_manifest.json", ("normalized_artifact", "sha256")),
        ("data/neotoma/relational/reconciliation.json", ("source_snapshot_id",)),
        (
            "data/collection_summary.json",
            ("source_hashes", "sead", "snapshot_sha256"),
        ),
    ),
)
def test_governed_digest_identities_require_sha256_syntax(
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    field_path: tuple[str, ...],
) -> None:
    def corrupt_digest(document: dict[str, object]) -> None:
        _set_nested(document, field_path, "not-a-sha256")

    _replace_input_document(monkeypatch, relative_path, corrupt_digest)

    with pytest.raises(ValueError, match="SHA-256 digest|sha256 identity"):
        _build()


def test_source_stage_authority_vocabulary_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fabricate_status(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows[0]["authority_status"] = "fabricated"

    _replace_input_document(
        monkeypatch, "data/source_family_evidence_stage_matrix.json", fabricate_status
    )

    with pytest.raises(ValueError, match="unsupported authority_status"):
        _build()

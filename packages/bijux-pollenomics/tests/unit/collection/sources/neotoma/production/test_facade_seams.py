from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import production


def test_production_resolves_all_orchestration_dependencies_from_facade(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []
    raw = production._RawArchive(
        rows=({},), source_snapshot_id="sha256:raw", part_digests=("part",)
    )
    boundary = production._BoundaryAuthority(
        boundaries={},
        artifact_digest="sha256:boundary",
        version="fixture",
        authority_id="sha256:authority",
    )

    def validate_output(output: Path, parent: Path) -> Path:
        calls.append("output")
        return output

    def load_raw(path: Path) -> production._RawArchive:
        calls.append("raw")
        return raw

    def load_boundary(path: Path) -> production._BoundaryAuthority:
        calls.append("boundary")
        return boundary

    monkeypatch.setattr(
        production,
        "_validated_output_target",
        validate_output,
    )
    monkeypatch.setattr(
        production,
        "_load_validated_raw_archive",
        load_raw,
    )
    monkeypatch.setattr(
        production,
        "_load_validated_boundary_authority",
        load_boundary,
    )
    monkeypatch.setattr(production, "_build_id", lambda **kwargs: "sha256:build")
    monkeypatch.setattr(
        production, "build_neotoma_site_country_decisions", lambda *args, **kwargs: {}
    )
    snapshot = {
        "sites": [],
        "reconciliation": {
            "country_counts": {
                code: {"sites": 0} for code in ("SE", "DK", "NO", "FI", "UNASSIGNED")
            },
            "country_attribution_counts": {"decision_statuses": {}},
        },
    }
    monkeypatch.setattr(
        production,
        "build_neotoma_relational_snapshot",
        lambda *args, **kwargs: snapshot,
    )
    monkeypatch.setattr(
        production,
        "materialize_neotoma_relational_snapshot",
        lambda *args, **kwargs: tmp_path / "manifest.json",
    )

    report = production.run_neotoma_relational_production(
        raw_archive_root=tmp_path,
        boundary_root=tmp_path,
        output_root=tmp_path / "output",
        approved_output_parent=tmp_path,
    )

    assert calls == ["output", "raw", "boundary"]
    assert report.to_dict() == {
        "manifest_path": str(tmp_path / "manifest.json"),
        "source_snapshot_id": "sha256:raw",
        "boundary_authority_id": "sha256:authority",
        "build_id": "sha256:build",
        "raw_part_count": 1,
        "raw_row_count": 1,
        "site_count": 0,
        "country_counts": dict.fromkeys(("SE", "DK", "NO", "FI", "UNASSIGNED"), 0),
        "country_decision_counts": dict.fromkeys(
            ("assigned", "review", "unassigned", "refused"), 0
        ),
    }


def test_validation_helpers_resolve_facade_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    integer_calls: list[tuple[object, str]] = []

    def parse_integer(value: object, label: str) -> int:
        integer_calls.append((value, label))
        return 7

    monkeypatch.setattr(production, "_integer", parse_integer)
    assert production._positive_integer("value", "positive") == 7
    assert production._non_negative_integer("value", "non-negative") == 7
    assert production._integer_list(["value"], "list") == [7]
    assert integer_calls == [
        ("value", "positive"),
        ("value", "non-negative"),
        ("value", "list"),
    ]


def test_cli_resolves_parser_runner_codec_and_error_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = SimpleNamespace(
        producer_version="1",
        rows_per_part=1,
        proximity_tolerance=0.15,
        raw_country_alias=[],
        raw_archive=Path("raw"),
        boundary_root=Path("boundaries"),
        output=Path("output"),
        approved_output_parent=Path("approved"),
    )
    parser = SimpleNamespace(parse_args=lambda argv: args)
    monkeypatch.setattr(production, "_parser", lambda: parser)

    def fail(**kwargs: Any) -> production.NeotomaProductionReport:
        raise ValueError("fixture refusal")

    monkeypatch.setattr(production, "run_neotoma_relational_production", fail)
    assert production.main([]) == 1


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (lambda: production._mapping([], "payload"), "payload must be an object"),
        (lambda: production._integer(True, "count"), "count must be an integer"),
        (
            lambda: production._parse_alias("invalid"),
            "aliases must use non-empty RAW=COUNTRY values",
        ),
    ],
)
def test_refusal_text_is_preserved(operation: Any, message: str) -> None:
    with pytest.raises((ValueError, argparse.ArgumentTypeError), match=message):
        operation()

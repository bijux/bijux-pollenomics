"""Bind real review artifact bytes while keeping source reports immutable."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.taxa_review.lra_parameters.intake import (
    bind_lra_parameter_authorities,
)
from bijux_pollenomics_dev.taxa_review.workflow import write_review

from .test_projection import authorities


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    priority, provenance, review = authorities()
    priority.pop("input_file_sha256")
    provenance.pop("input_file_sha256")
    review_path = tmp_path / "review"
    write_review(review, review_path)
    priority_path, provenance_path = (
        tmp_path / "priority.json",
        tmp_path / "provenance.json",
    )
    priority_path.write_text(json.dumps(priority, sort_keys=True) + "\n")
    provenance_path.write_text(json.dumps(provenance, sort_keys=True) + "\n")
    return (
        review_path,
        priority_path,
        provenance_path,
        {
            "expected_review_sha256": sha(review_path / "taxa-review.json"),
            "expected_priority_sha256": sha(priority_path),
            "expected_provenance_sha256": sha(provenance_path),
        },
    )


def test_physical_bindings_match_written_priority_and_review(tmp_path: Path) -> None:
    review, priority, provenance, pins = source(tmp_path)
    before = {
        path: path.read_bytes()
        for path in (priority, provenance, review / "taxa-review.json")
    }
    destination = tmp_path / "bound"
    bound_priority, bound_provenance, bundle, provenance_sha = (
        bind_lra_parameter_authorities(
            review,
            priority,
            provenance,
            destination,
            **pins,
        )
    )
    assert bound_priority["input_file_sha256"]["full_review"] == sha(
        review / "taxa-review.json"
    )
    assert bound_provenance["input_file_sha256"]["priority"] == sha(
        destination / "priority.json"
    )
    assert provenance_sha == sha(destination / "provenance.json")
    assert all(path.read_bytes() == body for path, body in before.items())
    assert bundle["scientific_admission_allowed"] is False
    receipt = json.loads((destination / "completion.json").read_text())
    assert receipt["canonical_import_allowed"] is False
    assert receipt["publication_allowed"] is False


@pytest.mark.parametrize("component", ["review", "priority", "provenance"])
def test_changed_physical_source_refuses_before_outputs(
    tmp_path: Path, component: str
) -> None:
    review, priority, provenance, pins = source(tmp_path)
    paths = {
        "review": review / "taxa-review.json",
        "priority": priority,
        "provenance": provenance,
    }
    with paths[component].open("a") as stream:
        stream.write(" ")
    destination = tmp_path / "bound"
    with pytest.raises(ValueError, match="source hash differs"):
        bind_lra_parameter_authorities(
            review, priority, provenance, destination, **pins
        )
    assert not destination.exists()


def test_semantically_foreign_provenance_refuses_before_outputs(tmp_path: Path) -> None:
    review, priority, provenance, pins = source(tmp_path)
    body: dict[str, Any] = json.loads(provenance.read_text())
    body["source_snapshot_id"] = "sha256:" + "9" * 64
    provenance.write_text(json.dumps(body) + "\n")
    pins["expected_provenance_sha256"] = sha(provenance)
    destination = tmp_path / "bound"
    with pytest.raises(ValueError, match="identities or denominators differ"):
        bind_lra_parameter_authorities(
            review, priority, provenance, destination, **pins
        )
    assert not destination.exists()


def test_existing_file_bindings_are_not_silently_replaced(tmp_path: Path) -> None:
    review, priority, provenance, pins = source(tmp_path)
    body: dict[str, Any] = json.loads(priority.read_text())
    body["input_file_sha256"] = {"full_review": "0" * 64}
    priority.write_text(json.dumps(body) + "\n")
    pins["expected_priority_sha256"] = sha(priority)
    with pytest.raises(ValueError, match="unsupported file bindings"):
        bind_lra_parameter_authorities(
            review, priority, provenance, tmp_path / "bound", **pins
        )


def test_incomplete_review_receipt_refuses(tmp_path: Path) -> None:
    review, priority, provenance, pins = source(tmp_path)
    (review / "completion.json").unlink()
    with pytest.raises(ValueError, match="completion receipt"):
        bind_lra_parameter_authorities(
            review, priority, provenance, tmp_path / "bound", **pins
        )


def test_existing_output_directory_is_preserved(tmp_path: Path) -> None:
    review, priority, provenance, pins = source(tmp_path)
    destination = tmp_path / "bound"
    destination.mkdir()
    protected = destination / "owner.txt"
    protected.write_text("existing owner\n")
    with pytest.raises(FileExistsError):
        bind_lra_parameter_authorities(
            review, priority, provenance, destination, **pins
        )
    assert protected.read_text() == "existing owner\n"

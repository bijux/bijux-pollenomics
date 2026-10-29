"""Keep fixed-start scientific publication authority finite and source-bound."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    author_love_starts as subject,
)


def _owner() -> JsonObject:
    return {
        "owner_id": subject.OWNER,
        "role": "retained_source",
        "paths": [subject.PREFIX + "report.json", subject.PREFIX + "trials.jsonl"],
        "producer_paths": [],
        "producer_inputs": [],
    }


def test_unregistered_absent_authority_admits_no_report(tmp_path: Path) -> None:
    assert subject.validated_author_love_start_capture(tmp_path, {}, []) == ((), {})


def test_foreign_owner_cannot_claim_new_numerical_products(tmp_path: Path) -> None:
    authority = tmp_path / subject.AUTHORITY
    authority.parent.mkdir(parents=True)
    authority.write_text("{}")
    owner = _owner()
    owner["owner_id"] = "different/scientific-owner"
    with pytest.raises(ReportRebuildError, match="exact new owner differs"):
        subject.validated_author_love_start_capture(tmp_path, {}, [owner])


def test_unbound_future_execution_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(subject, "AUTHORITY_SHA256", None)
    with pytest.raises(
        ReportRebuildError, match="actual execution authority not bound"
    ):
        subject.validated_author_love_start_capture(tmp_path, {}, [_owner()])


def test_public_receipt_hash_is_checked_before_json(tmp_path: Path) -> None:
    relative = "evidence.json"
    raw = b'{"actual_exit":0}'
    (tmp_path / relative).write_bytes(raw)
    assert (
        subject._read(tmp_path, relative, hashlib.sha256(raw).hexdigest(), 128) == raw
    )
    with pytest.raises(ReportRebuildError, match="evidence SHA256 differs"):
        subject._read(tmp_path, relative, "0" * 64, 128)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b"[]"])
def test_ambiguous_authority_json_is_refused(raw: bytes) -> None:
    with pytest.raises(ReportRebuildError):
        subject._decode(raw)

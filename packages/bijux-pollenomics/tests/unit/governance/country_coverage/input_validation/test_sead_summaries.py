"""SEAD embedded-summary and acquisition-lineage refusal tests."""

from __future__ import annotations

from typing import cast

import pytest

from ..fixtures import (
    _SEAD_ADMISSION_PATH,
    _SEAD_DECISIONS_PATH,
    _SEAD_SITES_PATH,
    _build,
    _replace_input_document,
    _set_nested,
)


@pytest.mark.parametrize(
    ("relative_path", "field_path", "value", "message"),
    (
        (
            _SEAD_DECISIONS_PATH,
            ("decision_status_counts", "assigned"),
            2_070,
            "decision status counts",
        ),
        (
            _SEAD_DECISIONS_PATH,
            ("country_counts", "SE"),
            1_924,
            "decision country counts",
        ),
        (
            _SEAD_DECISIONS_PATH,
            ("bbox_site_count",),
            2_194,
            "bbox site count",
        ),
        (
            _SEAD_ADMISSION_PATH,
            ("country_accounting", "admitted_site_count"),
            2_068,
            "admission identity changed",
        ),
        (
            _SEAD_ADMISSION_PATH,
            ("scope_id",),
            f"sha256:{'f' * 64}",
            "admission identity changed",
        ),
    ),
)
def test_sead_embedded_summaries_and_lineage_reconcile(
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    field_path: tuple[str, ...],
    value: object,
    message: str,
) -> None:
    def corrupt_summary(document: dict[str, object]) -> None:
        _set_nested(document, field_path, value)

    _replace_input_document(monkeypatch, relative_path, corrupt_summary)

    with pytest.raises(ValueError, match=message):
        _build()


def test_sead_decision_boundary_digest_matches_governed_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_boundary(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        decision = cast(dict[str, object], decisions[0]["decision"])
        decision["boundary_artifact_digest"] = f"sha256:{'f' * 64}"

    _replace_input_document(
        monkeypatch,
        _SEAD_DECISIONS_PATH,
        corrupt_boundary,
    )

    with pytest.raises(ValueError, match="governed geometry"):
        _build()


def test_sead_decision_method_counts_are_recomputed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_method_counts(document: dict[str, object]) -> None:
        counts = cast(dict[str, int], document["decision_method_counts"])
        counts["strict_boundary_containment"] += 1

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, corrupt_method_counts)

    with pytest.raises(ValueError, match="decision method counts"):
        _build()


def test_sead_country_assignment_digest_is_recomputed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_assignment_digest(document: dict[str, object]) -> None:
        accounting = cast(dict[str, object], document["country_accounting"])
        accounting["country_assignment_sha256"] = "f" * 64

    _replace_input_document(
        monkeypatch, _SEAD_ADMISSION_PATH, corrupt_assignment_digest
    )

    with pytest.raises(ValueError, match="admission identity changed"):
        _build()


def test_sead_admitted_site_identity_is_bound_to_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_site(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows[0]["site_uuid"] = "fabricated-site-uuid"

    _replace_input_document(monkeypatch, _SEAD_SITES_PATH, corrupt_site)

    with pytest.raises(ValueError, match="site_uuid"):
        _build()


def test_sead_bundle_digest_binds_copied_file_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_bundle(document: dict[str, object]) -> None:
        document["acquisition_bundle_sha256"] = f"sha256:{'f' * 64}"

    _replace_input_document(monkeypatch, _SEAD_ADMISSION_PATH, corrupt_bundle)

    with pytest.raises(ValueError, match="admission identity changed"):
        _build()

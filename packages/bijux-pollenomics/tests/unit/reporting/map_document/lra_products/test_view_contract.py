"""Exact view byte identity and explicit native row/site boundary refusals."""

from __future__ import annotations

import hashlib
import json

import pytest

from bijux_pollenomics.reporting.map_document.native_lra import bind_native_view

from .support import view_fixture


def test_view_hash_binds_original_bytes_with_unicode() -> None:
    view = view_fixture()
    bound = bind_native_view(view)
    assert json.loads(bound["bytes"]) == view
    assert hashlib.sha256(bound["bytes"].encode("ascii")).hexdigest() == bound["sha256"]


@pytest.mark.parametrize(
    "case",
    [
        "hash",
        "row",
        "membership",
        "unit",
        "value",
        "source",
        "unsafe_integer",
        "nonfinite",
        "anchor",
        "boolean_bin",
        "mixed_age",
        "multimodal",
        "signed",
    ],
)
def test_invalid_view_cannot_enter_renderer(case: str) -> None:
    view = view_fixture()
    if case == "hash":
        view["geometry_sha256"] = "missing"
    if case == "row":
        view["rows"].append(view["rows"][0])
    if case == "membership":
        view["sites"][0]["model_row_ids"] = []
    if case == "unit":
        view["rows"][0]["native_unit"] = "fraction"
    if case == "value":
        view["rows"][0]["native_value"] = 0
    if case == "source":
        view["data_kind"] = "source"
    if case == "unsafe_integer":
        view["rows"][0]["pairing_coordinate"] = 2**53 + 1
    if case == "nonfinite":
        view["rows"][0]["pairing_coordinate"] = float("nan")
    if case == "anchor":
        view["sites"][2]["anchor_id"] = "invented"
    if case == "boolean_bin":
        view["rows"][0]["declared_bin"]["younger_bp"] = True
    if case == "mixed_age":
        view["rows"][0]["age_type"] = "calibrated_bp"
    if case == "multimodal":
        view["rows"][0]["age_support_bp"] = [[10, 11], [19, 20]]
    if case == "signed":
        view["rows"][0]["declared_bin"]["younger_bp"] = -10
    with pytest.raises(ValueError):
        bind_native_view(view)


@pytest.mark.parametrize(
    "key", ["row_id", "role", "site_id", "taxon", "bin_id", "statistic"]
)
@pytest.mark.parametrize("value", [123, "", False])
def test_filter_identity_requires_nonempty_source_string(
    key: str, value: object
) -> None:
    view = view_fixture()
    view["rows"][0][key] = value
    with pytest.raises(ValueError, match="identities"):
        bind_native_view(view)


@pytest.mark.parametrize("value", ["not-a-number", "Infinity", "NaN", ""])
def test_original_native_text_must_still_be_finite_decimal(value: str) -> None:
    view = view_fixture()
    view["rows"][0]["native_value"] = value
    with pytest.raises(ValueError):
        bind_native_view(view)

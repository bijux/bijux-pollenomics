"""Finite unresolved-context requests never confer country authority."""

from __future__ import annotations

import importlib

import pytest


def api():
    """Require the separate context API rather than a country-schema alias."""
    name = "bijux_pollenomics.collection.sources.sead.acquisition.context"
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        pytest.fail("The explicit unresolved-context contract is not implemented")


def test_native_site_identity_and_unresolved_status_are_explicit():
    module = api()
    site = module.SeadContextSite(2, "c3e38c42-36ad-40dd-8958-436ad141d108", "review")
    assert site.site_id == 2
    assert site.membership_status == "review"
    assert not hasattr(site, "country_code")


@pytest.mark.parametrize("site_id", [True, 0, -1, "2", 2.0])
def test_context_site_refuses_non_native_identity(site_id):
    with pytest.raises(ValueError):
        api().SeadContextSite(site_id, "c3e38c42-36ad-40dd-8958-436ad141d108", "review")


@pytest.mark.parametrize("status", ["SE", "assigned", "", None])
def test_context_site_cannot_invent_country_decision(status):
    with pytest.raises(ValueError):
        api().SeadContextSite(2, "c3e38c42-36ad-40dd-8958-436ad141d108", status)


@pytest.mark.parametrize(
    "uuid", ["", "not-a-uuid", "C3E38C42-36AD-40DD-8958-436AD141D108"]
)
def test_context_site_refuses_ambiguous_uuid(uuid):
    with pytest.raises(ValueError):
        api().SeadContextSite(2, uuid, "review")


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_requests", 257),
        ("max_bytes", 16777217),
        ("max_rows", 20001),
        ("response_bytes", 1048577),
        ("max_seconds", 901),
        ("timeout_seconds", 31),
        ("page_size", 101),
        ("max_pages", 12),
        ("batch_size", 101),
        ("max_dependency_ids", 1001),
        ("max_requests", True),
        ("max_seconds", float("nan")),
        ("max_rows", 0),
    ],
)
def test_context_limits_cannot_expand_reviewed_profile(field, value):
    with pytest.raises(ValueError):
        api().SeadContextLimits(**{field: value})

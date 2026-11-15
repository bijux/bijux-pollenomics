"""Four literal country names have no dataset or numerical-role aliases."""

from __future__ import annotations

from dataclasses import replace
import importlib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from ..resources.native_payloads import response


def owner() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.country_authority"
    )


def plan(countries: Any = ("Sweden", "Norway")) -> Any:
    return owner().NeotomaCountryAuthorityPlan(countries)


def test_exact_country_routes_and_counts_do_not_admit_dictionary_semantics(
    tmp_path: Path,
) -> None:
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        assert kwargs["max_bytes"] < 2 * 1024 * 1024 and kwargs["timeout"] <= 45
        return response(url, b'{"status":"success","data":[{"unqualified_source":37}]}')

    result = owner().capture_neotoma_country_authority(
        tmp_path / "capture", plan=plan(), fetch=fetch
    )
    assert calls == [
        "https://api.neotomadb.org/v2.0/data/geopoliticalunits?gpname=Sweden&rank=1&lower=false",
        "https://api.neotomadb.org/v2.0/data/geopoliticalunits?gpname=Norway&rank=1&lower=false",
    ]
    assert result.request_count == 2
    assert result.partitions == {"received_complete_unqualified_country_metadata": 2}
    for row in result.countries:
        assert row["metadata_role"] == "reference_metadata"
        assert row["scientific_admission"] == "not_asserted"
        assert row["summary"]["dictionary_complete"] is False
        assert row["summary"]["absence_certified"] is False
        assert row["summary"]["schema_qualified"] is False


@pytest.mark.parametrize(
    "countries",
    [
        (),
        ("samples",),
        ("Sweden?limit=1",),
        ("sweden",),
        ("Sweden,Norway",),
        ("../downloads/19913",),
        (True,),
        ("Sweden", "Sweden"),
        ["Sweden"],
    ],
)
def test_unapproved_country_or_selector_is_refused_before_get(
    tmp_path: Path, countries: Any
) -> None:
    with pytest.raises(ValueError):
        owner().capture_neotoma_country_authority(
            tmp_path / "capture",
            plan=plan(countries),
            fetch=lambda *a, **k: pytest.fail(
                "arbitrary country selector reached HTTP"
            ),
        )
    assert not (tmp_path / "capture").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_attempts", 2),
        ("max_requests", True),
        ("max_requests", 5),
        ("max_response_bytes", 2 * 1024 * 1024),
        ("max_total_bytes", 8 * 1024 * 1024),
        ("retry_delay_seconds", 1),
        ("wall_seconds", 121),
    ],
)
def test_country_caps_are_hard_and_no_retry_is_permitted(
    tmp_path: Path, field: str, value: Any
) -> None:
    limits = replace(owner().DEFAULT_COUNTRY_LIMITS, **{field: value})
    with pytest.raises(ValueError):
        owner().capture_neotoma_country_authority(
            tmp_path / "capture",
            plan=plan(),
            limits=limits,
            fetch=lambda *a, **k: pytest.fail("expanded country plan reached HTTP"),
        )


def test_single_request_budget_retains_other_country_as_unattempted(
    tmp_path: Path,
) -> None:
    result = owner().capture_neotoma_country_authority(
        tmp_path / "capture",
        plan=plan(),
        limits=replace(owner().DEFAULT_COUNTRY_LIMITS, max_requests=1),
        fetch=lambda url, **k: response(url, b"{}"),
    )
    assert result.request_count == 1
    assert result.partitions == {
        "received_complete_unqualified_country_metadata": 1,
        "not_attempted_budget": 1,
    }


@pytest.mark.parametrize("status", [404, 429, 500])
def test_http_failure_is_retained_once_without_absence_or_retry(
    tmp_path: Path, status: int
) -> None:
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return response(url, b'{"source_error":true}', status=status)

    result = owner().capture_neotoma_country_authority(
        tmp_path / "capture", plan=plan(("Sweden",)), fetch=fetch
    )
    assert len(calls) == 1 and result.partitions == {"unavailable_http": 1}
    assert result.countries[0]["absence_certified"] is False


def test_transport_failure_and_existing_outputs_keep_their_evidence(
    tmp_path: Path,
) -> None:
    def timeout(*args: Any, **kwargs: Any) -> Any:
        raise TimeoutError("bounded source timeout")

    result = owner().capture_neotoma_country_authority(
        tmp_path / "capture", plan=plan(("Sweden",)), fetch=timeout
    )
    assert result.partitions == {"transport_failure": 1} and result.request_count == 1
    before = {p.name: p.read_bytes() for p in (tmp_path / "capture").iterdir()}
    with pytest.raises(FileExistsError):
        owner().capture_neotoma_country_authority(
            tmp_path / "capture",
            plan=plan(),
            fetch=lambda *a, **k: pytest.fail("existing output GET"),
        )
    assert before == {p.name: p.read_bytes() for p in (tmp_path / "capture").iterdir()}


@pytest.mark.parametrize(
    "body",
    [b'{"unitid":37,"unitid":38}', b'{"number":1e999}', b'{"number":1e-999}', b"[]"],
)
def test_ambiguous_or_lossy_reference_json_is_retained_as_refusal(
    tmp_path: Path, body: bytes
) -> None:
    result = owner().capture_neotoma_country_authority(
        tmp_path / "capture",
        plan=plan(("Sweden",)),
        fetch=lambda url, **k: response(url, body),
    )
    assert result.partitions == {"refused_native_json": 1}
    assert next((tmp_path / "capture").glob("*.body")).read_bytes() == body


def test_string_subclass_cannot_borrow_a_literal_country_selector(
    tmp_path: Path,
) -> None:
    class BorrowedCountry(str):
        def __str__(self) -> str:
            return "Sweden&rank=4&lower=true"

    with pytest.raises(ValueError):
        owner().capture_neotoma_country_authority(
            tmp_path / "capture",
            plan=plan((BorrowedCountry("Sweden"),)),
            fetch=lambda *a, **k: pytest.fail("nonliteral selector reached HTTP"),
        )


def test_all_four_names_are_explicit_routes_without_child_expansion(
    tmp_path: Path,
) -> None:
    calls = []
    names = ("Denmark", "Finland", "Norway", "Sweden")

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return response(url, b"{}")

    captured = owner().capture_neotoma_country_authority(
        tmp_path / "capture", plan=plan(names), fetch=fetch
    )
    assert calls == [
        f"https://api.neotomadb.org/v2.0/data/geopoliticalunits?gpname={name}&rank=1&lower=false"
        for name in names
    ]
    assert captured.request_count == 4
    assert [row["country"] for row in captured.countries] == list(names)


def test_bounded_incomplete_entity_is_retained_without_parsing_the_prefix(
    tmp_path: Path,
) -> None:
    root = tmp_path / "capture"
    body = b'{"data":[1,2,3,4'
    limits = replace(owner().DEFAULT_COUNTRY_LIMITS, max_response_bytes=len(body) - 1)
    captured = owner().capture_neotoma_country_authority(
        root,
        plan=plan(("Sweden",)),
        limits=limits,
        fetch=lambda url, **k: replace(response(url, body), body_complete=False),
    )
    assert captured.partitions == {"refused_incomplete_body": 1}
    assert next(root.glob("*.body")).read_bytes() == body
    derived = owner().qualify_neotoma_country_authority(
        root, expected_manifest_sha256=captured.manifest_sha256
    )
    assert derived["qualification_partitions"] == {"not_qualified_source_result": 1}

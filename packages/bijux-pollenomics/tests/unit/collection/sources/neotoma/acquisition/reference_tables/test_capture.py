"""Two literal reference endpoints have no dataset or numerical-role aliases."""

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
        "bijux_pollenomics.collection.sources.neotoma.capture.reference_tables"
    )


def plan(tables: Any = ("variableunits", "geopoliticalunits")) -> Any:
    return owner().NeotomaReferenceTablePlan(tables)


def test_exact_prefix_routes_and_counts_do_not_admit_dictionary_semantics(
    tmp_path: Path,
) -> None:
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        assert kwargs["max_bytes"] < 2 * 1024 * 1024 and kwargs["timeout"] <= 45
        return response(url, b'{"status":"success","data":[{"unqualified_source":37}]}')

    result = owner().capture_neotoma_reference_tables(
        tmp_path / "capture", plan=plan(), fetch=fetch
    )
    assert calls == [
        "https://api.neotomadb.org/v2.0/data/dbtables/variableunits?limit=10000&offset=0",
        "https://api.neotomadb.org/v2.0/data/dbtables/geopoliticalunits?limit=10000&offset=0",
    ]
    assert result.request_count == 2
    assert result.partitions == {"received_complete_unqualified_reference_table": 2}
    for row in result.tables:
        assert row["metadata_role"] == "reference_metadata"
        assert row["scientific_admission"] == "not_asserted"
        assert row["summary"]["table_population_complete"] is False
        assert row["summary"]["absence_certified"] is False
        assert row["summary"]["schema_qualified"] is False


@pytest.mark.parametrize(
    "tables",
    [
        (),
        ("samples",),
        ("variableunits?limit=1",),
        ("VariableUnits",),
        ("../downloads/19913",),
        (True,),
        ("variableunits", "variableunits"),
        ["variableunits"],
    ],
)
def test_unapproved_table_or_selector_is_refused_before_get(
    tmp_path: Path, tables: Any
) -> None:
    with pytest.raises(ValueError):
        owner().capture_neotoma_reference_tables(
            tmp_path / "capture",
            plan=plan(tables),
            fetch=lambda *a, **k: pytest.fail(
                "arbitrary reference selector reached HTTP"
            ),
        )
    assert not (tmp_path / "capture").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_attempts", 2),
        ("max_requests", True),
        ("max_response_bytes", 2 * 1024 * 1024),
        ("max_total_bytes", 4 * 1024 * 1024),
        ("retry_delay_seconds", 1),
        ("wall_seconds", 121),
    ],
)
def test_reference_caps_are_hard_and_no_retry_is_permitted(
    tmp_path: Path, field: str, value: Any
) -> None:
    limits = replace(owner().DEFAULT_REFERENCE_LIMITS, **{field: value})
    with pytest.raises(ValueError):
        owner().capture_neotoma_reference_tables(
            tmp_path / "capture",
            plan=plan(),
            limits=limits,
            fetch=lambda *a, **k: pytest.fail("expanded reference plan reached HTTP"),
        )


def test_single_request_budget_retains_other_table_as_unattempted(
    tmp_path: Path,
) -> None:
    result = owner().capture_neotoma_reference_tables(
        tmp_path / "capture",
        plan=plan(),
        limits=replace(owner().DEFAULT_REFERENCE_LIMITS, max_requests=1),
        fetch=lambda url, **k: response(url, b"{}"),
    )
    assert result.request_count == 1
    assert result.partitions == {
        "received_complete_unqualified_reference_table": 1,
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

    result = owner().capture_neotoma_reference_tables(
        tmp_path / "capture", plan=plan(("variableunits",)), fetch=fetch
    )
    assert len(calls) == 1 and result.partitions == {"unavailable_http": 1}
    assert result.tables[0]["absence_certified"] is False


def test_transport_failure_and_existing_outputs_keep_their_evidence(
    tmp_path: Path,
) -> None:
    def timeout(*args: Any, **kwargs: Any) -> Any:
        raise TimeoutError("bounded source timeout")

    result = owner().capture_neotoma_reference_tables(
        tmp_path / "capture", plan=plan(("variableunits",)), fetch=timeout
    )
    assert result.partitions == {"transport_failure": 1} and result.request_count == 1
    before = {p.name: p.read_bytes() for p in (tmp_path / "capture").iterdir()}
    with pytest.raises(FileExistsError):
        owner().capture_neotoma_reference_tables(
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
    result = owner().capture_neotoma_reference_tables(
        tmp_path / "capture",
        plan=plan(("variableunits",)),
        fetch=lambda url, **k: response(url, body),
    )
    assert result.partitions == {"refused_native_json": 1}
    assert next((tmp_path / "capture").glob("*.body")).read_bytes() == body

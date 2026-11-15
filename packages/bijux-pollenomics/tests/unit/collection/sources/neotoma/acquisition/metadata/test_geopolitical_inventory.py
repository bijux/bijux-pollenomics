"""Source-geopolitical query witnesses remain separate native inventories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataLimits,
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from .native_responses import response


def native(unit: int) -> dict[str, Any]:
    return {
        "site": {
            "siteid": unit + 1,
            "collectionunitid": unit,
            "geography": None,
            "datasets": [{"datasetid": unit + 1000, "datasettype": "native type"}],
        }
    }


def encoded(rows: list[dict[str, Any]]) -> bytes:
    return json.dumps({"status": "success", "data": rows}).encode()


def plan(**kwargs: Any) -> NeotomaMetadataPlan:
    return NeotomaMetadataPlan(
        **{
            "geopolitical_unit_ids": (101, 202),
            "inventory_limits": (400, 10000),
            "inventory_all_dataset_types": True,
            **kwargs,
        }
    )


def test_each_geopolitical_id_owns_each_limit_without_overwriting_native_rows(
    tmp_path: Path,
) -> None:
    urls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        urls.append(url)
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)
        assert parsed.path == "/v2.0/data/datasets"
        assert set(query) == {"gpid", "limit", "offset"}
        assert query["offset"] == ["0"]
        return response(url, encoded([native(int(query["gpid"][0]))]))

    captured = capture_neotoma_metadata(tmp_path / "capture", plan=plan(), fetch=fetch)
    assert captured.inventory_rows == {}
    assert captured.geopolitical_inventory_rows == {
        101: {400: [native(101)], 10000: [native(101)]},
        202: {400: [native(202)], 10000: [native(202)]},
    }
    assert len(urls) == captured.request_count == 4
    assert captured.site_responses == captured.dataset_responses == {}
    control = json.loads((tmp_path / "capture/request-plan.json").read_bytes())
    assert control["plan"]["geopolitical_unit_ids"] == [101, 202]
    assert control["plan"]["inventory_bbox"] is None
    receipt = json.loads(
        (
            tmp_path / "capture/inventory-gpid-101-limit-400-offset-0.receipt.json"
        ).read_bytes()
    )
    assert receipt["role"] == "dataset_inventory"
    assert receipt["parameters"] == {"gpid": "101", "limit": "400", "offset": "0"}


def test_same_native_unit_in_distinct_geopolitical_queries_is_preserved(
    tmp_path: Path,
) -> None:
    captured = capture_neotoma_metadata(
        tmp_path / "capture",
        plan=plan(inventory_limits=(400,)),
        fetch=lambda url, **_: response(url, encoded([native(100)])),
    )
    assert captured.geopolitical_inventory_rows == {
        101: {400: [native(100)]},
        202: {400: [native(100)]},
    }


def test_empty_geopolitical_scope_does_not_terminate_other_queries(
    tmp_path: Path,
) -> None:
    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        empty = parse_qs(urlsplit(url).query)["gpid"] == ["101"]
        return response(url, encoded([] if empty else [native(100)]))

    captured = capture_neotoma_metadata(
        tmp_path / "capture", plan=plan(inventory_limits=(400,)), fetch=fetch
    )
    assert captured.geopolitical_inventory_rows == {
        101: {400: []},
        202: {400: [native(100)]},
    }


@pytest.mark.parametrize(
    "ids",
    [None, [101], (True,), (0,), (-1,), (101.0,), ("101",), (101, 101)],
)
def test_invalid_geopolitical_populations_refuse_before_output_or_network(
    tmp_path: Path, ids: object
) -> None:
    output = tmp_path / "capture"
    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            output,
            plan=plan(geopolitical_unit_ids=ids),
            fetch=lambda *_a, **_k: pytest.fail("Invalid population reached network"),
        )
    assert not output.exists() and not build_staging_output_dir(output).exists()


def test_late_invalid_generator_is_not_consumed_during_acquisition(
    tmp_path: Path,
) -> None:
    def identifiers() -> Any:
        yield 101
        yield True

    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            tmp_path / "capture",
            plan=plan(geopolitical_unit_ids=identifiers()),
            fetch=lambda *_a, **_k: pytest.fail("Generator reached network"),
        )


@pytest.mark.parametrize(
    "fields",
    [
        {"inventory_bbox": (4, 54, 35, 82)},
        {"inventory_all_dataset_types": False},
        {"inventory_limits": ()},
        {"inventory_limits": (10001,)},
        {"inventory_limits": (400, 400)},
    ],
)
def test_geopolitical_plan_cannot_hide_a_bbox_or_pollen_filter(
    tmp_path: Path, fields: dict[str, Any]
) -> None:
    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            tmp_path / "capture",
            plan=plan(**fields),
            fetch=lambda *_a, **_k: pytest.fail("Invalid query scope reached network"),
        )


def test_partial_last_page_overlap_cannot_be_published_as_complete(
    tmp_path: Path,
) -> None:
    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        first = parse_qs(urlsplit(url).query)["offset"] == ["0"]
        return response(
            url, encoded([native(100), native(101)] if first else [native(101)])
        )

    output = tmp_path / "capture"
    with pytest.raises(ValueError, match="duplicate"):
        capture_neotoma_metadata(
            output,
            plan=plan(geopolitical_unit_ids=(101,), inventory_limits=(2,)),
            fetch=fetch,
        )
    assert not output.exists()
    assert (
        build_staging_output_dir(output) / "inventory-gpid-101-limit-2-offset-2.body"
    ).read_bytes() == encoded([native(101)])


@pytest.mark.parametrize(
    "body",
    [
        b'{"status":"error","data":[]}',
        b'{"status":"success","data":null}',
        encoded([{"site": {"siteid": 1, "collectionunitid": 2, "samples": []}}]),
    ],
)
@pytest.mark.parametrize("later", [False, True])
def test_malformed_metadata_is_not_an_empty_geopolitical_inventory(
    tmp_path: Path, body: bytes, later: bool
) -> None:
    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        first = parse_qs(urlsplit(url).query)["offset"] == ["0"]
        content = encoded([native(100)]) if later and first else body
        return response(url, content)

    output = tmp_path / "capture"
    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            output,
            plan=plan(geopolitical_unit_ids=(101,), inventory_limits=(1,)),
            fetch=fetch,
        )
    assert not output.exists()
    assert (build_staging_output_dir(output) / "refusal.json").is_file()


def test_page_quota_never_certifies_a_full_geopolitical_page(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="termination|budget"):
        capture_neotoma_metadata(
            tmp_path / "capture",
            plan=plan(geopolitical_unit_ids=(101,), inventory_limits=(1,)),
            limits=NeotomaMetadataLimits(max_pages_per_inventory=1),
            fetch=lambda url, **_: response(url, encoded([native(100)])),
        )


def test_request_quota_cannot_publish_only_the_first_geopolitical_scope(
    tmp_path: Path,
) -> None:
    urls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        urls.append(url)
        return response(url, encoded([]))

    output = tmp_path / "capture"
    with pytest.raises(ValueError, match="budget"):
        capture_neotoma_metadata(
            output,
            plan=plan(inventory_limits=(400,)),
            limits=NeotomaMetadataLimits(max_requests=1),
            fetch=fetch,
        )
    assert len(urls) == 1 and not output.exists()
    assert (
        build_staging_output_dir(output) / "inventory-gpid-101-limit-400-offset-0.body"
    ).read_bytes() == encoded([])

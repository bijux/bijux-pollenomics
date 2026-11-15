from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, urlsplit

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
    replay_neotoma_metadata_capture,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from .native_responses import SITE_BODY, response


@pytest.mark.parametrize(
    "dataset_type",
    ["geochronologic", "Metabarcoding aeDNA", "unregistered source type"],
)
def test_all_type_inventory_finds_non_pollen_sites_and_replays_its_scope(
    tmp_path: Path,
    dataset_type: str,
) -> None:
    non_pollen = SITE_BODY.replace(b'"pollen"', json.dumps(dataset_type).encode())
    calls: list[str] = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        calls.append(url)
        parameters = parse_qs(urlsplit(url).query)
        assert "datasettype" not in parameters
        return response(
            url,
            non_pollen
            if parameters["offset"] == ["0"]
            else b'{"status":"success","data":[]}',
        )

    result = capture_neotoma_metadata(
        tmp_path / "all-types",
        plan=NeotomaMetadataPlan(
            inventory_bbox=(4, 54, 35, 82),
            inventory_limits=(1,),
            inventory_all_dataset_types=True,
        ),
        fetch=fetch,
    )
    assert len(calls) == 2
    assert result.inventory_rows[1] == json.loads(non_pollen)["data"]
    replayed = replay_neotoma_metadata_capture(
        tmp_path / "all-types",
        expected_manifest_sha256=result.manifest_sha256,
    )
    assert replayed.inventory_rows == result.inventory_rows
    receipt = json.loads(
        (tmp_path / "all-types/inventory-limit-1-offset-0.receipt.json").read_bytes()
    )
    assert receipt["role"] == "dataset_inventory"


def test_replay_cannot_relabel_an_all_type_response_as_pollen_scope(
    tmp_path: Path,
) -> None:
    output = tmp_path / "all-types"
    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(
            inventory_bbox=(4, 54, 35, 82),
            inventory_limits=(2,),
            inventory_all_dataset_types=True,
        ),
        fetch=lambda url, **_: response(url),
    )
    plan_path = output / "request-plan.json"
    control = json.loads(plan_path.read_bytes())
    control["plan"]["inventory_all_dataset_types"] = False
    plan_path.write_text(json.dumps(control))
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["plan_sha256"] = sha256(plan_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="identity differs"):
        replay_neotoma_metadata_capture(output)


def test_all_type_inventory_still_refuses_numerical_source_bodies(
    tmp_path: Path,
) -> None:
    body = SITE_BODY.replace(
        b'"datasettype":"pollen"', b'"datasettype":"pollen","samples":[]'
    )
    output = tmp_path / "all-types"
    with pytest.raises(ValueError, match="numerical outcome"):
        capture_neotoma_metadata(
            output,
            plan=NeotomaMetadataPlan(
                inventory_bbox=(4, 54, 35, 82),
                inventory_limits=(2,),
                inventory_all_dataset_types=True,
            ),
            fetch=lambda url, **_: response(url, body),
        )
    assert not output.exists()
    assert (
        build_staging_output_dir(output) / "inventory-limit-2-offset-0.body"
    ).read_bytes() == body


def test_default_pollen_inventory_refuses_non_pollen_records(tmp_path: Path) -> None:
    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        assert parse_qs(urlsplit(url).query)["datasettype"] == ["pollen"]
        return response(url, SITE_BODY.replace(b'"pollen"', b'"geochronologic"'))

    with pytest.raises(ValueError, match="non-pollen"):
        capture_neotoma_metadata(
            tmp_path / "pollen-only",
            plan=NeotomaMetadataPlan(
                inventory_bbox=(4, 54, 35, 72), inventory_limits=(2,)
            ),
            fetch=fetch,
        )


@pytest.mark.parametrize("mode", [None, 0, 1, "all"])
def test_inventory_mode_requires_a_literal_boolean_before_any_get(
    tmp_path: Path,
    mode: object,
) -> None:
    with pytest.raises(ValueError, match="inventory mode"):
        capture_neotoma_metadata(
            tmp_path / "bad-mode",
            plan=NeotomaMetadataPlan(
                inventory_bbox=(4, 54, 35, 82),
                inventory_limits=(2,),
                inventory_all_dataset_types=cast(bool, mode),
            ),
            fetch=lambda *_args, **_kwargs: pytest.fail("must refuse before GET"),
        )


@pytest.mark.parametrize("all_dataset_types", [False, True])
def test_inventory_metadata_requires_short_page_and_unique_units(
    tmp_path: Path,
    all_dataset_types: bool,
) -> None:
    body = b'{"status":"success","data":[{"site":{"siteid":12,"collectionunitid":100,"datasets":[{"datasetid":201,"datasettype":"pollen"}]}}]}'
    calls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        calls.append(url)
        return response(
            url, body if len(calls) == 1 else b'{"status":"success","data":[]}'
        )

    result = capture_neotoma_metadata(
        tmp_path / "capture",
        plan=NeotomaMetadataPlan(
            inventory_bbox=(4.0, 54.0, 35.0, 72.0),
            inventory_limits=(1,),
            inventory_all_dataset_types=all_dataset_types,
        ),
        fetch=fetch,
    )
    assert len(calls) == 2
    assert len(result.inventory_rows[1]) == 1
    assert "offset=1" in calls[1]

    with pytest.raises(ValueError, match="duplicate"):
        capture_neotoma_metadata(
            tmp_path / "repeated",
            plan=NeotomaMetadataPlan(
                inventory_bbox=(4.0, 54.0, 35.0, 72.0),
                inventory_limits=(1,),
                inventory_all_dataset_types=all_dataset_types,
            ),
            fetch=lambda url, **_: response(url, body),
        )

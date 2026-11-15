"""Reference metadata replay binds exact routes, scalar kinds and returned bytes."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from ..resources.native_payloads import response
from .test_capture import owner, plan


def write(path: Path, value: Any) -> str:
    content = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(content)
    return sha256(content).hexdigest()


def captured(tmp_path: Path) -> tuple[Path, Any]:
    root = tmp_path / "capture"
    result = owner().capture_neotoma_country_authority(
        root,
        plan=plan(),
        fetch=lambda url, **k: response(url, b'{"status":"success","data":[]}'),
    )
    return root, result


def test_replay_and_selected_buffer_preserve_exact_source_entity(
    tmp_path: Path,
) -> None:
    root, result = captured(tmp_path)
    assert (
        owner().replay_neotoma_country_authority(
            root, expected_manifest_sha256=result.manifest_sha256
        )
        == result
    )
    body = owner().read_neotoma_country_authority_body(
        root, expected_manifest_sha256=result.manifest_sha256, country="Sweden"
    )
    assert (
        body.body == b'{"status":"success","data":[]}'
        and body.body_sha256 == sha256(body.body).hexdigest()
    )


@pytest.mark.parametrize(
    "damage",
    [
        "body",
        "receipt",
        "unknown_control",
        "unknown_manifest",
        "country",
        "role",
        "prefix",
        "ancestry",
        "absence",
    ],
)
def test_changed_sources_or_legally_rehashed_false_scope_is_refused(
    tmp_path: Path, damage: str
) -> None:
    root, result = captured(tmp_path)
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    control = json.loads((root / "request-plan.json").read_bytes())
    ref = manifest["countries"][0]["attempts"][0]
    if damage == "body":
        (root / ref["body_file"]).write_bytes(b'{"foreign":true}')
    elif damage == "receipt":
        (root / ref["receipt_file"]).write_bytes(b'{"foreign":true}')
    elif damage == "unknown_control":
        control["caller_url"] = "https://foreign.invalid"
    elif damage == "unknown_manifest":
        manifest["role_override"] = "development_resource_discovery"
    elif damage == "country":
        control["plan"]["countries"] = ["samples"]
    elif damage == "role":
        manifest["countries"][0]["metadata_role"] = "numerical_development"
    elif damage == "prefix":
        manifest["countries"][0]["summary"]["lower_units_included"] = 36
    elif damage == "ancestry":
        manifest["countries"][0]["reused_from"] = {"manifest_sha256": "f" * 64}
    else:
        manifest["countries"][0]["summary"]["absence_certified"] = True
    manifest["plan_sha256"] = write(root / "request-plan.json", control)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError):
        owner().replay_neotoma_country_authority(root, expected_manifest_sha256=digest)


def test_stricter_caller_request_limit_is_enforced(tmp_path: Path) -> None:
    root, result = captured(tmp_path)
    with pytest.raises(ValueError):
        owner().replay_neotoma_country_authority(
            root,
            expected_manifest_sha256=result.manifest_sha256,
            limits=replace(owner().DEFAULT_COUNTRY_LIMITS, max_requests=1),
        )


def test_unknown_country_read_refuses_before_any_body_buffer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, result = captured(tmp_path)
    original = Path.open

    def guard(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path.suffix != ".body", "Unselected source body opened"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    with pytest.raises(ValueError):
        owner().read_neotoma_country_authority_body(
            root, expected_manifest_sha256=result.manifest_sha256, country="samples"
        )


def test_actual_buffer_is_rechecked_after_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, result = captured(tmp_path)
    module = __import__(
        owner().__name__ + ".replay", fromlist=["replay_neotoma_country_authority"]
    )
    original = module.replay_neotoma_country_authority

    def swap(*args: Any, **kwargs: Any) -> Any:
        value = original(*args, **kwargs)
        (root / result.countries[0]["attempts"][0]["body_file"]).write_bytes(
            b'{"foreign":true}'
        )
        return value

    monkeypatch.setattr(module, "replay_neotoma_country_authority", swap)
    with pytest.raises(ValueError):
        owner().read_neotoma_country_authority_body(
            root, expected_manifest_sha256=result.manifest_sha256, country="Sweden"
        )


def test_success_reauthenticates_actual_published_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication import ownership

    module = ownership
    original = vars(module)["publish_new_output_tree"]

    def mutate(**kwargs: Any) -> Any:
        next(kwargs["staging_output_root"].glob("*.body")).write_bytes(
            b'{"foreign_stage":true}'
        )
        return original(**kwargs)

    monkeypatch.setattr(module, "publish_new_output_tree", mutate)
    with pytest.raises(ValueError):
        owner().capture_neotoma_country_authority(
            tmp_path / "capture",
            plan=plan(),
            fetch=lambda url, **k: response(url, b"{}"),
        )
    assert any(
        p.read_bytes() == b'{"foreign_stage":true}'
        for p in (tmp_path / "capture").glob("*.body")
    )


def test_legally_rehashed_other_country_receipt_cannot_change_endpoint_owner(
    tmp_path: Path,
) -> None:
    root, result = captured(tmp_path)
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    original, changed = [row["attempts"][0] for row in manifest["countries"]]
    record = json.loads((root / original["receipt_file"]).read_bytes())
    record["body_file"] = changed["body_file"]
    changed["receipt_sha256"] = write(root / changed["receipt_file"], record)
    digest = write(root / "capture-manifest.json", manifest)
    with pytest.raises(ValueError):
        owner().replay_neotoma_country_authority(root, expected_manifest_sha256=digest)


def native(country: str = "Sweden", native_id: int = 37) -> dict[str, Any]:
    return {
        "status": "success",
        "data": [
            {
                "geopoliticalid": native_id,
                "geopoliticalname": country,
                "rank": 1,
                "highergeopoliticalid": 0,
                "geopoliticalunit": "country",
                "recdatecreated": "native timestamp",
                "recdatemodified": None,
                "geog": {"opaque_native_geometry": [1, -0.0, None]},
                "unobserved_extra": {"source_literal": True},
            }
        ],
    }


def qualified(tmp_path: Path, payload: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    body = json.dumps(payload).encode()
    root = tmp_path / "capture"
    captured = owner().capture_neotoma_country_authority(
        root, plan=plan(("Sweden",)), fetch=lambda url, **k: response(url, body)
    )
    assert captured.partitions == {"received_complete_unqualified_country_metadata": 1}
    assert (
        owner()
        .read_neotoma_country_authority_body(
            root, expected_manifest_sha256=captured.manifest_sha256, country="Sweden"
        )
        .body
        == body
    )
    result = owner().qualify_neotoma_country_authority(
        root, expected_manifest_sha256=captured.manifest_sha256
    )
    return result["countries"][0], body


def test_exact_authority_preserves_entire_native_geometry_and_parent_literals(
    tmp_path: Path,
) -> None:
    original = native()
    row, body = qualified(tmp_path, original)
    assert row["qualification_status"] == "qualified_country_record"
    assert row["native_payload"] == original
    assert row["native_record_pointer"] == "/data/0"
    assert row["body_sha256"] == sha256(body).hexdigest()
    assert row["geometry_interpreted"] is False
    assert row["country_assignment_or_numerical_admission"] == "not_asserted"
    assert row["territorial_or_dictionary_completeness"] == "not_established"
    assert row["native_payload"]["data"][0]["highergeopoliticalid"] == 0
    assert json.dumps(row["native_payload"]) == json.dumps(original)


@pytest.mark.parametrize(
    "damage",
    [
        "wrong_name",
        "wrong_rank",
        "bool_rank",
        "bool_id",
        "fractional_id",
        "string_id",
        "null_id",
        "missing_id",
        "missing_parent",
        "null_parent",
        "wrong_unit",
        "foreign_row",
        "duplicate_row",
        "wrapper",
        "source_failure",
    ],
)
def test_unqualified_source_remains_readable_but_never_supplies_country_authority(
    tmp_path: Path,
    damage: str,
) -> None:
    value = native()
    record = value["data"][0]
    if damage == "wrong_name":
        record["geopoliticalname"] = "Norway"
    elif damage == "wrong_rank":
        record["rank"] = 2
    elif damage == "bool_rank":
        record["rank"] = True
    elif damage == "bool_id":
        record["geopoliticalid"] = True
    elif damage == "fractional_id":
        record["geopoliticalid"] = 37.9
    elif damage == "string_id":
        record["geopoliticalid"] = "37"
    elif damage == "null_id":
        record["geopoliticalid"] = None
    elif damage == "missing_id":
        del record["geopoliticalid"]
    elif damage == "missing_parent":
        del record["highergeopoliticalid"]
    elif damage == "null_parent":
        record["highergeopoliticalid"] = None
    elif damage == "wrong_unit":
        record["geopoliticalunit"] = 4
    elif damage == "foreign_row":
        value["data"].append(native("Norway")["data"][0])
    elif damage == "duplicate_row":
        value["data"].append(dict(record))
    elif damage == "wrapper":
        value["data"] = [{"site": record}]
    else:
        value["status"] = "failure"
    row, _ = qualified(tmp_path, value)
    assert row["qualification_status"] == "refused_country_record"
    assert "native_geopolitical_id" not in row
    assert "reason" in row


@pytest.mark.parametrize(
    "data",
    [
        [],
        [
            {
                "geopoliticalid": None,
                "geopoliticalname": None,
                "rank": None,
                "highergeopoliticalid": None,
                "geopoliticalunit": None,
            }
        ],
    ],
)
def test_empty_and_null_source_placeholder_are_unavailable_not_absence(
    tmp_path: Path,
    data: list[Any],
) -> None:
    row, _ = qualified(tmp_path, {"status": "success", "data": data})
    assert row["qualification_status"] == "unavailable_country_record"
    assert row["absence_certified"] is False


def test_country_queries_cannot_publish_two_names_under_one_native_id(
    tmp_path: Path,
) -> None:
    from urllib.parse import parse_qs, urlparse

    def fetch(url: str, **kwargs: Any) -> Any:
        country = parse_qs(urlparse(url).query)["gpname"][0]
        return response(url, json.dumps(native(country)).encode())

    root = tmp_path / "capture"
    captured = owner().capture_neotoma_country_authority(root, plan=plan(), fetch=fetch)
    derived = owner().qualify_neotoma_country_authority(
        root, expected_manifest_sha256=captured.manifest_sha256
    )
    assert captured.partitions == {"received_complete_unqualified_country_metadata": 2}
    assert derived["qualification_partitions"] == {
        "refused_conflicting_native_authority_ids": 2
    }
    assert all("native_geopolitical_id" not in row for row in derived["countries"])


def test_noncomplete_http_is_not_opened_as_a_qualified_country_record(
    tmp_path: Path,
) -> None:
    root = tmp_path / "capture"
    captured = owner().capture_neotoma_country_authority(
        root,
        plan=plan(("Sweden",)),
        fetch=lambda url, **k: response(url, b"source error", status=503),
    )
    derived = owner().qualify_neotoma_country_authority(
        root, expected_manifest_sha256=captured.manifest_sha256
    )
    assert derived["qualification_partitions"] == {"not_qualified_source_result": 1}

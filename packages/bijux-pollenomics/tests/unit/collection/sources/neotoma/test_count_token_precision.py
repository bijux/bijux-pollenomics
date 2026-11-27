"""Source count eligibility must not acquire integrality from float rounding."""

import hashlib
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.analysis.lra.materialization.reading import NeotomaEvidence
from bijux_pollenomics.collection.sources.neotoma.client import (
    decode_neotoma_json_object,
)
from bijux_pollenomics.collection.sources.neotoma.production.validation import (
    json_object,
)


def native(token: str, unit: str = "number") -> bytes:
    return (
        '{"rows":[{"site":{"collectionunit":{"dataset":{"samples":[{"datum":[{"units":"'
        + unit
        + '","value":'
        + token
        + "}] }]}}}}]}"
    ).encode()


def normalized(token: str, field: str) -> bytes:
    value = token if field == "source_value" else "1"
    payload = token if field == "payload" else "1"
    return (
        '{"rows":[{"source_value":'
        + value
        + ',"source_unit":"number","unit_family":"count","source_payload":{"units":"number","value":'
        + payload
        + "}}]}"
    ).encode()


def read_observation(tmp_path: Path, body: bytes) -> None:
    path = tmp_path / "part.json"
    path.write_bytes(body)
    manifest = b'{"surfaces":{"observations":{"parts":[{"path":"part.json"}]}}}'
    evidence = NeotomaEvidence(
        tmp_path,
        tmp_path,
        manifest,
        (),
        (("part.json", hashlib.sha256(body).hexdigest()),),
    )
    list(evidence.rows("observations"))


@pytest.mark.parametrize(
    "token",
    ["1.0000000000000001", "0.99999999999999999", "9007199254740993.0", "1e-999999"],
)
def test_native_decoder_and_archive_refuse_rounded_count(
    tmp_path: Path, token: str
) -> None:
    body = native(token)
    with pytest.raises(ValueError):
        decode_neotoma_json_object(body)
    with pytest.raises(ValueError):
        json_object(body, tmp_path / "part.json")


@pytest.mark.parametrize(
    "token",
    ["1.0000000000000001", "0.99999999999999999", "9007199254740993.0", "1e-999999"],
)
@pytest.mark.parametrize("field", ["source_value", "payload"])
def test_lra_observation_reader_refuses_each_rounded_count(
    tmp_path: Path, token: str, field: str
) -> None:
    with pytest.raises(ValueError):
        read_observation(tmp_path, normalized(token, field))


@pytest.mark.parametrize(
    "token", ["1.0", "0.5", "1e0", "0e-999999", "9007199254740992.0"]
)
def test_valid_count_tokens_preserve_existing_float_types(
    tmp_path: Path, token: str
) -> None:
    body = native(token)
    assert decode_neotoma_json_object(body) == json_object(body, tmp_path / "part.json")
    read_observation(tmp_path, normalized(token, "source_value"))


def test_unrelated_noncount_fields_are_not_precision_gated(tmp_path: Path) -> None:
    body = native("1.0000000000000001", "cm3")
    assert decode_neotoma_json_object(body) == json_object(body, tmp_path / "part.json")


@pytest.mark.parametrize("token", ["-1.0000000000000001", "-1e0", "9007199254740993"])
def test_already_refused_negative_or_exact_integer_retains_compatibility(
    tmp_path: Path, token: str
) -> None:
    body = native(token)
    assert decode_neotoma_json_object(body) == json_object(body, tmp_path / "part.json")


def test_native_response_data_wrapper_and_unrelated_metadata(tmp_path: Path) -> None:
    body = native("1.0000000000000001").replace(b'"rows"', b'"data"', 1)
    with pytest.raises(ValueError):
        decode_neotoma_json_object(body)
    unrelated = b'{"data":[{"site":{"metadata":{"units":"number","value":1.0000000000000001}}}]}'
    assert decode_neotoma_json_object(unrelated) == json_object(
        unrelated, tmp_path / "part.json"
    )


def test_existing_native_decoder_duplicate_and_nonfinite_refusals() -> None:
    with pytest.raises(ValueError):
        decode_neotoma_json_object(b'{"a":1,"a":2}')
    with pytest.raises(ValueError):
        decode_neotoma_json_object(b'{"a":NaN}')


def test_raw_archive_to_relational_and_count_consumer(tmp_path: Path) -> None:
    import json

    from bijux_pollenomics.analysis.lra.materialization.counts import assess_count
    from bijux_pollenomics.collection.sources.neotoma.materialization import (
        materialize_neotoma_relational_snapshot,
    )
    from bijux_pollenomics.collection.sources.neotoma.production import (
        load_validated_neotoma_raw_archive,
    )
    from bijux_pollenomics.collection.sources.neotoma.relational import (
        build_neotoma_relational_snapshot,
    )

    from .test_neotoma_lineage_review import _raw_archive

    raw = tmp_path / "raw"
    _raw_archive(raw)
    part = raw / "part-001.json"
    original = part.read_bytes()
    assert b'"value": 0' in original

    def replace_and_pin(token: bytes) -> None:
        body = original.replace(b'"value": 0', b'"value": ' + token, 1)
        part.write_bytes(body)
        manifest_path = raw / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["parts"][0]["sha256"] = hashlib.sha256(body).hexdigest()
        manifest_path.write_text(json.dumps(manifest))

    replace_and_pin(b"1.0")
    rows, source_id = load_validated_neotoma_raw_archive(raw.resolve())
    snapshot = build_neotoma_relational_snapshot(
        rows,
        source_snapshot_id=source_id,
        build_id="fixture-build",
        country_by_site_id=dict.fromkeys(range(1, 10), "Sweden"),
    )
    materialize_neotoma_relational_snapshot(
        (tmp_path / "relational").resolve(), snapshot, rows_per_part=3
    )
    candidate = next(
        row
        for row in cast(list[dict[str, Any]], snapshot["observations"])
        if row["source_value"] == 1.0
    )
    assert assess_count(candidate).exact_count == 1
    replace_and_pin(b"1.0000000000000001")
    with pytest.raises(ValueError, match="loses precision"):
        load_validated_neotoma_raw_archive(raw.resolve())


def test_authenticated_observation_read_reaches_count_assessment(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.analysis.lra.materialization.counts import assess_count

    body = b'{"rows":[{"source_value":1.0,"source_unit":"number","unit_family":"count","detection_status":"reported_value","source_payload":{"units":"number","value":1.0}}]}'
    (tmp_path / "part.json").write_bytes(body)
    manifest = b'{"surfaces":{"observations":{"parts":[{"path":"part.json"}]}}}'
    evidence = NeotomaEvidence(
        tmp_path,
        tmp_path,
        manifest,
        (),
        (("part.json", hashlib.sha256(body).hexdigest()),),
    )
    assert assess_count(next(evidence.rows("observations")).payload()).exact_count == 1


def test_lexical_pass_only_for_float_count_observations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma import count_precision

    original = json.loads
    calls: list[object] = []

    def observed(*args: Any, **kwargs: Any) -> object:
        calls.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(json, "loads", observed)
    integer_body = native("1")
    integer_parsed = original(integer_body)
    count_precision.check_native_count_tokens(integer_body, integer_parsed)
    unrelated = native("1.0000000000000001", "cm3")
    count_precision.check_native_count_tokens(unrelated, original(unrelated))
    assert not calls
    float_body = native("1.0")
    count_precision.check_native_count_tokens(float_body, original(float_body))
    assert len(calls) == 1
    underflow = native("-1e-999999")
    with pytest.raises(ValueError):
        count_precision.check_native_count_tokens(underflow, original(underflow))
    assert len(calls) == 2


def test_mismatched_units_remain_refused_by_count_assessment(tmp_path: Path) -> None:
    from bijux_pollenomics.analysis.lra.materialization.counts import assess_count

    body = b'{"rows":[{"source_value":1.0000000000000001,"source_unit":"cm3","unit_family":"volume","detection_status":"reported_value","source_payload":{"units":"number","value":1.0000000000000001}}]}'
    (tmp_path / "part.json").write_bytes(body)
    manifest = b'{"surfaces":{"observations":{"parts":[{"path":"part.json"}]}}}'
    evidence = NeotomaEvidence(
        tmp_path,
        tmp_path,
        manifest,
        (),
        (("part.json", hashlib.sha256(body).hexdigest()),),
    )
    assert (
        assess_count(next(evidence.rows("observations")).payload()).reason
        == "inconsistent_source_projection"
    )


def test_large_exponent_and_signed_zero_controls(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="loses precision"):
        decode_neotoma_json_object(native("1e308"))
    assert decode_neotoma_json_object(native("-0.0")) == json_object(
        native("-0.0"), tmp_path / "part.json"
    )
    with pytest.raises(ValueError):
        json_object(native("-1e-999999"), tmp_path / "part.json")

"""Independently compare saved SEAD native claim rows with five raw tables."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from typing import Any

import pytest

from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts
_RUN = "sead-full-evidence-39bfff6a-ce80714e"
_RAW = REPOSITORY_ROOT / "data/sead/raw/acquisitions" / _RUN
_OUTPUT = REPOSITORY_ROOT / "artifacts/sead-native-claim-rows/native-run"
_TABLES = {
    "tbl_analysis_dating_ranges": "analysis_dating_range_id",
    "tbl_dendro_dates": "dendro_date_id",
    "tbl_relative_dates": "relative_date_id",
    "tbl_geochronology": "geochron_id",
    "tbl_analysis_entity_ages": "analysis_entity_age_id",
}


def _encoded(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def test_saved_native_rows_match_every_original_json_value_and_type() -> None:
    if not (_OUTPUT / "claims.json").is_file():
        pytest.skip("Requires the completed retained-source native claim run")
    summary = json.loads((_OUTPUT / "summary.json").read_text())
    body = (_OUTPUT / "claims.json").read_bytes()
    assert sha256(body).hexdigest() == summary["bundle_sha256"]
    assert len(body) == summary["bundle_bytes"] == 72_689_748
    result = json.loads(body)
    del body
    account = json.loads(
        (
            REPOSITORY_ROOT
            / "docs/report/source-relations/sead/chronology-claim-review/native-annotations-source.json"
        ).read_text()
    )
    originals: dict[tuple[str, str], dict[str, Any]] = {}
    for table, primary_key in _TABLES.items():
        path = _RAW / "payloads" / f"{table}.json"
        original_bytes = path.read_bytes()
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        assert (
            sha256(original_bytes).hexdigest()
            == account["source_inputs_sha256"][relative]
        )
        assert (
            summary["input_sha256"][relative]
            == account["source_inputs_sha256"][relative]
        )
        payload = json.loads(original_bytes)
        assert payload["table"] == table
        for row in payload["rows"]:
            assert type(row[primary_key]) is int
            key = (table, str(row[primary_key]))
            assert key not in originals
            originals[key] = row
    assert len(originals) == len(result["claims"]) == 25_109
    seen = set()
    fields: Counter[str] = Counter()
    differences: Counter[str] = Counter()
    affected = 0
    null_flags = 0
    for claim in result["claims"]:
        identity = (claim["source_table"], claim["source_record_id"])
        assert identity not in seen
        seen.add(identity)
        original = originals[identity]
        native = claim["source_native_row"]
        assert _encoded(native) == _encoded(original)
        assert claim["source_native_record_id"] == identity[1]
        assert claim["propagation_eligibility"] == "refused"
        different = False
        projected = claim["source_age_value"]
        for name, value in original.items():
            fields["null" if value is None else type(value).__name__] += 1
            null_flags += name.endswith("is_uncertain") and value is None
            assert name in projected
            old = projected[name]
            if _encoded(value) == _encoded(old):
                differences["exact"] += 1
            elif value is None and type(old) is str and old == "":
                differences["null_to_empty_string"] += 1
                different = True
            elif type(value) is float and type(old) is int and value == old:
                differences["equal_numeric_value_different_type"] += 1
                different = True
            else:
                pytest.fail(f"Unexpected projected representation: {identity}/{name}")
        affected += different
    assert seen == originals.keys()
    assert sum(fields.values()) == summary["native_fields"] == 202_546
    assert (
        fields
        == summary["native_field_types"]
        == {
            "int": 110_568,
            "null": 56_721,
            "bool": 14_754,
            "str": 18_984,
            "float": 1_519,
        }
    )
    assert differences == {
        "exact": 186_797,
        "null_to_empty_string": 14_230,
        "equal_numeric_value_different_type": 1_519,
    }
    assert affected == 8_678
    assert null_flags == 0
    assert result["chronology_eligibility_counts"] == {
        "eligible": 13_170,
        "refused": 11_939,
    }
    assert summary["default_bundle_identical_after_removing_only_native_row"] is True
    assert summary["scientific_chronology_or_event_admission_changed"] is False

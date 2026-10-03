"""Keep private review interchange finite and preserve its nonadmitting status."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.evidence import digest
from bijux_pollenomics_dev.taxa_review.decisions import load_review_json
from bijux_pollenomics_dev.taxa_review.workflow import write_review

from . import test_review as FIXTURES


@pytest.mark.parametrize(
    "token", ["NaN", "Infinity", "-Infinity", "1e10000", "-1e10000"]
)
def test_review_parser_refuses_nonfinite_numbers_at_any_depth(token: str) -> None:
    with pytest.raises(ValueError, match="finite"):
        load_review_json(('{"review": [{"value": ' + token + "}]}").encode())


def test_review_parser_preserves_exact_integer_float_null_and_unicode_values() -> None:
    small, large = 1e-300, 1e300
    value = {
        "integer": 2**200,
        "zero": -0.0,
        "small": small,
        "large": large,
        "absent": None,
        "source_text": "Poaceae-type å",
        "flag": True,
    }
    parsed = load_review_json(json.dumps(value, ensure_ascii=False).encode())
    assert parsed == value
    assert isinstance(parsed["integer"], int)
    assert math.copysign(1.0, parsed["zero"]) == -1.0
    assert parsed["small"].hex() == small.hex()
    assert parsed["large"].hex() == large.hex()


def test_finite_review_parser_retains_duplicate_key_and_object_refusals() -> None:
    with pytest.raises(ValueError, match="Duplicate JSON field"):
        load_review_json(b'{"reviewer": "one", "reviewer": "two"}')
    with pytest.raises(ValueError, match="must be an object"):
        load_review_json(b'[1, null, "source"]')


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_review_writer_refuses_nonfinite_bundle_before_reserving_output(
    tmp_path: Path, value: float
) -> None:
    payload = FIXTURES.bundle()
    payload["source_summaries"]["fixture"] = {"source_value": value}
    payload["bundle_sha256"] = digest(
        {key: item for key, item in payload.items() if key != "bundle_sha256"}
    )
    output = tmp_path / "review"
    with pytest.raises(ValueError, match="Out of range float"):
        write_review(payload, output)
    assert not output.exists()
    assert payload["scientific_admission_allowed"] is False
    assert payload["publication_allowed"] is False

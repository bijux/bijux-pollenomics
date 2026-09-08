"""AADR date-method family classification tests."""

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization import (
    classify_aadr_date_method,
)


@pytest.mark.parametrize(
    ("raw_value", "family"),
    [
        ("Direct", "direct"),
        ("  DIRECT   (OxCal) ", "direct"),
        ("Context: grave assemblage", "contextual"),
        ("Modern", "modern"),
        ("Known age", "known_historical"),
        ("Historical: register", "known_historical"),
        ("Method: genetic inference", "modeled_relational"),
        ("Genetic relationship", "modeled_relational"),
        ("Other chronology", "unclassified"),
        ("", "unclassified"),
    ],
)
def test_method_family_uses_normalized_matching_but_preserves_raw_value(
    raw_value: str, family: str
) -> None:
    evidence = classify_aadr_date_method(raw_value)

    assert evidence.raw_value == raw_value
    assert evidence.normalized_value == " ".join(raw_value.split()).casefold()
    assert evidence.family == family


def test_prefix_words_do_not_overclassify_unrelated_tokens() -> None:
    assert classify_aadr_date_method("directly inferred").family == "unclassified"
    assert classify_aadr_date_method("contextless").family == "unclassified"
    assert classify_aadr_date_method("modernized").family == "unclassified"

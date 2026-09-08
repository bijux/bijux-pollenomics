"""Machine chronology-review preparation tests."""

from decimal import Decimal

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization import (
    classify_aadr_date_method,
    parse_aadr_full_date,
    parse_aadr_numeric_evidence,
    prepare_aadr_chronology_evidence,
)


@pytest.mark.parametrize(
    ("raw_value", "status", "parsed_value", "sign"),
    [
        ("0", "parsed", Decimal("0"), "zero"),
        (" -120.50 ", "parsed", Decimal("-120.50"), "negative"),
        ("−7", "parsed", Decimal("-7"), "negative"),
        ("+12", "parsed", Decimal("12"), "positive"),
        ("..", "missing", None, None),
        ("", "missing", None, None),
        ("not-a-year", "invalid", None, None),
        ("NaN", "non_finite", None, None),
        ("Infinity", "non_finite", None, None),
    ],
)
def test_numeric_evidence_preserves_raw_signed_and_null_values(
    raw_value: str,
    status: str,
    parsed_value: Decimal | None,
    sign: str | None,
) -> None:
    evidence = parse_aadr_numeric_evidence(raw_value)

    assert evidence.raw_value == raw_value
    assert evidence.status == status
    assert evidence.parsed_value == parsed_value
    assert evidence.sign == sign


def test_full_date_parser_retains_multiple_source_expressions_without_conversion() -> (
    None
):
    raw_value = " 7643-7492 calBCE (8432+-50 BP, Ua-1) "

    evidence = parse_aadr_full_date(raw_value)

    assert evidence.raw_value == raw_value
    assert evidence.status == "parsed"
    assert [
        (token.kind, token.first_value, token.second_value, token.era)
        for token in evidence.tokens
    ] == [
        ("range", Decimal("7643"), Decimal("7492"), "CALBCE"),
        ("uncertainty", Decimal("8432"), Decimal("50"), "BP"),
    ]
    assert all(
        token.normalized_start < token.normalized_end for token in evidence.tokens
    )


def test_full_date_parser_keeps_signed_range_endpoints_visible() -> None:
    evidence = parse_aadr_full_date("−12--3 BP")

    [token] = evidence.tokens
    assert token.kind == "range"
    assert token.first_value == Decimal("-12")
    assert token.second_value == Decimal("-3")
    assert not hasattr(token, "younger_bp")
    assert not hasattr(token, "older_bp")


@pytest.mark.parametrize(
    "method",
    ["Direct", "Context", "Modern", "Historical", "Method", "unclassified"],
)
def test_every_date_method_remains_unadmitted_without_policy(method: str) -> None:
    evidence = prepare_aadr_chronology_evidence(
        date_method=classify_aadr_date_method(method),
        date_mean_bp_raw="-25",
        date_stddev_bp_raw="10",
        full_date_raw="100-50 BP",
    )

    assert evidence.evaluation_status == "review_required"
    assert evidence.refusal_reason_code == "method_specific_policy_required"
    assert not evidence.scientifically_admitted
    assert evidence.date_mean_bp.parsed_value == Decimal("-25")
    assert evidence.date_mean_bp.sign == "negative"


def test_missing_and_invalid_chronology_have_explicit_refusals() -> None:
    missing = prepare_aadr_chronology_evidence(
        date_method=classify_aadr_date_method(""),
        date_mean_bp_raw="..",
        date_stddev_bp_raw="",
        full_date_raw="..",
    )
    invalid = prepare_aadr_chronology_evidence(
        date_method=classify_aadr_date_method("Direct"),
        date_mean_bp_raw="unknown",
        date_stddev_bp_raw="20",
        full_date_raw="120-80 BP",
    )

    assert missing.evaluation_status == "refused"
    assert missing.refusal_reason_code == "source_chronology_missing"
    assert invalid.evaluation_status == "refused"
    assert invalid.refusal_reason_code == "invalid_numeric_evidence"
    assert not missing.scientifically_admitted
    assert not invalid.scientifically_admitted


def test_present_but_unparsed_full_date_still_requires_scientific_review() -> None:
    evidence = prepare_aadr_chronology_evidence(
        date_method=classify_aadr_date_method("Modern"),
        date_mean_bp_raw="0",
        date_stddev_bp_raw="0",
        full_date_raw="living participant",
    )

    assert evidence.full_date.status == "unparsed"
    assert evidence.full_date.raw_value == "living participant"
    assert evidence.evaluation_status == "review_required"
    assert not evidence.scientifically_admitted

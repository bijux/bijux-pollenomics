"""Machine-readable AADR chronology evidence awaiting scientific policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import re
from typing import Literal

DateMethodFamily = Literal[
    "direct",
    "contextual",
    "modern",
    "known_historical",
    "modeled_relational",
    "unclassified",
]
NumericEvidenceStatus = Literal["parsed", "missing", "invalid", "non_finite"]
FullDateEvidenceStatus = Literal["parsed", "missing", "unparsed"]
FullDateTokenKind = Literal["range", "uncertainty"]
ChronologyEvaluationStatus = Literal["review_required", "refused"]
ChronologyRefusalReason = Literal[
    "method_specific_policy_required",
    "source_chronology_missing",
    "invalid_numeric_evidence",
]

_NUMBER = r"[+\-\N{MINUS SIGN}]?\d+(?:\.\d+)?"
_ERA = r"cal\s*(?:BCE|BC|CE|AD)|BCE|BC|CE|AD|BP"
_RANGE_RE = re.compile(
    rf"(?P<first>{_NUMBER})\s*(?:-|\N{{EN DASH}}|\N{{EM DASH}}|to)\s*"
    rf"(?P<second>{_NUMBER})\s*(?P<era>{_ERA})(?![A-Za-z])",
    re.IGNORECASE,
)
_UNCERTAINTY_RE = re.compile(
    rf"(?P<first>{_NUMBER})\s*(?:\+/-|\+-|\N{{PLUS-MINUS SIGN}})\s*"
    rf"(?P<second>\d+(?:\.\d+)?)\s*(?P<era>{_ERA})(?![A-Za-z])",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class AadrDateMethodEvidence:
    """Raw dating-method token and its syntax-only family classification."""

    raw_value: str
    normalized_value: str
    family: DateMethodFamily


@dataclass(frozen=True, slots=True)
class AadrNumericEvidence:
    """One source numeric token parsed without changing its raw representation."""

    raw_value: str
    parsed_value: Decimal | None
    status: NumericEvidenceStatus

    @property
    def sign(self) -> Literal["negative", "zero", "positive"] | None:
        """Expose the sign of finite numeric evidence, including source zero."""
        if self.parsed_value is None:
            return None
        if self.parsed_value < 0:
            return "negative"
        if self.parsed_value > 0:
            return "positive"
        return "zero"


@dataclass(frozen=True, slots=True)
class AadrFullDateToken:
    """One syntactic range or uncertainty expression from a Full Date field."""

    kind: FullDateTokenKind
    raw_value: str
    first_value: Decimal
    second_value: Decimal
    era: str
    normalized_start: int
    normalized_end: int


@dataclass(frozen=True, slots=True)
class AadrFullDateEvidence:
    """Raw Full Date text and machine-readable tokens without BP conversion."""

    raw_value: str
    normalized_value: str
    tokens: tuple[AadrFullDateToken, ...]
    status: FullDateEvidenceStatus


@dataclass(frozen=True, slots=True)
class AadrChronologyEvidence:
    """Parsed source evidence explicitly withheld from scientific admission."""

    date_method: AadrDateMethodEvidence
    date_mean_bp: AadrNumericEvidence
    date_stddev_bp: AadrNumericEvidence
    full_date: AadrFullDateEvidence
    evaluation_status: ChronologyEvaluationStatus
    refusal_reason_code: ChronologyRefusalReason
    scientifically_admitted: Literal[False] = field(default=False, init=False)

    @property
    def date_mean_bp_raw(self) -> str:
        """Return the source-native mean token for compatibility and review."""
        return self.date_mean_bp.raw_value

    @property
    def date_stddev_bp_raw(self) -> str:
        """Return the source-native standard-deviation token for review."""
        return self.date_stddev_bp.raw_value

    @property
    def full_date_raw(self) -> str:
        """Return the unmodified source Full Date field."""
        return self.full_date.raw_value


def parse_aadr_numeric_evidence(raw_value: str) -> AadrNumericEvidence:
    """Parse one decimal source token without coercing absence to zero."""
    normalized_value = raw_value.strip()
    if not normalized_value or normalized_value == "..":
        return AadrNumericEvidence(
            raw_value=raw_value, parsed_value=None, status="missing"
        )
    try:
        value = Decimal(normalized_value.replace("\N{MINUS SIGN}", "-"))
    except InvalidOperation:
        return AadrNumericEvidence(
            raw_value=raw_value, parsed_value=None, status="invalid"
        )
    if not value.is_finite():
        return AadrNumericEvidence(
            raw_value=raw_value, parsed_value=None, status="non_finite"
        )
    return AadrNumericEvidence(raw_value=raw_value, parsed_value=value, status="parsed")


def parse_aadr_full_date(raw_value: str) -> AadrFullDateEvidence:
    """Extract date syntax while leaving calendar interpretation to policy."""
    normalized_value = " ".join(raw_value.split())
    if not normalized_value or normalized_value == "..":
        return AadrFullDateEvidence(
            raw_value=raw_value,
            normalized_value=normalized_value,
            tokens=(),
            status="missing",
        )
    matches = sorted(
        (
            *_RANGE_RE.finditer(normalized_value),
            *_UNCERTAINTY_RE.finditer(normalized_value),
        ),
        key=lambda match: (match.start(), match.end()),
    )
    tokens: list[AadrFullDateToken] = []
    occupied_ranges: list[tuple[int, int]] = []
    for match in matches:
        source_range = (match.start(), match.end())
        if any(
            start < source_range[1] and source_range[0] < end
            for start, end in occupied_ranges
        ):
            continue
        kind: FullDateTokenKind = (
            "uncertainty" if match.re is _UNCERTAINTY_RE else "range"
        )
        first_raw = match.group("first")
        second_raw = match.group("second")
        tokens.append(
            AadrFullDateToken(
                kind=kind,
                raw_value=match.group(0),
                first_value=Decimal(first_raw.replace("\N{MINUS SIGN}", "-")),
                second_value=Decimal(second_raw.replace("\N{MINUS SIGN}", "-")),
                era=" ".join(match.group("era").upper().split()),
                normalized_start=match.start(),
                normalized_end=match.end(),
            )
        )
        occupied_ranges.append(source_range)
    return AadrFullDateEvidence(
        raw_value=raw_value,
        normalized_value=normalized_value,
        tokens=tuple(tokens),
        status="parsed" if tokens else "unparsed",
    )


def prepare_aadr_chronology_evidence(
    *,
    date_method: AadrDateMethodEvidence,
    date_mean_bp_raw: str,
    date_stddev_bp_raw: str,
    full_date_raw: str,
) -> AadrChronologyEvidence:
    """Prepare machine review evidence without admitting a chronology claim."""
    date_mean_bp = parse_aadr_numeric_evidence(date_mean_bp_raw)
    date_stddev_bp = parse_aadr_numeric_evidence(date_stddev_bp_raw)
    full_date = parse_aadr_full_date(full_date_raw)
    numeric_statuses = {date_mean_bp.status, date_stddev_bp.status}
    if numeric_statuses & {"invalid", "non_finite"}:
        evaluation_status: ChronologyEvaluationStatus = "refused"
        refusal_reason: ChronologyRefusalReason = "invalid_numeric_evidence"
    elif (
        not date_method.normalized_value
        and date_mean_bp.status == "missing"
        and date_stddev_bp.status == "missing"
        and full_date.status == "missing"
    ):
        evaluation_status = "refused"
        refusal_reason = "source_chronology_missing"
    else:
        evaluation_status = "review_required"
        refusal_reason = "method_specific_policy_required"
    return AadrChronologyEvidence(
        date_method=date_method,
        date_mean_bp=date_mean_bp,
        date_stddev_bp=date_stddev_bp,
        full_date=full_date,
        evaluation_status=evaluation_status,
        refusal_reason_code=refusal_reason,
    )


__all__ = [
    "AadrChronologyEvidence",
    "AadrDateMethodEvidence",
    "AadrFullDateEvidence",
    "AadrFullDateToken",
    "AadrNumericEvidence",
    "ChronologyEvaluationStatus",
    "ChronologyRefusalReason",
    "DateMethodFamily",
    "FullDateEvidenceStatus",
    "FullDateTokenKind",
    "NumericEvidenceStatus",
    "parse_aadr_full_date",
    "parse_aadr_numeric_evidence",
    "prepare_aadr_chronology_evidence",
]

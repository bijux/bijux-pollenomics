from __future__ import annotations

import re


ADNA_CHRONOLOGY_STRENGTHS = (
    "sample_owned_interval",
    "sample_owned_text_only",
    "project_context_interval",
    "project_context_text_only",
    "unresolved",
)


ADNA_CHRONOLOGY_NORMALIZATION_STATUSES = (
    "normalized_interval",
    "normalized_point",
    "text_only_unparsed",
    "unresolved",
)


_BROAD_PERIOD_TEXT_RE = re.compile(
    r"\b("
    r"bronze|iron|neolithic|mesolithic|palaeolithic|paleolithic|chalcolithic|eneolithic|"
    r"roman|medieval|viking|migration|hellenistic|dynasty|period|epoch|century|millennium|"
    r"late antiquity|prehistoric|historic|holocene"
    r")\b",
    re.IGNORECASE,
)


_MODELED_DATE_RE = re.compile(
    r"\b(modeled|modelled|bayesian|posterior|oxcal|phase|sigma|2σ|1σ|calibrated|cal\.)\b",
    re.IGNORECASE,
)


_APPROXIMATE_DATE_RE = re.compile(
    r"\b(ca\.?|circa|around|approx(?:\.|imately)?|c\.)\b",
    re.IGNORECASE,
)


_HISTORICAL_DATE_RE = re.compile(
    r"\b(modern|present|recent|historic|historical|ce|ad)\b",
    re.IGNORECASE,
)

"""Stable country vocabulary and boundary-review policy identifiers."""

from __future__ import annotations

from ..collection import BOUNDARY_CODES, NATURAL_EARTH_VERSION

COUNTRY_ORDER = ("SE", "DK", "NO", "FI")
COUNTRY_NAMES_BY_CODE = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}
COUNTRY_CODES_BY_NAME = {name: code for code, name in COUNTRY_NAMES_BY_CODE.items()}
COUNTRY_ALIASES = {
    **dict(COUNTRY_NAMES_BY_CODE),
    **{code3: country for country, code3 in BOUNDARY_CODES.items()},
    **{country: country for country in BOUNDARY_CODES},
}
BOUNDARY_VERSION = f"natural-earth:{NATURAL_EARTH_VERSION}"
BOUNDARY_DIGEST_PREFIX = "sha256:"

"""Opt-in binding of selected Neotoma points to validated relational sites."""

from collections.abc import Mapping
import hashlib
import json
import math
from pathlib import Path
import re

from bijux_pollenomics.collection.sources.neotoma.country.site_geometry import (
    neotoma_site_representative_point,
)
from bijux_pollenomics.core.filesystem import read_regular_file
from bijux_pollenomics.core.text import clean_optional_text
from bijux_pollenomics.evidence.sources.neotoma import (
    read_validated_neotoma_relational_manifest,
)


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    except (TypeError, ValueError) as exc:
        raise ValueError("Neotoma manifest JSON differs") from exc


def read_bound_neotoma_manifest(root: Path, expected_sha256: str) -> dict[str, object]:
    """Bind the caller's exact manifest bytes to the validated manifest consumed."""
    if (
        not isinstance(expected_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
    ):
        raise ValueError("Neotoma manifest pin differs")
    raw = read_regular_file(root / "manifest.json", max_bytes=16 * 1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Neotoma manifest digest differs")
    try:
        captured = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Neotoma manifest JSON differs") from exc
    validated = read_validated_neotoma_relational_manifest(root)
    if _canonical(captured) != _canonical(validated):
        raise ValueError("Neotoma validated manifest differs from captured bytes")
    return validated


def validate_neotoma_site_binding(
    feature: Mapping[str, object], site: Mapping[str, object]
) -> None:
    """Check a point against source-native geography, name and assigned country."""
    source = site.get("source_payload")
    if not isinstance(source, Mapping):
        raise ValueError("Neotoma site source payload is unavailable")
    xy = neotoma_site_representative_point(source)
    name = clean_optional_text(source.get("sitename"))
    country = site.get("derived_country")
    if (
        xy is None
        or not name
        or not isinstance(country, str)
        or not country
        or site.get("country_decision_status") != "assigned"
    ):
        raise ValueError("Neotoma site binding source is unavailable")
    if (
        str(site.get("source_site_id")) != feature.get("evidence_row_id")
        or feature.get("country") != country
        or feature.get("title") != name
    ):
        raise ValueError("Neotoma site identity, country or name differs")
    for key, expected in [("longitude", xy[0]), ("latitude", xy[1])]:
        value = feature.get(key)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value != expected
        ):
            raise ValueError("Neotoma site coordinates differ")


def require_neotoma_binding_owner(
    pin: str | None, point_capture: object, projection: object, details: object
) -> None:
    """Require held point bytes and maintained source projection for this opt-in."""
    if pin is None:
        return
    from bijux_pollenomics.reporting.context.nordic_point_inputs import (
        NordicPointInputs,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.service import (
        build_map_evidence_projection,
    )

    if type(point_capture) is not NordicPointInputs:
        raise ValueError("Neotoma binding requires the captured Nordic point inputs")
    if projection is not build_map_evidence_projection or details is not None:
        raise ValueError("Neotoma binding requires the maintained source projection")

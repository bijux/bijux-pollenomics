"""Exact Neotoma source-label presets for chronology browsing."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType
from typing import Final

CATALOG_SCHEMA_VERSION: Final = "neotoma-source-label-presets.v1"
MEMBERSHIP_SEMANTICS: Final = "literal_source_label_membership"

_CONTENT_ID_PATTERN: Final = re.compile(r"sha256:[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class SourceLabelTaxon:
    """One exact source taxon identity admitted to a literal-label preset."""

    source_taxon_id: int
    source_reported_name: str
    preset_keys: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible taxon metadata."""
        return {
            "source_taxon_id": self.source_taxon_id,
            "source_reported_name": self.source_reported_name,
            "preset_keys": list(self.preset_keys),
        }


@dataclass(frozen=True, slots=True)
class SourceLabelPreset:
    """An immutable exact-ID selection that makes no classification claim."""

    key: str
    label: str
    member_taxon_ids: tuple[int, ...]

    def contains(self, source_taxon_id: int) -> bool:
        """Return membership by exact Neotoma taxon ID only."""
        return type(source_taxon_id) is int and source_taxon_id in self.member_taxon_ids

    def as_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible preset metadata."""
        return {
            "key": self.key,
            "label": self.label,
            "membership_semantics": MEMBERSHIP_SEMANTICS,
            "accepted_classification": False,
            "aggregation_is_abundance": False,
            "propagation_allowed": False,
            "member_taxon_count": len(self.member_taxon_ids),
            "member_taxon_ids": list(self.member_taxon_ids),
        }


NEOTOMA_SOURCE_LABEL_TAXA: Final = (
    SourceLabelTaxon(414, "Avena-type", ("avena",)),
    SourceLabelTaxon(415, "Avena/Triticum", ("avena", "triticum")),
    SourceLabelTaxon(416, "Poaceae (Cerealia)", ("cerealia",)),
    SourceLabelTaxon(427, "Poaceae (Cerealia) undiff.", ("cerealia",)),
    SourceLabelTaxon(488, "Secale-type", ("secale",)),
    SourceLabelTaxon(497, "Triticum-type", ("triticum",)),
    SourceLabelTaxon(967, "Secale", ("secale",)),
    SourceLabelTaxon(969, "Triticum", ("triticum",)),
    SourceLabelTaxon(1947, "Poaceae (Cerealia-type)", ("cerealia",)),
    SourceLabelTaxon(2941, "Poaceae (Cerealia-type) undiff.", ("cerealia",)),
    SourceLabelTaxon(3705, "Hordeum-type", ("hordeum",)),
    SourceLabelTaxon(3915, "Avena", ("avena",)),
    SourceLabelTaxon(3917, "Avena/Triticum-type", ("avena", "triticum")),
    SourceLabelTaxon(3918, "Avena sativa", ("avena",)),
    SourceLabelTaxon(3923, "Hordeum", ("hordeum",)),
    SourceLabelTaxon(3924, "Hordeum/Secale", ("hordeum", "secale")),
    SourceLabelTaxon(3926, "Secale cereale", ("secale",)),
    SourceLabelTaxon(31581, "cf. Avena", ("avena",)),
    SourceLabelTaxon(33008, "Hordeum group", ("hordeum",)),
    SourceLabelTaxon(48827, "cf. Avena sativa", ("avena",)),
    SourceLabelTaxon(49802, "Triticum aestivum", ("triticum",)),
)


def _members(preset_key: str) -> tuple[int, ...]:
    return tuple(
        taxon.source_taxon_id
        for taxon in NEOTOMA_SOURCE_LABEL_TAXA
        if preset_key in taxon.preset_keys
    )


NEOTOMA_SOURCE_LABEL_PRESETS: Final = (
    SourceLabelPreset("avena", "Avena source labels", _members("avena")),
    SourceLabelPreset("hordeum", "Hordeum source labels", _members("hordeum")),
    SourceLabelPreset("triticum", "Triticum source labels", _members("triticum")),
    SourceLabelPreset("secale", "Secale source labels", _members("secale")),
    SourceLabelPreset("cerealia", "Cerealia source labels", _members("cerealia")),
)

_TAXON_BY_ID: Final[Mapping[int, SourceLabelTaxon]] = MappingProxyType(
    {taxon.source_taxon_id: taxon for taxon in NEOTOMA_SOURCE_LABEL_TAXA}
)
_PRESET_BY_KEY: Final[Mapping[str, SourceLabelPreset]] = MappingProxyType(
    {preset.key: preset for preset in NEOTOMA_SOURCE_LABEL_PRESETS}
)


def source_label_taxon(source_taxon_id: int) -> SourceLabelTaxon | None:
    """Return the governed exact-label identity for one Neotoma taxon ID."""
    if type(source_taxon_id) is not int:
        return None
    return _TAXON_BY_ID.get(source_taxon_id)


def source_label_preset(preset_key: str) -> SourceLabelPreset:
    """Return one preset or reject a key outside the governed catalog."""
    try:
        return _PRESET_BY_KEY[preset_key]
    except KeyError as error:
        raise ValueError(
            f"unknown Neotoma source-label preset: {preset_key}"
        ) from error


def source_label_preset_contains(preset_key: str, *, source_taxon_id: int) -> bool:
    """Return exact-ID membership without source-label pattern matching."""
    return source_label_preset(preset_key).contains(source_taxon_id)


def source_label_preset_keys(source_taxon_id: int) -> tuple[str, ...]:
    """Return every deliberate preset membership for one exact source ID."""
    taxon = source_label_taxon(source_taxon_id)
    return () if taxon is None else taxon.preset_keys


def build_neotoma_source_label_preset_catalog(
    *, source_snapshot_id: str, build_id: str
) -> dict[str, object]:
    """Bind the immutable definitions to validated caller-supplied identities."""
    _validate_content_identity(source_snapshot_id, field_name="source_snapshot_id")
    _validate_content_identity(build_id, field_name="build_id")
    definition = _catalog_definition()
    payload: dict[str, object] = {
        **definition,
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
        "definition_sha256": _content_digest(definition),
    }
    payload["content_sha256"] = _content_digest(payload)
    return payload


def _catalog_definition() -> dict[str, object]:
    return {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "source": "neotoma",
        "membership_semantics": MEMBERSHIP_SEMANTICS,
        "accepted_classification": False,
        "aggregation_is_abundance": False,
        "propagation_allowed": False,
        "source_taxon_count": len(NEOTOMA_SOURCE_LABEL_TAXA),
        "preset_count": len(NEOTOMA_SOURCE_LABEL_PRESETS),
        "membership_count": sum(
            len(taxon.preset_keys) for taxon in NEOTOMA_SOURCE_LABEL_TAXA
        ),
        "source_taxa": [taxon.as_dict() for taxon in NEOTOMA_SOURCE_LABEL_TAXA],
        "presets": [preset.as_dict() for preset in NEOTOMA_SOURCE_LABEL_PRESETS],
    }


def _validate_content_identity(value: str, *, field_name: str) -> None:
    if not isinstance(value, str) or _CONTENT_ID_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 content identity")


def _content_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


__all__ = [
    "CATALOG_SCHEMA_VERSION",
    "MEMBERSHIP_SEMANTICS",
    "NEOTOMA_SOURCE_LABEL_PRESETS",
    "NEOTOMA_SOURCE_LABEL_TAXA",
    "SourceLabelPreset",
    "SourceLabelTaxon",
    "build_neotoma_source_label_preset_catalog",
    "source_label_preset",
    "source_label_preset_contains",
    "source_label_preset_keys",
    "source_label_taxon",
]

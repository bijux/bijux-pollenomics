"""Exact source-label preset contract tests."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
from typing import cast

import pytest

from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    MEMBERSHIP_SEMANTICS,
    NEOTOMA_SOURCE_LABEL_PRESETS,
    NEOTOMA_SOURCE_LABEL_TAXA,
    build_neotoma_source_label_preset_catalog,
    source_label_preset,
    source_label_preset_contains,
    source_label_preset_keys,
    source_label_taxon,
)

SOURCE_SNAPSHOT_ID = "sha256:" + "a" * 64
BUILD_ID = "sha256:" + "b" * 64

EXPECTED_TAXA = (
    (414, "Avena-type", ("avena",)),
    (415, "Avena/Triticum", ("avena", "triticum")),
    (416, "Poaceae (Cerealia)", ("cerealia",)),
    (427, "Poaceae (Cerealia) undiff.", ("cerealia",)),
    (488, "Secale-type", ("secale",)),
    (497, "Triticum-type", ("triticum",)),
    (967, "Secale", ("secale",)),
    (969, "Triticum", ("triticum",)),
    (1947, "Poaceae (Cerealia-type)", ("cerealia",)),
    (2941, "Poaceae (Cerealia-type) undiff.", ("cerealia",)),
    (3705, "Hordeum-type", ("hordeum",)),
    (3915, "Avena", ("avena",)),
    (3917, "Avena/Triticum-type", ("avena", "triticum")),
    (3918, "Avena sativa", ("avena",)),
    (3923, "Hordeum", ("hordeum",)),
    (3924, "Hordeum/Secale", ("hordeum", "secale")),
    (3926, "Secale cereale", ("secale",)),
    (31581, "cf. Avena", ("avena",)),
    (33008, "Hordeum group", ("hordeum",)),
    (48827, "cf. Avena sativa", ("avena",)),
    (49802, "Triticum aestivum", ("triticum",)),
)

EXPECTED_PRESETS = {
    "avena": (414, 415, 3915, 3917, 3918, 31581, 48827),
    "hordeum": (3705, 3923, 3924, 33008),
    "triticum": (415, 497, 969, 3917, 49802),
    "secale": (488, 967, 3924, 3926),
    "cerealia": (416, 427, 1947, 2941),
}


def test_catalog_has_the_exact_governed_taxon_inventory() -> None:
    assert (
        tuple(
            (taxon.source_taxon_id, taxon.source_reported_name, taxon.preset_keys)
            for taxon in NEOTOMA_SOURCE_LABEL_TAXA
        )
        == EXPECTED_TAXA
    )
    assert len({taxon.source_taxon_id for taxon in NEOTOMA_SOURCE_LABEL_TAXA}) == 21
    assert tuple(taxon.source_taxon_id for taxon in NEOTOMA_SOURCE_LABEL_TAXA) == (
        tuple(sorted(taxon.source_taxon_id for taxon in NEOTOMA_SOURCE_LABEL_TAXA))
    )


def test_presets_have_exact_id_memberships_and_deliberate_overlaps() -> None:
    assert {
        preset.key: preset.member_taxon_ids for preset in NEOTOMA_SOURCE_LABEL_PRESETS
    } == (EXPECTED_PRESETS)
    assert source_label_preset_keys(415) == ("avena", "triticum")
    assert source_label_preset_keys(3917) == ("avena", "triticum")
    assert source_label_preset_keys(3924) == ("hordeum", "secale")
    assert sum(len(ids) for ids in EXPECTED_PRESETS.values()) == 24
    assert set().union(*(set(ids) for ids in EXPECTED_PRESETS.values())) == {
        taxon_id for taxon_id, _label, _presets in EXPECTED_TAXA
    }


def test_runtime_selection_uses_only_exact_source_taxon_ids() -> None:
    assert source_label_preset_contains("avena", source_taxon_id=414)
    assert not source_label_preset_contains("avena", source_taxon_id=4150)
    assert not source_label_preset_contains("avena", source_taxon_id=True)
    assert source_label_taxon(414) is not None
    assert source_label_taxon(4150) is None
    assert source_label_taxon(True) is None
    assert source_label_preset_keys(4150) == ()
    assert tuple(inspect.signature(source_label_preset_contains).parameters) == (
        "preset_key",
        "source_taxon_id",
    )


def test_catalog_is_explicitly_nonclassifying_and_nonpropagating() -> None:
    catalog = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=SOURCE_SNAPSHOT_ID,
        build_id=BUILD_ID,
    )

    assert catalog["membership_semantics"] == MEMBERSHIP_SEMANTICS
    assert catalog["accepted_classification"] is False
    assert catalog["aggregation_is_abundance"] is False
    assert catalog["propagation_allowed"] is False
    assert catalog["source_taxon_count"] == 21
    assert catalog["preset_count"] == 5
    assert catalog["membership_count"] == 24
    presets = cast(list[dict[str, object]], catalog["presets"])
    assert all(row["membership_semantics"] == MEMBERSHIP_SEMANTICS for row in presets)
    assert all(row["accepted_classification"] is False for row in presets)
    assert all(row["aggregation_is_abundance"] is False for row in presets)
    assert all(row["propagation_allowed"] is False for row in presets)


def test_catalog_serialization_and_digests_are_deterministic() -> None:
    first = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=SOURCE_SNAPSHOT_ID,
        build_id=BUILD_ID,
    )
    second = build_neotoma_source_label_preset_catalog(
        source_snapshot_id=SOURCE_SNAPSHOT_ID,
        build_id=BUILD_ID,
    )

    assert first == second
    assert first["definition_sha256"] == (
        "sha256:eb97dda901698c7274b15591c70276e6f5267f812eddfaf92ea6a0703c20f926"
    )
    assert first["content_sha256"] == (
        "sha256:d7b9f6564676a0ce9587e85054a3f02ab663d1fdf06c28aec846817e74a77f83"
    )
    without_content_digest = deepcopy(first)
    content_digest = without_content_digest.pop("content_sha256")
    assert content_digest == _digest(without_content_digest)
    without_definition_digest = deepcopy(without_content_digest)
    without_definition_digest.pop("source_snapshot_id")
    without_definition_digest.pop("build_id")
    definition_digest = without_definition_digest.pop("definition_sha256")
    assert definition_digest == _digest(without_definition_digest)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("source_snapshot_id", ""),
        ("source_snapshot_id", "sha256:fixture"),
        ("source_snapshot_id", "sha256:" + "A" * 64),
        ("build_id", "build-1"),
    ],
)
def test_catalog_rejects_unvalidated_source_identities(
    field_name: str, value: str
) -> None:
    identities = {
        "source_snapshot_id": SOURCE_SNAPSHOT_ID,
        "build_id": BUILD_ID,
    }
    identities[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        build_neotoma_source_label_preset_catalog(**identities)


def test_unknown_preset_is_rejected_instead_of_inferred() -> None:
    with pytest.raises(ValueError, match="unknown Neotoma source-label preset"):
        source_label_preset("cereal")


def _digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

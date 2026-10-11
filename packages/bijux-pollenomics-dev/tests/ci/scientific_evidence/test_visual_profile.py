"""Keep the governed classification visual reference and receipt pins closed."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re

import yaml

from bijux_pollenomics.analysis.classification.events.authority import (
    _CLASSIFICATION_AUTHORITY as EVENT_AUTHORITY,
)
from bijux_pollenomics.analysis.propagation.outputs.models import (
    _CLASSIFICATION_AUTHORITY as PROPAGATION_AUTHORITY,
)

_REPOSITORY = Path(__file__).resolve().parents[5]
_CONTRACT = (
    _REPOSITORY / "configs/scientific-contracts/ecological-classification.v1.yaml"
)


def test_visual_profile_reference_resolves_with_matching_palette() -> None:
    classification = yaml.safe_load(_CONTRACT.read_bytes())
    policy = classification["taxon_color_policy"]
    relative = Path(policy["normative_visual_profile"])
    assert not relative.is_absolute() and ".." not in relative.parts
    profile = yaml.safe_load((_REPOSITORY / relative).read_bytes())
    assert profile["contract_id"] == "bijux-pollenomics.map-visual-profile"
    assert profile["contract_version"] == "1.0.0"
    assert profile["palette_id"] == policy["palette_id"]
    assert profile["palette_version"] == policy["palette_version"]
    required = {"whole:pollen"}
    for group in classification["hierarchy"]["groups"]:
        required.add(f"group:{group['group_id']}")
        required.update(
            f"subgroup:{subgroup['subgroup_id']}" for subgroup in group["subgroups"]
        )
    vocabulary = classification["role_vocabulary"]
    required.update(
        f"role:{role['role_id']}" for role in vocabulary["crop_evidence_roles"]
    )
    required.update(f"role:{role}" for role in vocabulary["ecological_roles"])
    anchors = profile["normative_anchors"]
    assert required <= anchors.keys()
    assert all(
        re.fullmatch(r"#[0-9A-F]{6}", anchor["hex"]) for anchor in anchors.values()
    )
    distinct = profile["distinctions"]["required_distinct_keys"]
    assert len({anchors[key]["hex"] for key in distinct}) == len(distinct)
    for status in ("indeterminate_order", "unresolved"):
        assert profile["certainty_styles"][status]["directional"] is False
        assert profile["certainty_styles"][status]["arrowhead"] == "none"
    assert profile["non_color_requirements"]["color_only_encoding_allowed"] is False
    fallback = profile["fallback_policy"]["palette_registry_load_failure"]
    assert fallback["silent_default_palette_allowed"] is False


def test_classification_receipt_owners_bind_the_current_contract() -> None:
    digest = f"sha256:{hashlib.sha256(_CONTRACT.read_bytes()).hexdigest()}"
    for authority in (EVENT_AUTHORITY, PROPAGATION_AUTHORITY):
        assert authority.contract_digest == digest
        assert authority.manifest_sha256 == EVENT_AUTHORITY.manifest_sha256
        assert authority.source_snapshot_id == EVENT_AUTHORITY.source_snapshot_id
        assert authority.build_id == EVENT_AUTHORITY.build_id
        assert authority.producer_digest == EVENT_AUTHORITY.producer_digest
        assert authority.accepted_mapping_count == len(
            EVENT_AUTHORITY.accepted_mapping_sha256_by_concept
        )

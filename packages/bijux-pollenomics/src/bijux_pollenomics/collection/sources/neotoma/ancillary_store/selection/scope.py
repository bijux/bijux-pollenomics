"""Fresh selected-root obligations from independently pinned outcome-free metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...capture.facets.models import (
    SCOPED_FACET_SCHEMA,
    NeotomaFacetPlan,
    NeotomaFacetScopeInputs,
)
from ...capture.facets.scope import prepare_facet_parent_scope
from ...capture.parent_scope import _roster
from ...capture.receipts import _object, _safe_root
from ...capture.resources.models import DEVELOPMENT_ROLES, NeotomaResourceSpec
from ...capture.resources.protocol import identity
from ...client import positive_native_id
from ...resource_catalogue.archive.files import validate_manifest
from ...resource_catalogue.source_projection import _same
from ..capsule.inventory import _legacy_roots
from ..context.validation import _FIELDS as CONTEXT_FIELDS
from ..context.validation import SCHEMA, NeotomaAncillaryContext
from .metadata import SelectedMetadata, members, pinned

_OWNER = ("dataset_id", "site_id", "collection_unit_id", "dataset_type", "database")


def resource(row: dict[str, Any]) -> NeotomaResourceSpec:
    locator = row["metadata_locator"]
    return NeotomaResourceSpec(
        row["dataset_id"],
        row["site_id"],
        row["collection_unit_id"],
        row["dataset_type"],
        row["database"],
        row["exposure_roles"]["current"],
        locator["response_sha256"],
        locator["json_pointer"],
        ("current",),
    )


def _header(proof: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in proof.items() if key != "parents"}


@dataclass
class CurrentScope:
    context: NeotomaAncillaryContext
    roster: dict[str, Any]
    inputs: NeotomaFacetScopeInputs
    roster_pin: str
    published: dict[str, Any]
    proof: dict[str, Any] | None = None

    def guard(self, owners: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
        """Check every recorded owner before deduplicating native dataset roots."""
        rows = {row["dataset_id"]: row for row in self.roster["resources"]}
        selected = {}
        for owner in owners:
            dataset = positive_native_id(owner.get("dataset_id"))
            row = rows.get(dataset)
            if row is None or not _same(
                {key: owner.get(key) for key in _OWNER},
                {key: row[key] for key in _OWNER},
            ):
                raise ValueError("Selected source owner differs from current context")
            if (
                owner.get("exposure_role") not in DEVELOPMENT_ROLES
                or row["exposure_roles"]["current"] not in DEVELOPMENT_ROLES
            ):
                raise ValueError("Selected source role forbids entity access")
            selected[dataset] = resource(row)
        self.proof = prepare_facet_parent_scope(
            NeotomaFacetPlan(
                tuple(selected[key] for key in sorted(selected)),
                self.roster_pin,
                ("taxa",),
            ),
            self.inputs,
        )
        if not _same(_header(self.proof), _header(self.published)):
            raise ValueError("Selected current parent proof header is stale or differs")
        published = self.published.get("parents")
        if not isinstance(published, list):
            raise ValueError("Selected current parent proof population is malformed")
        parents = {}
        for parent in self.proof["parents"]:
            matches = [
                row
                for row in published
                if isinstance(row, dict)
                and row.get("dataset_id") == parent["dataset_id"]
            ]
            if len(matches) != 1 or not _same(matches[0], parent):
                raise ValueError("Selected current parent obligation differs")
            if parent["effective_scope_role"] not in DEVELOPMENT_ROLES:
                raise ValueError("Selected current parent scope forbids entity access")
            parents[parent["dataset_id"]] = parent
        return parents

    def original(
        self, metadata: SelectedMetadata, capture: dict[str, Any], entry: dict[str, Any]
    ) -> None:
        control = capture["control"]
        plan = capture["plan"]
        if capture["document"]["schema_version"] != SCOPED_FACET_SCHEMA:
            # Restrict original identity validation to the named root; no pre-GET proof is invented.
            selected_control = {
                **control,
                "plan": {
                    **control["plan"],
                    "resources": [
                        row
                        for row in control["plan"]["resources"]
                        if row["dataset_id"] == entry["root_identity"]["dataset_id"]
                    ],
                },
            }
            digest = plan.roster_sha256
            if digest not in self.context.legacy_rosters:
                raise ValueError("Selected original roster identity is unavailable")
            member = self.context.manifest["legacy_rosters"][digest]
            pinned(self.context.legacy_rosters[digest], digest, member["bytes"])
            _legacy_roots(selected_control, self.context)
            return
        if plan.roster_sha256 != self.roster_pin or self.proof is None:
            raise ValueError(
                "Selected original parent scope has no authenticated current resolver"
            )
        rows = [
            row
            for row in self.roster["resources"]
            if row["dataset_id"] == entry["root_identity"]["dataset_id"]
        ]
        if len(rows) != 1 or not _same(
            entry["root_identity"], identity(resource(rows[0]))
        ):
            raise ValueError(
                "Selected original source locator differs from frozen roster"
            )
        reference = control.get("parent_scope")
        if (
            not isinstance(reference, dict)
            or set(reference) != {"file", "sha256"}
            or reference["file"] != "parent-scope.json"
        ):
            raise ValueError("Selected original parent scope reference differs")
        original = _object(metadata.source_member(capture, reference["file"]))

        if (
            capture["descriptor"]["files"][reference["file"]]["sha256"]
            != reference["sha256"]
        ):
            raise ValueError("Selected original parent scope identity differs")
        if not _same(_header(original), _header(self.proof)):
            raise ValueError("Selected original parent scope header differs")
        dataset = entry["root_identity"]["dataset_id"]
        expected = [
            row for row in self.proof["parents"] if row["dataset_id"] == dataset
        ]
        observed = [
            row
            for row in original.get("parents", [])
            if isinstance(row, dict) and row.get("dataset_id") == dataset
        ]
        if (
            len(expected) != 1
            or not _same(observed, expected)
            or entry.get("parent_scope_role") != expected[0]["effective_scope_role"]
        ):
            raise ValueError("Selected original parent scope obligation differs")


def current_scope(
    metadata: SelectedMetadata, context_directory: Path, native_archive_directory: Path
) -> CurrentScope:
    """Resolve selected scope without scanning native archive inventories or entities."""
    root, native_root = (
        _safe_root(context_directory),
        _safe_root(native_archive_directory),
    )
    raw = pinned(root / "manifest.json", metadata.context_pin)
    context = _object(raw)
    members(context, raw)
    if (
        set(context) != CONTEXT_FIELDS
        or context["schema_version"] != SCHEMA
        or context["scientific_admission"] != "not_asserted"
        or type(context["native_body_copies"]) is not int
        or context["native_body_copies"] != 0
        or context["historical_snapshot_replaced"] is not False
        or context["pre_get_scope_reconstructed"] is not False
        or context["current_scope_verification"]
        != "resolver_identity_only_parent_obligations_not_replayed"
    ):
        raise ValueError("Selected current context claims differ")
    claim = context["native_archive"]
    if (
        not isinstance(claim, dict)
        or claim.get("manifest_sha256") != metadata.native_pin
        or claim.get("current_roster_sha256")
        != metadata.manifest["current_roster_sha256"]
    ):
        raise ValueError("Selected context and native archive anchors differ")
    archive = _object(pinned(native_root / "manifest.json", metadata.native_pin))
    validate_manifest(archive)
    if archive["catalogue_manifest_sha256"] != claim.get("catalogue_manifest_sha256"):
        raise ValueError("Selected native catalogue identity differs")
    current_path = native_root / "catalogue/source-inventory.json"
    native_member = archive["files"].get("catalogue/source-inventory.json")
    if (
        not isinstance(native_member, dict)
        or native_member["sha256"] != claim["current_roster_sha256"]
    ):
        raise ValueError("Selected current roster identity differs")
    metadata.member(native_root, archive, "catalogue/source-inventory.json")
    roster_pin = claim["current_roster_sha256"]
    roster = _roster(current_path, roster_pin)
    required = set(roster.get("source_metadata_capture_manifest_sha256", []))
    historical_required = set()
    for row in roster["resources"]:
        lookup = row.get("current_metadata_lookup")
        if lookup is not None:
            required.add(lookup["manifest_sha256"])
        locator = row["metadata_locator"]
        if (
            locator.get("source_kind")
            == "retained_relational_dataset_metadata_not_current_HTTP"
        ):
            historical_required.add(locator["response_sha256"])
    if sorted(required) != claim.get("metadata_capture_manifest_sha256s") or sorted(
        historical_required
    ) != claim.get("historical_metadata_part_sha256s"):
        raise ValueError("Selected native metadata resolver closure differs")
    captures = {}
    for pin in required:
        relative = f"captures/{pin}/capture-manifest.json"
        if archive["files"].get(relative, {}).get("sha256") != pin:
            raise ValueError("Selected native metadata capture identity differs")
        metadata.member(native_root, archive, relative)
        captures[pin] = native_root / "captures" / pin
    historical = {}
    if historical_required:
        relative = "captures/original-metadata/manifest.json"
        original_pin = claim["original_relational_manifest_sha256"]
        if archive["files"].get(relative, {}).get("sha256") != original_pin:
            raise ValueError("Selected original metadata manifest differs")
        original = _object(metadata.member(native_root, archive, relative))
        for part in original["surfaces"]["datasets"]["parts"]:
            if part["sha256"] in historical_required:
                name = f"captures/original-metadata/{part['path']}"
                if archive["files"].get(name, {}).get("sha256") != part["sha256"]:
                    raise ValueError("Selected original metadata part differs")
                historical[part["sha256"]] = native_root / name
        if set(historical) != historical_required:
            raise ValueError("Selected original metadata resolver closure differs")
    legacy = {}
    for digest, member in context["legacy_rosters"].items():
        relative = f"rosters/{digest}.json"
        if member != {
            "path": relative,
            "sha256": digest,
            "bytes": member.get("bytes"),
            "parent_scope_verification": "not_recorded_legacy_capture",
            "use_scope": "original_capture_identity_only",
        } or not _same(
            context["files"].get(relative),
            {key: member[key] for key in ("sha256", "bytes")},
        ):
            raise ValueError("Selected original roster declaration differs")
        legacy[digest] = root / relative
    authority = context["exposure_authority"]
    relative = f"evidence/exposure/{authority['sha256']}.json"
    if (
        authority.get("path") != relative
        or not _same(
            context["files"].get(relative),
            {key: authority[key] for key in ("sha256", "bytes")},
        )
        or set(context["files"])
        != {relative, *(f"rosters/{digest}.json" for digest in legacy)}
    ):
        raise ValueError("Selected context exposure authority declaration differs")
    reviewed = roster.get("reviewed_exposure_metadata_sha256")
    if reviewed != claim.get("reviewed_exposure_metadata_sha256") or reviewed not in (
        None,
        authority["sha256"],
    ):
        raise ValueError("Selected exposure authority binding differs")
    if reviewed is not None:
        metadata.member(root, context, relative)
    inputs = NeotomaFacetScopeInputs(
        current_path,
        captures,
        historical,
        root / relative if reviewed is not None else None,
    )
    reference = metadata.manifest["current_use_parent_obligations"]
    name = "scope/current-parent-proof.json"
    if (
        not isinstance(reference, dict)
        or not _same(
            reference,
            {
                "path": name,
                **metadata.manifest["files"][name],
                "scope": "current_use_metadata_only_not_historical_preget",
            },
        )
        or reference["sha256"]
        != metadata.manifest["current_use_parent_obligations_sha256"]
    ):
        raise ValueError("Selected current parent proof declaration differs")
    published = _object(metadata.member(metadata.root, metadata.manifest, name))
    return CurrentScope(
        NeotomaAncillaryContext(context, {roster_pin: inputs}, legacy),
        roster,
        inputs,
        roster_pin,
        published,
    )

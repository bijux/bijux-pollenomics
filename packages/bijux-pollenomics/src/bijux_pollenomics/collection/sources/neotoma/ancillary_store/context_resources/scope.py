"""Independent original/current source anchors and whole-site native-role duties."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ...capture.context_resources.models import NeotomaContextResourcePlan
from ...capture.context_resources.protocol import digest
from ...capture.context_resources.scope import prepare_scope
from ...capture.resources.replay import _same_json


@dataclass(frozen=True)
class NeotomaContextArchiveBindings:
    context_directory: Path
    expected_context_sha256: str
    native_archive_directory: Path
    expected_native_archive_sha256: str


@dataclass(frozen=True)
class ContextScopes:
    original: dict[str, Any]
    current: dict[str, Any]

    def account(self, site_id: int) -> dict[str, Any]:
        old = next(
            row for row in self.original["requested_sites"] if row["site_id"] == site_id
        )
        new = next(
            row for row in self.current["requested_sites"] if row["site_id"] == site_id
        )
        same = _same_json(old["current_native_units"], new["current_native_units"])
        return {
            "site_id": site_id,
            "original_scope_status": old["scope_status"],
            "current_scope_status": new["scope_status"],
            "original_role": old["effective_scope_role"],
            "current_role": new["effective_scope_role"],
            "native_owner_span_matches_original": same,
            "current_access": "selected_source_guard_required"
            if same
            and old["scope_status"] == new["scope_status"] == "eligible_current_scope"
            else "blocked_current_or_original_scope",
            "scientific_admission": "not_asserted",
        }

    def guard(self, site_id: int) -> None:
        if self.account(site_id)["current_access"] != "selected_source_guard_required":
            raise ValueError(
                "Context original/current native owner or protected scope forbids body access"
            )


def prepare_scopes(
    plan: NeotomaContextResourcePlan,
    source_proof: dict[str, Any],
    *,
    original: NeotomaContextArchiveBindings,
    current: NeotomaContextArchiveBindings,
) -> ContextScopes:
    for binding in (original, current):
        if not isinstance(binding, NeotomaContextArchiveBindings):
            raise ValueError(
                "Independent original/current context bindings are required"
            )
        digest(binding.expected_context_sha256)
        digest(binding.expected_native_archive_sha256)
    if (
        original.expected_context_sha256 != plan.context_manifest_sha256
        or original.expected_native_archive_sha256
        != plan.native_archive_manifest_sha256
    ):
        raise ValueError("Original context/native source epoch differs from capture")
    old = prepare_scope(
        plan,
        context_directory=original.context_directory,
        native_archive_directory=original.native_archive_directory,
    )
    if not _same_json(old, source_proof):
        raise ValueError("Original context pre-GET source scope differs")
    if original == current:
        new = old
    else:
        new = prepare_scope(
            replace(
                plan,
                context_manifest_sha256=current.expected_context_sha256,
                native_archive_manifest_sha256=current.expected_native_archive_sha256,
            ),
            context_directory=current.context_directory,
            native_archive_directory=current.native_archive_directory,
        )
    return ContextScopes(old, new)

"""Bind reviewed checked-in report documentation and code to the Git candidate."""

from __future__ import annotations

import ast
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import (
    InventoryEntry,
    ReproducibleReportError,
    repository_identity,
)

from .contracts import (
    JsonObject,
    ReportRebuildError,
    canonical_json_sha256,
    sha256_bytes,
)
from .evidence import inventory_json
from .ownership import (
    DEFAULT_INVENTORY,
    ReportOwnershipError,
    _load_inventory,
    _regular_confined_file,
    check_report_ownership,
)
from .scientific_captures.adna.current_domain import (
    validated_current_domain_evidence,
)
from .scientific_captures.adna.current_export import (
    validated_aadr_current_export_evidence,
)
from .scientific_captures.author_grid.admission import (
    validated_author_grid_capture,
)
from .scientific_captures.author_native_reference import (
    validated_author_native_reference_capture,
)
from .scientific_captures.author_optimizer_diagnostics import (
    validated_author_optimizer_diagnostic_capture,
)
from .scientific_captures.author_radius import validated_author_radius_capture
from .scientific_captures.author_site_evaluations import (
    validated_author_site_evaluation_captures,
)
from .scientific_captures.constrained_author import validated_constrained_author_capture
from .scientific_captures.controlled_numerical.love_objective import (
    validated_love_objective_capture,
)
from .scientific_captures.controlled_numerical.lra_comparison import (
    validated_controlled_lra_comparison_capture,
)
from .scientific_captures.country_reports.sweden import (
    validated_sweden_country_capture,
)
from .scientific_captures.lake_registry.neotoma_lake import (
    validated_neotoma_lake_capture,
)
from .scientific_captures.lake_registry.svar import (
    validated_svar_capture,
)
from .scientific_captures.lake_registry.svar_census import (
    validated_svar_feature_census_capture,
)
from .scientific_captures.land_use.hyde_country import (
    validated_hyde_country_capture,
)
from .scientific_captures.land_use.hyde_grid import (
    validated_hyde_grid_source_captures,
)
from .scientific_captures.land_use.openland_members import (
    validated_openland_member_capture,
)
from .scientific_captures.linux_r_reference import (
    validated_linux_r_reference_capture,
)
from .scientific_captures.nordic_static_basin import (
    validated_nordic_static_basin_captures,
)
from .scientific_captures.pollen_source.amsoldingersee import (
    validated_amsoldingersee_capture,
)
from .scientific_captures.pollen_source.neotoma_counts import (
    validated_neotoma_selected_count_evidence,
)
from .scientific_captures.pollen_source.neotoma_publication import (
    validated_neotoma_publication_capture,
)
from .scientific_captures.pollen_source.rootsi_chronology import (
    validated_rootsi_capture,
)
from .scientific_captures.pollen_source.solsoe_pollen import (
    validated_solsoe_pollen_capture,
)
from .scientific_captures.pollen_source.solsoe_selection import (
    validated_solsoe_selection_capture,
)
from .scientific_captures.pollen_source.swedish_cohort import (
    validated_swedish_cohort_capture,
)
from .scientific_captures.pollen_source.swedish_direct_pollen import (
    validated_swedish_direct_pollen_capture,
)
from .scientific_captures.representative_performance import (
    validated_representative_performance_capture,
)
from .scientific_captures.source_accounting.current_audit import (
    validated_current_source_accounting_capture,
)
from .scientific_captures.swedish_parameter_transfer import (
    validated_swedish_parameter_transfer_captures,
)
from .scientific_captures.swedish_source_chronology import (
    validated_swedish_source_chronology_captures,
)
from .scientific_captures.swedish_static_basin import (
    validated_swedish_static_basin_captures,
)
from .scientific_captures.vegetation_reference.empd2_nfi_pairing import (
    validated_empd2_nfi_pairing_capture,
)
from .scientific_captures.vegetation_reference.nfi_measurement import (
    validated_nfi_measurement_capture,
)
from .scientific_captures.vegetation_reference.slu_guide import (
    validated_slu_guide_capture,
)

# This independent admission set is reviewed separately from mutable role labels.
# Updating a maintained report path requires an explicit transport-contract change.
MAINTAINED_ROLE_PATHS = {
    "maintained_code": (
        63,
        "0180b0dc0e74063546778f1d63acdfcccf13f476ac9c5f0048ccaeb19df6c56d",
    ),
    "maintained_editorial": (
        204,
        "ce1c97b558ca8af8eeb8bacbb07cea0b32d2399f6b2e1fcaa7c496ffadf074ad",
    ),
    "maintained_configuration": (
        14,
        "a81101b6cffc4ddc16e6691dc8a0eab0364b40e3787a316b4e7757d633298774",
    ),
}
SOURCE_FORMATS = {
    "maintained_code": frozenset({".py", ".R"}),
    "maintained_editorial": frozenset({".md"}),
    "maintained_configuration": frozenset({".json"}),
}


def _configuration_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReportRebuildError(f"duplicate maintained configuration key: {key}")
        result[key] = value
    return result


def _finite_json(value: object) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite_json(child) for child in value.values())
    if isinstance(value, list):
        return all(_finite_json(child) for child in value)
    return True


def _configuration_constant(value: str) -> None:
    raise ReportRebuildError(f"nonfinite maintained configuration value: {value}")


def _head_blob(repository: Path, path: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "show", f"HEAD:{path}"],
            capture_output=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ReportRebuildError(
            f"maintained source has no committed blob: {path}"
        ) from error
    return result.stdout


def validated_maintained_report_sources(
    repository: Path,
    tracked: tuple[InventoryEntry, ...],
    *,
    expected_repository: JsonObject,
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only reviewed source formats and bytes from this clean Git commit."""
    repository = repository.resolve()
    try:
        ownership = check_report_ownership(repository)
        inventory = _load_inventory(repository, DEFAULT_INVENTORY)
        inventory_path = _regular_confined_file(
            repository, DEFAULT_INVENTORY.as_posix(), "ownership inventory"
        )
        inventory_bytes = inventory_path.read_bytes()
        if inventory_bytes != _head_blob(repository, DEFAULT_INVENTORY.as_posix()):
            raise ReportRebuildError("ownership inventory differs from Git candidate")
        if repository_identity(repository, required=True) != expected_repository:
            raise ReportRebuildError("maintained source Git candidate changed")
    except (ReportOwnershipError, ReproducibleReportError) as error:
        raise ReportRebuildError(
            "maintained source ownership or Git identity failed"
        ) from error

    role_paths: dict[str, list[str]] = {role: [] for role in MAINTAINED_ROLE_PATHS}
    role_owners: dict[str, dict[str, list[str]]] = {
        role: {} for role in MAINTAINED_ROLE_PATHS
    }
    for raw in inventory["owners"]:
        owner = raw if isinstance(raw, dict) else {}
        role = owner.get("role")
        if role not in MAINTAINED_ROLE_PATHS:
            continue
        paths = owner["paths"]
        if not isinstance(paths, list) or not all(
            isinstance(path, str) for path in paths
        ):
            raise ReportRebuildError("maintained source owner paths are invalid")
        role_paths[role].extend(paths)
        role_owners[role][owner["owner_id"]] = paths

    for role, (expected_count, expected_digest) in MAINTAINED_ROLE_PATHS.items():
        paths = sorted(role_paths[role])
        if (
            len(paths) != expected_count
            or canonical_json_sha256(paths) != expected_digest
            or ownership.role_counts.get(role) != expected_count
        ):
            raise ReportRebuildError(f"reviewed {role} path set changed")
        if any(Path(path).suffix not in SOURCE_FORMATS[role] for path in paths):
            raise ReportRebuildError(f"unsupported {role} source format")

    tracked_by_path = {f"docs/report/{entry.path}": entry for entry in tracked}
    selected: list[InventoryEntry] = []
    for role in MAINTAINED_ROLE_PATHS:
        for path in sorted(role_paths[role]):
            try:
                source = _regular_confined_file(repository, path, "maintained source")
                payload = source.read_bytes()
                text = payload.decode("utf-8")
                if "\x00" in text:
                    raise ReportRebuildError(f"maintained source contains NUL: {path}")
                if source.suffix == ".py":
                    ast.parse(text, filename=path)
                if role == "maintained_configuration":
                    configuration = json.loads(
                        text,
                        object_pairs_hook=_configuration_object,
                        parse_constant=_configuration_constant,
                    )
                    if not isinstance(configuration, dict) or not _finite_json(
                        configuration
                    ):
                        raise ReportRebuildError(
                            f"maintained configuration must be a finite object: {path}"
                        )
            except (
                OSError,
                SyntaxError,
                ValueError,
                RecursionError,
            ) as error:
                raise ReportRebuildError(
                    f"maintained source format invalid: {path}"
                ) from error
            if payload != _head_blob(repository, path):
                raise ReportRebuildError(
                    f"maintained source differs from Git candidate: {path}"
                )
            entry = tracked_by_path.get(path)
            if (
                entry is None
                or entry.kind != "file"
                or entry.sha256 != sha256_bytes(payload)
                or entry.size != len(payload)
            ):
                raise ReportRebuildError(f"maintained source inventory differs: {path}")
            selected.append(entry)
    capture_entries, capture_evidence = validated_swedish_static_basin_captures(
        repository, tracked_by_path, inventory["owners"]
    )
    parameter_entries, parameter_evidence = (
        validated_swedish_parameter_transfer_captures(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    chronology_entries, chronology_evidence = (
        validated_swedish_source_chronology_captures(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    nordic_entries, nordic_evidence = validated_nordic_static_basin_captures(
        repository, tracked_by_path, inventory["owners"]
    )
    linux_entries, linux_evidence = validated_linux_r_reference_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    slu_guide_entries, slu_guide_evidence = validated_slu_guide_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    if slu_guide_entries:
        raise ReportRebuildError("Original owner acceptance remains unresolved")
    author_entries, author_evidence = validated_author_site_evaluation_captures(
        repository, tracked_by_path, inventory["owners"]
    )
    author_native_entries, author_native_evidence = (
        validated_author_native_reference_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    constrained_entries, constrained_evidence = validated_constrained_author_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    optimizer_entries, optimizer_evidence = (
        validated_author_optimizer_diagnostic_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    performance_entries, performance_evidence = (
        validated_representative_performance_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    nfi_entries, nfi_evidence = validated_nfi_measurement_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    controlled_entries, controlled_evidence = (
        validated_controlled_lra_comparison_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    radius_entries, radius_evidence = validated_author_radius_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    grid_entries, grid_evidence = validated_author_grid_capture(
        repository, tracked_by_path, inventory["owners"]
    )

    svar_entries, svar_evidence = validated_svar_capture(
        repository, tracked_by_path, inventory["owners"]
    )

    solsoe_selection_entries, solsoe_selection_evidence = (
        validated_solsoe_selection_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )

    solsoe_pollen_entries, solsoe_pollen_evidence = validated_solsoe_pollen_capture(
        repository, tracked_by_path, inventory["owners"]
    )

    rootsi_entries, rootsi_evidence = validated_rootsi_capture(
        repository, tracked_by_path, inventory["owners"]
    )

    swedish_entries, swedish_evidence = validated_swedish_cohort_capture(
        repository, tracked_by_path, inventory["owners"]
    )

    hyde_entries, hyde_evidence = validated_hyde_country_capture(
        repository, tracked_by_path, inventory["owners"]
    )

    love_objective_entries, love_objective_evidence = validated_love_objective_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    neotoma_lake_entries, neotoma_lake_evidence = validated_neotoma_lake_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    svar_census_entries, svar_census_evidence = validated_svar_feature_census_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    hyde_grid_entries, hyde_grid_evidence = validated_hyde_grid_source_captures(
        repository, tracked_by_path, inventory["owners"]
    )
    openland_entries, openland_evidence = validated_openland_member_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    amsoldingersee_entries, amsoldingersee_evidence = validated_amsoldingersee_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    neotoma_publication_entries, neotoma_publication_evidence = (
        validated_neotoma_publication_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    swedish_direct_entries, swedish_direct_evidence = (
        validated_swedish_direct_pollen_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    empd2_nfi_entries, empd2_nfi_evidence = validated_empd2_nfi_pairing_capture(
        repository, tracked_by_path, inventory["owners"]
    )
    if openland_entries or neotoma_publication_entries:
        raise ReportRebuildError("Original owner acceptance remains unresolved")
    adna_current_export_evidence = validated_aadr_current_export_evidence(
        repository, inventory["owners"]
    )
    adna_current_domain_evidence = validated_current_domain_evidence(
        repository, inventory["owners"], adna_current_export_evidence
    )
    neotoma_count_evidence = validated_neotoma_selected_count_evidence(
        repository, tracked_by_path, inventory["owners"]
    )
    source_accounting_entries, source_accounting_evidence = (
        validated_current_source_accounting_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    sweden_semantic_entries, sweden_semantic_evidence = (
        validated_sweden_country_capture(
            repository, tracked_by_path, inventory["owners"]
        )
    )
    all_capture_entries = (
        (
            (
                (
                    capture_entries
                    + parameter_entries
                    + chronology_entries
                    + nordic_entries
                    + linux_entries
                    + author_entries
                    + author_native_entries
                )
                + constrained_entries
                + optimizer_entries
            )
            + performance_entries
            + nfi_entries
            + controlled_entries
            + radius_entries
        )
        + grid_entries
        + svar_entries
        + solsoe_selection_entries
        + solsoe_pollen_entries
        + rootsi_entries
        + swedish_entries
        + hyde_entries
        + love_objective_entries
        + neotoma_lake_entries
        + svar_census_entries
        + hyde_grid_entries
        + amsoldingersee_entries
        + swedish_direct_entries
        + empd2_nfi_entries
        + source_accounting_entries
        + sweden_semantic_entries
    )
    for entry in all_capture_entries:
        name = "docs/report/" + entry.path
        capture = _regular_confined_file(repository, name, "scientific capture")
        if capture.read_bytes() != _head_blob(repository, name):
            raise ReportRebuildError("scientific capture differs from Git candidate")
    selected.extend(all_capture_entries)
    try:
        if repository_identity(repository, required=True) != expected_repository:
            raise ReportRebuildError("maintained source Git candidate changed")
    except ReproducibleReportError as error:
        raise ReportRebuildError("maintained source Git candidate changed") from error
    if len(selected) != sum(count for count, _ in MAINTAINED_ROLE_PATHS.values()) + len(
        all_capture_entries
    ):
        raise ReportRebuildError("maintained source coverage is incomplete")
    evidence: JsonObject = {
        "schema_version": "maintained-report-source-evidence.v1",
        "repository": expected_repository,
        "ownership_inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "roles": {
            role: {
                "path_count": len(role_paths[role]),
                "paths_sha256": canonical_json_sha256(sorted(role_paths[role])),
                "owners": role_owners[role],
            }
            for role in MAINTAINED_ROLE_PATHS
        },
        "inventory": inventory_json(sorted(selected, key=lambda entry: entry.path)),
    }
    if capture_entries:
        evidence["retained_scientific_captures"] = capture_evidence
    if parameter_entries:
        evidence["retained_parameter_transfer_captures"] = parameter_evidence
    if chronology_entries:
        evidence["retained_source_chronology_captures"] = chronology_evidence
    if nordic_entries:
        evidence["retained_nordic_static_basin_captures"] = nordic_evidence
    if linux_entries:
        evidence["retained_linux_r_reference_capture"] = linux_evidence
    if slu_guide_evidence:
        evidence["current_slu_guide_partial_evidence"] = slu_guide_evidence
    if author_entries:
        evidence["retained_author_site_evaluation_captures"] = author_evidence
    if author_native_entries:
        evidence["retained_author_native_reference_capture"] = author_native_evidence
    if constrained_entries:
        evidence["retained_constrained_author_capture"] = constrained_evidence
    if optimizer_entries:
        evidence["retained_author_optimizer_diagnostic_capture"] = optimizer_evidence
    if performance_entries:
        evidence["retained_representative_performance_capture"] = performance_evidence
    if nfi_entries:
        evidence["retained_nfi_measurement_capture"] = nfi_evidence
    if controlled_entries:
        evidence["retained_controlled_lra_comparison_capture"] = controlled_evidence
    if radius_entries:
        evidence["retained_author_radius_capture"] = radius_evidence
    if grid_evidence:
        evidence["retained_grid_source_capture"] = grid_evidence

    if svar_evidence:
        evidence["retained_svar_source_capture"] = svar_evidence

    if solsoe_selection_evidence:
        evidence["retained_solsoe_selection_source_capture"] = solsoe_selection_evidence

    if solsoe_pollen_evidence:
        evidence["retained_solsoe_pollen_source_capture"] = solsoe_pollen_evidence

    if rootsi_evidence:
        evidence["retained_rootsi_source_capture"] = rootsi_evidence

    if swedish_evidence:
        evidence["current_swedish_cohort_partial_evidence"] = swedish_evidence

    if hyde_evidence:
        evidence["current_hyde_country_partial_evidence"] = hyde_evidence

    if love_objective_evidence:
        evidence["retained_love_objective_source_capture"] = love_objective_evidence
    if neotoma_lake_evidence:
        evidence["retained_neotoma_lake_source_capture"] = neotoma_lake_evidence
    if svar_census_evidence:
        evidence["retained_svar_census_source_capture"] = svar_census_evidence
    if hyde_grid_evidence:
        evidence["retained_hyde_grid_source_capture"] = hyde_grid_evidence
    if openland_evidence:
        evidence["current_openland_partial_evidence"] = openland_evidence
    if amsoldingersee_evidence:
        evidence["retained_amsoldingersee_source_capture"] = amsoldingersee_evidence
    if neotoma_publication_evidence:
        evidence["current_neotoma_publication_partial_evidence"] = (
            neotoma_publication_evidence
        )
    if swedish_direct_evidence:
        evidence["retained_swedish_direct_source_capture"] = swedish_direct_evidence
    if empd2_nfi_evidence:
        evidence["retained_empd2_nfi_source_capture"] = empd2_nfi_evidence
    if adna_current_export_evidence is not None:
        evidence["retained_adna_current_export_evidence"] = adna_current_export_evidence
    if adna_current_domain_evidence is not None:
        evidence["retained_adna_current_domain_evidence"] = adna_current_domain_evidence
    if neotoma_count_evidence:
        evidence["current_neotoma_selected_count_partial_evidence"] = (
            neotoma_count_evidence
        )
    if source_accounting_entries:
        evidence["retained_current_source_accounting"] = source_accounting_evidence
    if sweden_semantic_evidence is not None:
        evidence["retained_sweden_current_semantic_replay"] = sweden_semantic_evidence
    return tuple(sorted(selected, key=lambda entry: entry.path)), evidence

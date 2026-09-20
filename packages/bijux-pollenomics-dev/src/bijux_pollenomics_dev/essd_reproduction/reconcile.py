"""Reconcile publication claims without promoting a candidate implementation."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import tomllib
from typing import cast
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

JsonObject = dict[str, object]

_COMPARISON = Path("artifacts/v2/engine/publication-check-004/comparison/report.json")
_DESIGN = Path("artifacts/v2/engine/multisite-audit/IMPLEMENTATION-DESIGN.md")
_RIGHTS = Path("artifacts/v2/engine/publication-license-audit/DISPOSITION.md")
_TAXONOMY = Path("data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv")
_PUBLISHED = Path("data/landclim/raw/landclim_ii_reveals_results.zip")

_MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
_MAX_MEMBER_COUNT = 512
_MAX_MEMBER_BYTES = 2 * 1024 * 1024
_MAX_EXPANDED_BYTES = 32 * 1024 * 1024
_MAX_COMPRESSION_RATIO = 100.0
_ALLOWED_COMPRESSION = {ZIP_STORED, ZIP_DEFLATED}
_EXPECTED_EXAMPLE_SITES = {
    "512": (
        "BROADOWN",
        "CUTHILL2",
        "HANGINGS",
        "HARESDOWN",
        "LOBBSBOG",
        "WHH05",
        "WHH11",
        "WINDMILL",
        "WINNEYS",
    ),
    "562": (
        "BECKHAM",
        "COMERSLA",
        "EXEBRID",
        "GOURTEMIRES",
        "LARKBARR",
        "LONGBREACH",
        "MOLECHAM",
        "NTWITCHEN",
    ),
}


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _object(content: bytes, source: str) -> JsonObject:
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {source}")
    return cast(JsonObject, value)


def _read(repository: Path, relative: Path) -> bytes:
    root = repository.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Required repository evidence is unavailable: {relative}")
    return path.read_bytes()


def _evidence_receipt(repository: Path, relative: Path) -> JsonObject:
    content = _read(repository, relative)
    return {
        "path": relative.as_posix(),
        "byte_count": len(content),
        "sha256": _sha256(content),
    }


def _member_name(names: list[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one archive member ending {suffix!r}, got {matches}"
        )
    return matches[0]


def _validate_member_names(names: list[str]) -> str:
    if len(names) != len(set(names)):
        raise ValueError("Candidate archive has duplicate member names")
    unsafe = []
    roots = set()
    for name in names:
        trimmed = name.removesuffix("/")
        path = PurePosixPath(trimmed)
        normalized = "/".join(path.parts) + ("/" if name.endswith("/") else "")
        if (
            not trimmed
            or "\\" in name
            or "\x00" in name
            or path.is_absolute()
            or any(part in {"", ".", ".."} for part in path.parts)
            or normalized != name
        ):
            unsafe.append(name)
            continue
        roots.add(path.parts[0])
    if unsafe:
        raise ValueError(f"Candidate archive has unsafe member names: {unsafe}")
    if len(roots) != 1:
        raise ValueError(
            f"Candidate archive must have one relative root: {sorted(roots)}"
        )
    return next(iter(roots))


def _validate_archive(archive_path: Path) -> tuple[JsonObject, dict[str, bytes]]:
    archive_size = archive_path.stat().st_size
    if archive_size > _MAX_ARCHIVE_BYTES:
        raise ValueError(
            "Candidate archive exceeds archive byte limit: "
            f"{archive_size} > {_MAX_ARCHIVE_BYTES}"
        )
    archive_bytes = archive_path.read_bytes()
    if len(archive_bytes) > _MAX_ARCHIVE_BYTES:
        raise ValueError(
            "Candidate archive exceeds archive byte limit after read: "
            f"{len(archive_bytes)} > {_MAX_ARCHIVE_BYTES}"
        )
    with ZipFile(io.BytesIO(archive_bytes)) as archive:
        infos = archive.infolist()
        if len(infos) > _MAX_MEMBER_COUNT:
            raise ValueError(
                "Candidate archive exceeds member count limit: "
                f"{len(infos)} > {_MAX_MEMBER_COUNT}"
            )
        _validate_member_names([info.filename for info in infos])
        rejected_members = []
        total_expanded_bytes = 0
        maximum_member_bytes = 0
        maximum_compression_ratio = 0.0
        for info in infos:
            unix_mode = info.external_attr >> 16
            file_type = stat.S_IFMT(unix_mode)
            reasons = []
            if info.is_dir() or file_type != stat.S_IFREG:
                reasons.append("not_regular_file")
            if info.flag_bits & 0x1:
                reasons.append("encrypted")
            if info.compress_type not in _ALLOWED_COMPRESSION:
                reasons.append(f"unsupported_compression_{info.compress_type}")
            if reasons:
                rejected_members.append(
                    {"name": info.filename, "reasons": sorted(reasons)}
                )
                continue
            if info.file_size > _MAX_MEMBER_BYTES:
                raise ValueError(
                    "Candidate archive member exceeds byte limit: "
                    f"{info.filename} has {info.file_size} > {_MAX_MEMBER_BYTES}"
                )
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > _MAX_COMPRESSION_RATIO:
                raise ValueError(
                    "Candidate archive member exceeds compression ratio limit: "
                    f"{info.filename} has {ratio:.3f} > {_MAX_COMPRESSION_RATIO:.3f}"
                )
            total_expanded_bytes += info.file_size
            maximum_member_bytes = max(maximum_member_bytes, info.file_size)
            maximum_compression_ratio = max(maximum_compression_ratio, ratio)
        if rejected_members:
            raise ValueError(
                f"Candidate archive has rejected member envelope: {rejected_members}"
            )
        if total_expanded_bytes > _MAX_EXPANDED_BYTES:
            raise ValueError(
                "Candidate archive exceeds total expanded byte limit: "
                f"{total_expanded_bytes} > {_MAX_EXPANDED_BYTES}"
            )
        names = [info.filename for info in infos]
        checksum_name = _member_name(names, "/SHA256SUMS")
        members = {name: archive.read(name) for name in names}
    prefix = checksum_name.removesuffix("SHA256SUMS")
    checksums: dict[str, str] = {}
    for line in members[checksum_name].decode().splitlines():
        expected, separator, relative = line.partition("  ")
        if not separator or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError(f"Malformed SHA256SUMS line: {line!r}")
        relative_path = PurePosixPath(relative)
        if (
            not relative
            or "\\" in relative
            or relative_path.is_absolute()
            or any(part in {"", ".", ".."} for part in relative_path.parts)
            or "/".join(relative_path.parts) != relative
        ):
            raise ValueError(f"Unsafe SHA256SUMS path: {relative!r}")
        if relative in checksums:
            raise ValueError(f"Duplicate SHA256SUMS path: {relative}")
        checksums[relative] = expected
    listed_members = {prefix + relative for relative in checksums}
    expected_members = set(names) - {checksum_name}
    if listed_members != expected_members:
        raise ValueError(
            "Candidate archive manifest does not cover archive exactly: "
            f"unlisted={sorted(expected_members - listed_members)}, "
            f"missing={sorted(listed_members - expected_members)}"
        )
    failures = []
    for relative, expected in checksums.items():
        name = prefix + relative
        content = members.get(name)
        if content is None or _sha256(content) != expected:
            failures.append(relative)
    if failures:
        raise ValueError(f"Candidate archive checksum failure: {failures}")
    required_suffixes = (
        "/docs/SCIENTIFIC_AUDIT.md",
        "/docs/INTEGRATION.md",
        "/verification/delivery-scope.json",
        "/verification/environment.json",
        "/pyproject.toml",
        "/tests/test_science.py",
        "/tests/test_products.py",
    )
    required = {
        suffix.removeprefix("/"): _member_name(names, suffix)
        for suffix in required_suffixes
    }
    receipt: JsonObject = {
        "schema_version": "essd-archive-receipt.v1",
        "archive_name": archive_path.name,
        "byte_count": len(archive_bytes),
        "sha256": _sha256(archive_bytes),
        "file_member_count": len(names),
        "member_names_sha256": _sha256("\n".join(sorted(names)).encode()),
        "internal_checksum_manifest": checksum_name,
        "internal_checksum_entry_count": len(checksums),
        "internal_checksums_match": True,
        "archive_envelope": {
            "allowed_compression_methods": sorted(_ALLOWED_COMPRESSION),
            "archive_byte_limit": _MAX_ARCHIVE_BYTES,
            "expanded_byte_limit": _MAX_EXPANDED_BYTES,
            "member_byte_limit": _MAX_MEMBER_BYTES,
            "member_count_limit": _MAX_MEMBER_COUNT,
            "compression_ratio_limit": _MAX_COMPRESSION_RATIO,
            "observed_expanded_bytes": total_expanded_bytes,
            "observed_maximum_member_bytes": maximum_member_bytes,
            "observed_maximum_compression_ratio": maximum_compression_ratio,
            "regular_file_members_only": True,
            "encrypted_members_allowed": False,
        },
        "required_members": required,
        "intake_disposition": "read_only_candidate_not_adopted_or_shipped",
    }
    return receipt, members


def _decorator_name(node: ast.expr) -> str:
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    if isinstance(node, ast.Attribute):
        parent = _decorator_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _test_inventory(members: dict[str, bytes], receipt: JsonObject) -> JsonObject:
    required = cast(dict[str, str], receipt["required_members"])
    prefix = required["tests/test_science.py"].removesuffix("tests/test_science.py")
    tests: list[JsonObject] = []
    for name in sorted(members):
        if not name.startswith(prefix + "tests/test_") or not name.endswith(".py"):
            continue
        tree = ast.parse(members[name], filename=name)
        for node in tree.body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.name.startswith("test_"):
                decorators = [
                    decorator
                    for decorator in (
                        _decorator_name(item) for item in node.decorator_list
                    )
                    if decorator
                ]
                tests.append(
                    {
                        "module": name.removeprefix(prefix),
                        "name": node.name,
                        "decorators": decorators,
                    }
                )
    delivery = _object(
        members[required["verification/delivery-scope.json"]],
        "verification/delivery-scope.json",
    )
    environment = _object(
        members[required["verification/environment.json"]],
        "verification/environment.json",
    )
    project = tomllib.loads(members[required["pyproject.toml"]].decode())
    optional = cast(dict[str, list[str]], project["project"]["optional-dependencies"])
    packages = cast(dict[str, str], environment["packages"])
    offline = cast(JsonObject, delivery["offline_tests"])
    actual_r = next(
        item for item in tests if item["name"] == "test_actual_R_parity_optional"
    )
    return {
        "schema_version": "essd-candidate-test-inventory.v1",
        "candidate_archive_sha256": receipt["sha256"],
        "test_function_count": len(tests),
        "recorded_test_case_outcome": {
            "passed": offline["passed"],
            "skipped": offline["skipped"],
            "source": "verification/delivery-scope.json",
        },
        "actual_r_parity": {
            "executed": delivery["actual_R_parity_executed"],
            "test": actual_r,
            "required_environment": "Rscript, zipfR, LANDCLIM_REFERENCE_R",
            "recorded_rscript_path": environment["Rscript_path"],
            "acceptance_effect": "skip_or_synthetic_parity_is_not_actual_R_parity",
        },
        "dependency_evidence": {
            "declared_test_requirements": optional["test"],
            "recorded_pytest_version": packages["pytest"],
            "declared_recorded_mismatch": True,
            "note": "The candidate declares pytest>=8,<9 but records pytest 9.0.2.",
        },
        "selective_port_candidates": [
            "test_table1_inventory",
            "test_lake_igamma_is_lower_unregularized",
            "test_single_variance_literal_loop_oracle",
            "test_multi_bootstrap_literal_pooling",
            "test_multi_SE_ignores_RPP_variance_in_reference_branch",
            "test_empty_window_not_measured_absence",
            "test_published_25_windows",
            "test_all_zero_closure_is_flagged_not_absence",
            "test_parity_must_compare_missing_masks",
            "test_audit_never_confuses_archive_with_all_paper",
        ],
        "tests": tests,
    }


def _published_pft_evidence(repository: Path) -> JsonObject:
    taxonomy_content = _read(repository, _TAXONOMY).decode("utf-8-sig")
    taxonomy_rows = list(csv.DictReader(io.StringIO(taxonomy_content)))
    taxonomy_pfts = sorted({row["PFT"] for row in taxonomy_rows if row["PFT"]})
    lct_codes = set()
    for row in taxonomy_rows:
        heading = row["Land-cover types (LCTs)"]
        if not heading:
            continue
        match = re.search(r"\(([^)]+)\)$", heading)
        if match is None:
            raise ValueError(f"Land-cover heading has no code: {heading}")
        lct_codes.add(match.group(1))
    with ZipFile(io.BytesIO(_read(repository, _PUBLISHED))) as archive:
        csv_names = sorted(name for name in archive.namelist() if name.endswith(".csv"))
        header_sets = {
            tuple(next(csv.reader(io.StringIO(archive.read(name).decode("utf-8-sig")))))
            for name in csv_names
        }
    if len(header_sets) != 1:
        raise ValueError("Published result CSV headers do not agree")
    header = next(iter(header_sets))
    first_group = min(header.index(code) for code in taxonomy_pfts if code in header)
    grouped_headers = list(header[first_group:])
    if len(header[:first_group]) != 34:
        raise ValueError(
            "Published result header does not contain three identity columns and 31 taxa"
        )
    if len(grouped_headers) != len(set(grouped_headers)):
        raise ValueError("Published result grouped headers contain duplicates")
    allowed_unmatched_pfts = {"ISTS"}
    allowed_grouped_headers = set(taxonomy_pfts) | allowed_unmatched_pfts | lct_codes
    unknown_grouped_headers = sorted(set(grouped_headers) - allowed_grouped_headers)
    if unknown_grouped_headers:
        raise ValueError(
            "Published result has unknown trailing grouped headers: "
            f"{unknown_grouped_headers}"
        )
    missing_grouped_headers = sorted(allowed_grouped_headers - set(grouped_headers))
    if missing_grouped_headers:
        raise ValueError(
            "Published result is missing required grouped headers: "
            f"{missing_grouped_headers}"
        )
    output_pfts = [
        code
        for code in grouped_headers
        if code in set(taxonomy_pfts) | allowed_unmatched_pfts
    ]
    return {
        "taxonomy_pft_count": len(taxonomy_pfts),
        "taxonomy_pfts": taxonomy_pfts,
        "published_output_pft_header_count": len(output_pfts),
        "published_output_pft_headers": output_pfts,
        "published_output_lct_headers": sorted(lct_codes),
        "published_csv_member_count": len(csv_names),
        "headers_consistent_across_members": True,
        "unmatched_output_pft_headers": sorted(set(output_pfts) - set(taxonomy_pfts)),
    }


def _repository_evidence(repository: Path) -> JsonObject:
    comparison = _object(_read(repository, _COMPARISON), _COMPARISON.as_posix())
    design = _read(repository, _DESIGN).decode()
    rights = _read(repository, _RIGHTS).decode()
    raw_grids = comparison.get("grids")
    if not isinstance(raw_grids, list) or len(raw_grids) != 2:
        raise ValueError("Host comparison must contain exactly two grid objects")
    grids = cast(list[JsonObject], raw_grids)
    if comparison.get("profile") != "landclimii-2016-release-source-v1":
        raise ValueError("Host comparison profile identity is not the author example")
    if (
        comparison.get("coverage")
        != "two_author_example_grids_only_not_full_1128_record_study"
    ):
        raise ValueError("Host comparison no longer declares its bounded coverage")
    grids_by_id = {str(grid.get("grid_id")): grid for grid in grids}
    if len(grids_by_id) != 2 or set(grids_by_id) != set(_EXPECTED_EXAMPLE_SITES):
        raise ValueError(
            "Host comparison does not contain the two expected example grids"
        )
    for grid_id, expected_sites in _EXPECTED_EXAMPLE_SITES.items():
        grid = grids_by_id[grid_id]
        if grid.get("sites") != len(expected_sites):
            raise ValueError(f"Host comparison grid {grid_id} has wrong site count")
        if grid.get("bins") != 25 or grid.get("taxa") != 31:
            raise ValueError(f"Host comparison grid {grid_id} has wrong dimensions")
        if grid.get("passed") is not True:
            raise ValueError(f"Host comparison grid {grid_id} did not pass")
        checks = grid.get("checks")
        if not isinstance(checks, dict) or checks.get("site_counts_equal") is not True:
            raise ValueError(f"Host comparison grid {grid_id} site counts differ")
        for check_name in ("regional_cover", "regional_se"):
            check = checks.get(check_name)
            if not isinstance(check, dict) or check.get("passed") is not True:
                raise ValueError(
                    f"Host comparison grid {grid_id} {check_name} did not pass"
                )
        site_checks = checks.get("sites")
        if not isinstance(site_checks, list):
            raise ValueError(f"Host comparison grid {grid_id} has no site checks")
        site_ids = tuple(
            str(site.get("site_id")) for site in site_checks if isinstance(site, dict)
        )
        if site_ids != expected_sites:
            raise ValueError(f"Host comparison grid {grid_id} site identity differs")
        for site in site_checks:
            site_object = cast(JsonObject, site)
            for check_name in ("cover", "se"):
                check = site_object.get(check_name)
                if not isinstance(check, dict) or check.get("passed") is not True:
                    raise ValueError(
                        "Host comparison site check did not pass: "
                        f"{grid_id}/{site_object.get('site_id')}/{check_name}"
                    )
    if "reports 1128 pollen records, 31 taxa, 12 PFTs" not in design:
        raise ValueError("ESSD paper scope is absent from the implementation design")
    if "host redistribution are **not cleared**" not in rights:
        raise ValueError("Rights disposition no longer preserves the release blocker")
    return {
        "comparison": comparison,
        "example_site_count": sum(
            len(sites) for sites in _EXPECTED_EXAMPLE_SITES.values()
        ),
        "pft": _published_pft_evidence(repository),
        "evidence_receipts": [
            _evidence_receipt(repository, path)
            for path in (_COMPARISON, _DESIGN, _RIGHTS, _TAXONOMY, _PUBLISHED)
        ],
        "rights_status": {
            "published_product_rights": "not_evaluated_by_pinned_local_disposition",
            "author_example_source_rights": "no_clear_redistribution_grant",
            "original_input_rights": "not_evaluated_without_full_input_closure",
            "gpl_derived_host_integration": "compatibility_and_distribution_unresolved",
            "overall_host_release": "not_cleared",
        },
    }


def _pft_discrepancy(
    members: dict[str, bytes], archive: JsonObject, repository: JsonObject
) -> JsonObject:
    required = cast(dict[str, str], archive["required_members"])
    audit = members[required["docs/SCIENTIFIC_AUDIT.md"]].decode()
    if "paper/Table 1 uses 12 PFTs" not in audit:
        raise ValueError(
            "Candidate audit does not preserve the paper's 12-PFT statement"
        )
    if "PANGAEA description states 11" not in audit:
        raise ValueError(
            "Candidate audit does not preserve the description's 11-PFT statement"
        )
    pft = cast(JsonObject, repository["pft"])
    if pft["taxonomy_pft_count"] != 12:
        raise ValueError("Repository taxonomy table no longer has 12 PFT definitions")
    if pft["published_output_pft_header_count"] != 13:
        raise ValueError("Repository published outputs no longer have 13 PFT headers")
    if pft["unmatched_output_pft_headers"] != ["ISTS"]:
        raise ValueError(
            "The unmatched published output header is no longer exactly ISTS"
        )
    return {
        "schema_version": "essd-pft-discrepancy.v1",
        "resolution_status": "unresolved_requires_author_and_qualified_taxonomy_review",
        "scientific_admission_allowed": False,
        "observations": [
            {
                "evidence_role": "paper_table_1",
                "pft_count": 12,
                "source": "candidate:docs/SCIENTIFIC_AUDIT.md",
                "source_status": "candidate_prose_not_pinned_primary_source",
            },
            {
                "evidence_role": "pangaea_description",
                "pft_count": 11,
                "source": "candidate:docs/SCIENTIFIC_AUDIT.md",
                "source_status": "candidate_prose_not_pinned_primary_source",
            },
            {
                "evidence_role": "repository_parameter_table",
                "pft_count": pft["taxonomy_pft_count"],
                "pft_headers": pft["taxonomy_pfts"],
                "source": _TAXONOMY.as_posix(),
            },
            {
                "evidence_role": "published_result_headers",
                "pft_count": pft["published_output_pft_header_count"],
                "pft_headers": pft["published_output_pft_headers"],
                "unmatched_headers": ["ISTS"],
                "source": _PUBLISHED.as_posix(),
            },
        ],
        "required_disposition": {
            "ISTS": "retain_unmatched; do_not_drop_or_map_without_review",
            "minimum_evidence": [
                "author_or_deposit clarification",
                "qualified taxonomy/PFT reviewer identity, decision date, and rationale",
                "row-level mapping to the parameter table and released output schema",
            ],
        },
    }


def _availability_csv(repository: JsonObject) -> bytes:
    comparison = cast(JsonObject, repository["comparison"])
    rows = [
        (
            "candidate_archive",
            "software_candidate",
            "present",
            "1 archive",
            "intake_only",
            "Archive bytes and internal checksums verified",
        ),
        (
            "author_example_sequences",
            "source_profile_input",
            "present",
            f"{repository['example_site_count']} sequences / 2 grids",
            "bounded_replay_only",
            "Host comparison grids 512 and 562",
        ),
        (
            "published_reconstructions",
            "processed_model_output",
            "present",
            "25 windows",
            "comparison_target_not_raw_truth",
            "PANGAEA reconstructed means and standard errors",
        ),
        (
            "original_1128_pollen_records",
            "primary_pollen_input",
            "missing",
            "0 present in declared closure / 1128 study records",
            "blocks_whole_paper_reproduction",
            "No original full-study raw record closure; not an exhaustive repository-wide absence proof",
        ),
        (
            "selected_calibrated_ages",
            "chronology_input",
            "missing",
            "0 present in declared closure / 1128-record crosswalk",
            "blocks_whole_paper_reproduction",
            "Historical selected ages and age-model choices are absent from the declared closure",
        ),
        (
            "full_taxon_harmonization_ledger",
            "taxonomy_input",
            "missing",
            "paper-wide ledger unavailable",
            "blocks_whole_paper_reproduction",
            "Example taxonomy does not establish full historical selection",
        ),
        (
            "historical_resampling_state",
            "uncertainty_input",
            "missing",
            "seed/draws unavailable",
            "blocks_stochastic_identity",
            "Shared-index algorithm tests do not recover the publication run",
        ),
        (
            "actual_R_parity",
            "algorithm_parity",
            "missing",
            "not executed",
            "blocks_R_certification",
            "Candidate recorded one skipped integration test",
        ),
        (
            "independent_measured_vegetation",
            "validation_target",
            "missing",
            "not evaluated",
            "blocks_ecological_accuracy",
            str(comparison["independent_measured_vegetation_accuracy"]),
        ),
        (
            "original_grouped_uncertainty",
            "PFT_LCT_uncertainty",
            "missing",
            "covariance/workflow unavailable",
            "blocks_grouped_SE_reproduction",
            "Marginal taxon SE cannot recover group covariance",
        ),
        (
            "original_cartographic_inputs",
            "figure_input",
            "missing",
            "GIS/projection layers unavailable",
            "blocks_original_figure_reproduction",
            "Candidate scope record says original figures were not regenerated",
        ),
        (
            "published_product_rights",
            "distribution_authority",
            "not_evaluated",
            "component-specific grant not pinned here",
            "requires_component_receipt",
            "Do not infer published-product rights from author-source or host-integration status",
        ),
        (
            "author_example_source_rights",
            "distribution_authority",
            "unresolved",
            "no clear author-source grant",
            "blocks_author_source_redistribution",
            str(
                cast(JsonObject, repository["rights_status"])[
                    "author_example_source_rights"
                ]
            ),
        ),
        (
            "original_input_rights",
            "distribution_authority",
            "not_evaluated",
            "full input closure unavailable",
            "blocks_original_input_redistribution",
            str(cast(JsonObject, repository["rights_status"])["original_input_rights"]),
        ),
        (
            "gpl_derived_host_integration",
            "distribution_authority",
            "unresolved",
            "compatibility and distribution unresolved",
            "blocks_host_release",
            str(
                cast(JsonObject, repository["rights_status"])[
                    "gpl_derived_host_integration"
                ]
            ),
        ),
    ]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        (
            "input_id",
            "evidence_role",
            "availability",
            "observed_quantity",
            "acceptance_effect",
            "evidence_note",
        )
    )
    writer.writerows(rows)
    return stream.getvalue().encode()


def _profile_crosswalk(
    members: dict[str, bytes], archive: JsonObject, repository: JsonObject
) -> JsonObject:
    required = cast(dict[str, str], archive["required_members"])
    delivery = _object(
        members[required["verification/delivery-scope.json"]],
        "verification/delivery-scope.json",
    )
    comparison = cast(JsonObject, repository["comparison"])
    return {
        "schema_version": "essd-publication-profile-crosswalk.v1",
        "whole_paper_reproduction_certified": False,
        "profiles": [
            {
                "profile_id": "essd-2022-paper-method",
                "evidence_role": "publication_method_and_declared_scope",
                "records": 1128,
                "taxa": 31,
                "pfts": 12,
                "source_status": "candidate_prose_not_pinned_primary_source",
                "time_support": "coring-year present,100,350,700,1200,...,11700 BP",
                "status": "blocked_missing_original_inputs",
            },
            {
                "profile_id": "pangaea-937075-published-products",
                "evidence_role": "processed_reconstruction_comparison_target",
                "description_pfts": 11,
                "source_status": "candidate_prose_not_pinned_primary_source",
                "observed_output_pft_headers": 13,
                "time_windows": 25,
                "status": "available_not_primary_pollen_or_independent_vegetation",
            },
            {
                "profile_id": str(comparison["profile"]),
                "evidence_role": "author_example_source_replay",
                "records": repository["example_site_count"],
                "grids": ["512", "562"],
                "taxa": 31,
                "time_windows": 25,
                "time_support": "-65,100,350,750,1250,...,11750 BP source bins",
                "status": "numerical_parity_passed_for_bounded_example_only",
                "coverage": comparison["coverage"],
            },
            {
                "profile_id": "bijux-landclim-reproduce-0.1.0-candidate",
                "evidence_role": "unadopted_research_candidate",
                "offline_tests_passed": cast(JsonObject, delivery["offline_tests"])[
                    "passed"
                ],
                "offline_tests_skipped": cast(JsonObject, delivery["offline_tests"])[
                    "skipped"
                ],
                "actual_R_parity_executed": delivery["actual_R_parity_executed"],
                "original_1128_raw_records_collected": delivery[
                    "original_1128_raw_records_collected"
                ],
                "status": "intake_only_not_host_implementation",
            },
            {
                "profile_id": "host-release-publication-profile",
                "evidence_role": "potential_shipped_profile",
                "status": "withheld_rights_and_scientific_acceptance_unresolved",
                "redistribution_cleared": False,
            },
        ],
        "non_equivalences": [
            "paper time windows are not the author example bins",
            "17 example sequences are not the original 1128-record study",
            "published reconstructions are not raw pollen inputs",
            "published reconstructions are not independent measured vegetation",
            "offline or synthetic tests are not actual R parity",
            "source replay parity is not ecological accuracy or scientific approval",
        ],
    }


def _scope_report(
    archive: JsonObject,
    tests: JsonObject,
    profiles: JsonObject,
    pfts: JsonObject,
    repository: JsonObject,
) -> bytes:
    comparison = cast(JsonObject, repository["comparison"])
    outcome = cast(JsonObject, tests["recorded_test_case_outcome"])
    lines = [
        "# ESSD reproduction scientific-scope reconciliation",
        "",
        "## Determination",
        "",
        "Whole-paper reproduction is **not certified**. The supplied package is a read-only research candidate, not an adopted or shipped host implementation.",
        "",
        "## Verified local evidence",
        "",
        f"- Candidate archive SHA-256: `{archive['sha256']}`; all {archive['internal_checksum_entry_count']} listed internal member hashes match.",
        f"- Candidate evidence records {outcome['passed']} offline tests passing and {outcome['skipped']} skipped; actual-R parity was not executed.",
        f"- Host profile `{comparison['profile']}` passes numerical comparison for 17 sequences in grids 512 and 562 only.",
        f"- Host coverage is `{comparison['coverage']}` and independent measured vegetation accuracy is `{comparison['independent_measured_vegetation_accuracy']}`.",
        "",
        "## PFT discrepancy",
        "",
        "Candidate prose records **12 PFTs** for the paper/Table 1 and **11** for the PANGAEA description; those primary-source bytes are not pinned in this reconciliation closure. The archived result tables expose **13 PFT-position headers**. `ISTS` has no matching definition in the repository parameter table. It is retained as unmatched; it is not dropped, guessed, or admitted. Resolution requires pinned author/deposit evidence and qualified row-level review.",
        "",
        "## Missing closure",
        "",
        "- No original 1,128 pollen records, selected calibrated ages, historical preparation recipe, or full taxon crosswalk are present in the declared reconciliation closure; this is not an exhaustive repository-wide absence proof.",
        "- Historical resampling draws, original grouped PFT/LCT uncertainty workflow, and original GIS inputs are unavailable.",
        "- Actual publication-specific R parity has not run; a skipped test or synthetic oracle is not parity evidence.",
        "- Published reconstruction products are comparison targets, not raw pollen observations or independent measured vegetation truth.",
        "- Rights remain component-specific: published-product rights are not evaluated by the pinned local disposition; author-example source redistribution has no clear grant; original-input rights lack a full input closure; and GPL-derived host integration remains unresolved. Overall host release is not cleared.",
        "",
        "## Profile separation",
        "",
        "Paper windows (present/100/350/700/1200 … 11700 BP), author example bins (-65/100/350/750/1250 … 11750 BP), and TW lookup labels are distinct profiles. The candidate cannot relabel them as equivalent. Source replay, algorithm parity, whole-paper reproduction, ecological accuracy, rights clearance, and scientific approval remain separate gates.",
        "",
        "## Acceptance posture",
        "",
        f"PFT resolution: `{pfts['resolution_status']}`. Whole-paper certification: `{profiles['whole_paper_reproduction_certified']}`. The strongest truthful state is bounded two-grid source parity plus a checksum-verified candidate intake.",
    ]
    return ("\n".join(lines) + "\n").encode()


def build_reconciliation(archive_path: Path, repository: Path) -> dict[str, object]:
    """Build six deterministic outputs from the candidate and host evidence."""
    archive, members = _validate_archive(archive_path)
    repository_evidence = _repository_evidence(repository)
    tests = _test_inventory(members, archive)
    pfts = _pft_discrepancy(members, archive, repository_evidence)
    profiles = _profile_crosswalk(members, archive, repository_evidence)
    archive["repository_evidence"] = repository_evidence["evidence_receipts"]
    outputs: dict[str, object] = {
        "archive-receipt.json": archive,
        "candidate-test-inventory.json": tests,
        "input-availability.csv": _availability_csv(repository_evidence),
        "publication-profile-crosswalk.json": profiles,
        "pft-discrepancy.json": pfts,
    }
    outputs["scientific-scope-report.md"] = _scope_report(
        archive, tests, profiles, pfts, repository_evidence
    )
    return outputs


def publish_reconciliation(
    archive_path: Path, repository: Path, output: Path
) -> dict[str, JsonObject]:
    """Atomically publish the six products to a new directory."""
    products = build_reconciliation(archive_path, repository)
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to replace existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for name, value in products.items():
            content = value if isinstance(value, bytes) else _json_bytes(value)
            (temporary / name).write_bytes(content)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {
        name: cast(JsonObject, value)
        for name, value in products.items()
        if isinstance(value, dict)
    }

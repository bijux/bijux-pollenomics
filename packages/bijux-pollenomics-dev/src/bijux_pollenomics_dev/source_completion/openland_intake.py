"""Reconcile a private OpenLand archive with its pinned primary-source tree."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, cast
from zipfile import ZipFile, ZipInfo

from bijux_pollenomics.collection.sources.open_land.authority import (
    ADMITTED_CSV_MEMBERS,
    ARCHIVE_EXPANDED_BYTES,
    ARCHIVE_MEMBER_COUNT,
    ARCHIVE_SHA256,
    SOURCE_CITATION_DOI,
    SOURCE_COMMIT,
    SOURCE_DATA_LICENSE,
    SOURCE_REPOSITORY,
)

TREE_URL = (
    "https://api.github.com/repos/BehnazP/SpatioCompo_entireHolocene_EU/"
    f"git/trees/{SOURCE_COMMIT}?recursive=1"
)
LANDCLIM_RECEIPT = Path("data/landclim/raw/landclim_sources.json")
AUTHORITY = Path(
    "packages/bijux-pollenomics/src/bijux_pollenomics/"
    "collection/sources/open_land/authority.py"
)
PRODUCER = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "source_completion/openland_intake.py"
)
FIELDS = (
    "member_path",
    "member_type",
    "uncompressed_bytes",
    "compressed_bytes",
    "zip_crc32",
    "member_sha256",
    "upstream_path",
    "upstream_git_blob_sha1",
    "upstream_identity",
    "semantic_role",
    "rights_basis",
    "redistribution_posture",
    "source_route",
    "independent_vegetation_benchmark",
    "decision",
    "reason_code",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(data)}\0".encode() + data, usedforsecurity=False
    ).hexdigest()


def validate_upstream_tree(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Require an exact, complete source tree at the reviewed upstream commit."""
    if payload.get("sha") != SOURCE_COMMIT or payload.get("truncated") is not False:
        raise ValueError("OpenLand upstream tree identity or completeness changed")
    entries = payload.get("tree")
    if not isinstance(entries, list) or len(entries) != 29:
        raise ValueError("OpenLand upstream tree entry count changed")
    blobs = {entry["path"]: entry for entry in entries if entry.get("type") == "blob"}
    expected = {
        "README.md",
        "LICENSE",
        "Land-cover Maps/res_all.pdf",
        *(
            f"Land-cover Maps/{PurePosixPath(path).name}"
            for path in ADMITTED_CSV_MEMBERS
        ),
    }
    if set(blobs) != expected or len(blobs) != 28:
        raise ValueError("OpenLand upstream blob inventory changed")
    if any(
        not re.fullmatch(r"[0-9a-f]{40}", str(entry.get("sha", "")))
        or not isinstance(entry.get("size"), int)
        or entry["size"] < 0
        for entry in blobs.values()
    ):
        raise ValueError("OpenLand upstream blob identity is incomplete")
    return blobs


def classify_member(
    path: str, *, upstream_identity: str
) -> tuple[str, str, str, str, str, str]:
    """Give each source member one role, rights basis, route, and refusal."""
    if path.endswith("/"):
        return (
            "container",
            "not_applicable",
            "no_member_data_to_redistribute",
            "none",
            "exclude",
            "directory_only",
        )
    if path in ADMITTED_CSV_MEMBERS:
        if upstream_identity != "exact_pinned_git_blob":
            raise ValueError(
                f"OpenLand modeled slice lacks exact upstream identity: {path}"
            )
        return (
            "pollen_derived_modeled_cover_slice",
            SOURCE_DATA_LICENSE,
            "not_authorized_by_this_review",
            "existing_open_land_source_authority",
            "private_source_review_only",
            "modeled_source_not_independent_truth",
        )
    if path == "LandCover_OpenLand/Data/res_all.pdf":
        return (
            "source_documentation",
            "member_scope_unresolved",
            "not_authorized_by_this_review",
            "source_reference_only",
            "reference_only",
            "document_rights_not_established",
        )
    if path == "LandCover_OpenLand/output.gpkg":
        return (
            "local_interpolated_derivative",
            "local_derivative_rights_unresolved",
            "not_authorized_by_this_review",
            "none",
            "exclude",
            "not_pinned_upstream_and_interpolation_unreviewed",
        )
    if path == "LandCover_OpenLand/load_data.R":
        return (
            "local_processing_script",
            "local_script_rights_unresolved",
            "not_authorized_by_this_review",
            "source_reference_only",
            "reference_only_no_execution",
            "not_pinned_upstream_code",
        )
    if path == "LandCover_OpenLand/LandCover_OpenLand.Rproj":
        return (
            "local_project_configuration",
            "local_configuration_rights_unresolved",
            "not_authorized_by_this_review",
            "none",
            "exclude",
            "not_source_data",
        )
    if path.startswith("LandCover_OpenLand/.Rproj.user/"):
        return (
            "local_private_project_state",
            "private_state_rights_unresolved",
            "not_authorized_by_this_review",
            "none",
            "exclude_private_state",
            "not_source_data",
        )
    return (
        "unresolved_member",
        "rights_unresolved",
        "not_authorized_by_this_review",
        "none",
        "exclude_pending_member_review",
        "unrecognized_archive_member",
    )


def _safe_members(infos: list[ZipInfo]) -> None:
    paths = [info.filename for info in infos]
    if len(paths) != ARCHIVE_MEMBER_COUNT or len(set(paths)) != len(paths):
        raise ValueError("OpenLand archive member count or path identity changed")
    if sum(info.file_size for info in infos) != ARCHIVE_EXPANDED_BYTES:
        raise ValueError("OpenLand archive expanded size changed")
    for info in infos:
        path = PurePosixPath(info.filename)
        mode = stat.S_IFMT(info.external_attr >> 16)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not info.filename.startswith("LandCover_OpenLand/")
            or info.flag_bits & 1
            or mode == stat.S_IFLNK
        ):
            raise ValueError(f"Unsafe OpenLand archive member: {info.filename}")
    if {path for path in paths if path.endswith(".csv")} != set(ADMITTED_CSV_MEMBERS):
        raise ValueError("OpenLand modeled slice inventory changed")


def _decide_member(
    archive: ZipFile, info: ZipInfo, blobs: dict[str, dict[str, Any]]
) -> dict[str, object]:
    path = info.filename
    upstream_path = (
        f"Land-cover Maps/{PurePosixPath(path).name}"
        if path in ADMITTED_CSV_MEMBERS or path == "LandCover_OpenLand/Data/res_all.pdf"
        else ""
    )
    source = blobs.get(upstream_path)
    member_sha = ""
    upstream_identity = "no_pinned_upstream_member"
    if source is not None:
        data = archive.read(info)
        member_sha = _sha(data)
        if len(data) != source["size"] or _git_blob_sha(data) != source["sha"]:
            raise ValueError(f"OpenLand upstream member digest mismatch: {path}")
        upstream_identity = "exact_pinned_git_blob"
    elif path == "LandCover_OpenLand/load_data.R":
        member_sha = _sha(archive.read(info))
    role, rights, redistribution, route, decision, reason = classify_member(
        path, upstream_identity=upstream_identity
    )
    return {
        "member_path": path,
        "member_type": "directory" if info.is_dir() else "file",
        "uncompressed_bytes": info.file_size,
        "compressed_bytes": info.compress_size,
        "zip_crc32": f"{info.CRC:08x}",
        "member_sha256": member_sha,
        "upstream_path": upstream_path,
        "upstream_git_blob_sha1": source["sha"] if source else "",
        "upstream_identity": upstream_identity,
        "semantic_role": role,
        "rights_basis": rights,
        "redistribution_posture": redistribution,
        "source_route": route,
        "independent_vegetation_benchmark": "false",
        "decision": decision,
        "reason_code": reason,
    }


def build(
    repository: Path, archive_path: Path, upstream_tree_path: Path, output: Path
) -> dict[str, object]:
    """Write one bounded metadata/member decision without copying raw inputs."""
    if archive_path.is_symlink() or upstream_tree_path.is_symlink():
        raise ValueError("OpenLand input symlink refused")
    repository, archive_path, upstream_tree_path, output = (
        path.resolve()
        for path in (repository, archive_path, upstream_tree_path, output)
    )
    if output.exists():
        raise ValueError("Absent output destination required")
    if not archive_path.is_file():
        raise ValueError("OpenLand private archive must be a regular file")
    archive_sha = _file_sha(archive_path)
    if archive_sha != ARCHIVE_SHA256:
        raise ValueError("OpenLand archive SHA-256 changed")
    tree_bytes = upstream_tree_path.read_bytes()
    blobs = validate_upstream_tree(json.loads(tree_bytes))
    authority_path = repository / AUTHORITY
    landclim_path = repository / LANDCLIM_RECEIPT
    landclim = json.loads(landclim_path.read_bytes())
    if not any(
        dataset.get("dataset_id") == "937075"
        and dataset.get("doi") == "https://doi.org/10.1594/PANGAEA.937075"
        for dataset in landclim["datasets"]
    ):
        raise ValueError("LandClim II source identity changed")
    with ZipFile(archive_path) as archive:
        infos = archive.infolist()
        _safe_members(infos)
        rows = [_decide_member(archive, info, blobs) for info in infos]
    rows.sort(key=lambda row: str(row["member_path"]))
    role_counts = dict(sorted(Counter(row["semantic_role"] for row in rows).items()))
    if (
        role_counts.get("pollen_derived_modeled_cover_slice") != 25
        or role_counts.get("source_documentation") != 1
        or sum(role_counts.values()) != 51
    ):
        raise ValueError("OpenLand member role inventory changed")
    output.mkdir(parents=True)
    ledger_path = output / "members.csv"
    with ledger_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report: dict[str, object] = {
        "schema_version": "openland-member-intake.v1",
        "status": "source_identified_private_review_only",
        "source_archive": {
            "custody": "preexisting_private_workspace_archive_not_copied",
            "bytes": archive_path.stat().st_size,
            "sha256": archive_sha,
            "member_count": len(rows),
            "expanded_bytes": sum(cast(int, row["uncompressed_bytes"]) for row in rows),
            "raw_archive_copied": False,
        },
        "upstream": {
            "repository": SOURCE_REPOSITORY,
            "commit": SOURCE_COMMIT,
            "tree_api_url": TREE_URL,
            "tree_metadata_path": upstream_tree_path.relative_to(repository).as_posix(),
            "tree_metadata_sha256": _sha(tree_bytes),
            "citation_doi": SOURCE_CITATION_DOI,
            "modeled_data_license": SOURCE_DATA_LICENSE,
        },
        "inputs": {
            AUTHORITY.as_posix(): _file_sha(authority_path),
            LANDCLIM_RECEIPT.as_posix(): _file_sha(landclim_path),
            PRODUCER.as_posix(): _file_sha(repository / PRODUCER),
        },
        "member_roles": role_counts,
        "exact_pinned_upstream_members": sum(
            row["upstream_identity"] == "exact_pinned_git_blob" for row in rows
        ),
        "member_content_sha256_count": sum(bool(row["member_sha256"]) for row in rows),
        "modeled_source_member_count": 25,
        "public_member_admissions": 0,
        "independent_vegetation_benchmarks": 0,
        "source_overlap": {
            "shared_family": "pollen_derived_REVEALS_land_cover",
            "upstream_paper_reveals_doi": "https://doi.org/10.1594/PANGAEA.931856",
            "local_landclim_ii_doi": "https://doi.org/10.1594/PANGAEA.937075",
            "exact_row_or_input_identity": "unresolved",
            "decision": "route_to_existing_open_land_authority;do_not_duplicate_landclim_or_count_as_independent_truth",
        },
        "rights": {
            "matched_csv_data_license": SOURCE_DATA_LICENSE,
            "upstream_code_license": "GPL-3.0",
            "data_rights_evidence": (
                f"{SOURCE_REPOSITORY}/blob/{SOURCE_COMMIT}/README.md"
            ),
            "code_rights_evidence": (
                f"{SOURCE_REPOSITORY}/blob/{SOURCE_COMMIT}/LICENSE"
            ),
            "local_script_rights": "unresolved",
            "source_document_rights": "unresolved",
            "mixed_archive_redistribution_authorized": False,
            "public_map_or_export_authorized": False,
        },
        "members_csv": {
            "bytes": ledger_path.stat().st_size,
            "sha256": _file_sha(ledger_path),
        },
        "limitations": [
            "The source CSVs are spatially modeled land cover based on pollen-derived REVEALS inputs and KK10 covariates, not raw counts or independent vegetation observations.",
            "Exact source-row overlap with local PANGAEA 937075 remains unresolved despite shared REVEALS/LandClim family context.",
            "The local GeoPackage, script, project configuration, and private editor state do not have pinned upstream member identities.",
            "No member is admitted for public redistribution, map display, export, propagation, or independent benchmark use by this review.",
            "Only the 26 pinned upstream member contents and the small local script were read; the 199,933,952-byte GeoPackage and private editor state were classified from the verified ZIP directory without content extraction.",
        ],
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--upstream-tree", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.repository, args.archive, args.upstream_tree, args.output)
    source_archive = cast(dict[str, object], result["source_archive"])
    print(
        json.dumps(
            {
                "members": source_archive["member_count"],
                "upstream_matches": result["exact_pinned_upstream_members"],
                "public_member_admissions": result["public_member_admissions"],
            }
        )
    )


if __name__ == "__main__":
    main()

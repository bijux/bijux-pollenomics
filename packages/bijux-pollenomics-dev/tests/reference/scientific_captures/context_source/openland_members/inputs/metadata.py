"""Rejoin the OpenLand archive, pinned source tree and explicit retained-input roles."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
from io import StringIO
from pathlib import Path, PurePosixPath
import stat
from typing import Any
from zipfile import ZipFile, ZipInfo

from contracts import exact, require

SOURCE_COMMIT = "894d44d58f66bb5c273491d98c3ec23a35e6a796"
SOURCE_SHA = "7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b"
SOURCE_BYTES = 204058381
AGE_LABELS = (50, 225, 550, 1000, *range(1500, 11501, 500))
CSV_MEMBERS = tuple(
    f"LandCover_OpenLand/Data/Land_Cover_{label}.csv" for label in AGE_LABELS
)
PDF_MEMBER = "LandCover_OpenLand/Data/res_all.pdf"
SCRIPT_MEMBER = "LandCover_OpenLand/load_data.R"
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


def upstream_blobs(tree: dict[str, Any]) -> dict[str, dict[str, Any]]:
    require(
        tree.get("sha") == SOURCE_COMMIT and tree.get("truncated") is False,
        "Complete pinned upstream tree required",
    )
    rows = tree.get("tree")
    require(
        type(rows) is list and len(rows) == 29, "Exact29 source tree entries required"
    )
    assert isinstance(rows, list)
    require(
        all(type(r) is dict and type(r.get("path")) is str for r in rows),
        "Typed tree rows required",
    )
    require(len({r["path"] for r in rows}) == len(rows), "Duplicate upstream tree path")
    blobs = {r["path"]: r for r in rows if r.get("type") == "blob"}
    names = {
        "README.md",
        "LICENSE",
        "Land-cover Maps/res_all.pdf",
        *["Land-cover Maps/" + PurePosixPath(name).name for name in CSV_MEMBERS],
    }
    require(
        set(blobs) == names and len(blobs) == 28, "Upstream28blob membership differs"
    )
    for row in blobs.values():
        require(
            type(row.get("sha")) is str
            and len(row["sha"]) == 40
            and all(c in "0123456789abcdef" for c in row["sha"]),
            "Git blob identity differs",
        )
        require(
            type(row.get("size")) is int and row["size"] >= 0,
            "Typed nonnegative source size required",
        )
    return blobs


def safe_directory(infos: list[ZipInfo]) -> None:
    names = [r.filename for r in infos]
    require(len(names) == len(set(names)) == 51, "Exact unique51 ZIP entries required")
    require(
        sum(r.file_size for r in infos) == 204016242, "Archive expanded size differs"
    )
    for info in infos:
        name = info.filename
        path = PurePosixPath(name)
        require(
            not path.is_absolute()
            and ".." not in path.parts
            and "\\" not in name
            and "\x00" not in name
            and name.startswith("LandCover_OpenLand/"),
            "Unsafe source ZIP path",
        )
        require(
            path.as_posix() + ("/" if info.is_dir() else "") == name
            and not (info.flag_bits & 1),
            "Normalized unencrypted member required",
        )
        mode = stat.S_IFMT(info.external_attr >> 16)
        require(
            mode in (0, stat.S_IFREG, stat.S_IFDIR)
            and (mode != stat.S_IFDIR or info.is_dir())
            and (mode != stat.S_IFREG or not info.is_dir()),
            "ZIP alias/special/type mismatch",
        )
    require(
        {n for n in names if n.endswith(".csv")} == set(CSV_MEMBERS),
        "Exact25 modeled slice identities required",
    )


def role(name: str) -> tuple[str, str, str, str, str]:
    if name.endswith("/"):
        return ("container", "not_applicable", "none", "exclude", "directory_only")
    if name in CSV_MEMBERS:
        return (
            "pollen_derived_modeled_cover_slice",
            "CC-BY-SA-4.0",
            "existing_open_land_source_authority",
            "private_source_review_only",
            "modeled_source_not_independent_truth",
        )
    if name == PDF_MEMBER:
        return (
            "source_documentation",
            "member_scope_unresolved",
            "source_reference_only",
            "reference_only",
            "document_rights_not_established",
        )
    if name == SCRIPT_MEMBER:
        return (
            "local_processing_script",
            "local_script_rights_unresolved",
            "source_reference_only",
            "reference_only_no_execution",
            "not_pinned_upstream_code",
        )
    if name == "LandCover_OpenLand/output.gpkg":
        return (
            "local_interpolated_derivative",
            "local_derivative_rights_unresolved",
            "none",
            "exclude",
            "not_pinned_upstream_and_interpolation_unreviewed",
        )
    if name == "LandCover_OpenLand/LandCover_OpenLand.Rproj":
        return (
            "local_project_configuration",
            "local_configuration_rights_unresolved",
            "none",
            "exclude",
            "not_source_data",
        )
    require(
        name.startswith("LandCover_OpenLand/.Rproj.user/"),
        "Unknown archive member role",
    )
    return (
        "local_private_project_state",
        "private_state_rights_unresolved",
        "none",
        "exclude_private_state",
        "not_source_data",
    )


def expected_rows(
    archive: ZipFile, infos: list[ZipInfo], blobs: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, object]], list[str]]:
    rows = []
    reads = []
    for info in infos:
        name = info.filename
        upstream_path = (
            "Land-cover Maps/" + PurePosixPath(name).name
            if name in {*CSV_MEMBERS, PDF_MEMBER}
            else ""
        )
        entry = blobs.get(upstream_path)
        digest = ""
        identity = "no_pinned_upstream_member"
        if entry is not None or name == SCRIPT_MEMBER:
            raw = archive.read(info)
            reads.append(name)
            digest = hashlib.sha256(raw).hexdigest()
            if entry is not None:
                git = hashlib.sha1(
                    b"blob " + str(len(raw)).encode() + b"\x00" + raw,
                    usedforsecurity=False,
                ).hexdigest()
                require(
                    len(raw) == entry["size"] and git == entry["sha"],
                    "Exact pinned upstream member bytes differ",
                )
                identity = "exact_pinned_git_blob"
        semantic, rights, route, decision, reason = role(name)
        rows.append(
            dict(
                zip(
                    FIELDS,
                    (
                        name,
                        "directory" if info.is_dir() else "file",
                        info.file_size,
                        info.compress_size,
                        f"{info.CRC:08x}",
                        digest,
                        upstream_path,
                        entry["sha"] if entry else "",
                        identity,
                        semantic,
                        rights,
                        "no_member_data_to_redistribute"
                        if info.is_dir()
                        else "not_authorized_by_this_review",
                        route,
                        "false",
                        decision,
                        reason,
                    ),
                    strict=True,
                )
            )
        )
    require(
        set(reads) == {*CSV_MEMBERS, PDF_MEMBER, SCRIPT_MEMBER} and len(reads) == 27,
        "Only27 declared member content reads allowed",
    )
    return sorted(rows, key=lambda r: str(r["member_path"])), reads


def csv_bytes(rows: list[dict[str, object]]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def compare_products(
    historical: dict[str, Any],
    actual: dict[str, Any],
    rows: list[dict[str, object]],
    actual_csv: bytes,
    bridge: dict[str, Any],
) -> bytes:
    expected_csv = csv_bytes(rows)
    require(actual_csv == expected_csv, "Independent complete51member CSV differs")
    expected = {**historical, "inputs": dict(historical["inputs"])}
    expected["inputs"][bridge["path"]] = bridge["current"]["sha256"]
    require(
        exact(actual, expected),
        "Report changed outside exact attribution source digest",
    )
    counts = dict(sorted(Counter(str(r["semantic_role"]) for r in rows).items()))
    require(
        exact(counts, actual["member_roles"]) and sum(counts.values()) == 51,
        "Source role counts differ",
    )
    require(
        actual["exact_pinned_upstream_members"]
        == sum(r["upstream_identity"] == "exact_pinned_git_blob" for r in rows)
        == 26,
        "Exact26 source member identity count differs",
    )
    require(
        actual["member_content_sha256_count"]
        == sum(bool(r["member_sha256"]) for r in rows)
        == 27,
        "Exact27 content identity count differs",
    )
    require(
        type(actual["public_member_admissions"]) is int
        and actual["public_member_admissions"] == 0
        and type(actual["independent_vegetation_benchmarks"]) is int
        and actual["independent_vegetation_benchmarks"] == 0,
        "Scientific/public admission inflation",
    )
    require(
        actual["members_csv"]
        == {
            "bytes": len(expected_csv),
            "sha256": hashlib.sha256(expected_csv).hexdigest(),
        },
        "Full CSV report identity differs",
    )
    return expected_csv


def validate_copies(
    copies: list[dict[str, Any]], source_records: dict[str, Any], root: Path
) -> None:
    from contracts import pin

    require(len(copies) == 2, "Exactly two metadata input copy roles required")
    names = {
        Path(source_records[role]["path"]).name
        for role in ("upstream_tree", "doi_lineage")
    }
    require(
        {p.name for p in root.iterdir()} == names,
        "Retained-input directory membership differs",
    )
    for role, item in zip(("upstream_tree", "doi_lineage"), copies, strict=True):
        require(
            set(item) == {"role", "source", "copied"},
            "Closed input copy fields required",
        )
        original = source_records[role]
        source = Path(original["path"])
        target = root / source.name
        require(
            not any(
                p.is_symlink()
                for p in (source, *source.parents, target, *target.parents)
            ),
            "Input/copy aliases refused",
        )
        require(
            item["role"] == "retained_declared_metadata_input_not_new_acquisition"
            and exact(item["source"], original)
            and exact(pin(source), original)
            and exact(item["copied"], pin(target))
            and target.read_bytes() == source.read_bytes(),
            "Source/copy identity or role differs",
        )

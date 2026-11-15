from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import date
from pathlib import Path
import re

from ....core.files import write_json
from ....core.owned_tree import (
    build_staging_output_dir,
    remove_output_tree,
    replace_output_tree,
)
from .client import validate_neotoma_download_coverage

__all__ = ["build_neotoma_download_archive_parts", "write_neotoma_download_archive"]


def build_neotoma_download_archive_parts(
    download_rows: Iterable[Mapping[str, object]],
    *,
    rows_per_part: int,
    extract_neotoma_download_dataset_ids_fn: Callable[
        [Iterable[Mapping[str, object]]], list[int]
    ],
) -> list[dict[str, object]]:
    """Split large Neotoma download payloads into stable part files."""
    if rows_per_part < 1:
        raise ValueError("rows_per_part must be at least 1")

    rows = [dict(row) for row in download_rows]
    part_count = (len(rows) + rows_per_part - 1) // rows_per_part
    parts: list[dict[str, object]] = []
    for index, start in enumerate(range(0, len(rows), rows_per_part), start=1):
        part_rows = rows[start : start + rows_per_part]
        part_dataset_ids = extract_neotoma_download_dataset_ids_fn(part_rows)
        parts.append(
            {
                "filename": f"part-{index:03d}.json",
                "part_number": index,
                "part_count": part_count,
                "row_count": len(part_rows),
                "downloaded_dataset_count": len(part_dataset_ids),
                "downloaded_dataset_ids": part_dataset_ids,
                "rows": part_rows,
            }
        )
    return parts


def write_neotoma_download_archive(
    raw_dir: Path,
    *,
    requested_dataset_ids: Iterable[int],
    downloaded_dataset_ids: Iterable[int],
    download_rows: Iterable[Mapping[str, object]],
    rows_per_part: int,
    neotoma_data_url: str,
    neotoma_datasettype: str,
    neotoma_download_archive_dirname: str,
    neotoma_download_archive_label: str,
    extract_neotoma_download_dataset_ids_fn: Callable[
        [Iterable[Mapping[str, object]]], list[int]
    ],
) -> Path:
    """Stage reconciled downloads before replacing the owned archive together."""
    archive_dir = Path(raw_dir) / neotoma_download_archive_dirname
    rows = [dict(row) for row in download_rows]
    requested_ids = sorted({int(dataset_id) for dataset_id in requested_dataset_ids})
    returned_ids = sorted({int(dataset_id) for dataset_id in downloaded_dataset_ids})
    validate_neotoma_download_coverage(
        requested_ids,
        rows,
        extract_neotoma_download_dataset_ids_fn=extract_neotoma_download_dataset_ids_fn,
    )
    actual_ids = extract_neotoma_download_dataset_ids_fn(rows)
    if sorted(actual_ids) != returned_ids:
        raise ValueError("Neotoma declared download IDs do not match archive rows")
    parts = build_neotoma_download_archive_parts(
        rows,
        rows_per_part=rows_per_part,
        extract_neotoma_download_dataset_ids_fn=extract_neotoma_download_dataset_ids_fn,
    )
    _require_owned_archive(
        archive_dir,
        endpoint=f"{neotoma_data_url}/downloads/{{datasetid}}",
        dataset_type=neotoma_datasettype,
        archive_label=neotoma_download_archive_label,
        extract_ids=extract_neotoma_download_dataset_ids_fn,
    )
    stage = build_staging_output_dir(archive_dir)
    stage.mkdir(parents=True, exist_ok=False)
    try:
        _write_archive_members(
            stage,
            parts=parts,
            requested_ids=requested_ids,
            returned_ids=returned_ids,
            row_count=len(rows),
            rows_per_part=rows_per_part,
            neotoma_data_url=neotoma_data_url,
            neotoma_datasettype=neotoma_datasettype,
            neotoma_download_archive_label=neotoma_download_archive_label,
        )
        replace_output_tree(final_output_root=archive_dir, staging_output_root=stage)
    except Exception:
        remove_output_tree(stage)
        raise
    return archive_dir / "manifest.json"


def _require_owned_archive(
    path: Path,
    *,
    endpoint: str,
    dataset_type: str,
    archive_label: str,
    extract_ids: Callable[[Iterable[Mapping[str, object]]], list[int]],
) -> None:
    """Refuse to replace unrelated files or follow a source-directory alias."""
    if path.absolute() != path.resolve(strict=False):
        raise ValueError(
            "Neotoma archive destination must not contain a symlink or alias"
        )
    if not path.exists():
        return
    if not path.is_dir():
        raise ValueError("Neotoma archive destination contains unowned content")
    for member in path.iterdir():
        if (
            member.is_symlink()
            or not member.is_file()
            or (
                member.name != "manifest.json"
                and re.fullmatch(r"part-[0-9]{3,}\.json", member.name) is None
            )
        ):
            raise ValueError(f"Neotoma archive contains unowned content: {member.name}")
    # Reuse the source reader's complete manifest/member contract, including
    # dataset ownership and coverage; filenames alone do not establish ownership.
    from .production import validation
    from .production.raw_archive import load_raw_archive

    def dataset_id(row: Mapping[str, object], label: str) -> int:
        identities = extract_ids([row])
        if len(identities) != 1:
            raise ValueError(f"Neotoma archive has no unique dataset: {label}")
        return validation.positive_integer(identities[0], label)

    try:
        manifest = validation.json_object(
            validation.read_regular_file(path / "manifest.json"), path / "manifest.json"
        )
        count = validation.non_negative_integer(
            manifest.get("part_count"), "part_count"
        )
        load_raw_archive(
            path.absolute(),
            expected_part_count=count,
            raw_source="Neotoma",
            archive_label=archive_label,
            endpoint=endpoint,
            dataset_type=dataset_type,
            sha256_pattern=re.compile(r"[0-9a-f]{64}\Z"),
            validate_directory=validation.validated_input_directory,
            read_file=validation.read_regular_file,
            parse_object=validation.json_object,
            parse_mapping=validation.mapping,
            parse_positive_integer=validation.positive_integer,
            parse_non_negative_integer=validation.non_negative_integer,
            parse_integer_list=validation.integer_list,
            expect_equal=validation.expect_equal,
            download_dataset_id=dataset_id,
            canonical_digest=validation.canonical_digest,
        )
    except (OSError, ValueError) as error:
        raise ValueError(
            "Neotoma archive contains unowned or invalid source members"
        ) from error


def _write_archive_members(
    archive_dir: Path,
    *,
    parts: list[dict[str, object]],
    requested_ids: list[int],
    returned_ids: list[int],
    row_count: int,
    rows_per_part: int,
    neotoma_data_url: str,
    neotoma_datasettype: str,
    neotoma_download_archive_label: str,
) -> None:
    """Write members into the exclusive, unpublished candidate tree."""
    generated_on = str(date.today())

    manifest_parts: list[dict[str, object]] = []
    for part in parts:
        filename = str(part["filename"])
        write_json(
            archive_dir / filename,
            {
                "generated_on": generated_on,
                "source": "Neotoma",
                "endpoint_template": f"{neotoma_data_url}/downloads/{{datasetid}}",
                "datasettype": neotoma_datasettype,
                "part_number": part["part_number"],
                "part_count": part["part_count"],
                "row_count": part["row_count"],
                "downloaded_dataset_count": part["downloaded_dataset_count"],
                "downloaded_dataset_ids": part["downloaded_dataset_ids"],
                "rows": part["rows"],
            },
        )
        manifest_parts.append(
            {
                "filename": filename,
                "part_number": part["part_number"],
                "row_count": part["row_count"],
                "downloaded_dataset_count": part["downloaded_dataset_count"],
                "downloaded_dataset_ids": part["downloaded_dataset_ids"],
            }
        )

    manifest_path = archive_dir / "manifest.json"
    write_json(
        manifest_path,
        {
            "generated_on": generated_on,
            "source": "Neotoma",
            "archive_dir": neotoma_download_archive_label,
            "endpoint_template": f"{neotoma_data_url}/downloads/{{datasetid}}",
            "datasettype": neotoma_datasettype,
            "requested_dataset_count": len(requested_ids),
            "requested_dataset_ids": requested_ids,
            "downloaded_dataset_count": len(returned_ids),
            "downloaded_dataset_ids": returned_ids,
            "row_count": row_count,
            "rows_per_part": rows_per_part,
            "part_count": len(parts),
            "parts": manifest_parts,
        },
    )

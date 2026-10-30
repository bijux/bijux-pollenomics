"""Check source storage using Git names and declared witness metadata, never bodies."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source.descriptor import (
    json_object,
)

from .test_data_source_identity import HISTORICAL_BUILD_RESOURCE

REPOSITORY = Path(__file__).resolve().parents[5]


def _staged_entries(repository: Path, *paths: str) -> list[tuple[str, str, str]]:
    raw = subprocess.check_output(
        ["git", "--no-replace-objects", "ls-files", "--stage", "-z", "--", *paths],
        cwd=repository,
        timeout=20,
    )
    result = []
    for item in raw.split(b"\0"):
        if item:
            metadata, name = item.split(b"\t", 1)
            mode, blob, stage = metadata.decode().split()
            assert stage == "0", "Resolve unmerged source before checking retention"
            result.append((name.decode(), mode, blob))
    return result


def _data_program_paths(entries: list[tuple[str, str, str]]) -> list[str]:
    """Forbid plain Python/R programs, independently of mode, origin or generated status."""
    return [
        name
        for name, _, _ in entries
        if PurePosixPath(name).parts[:1] == ("data",)
        and PurePosixPath(name).suffix in {".py", ".pyi", ".R", ".r"}
    ]


def _staged_descriptors(repository: Path) -> list[tuple[str, dict[str, Any]]]:
    def metadata(name: str) -> dict[str, Any]:
        raw = subprocess.check_output(
            ["git", "--no-replace-objects", "show", ":" + name],
            cwd=repository,
            timeout=20,
        )
        assert len(raw) <= 8 * 1024**2, "Bounded staged source metadata required"
        return json_object(raw)

    index = metadata("configs/ci/source-retention/index.json")
    assert index["schema_version"] == "retained-source-index.v1"
    return [
        (prefix, metadata(prefix + "/" + entry["descriptor"]))
        for prefix, entry in index["capsules"].items()
        if prefix.startswith("data/")
    ]


def _restored_witness_paths(
    repository: Path,
    entries: list[tuple[str, str, str]],
    descriptors: list[tuple[str, dict[str, Any]]],
) -> list[str]:
    tracked = {name for name, _, _ in entries}
    restored = set()
    for prefix, descriptor in descriptors:
        assert PurePosixPath(prefix).parts[:1] == ("data",)
        assert ".." not in PurePosixPath(prefix).parts
        for group in descriptor["git_groups"]:
            if group.get("storage_role") != "historical_code_witness":
                continue
            assert "prefixes" not in group and type(group["paths"]) is list
            for member, stored in group["paths"]:
                name = PurePosixPath(member)
                assert name.parts and not name.is_absolute() and ".." not in name.parts
                assert name.as_posix() == member and "\\" not in member
                relative = prefix + "/" + member
                assert stored == relative, "Witness must remain in its exact capsule"
                physical = repository / relative
                if (
                    relative in tracked
                    or physical.exists()
                    or any(node.is_symlink() for node in (physical, *physical.parents))
                ):
                    restored.add(relative)
    return sorted(restored)


@pytest.mark.parametrize(
    "name",
    [
        "data/observer.py",
        "data/oracle.R",
        "data/capture/model.r",
        "data/generated/_build_version.py",
        "data/types.pyi",
        "data/vendor/author.R",
    ],
)
@pytest.mark.parametrize("mode", ["100644", "100755", "120000"])
def test_plain_programs_cannot_return_under_data(name: str, mode: str) -> None:
    assert _data_program_paths([(name, mode, "1" * 40)]) == [name]


@pytest.mark.parametrize(
    "name",
    [
        "data/counts.csv",
        "data/capture.json",
        "data/source.xlsx",
        "data/input.rds",
        "data/original.R.gz",
        "data/upstream.tar.gz",
        "data/author.zip",
        "artifacts/oracle.R",
        "packages/example/oracle.R",
    ],
)
def test_datasets_compressed_archives_and_canonical_sources_remain_allowed(
    name: str,
) -> None:
    assert not _data_program_paths([(name, "100644", "1" * 40)])


def witness(member: str = "payloads/" + "a" * 64) -> tuple[str, dict[str, Any]]:
    prefix = "data/controlled-capture"
    return prefix, {
        "git_groups": [
            {
                "storage_role": "historical_code_witness",
                "paths": [[member, prefix + "/" + member]],
            }
        ]
    }


@pytest.mark.parametrize(
    "placement", ["staged", "physical", "dangling", "ancestor_alias"]
)
@pytest.mark.parametrize(
    "member", ["payloads/" + "a" * 64, "members/" + "b" * 64, "capture/oracle/oracle.R"]
)
def test_restored_declared_witness_is_refused_without_reading_its_body(
    tmp_path: Path,
    placement: str,
    member: str,
) -> None:
    prefix, descriptor = witness(member)
    name = prefix + "/" + member
    target = tmp_path / name
    entries = []
    if placement == "staged":
        entries = [(name, "100644", "1" * 40)]
    elif placement == "ancestor_alias":
        parent = tmp_path / prefix
        parent.parent.mkdir(parents=True)
        parent.symlink_to(tmp_path / "missing-directory", target_is_directory=True)
    else:
        target.parent.mkdir(parents=True)
        if placement == "dangling":
            target.symlink_to(tmp_path / "missing-body")
        else:
            target.write_bytes(b"opaque synthetic witness; never executed")
    assert _restored_witness_paths(tmp_path, entries, [(prefix, descriptor)]) == [name]


def test_absent_witness_and_unrelated_data_do_not_require_source_bodies(
    tmp_path: Path,
) -> None:
    prefix, descriptor = witness()
    assert not _restored_witness_paths(
        tmp_path, [("data/raw/input.gz", "100644", "1" * 40)], [(prefix, descriptor)]
    )


def test_foreign_witness_storage_is_not_silently_ignored(tmp_path: Path) -> None:
    prefix, descriptor = witness()
    descriptor["git_groups"][0]["paths"][0][1] = "data/foreign/payload"
    with pytest.raises(AssertionError, match="exact capsule"):
        _restored_witness_paths(tmp_path, [], [(prefix, descriptor)])


def test_staged_descriptor_inventory_reads_only_declared_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    metadata = {
        ":configs/ci/source-retention/index.json": b'{"schema_version":"retained-source-index.v1","capsules":{"data/capture":{"descriptor":"source-transport.json"},"artifacts/runtime":{"descriptor":"source-transport.json"}}}',
        ":data/capture/source-transport.json": b'{"git_groups":[]}',
    }

    def query(arguments: list[str], **options: Any) -> bytes:
        assert arguments[:3] == ["git", "--no-replace-objects", "show"]
        assert options["cwd"] == tmp_path
        calls.append(arguments[3])
        return metadata[arguments[3]]

    monkeypatch.setattr(subprocess, "check_output", query)
    assert _staged_descriptors(tmp_path) == [("data/capture", {"git_groups": []})]
    assert calls == list(metadata)


# This exact existing resource is a governed metadata fixture, not an exemption
# for generated programmes or sibling package snapshots.
def _ordinary_program_entries(
    entries: list[tuple[str, str, str]],
) -> list[tuple[str, str, str]]:
    return [
        row
        for row in entries
        if row
        != (
            HISTORICAL_BUILD_RESOURCE,
            "100644",
            "05d6713c0658290c2e88e7cf8c86fe547aba9d1e",
        )
    ]


@pytest.mark.parametrize(
    "entry,retained",
    [
        (
            (
                HISTORICAL_BUILD_RESOURCE,
                "100644",
                "05d6713c0658290c2e88e7cf8c86fe547aba9d1e",
            ),
            False,
        ),
        (
            (
                HISTORICAL_BUILD_RESOURCE,
                "100755",
                "05d6713c0658290c2e88e7cf8c86fe547aba9d1e",
            ),
            True,
        ),
        (
            (
                HISTORICAL_BUILD_RESOURCE,
                "120000",
                "05d6713c0658290c2e88e7cf8c86fe547aba9d1e",
            ),
            True,
        ),
        ((HISTORICAL_BUILD_RESOURCE, "100644", "1" * 40), True),
        (("data/other.py", "100644", "05d6713c0658290c2e88e7cf8c86fe547aba9d1e"), True),
        (
            (
                HISTORICAL_BUILD_RESOURCE + ".py",
                "100644",
                "05d6713c0658290c2e88e7cf8c86fe547aba9d1e",
            ),
            True,
        ),
    ],
)
def test_historical_metadata_resource_exception_is_exact_regular_identity(
    entry: tuple[str, str, str], retained: bool
) -> None:
    assert bool(_ordinary_program_entries([entry])) is retained
    if retained:
        assert _data_program_paths(_ordinary_program_entries([entry])) == [entry[0]]


def test_tracked_data_does_not_store_plain_python_or_r_programs() -> None:
    forbidden = _data_program_paths(
        _ordinary_program_entries(_staged_entries(REPOSITORY, "data"))
    )
    assert not forbidden, "Data contains Python/R programs: " + repr(forbidden[:8])


def test_declared_historical_code_witnesses_are_not_staged_or_physically_restored() -> (
    None
):
    forbidden = _restored_witness_paths(
        REPOSITORY, _staged_entries(REPOSITORY, "data"), _staged_descriptors(REPOSITORY)
    )
    assert not forbidden, "Historical code witnesses restored in data: " + repr(
        forbidden[:8]
    )

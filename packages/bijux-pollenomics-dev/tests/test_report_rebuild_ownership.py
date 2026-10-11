"""Exercise report ownership declarations against a real Git index."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.ownership import (
    ReportOwnershipError,
    check_report_ownership,
    main,
)

REPORT_PATHS = [
    "docs/report/README.md",
    "docs/report/analysis/replay.py",
    "docs/report/analysis/result.json",
    "docs/report/guide.md",
    "docs/report/pending.json",
    "docs/report/published.md",
    "docs/report/source/seed.csv",
]


def _digest(paths: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(sorted(paths), separators=(",", ":")).encode()
    ).hexdigest()


def _git(repository: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *args], check=True, capture_output=True
    )


def _write_inventory(repository: Path, payload: dict[str, object]) -> None:
    path = repository / "configs/ci/report-ownership.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _inventory(repository: Path) -> dict[str, object]:
    value: object = json.loads(
        (repository / "configs/ci/report-ownership.json").read_text(encoding="utf-8")
    )
    assert isinstance(value, dict)
    return value


def _owner(payload: dict[str, object], owner_id: str) -> dict[str, object]:
    owners = payload["owners"]
    assert isinstance(owners, list)
    return next(owner for owner in owners if owner["owner_id"] == owner_id)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    for relative in REPORT_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"source for {relative}\n", encoding="utf-8")
    producer = tmp_path / "packages/report_producer.py"
    producer.parent.mkdir(parents=True)
    producer.write_text("# maintained producer\n", encoding="utf-8")
    source = tmp_path / "data/source.csv"
    source.parent.mkdir(parents=True)
    source.write_text("id\na\n", encoding="utf-8")
    _git(tmp_path, "add", "--", "docs/report")
    owners = [
        {
            "owner_id": "publisher",
            "role": "publisher_partition",
            "paths": ["docs/report/published.md"],
            "producer_paths": [],
            "producer_inputs": [],
            "verification": "Publisher partition manifests govern this path.",
        },
        {
            "owner_id": "analysis/result",
            "role": "generated_owner",
            "paths": ["docs/report/analysis/result.json"],
            "producer_paths": ["packages/report_producer.py"],
            "producer_inputs": ["data/source.csv"],
            "verification": "Two owner lanes must match the governed result.",
        },
        {
            "owner_id": "source/reference",
            "role": "retained_source",
            "paths": ["docs/report/source/seed.csv"],
            "producer_paths": [],
            "producer_inputs": [],
            "verification": "Check the independent source certificate and member identity.",
        },
        {
            "owner_id": "reader-pages",
            "role": "maintained_editorial",
            "paths": ["docs/report/README.md", "docs/report/guide.md"],
            "producer_paths": [],
            "producer_inputs": [],
            "verification": "Review tracked editorial page identity and links.",
        },
        {
            "owner_id": "analysis/code",
            "role": "maintained_code",
            "paths": ["docs/report/analysis/replay.py"],
            "producer_paths": [],
            "producer_inputs": [],
            "verification": "Review and test maintained producer source.",
        },
        {
            "owner_id": "open-evidence",
            "role": "unresolved",
            "paths": ["docs/report/pending.json"],
            "producer_paths": [],
            "producer_inputs": [],
            "verification": "Independent source closure remains to be established.",
        },
    ]
    _write_inventory(
        tmp_path,
        {
            "schema_version": "report-output-ownership.v1",
            "root": "docs/report",
            "inventory_scope": (
                "tracked report paths; ownership declarations do not certify reproduction"
            ),
            "path_count": len(REPORT_PATHS),
            "paths_sha256": _digest(REPORT_PATHS),
            "owners": owners,
        },
    )
    return tmp_path


def test_exact_git_population_and_unresolved_reporting(
    repository: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = check_report_ownership(repository)
    assert result.path_count == 7
    assert result.role_counts["maintained_editorial"] == 2
    assert result.unresolved_owner_ids == ["open-evidence"]
    assert result.unresolved_path_count == 1
    assert (
        check_report_ownership(
            repository, Path("configs/ci/report-ownership.json")
        ).path_count
        == 7
    )
    assert main(["--repository", str(repository)]) == 0
    assert json.loads(capsys.readouterr().out)["unresolved_path_count"] == 1
    assert main(["--repository", str(repository), "--require-resolved"]) == 1
    assert "unresolved report owners remain" in capsys.readouterr().err


def test_maintained_configuration_requires_json_path(repository: Path) -> None:
    payload = _inventory(repository)
    _owner(payload, "reader-pages").update(role="maintained_configuration")
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match="non-JSON path"):
        check_report_ownership(repository)


def test_rejects_omitted_and_extra_declarations(repository: Path) -> None:
    payload = _inventory(repository)
    _owner(payload, "reader-pages")["paths"] = ["docs/report/README.md"]
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match="population differs: missing"):
        check_report_ownership(repository)

    _owner(payload, "reader-pages")["paths"] = [
        "docs/report/README.md",
        "docs/report/ghost.md",
        "docs/report/guide.md",
    ]
    _write_inventory(repository, payload)
    with pytest.raises(
        ReportOwnershipError, match=r"population differs: missing=\[\], extra"
    ):
        check_report_ownership(repository)


def test_rejects_added_tracked_path_until_inventory_covers_it(repository: Path) -> None:
    added = repository / "docs/report/new.md"
    added.write_text("# New\n", encoding="utf-8")
    _git(repository, "add", "--", "docs/report/new.md")
    payload = _inventory(repository)
    payload["path_count"] = 8
    payload["paths_sha256"] = _digest([*REPORT_PATHS, "docs/report/new.md"])
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match="population differs: missing"):
        check_report_ownership(repository)


def test_rejects_duplicate_and_overlapping_ownership(repository: Path) -> None:
    payload = _inventory(repository)
    owners = payload["owners"]
    assert isinstance(owners, list)
    owners.append(dict(owners[0]))
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match="duplicate owner_id"):
        check_report_ownership(repository)

    owners.pop()
    _owner(payload, "open-evidence")["paths"] = [
        "docs/report/pending.json",
        "docs/report/published.md",
    ]
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match="overlapping owners"):
        check_report_ownership(repository)


@pytest.mark.parametrize("field,value", [("path_count", 6), ("paths_sha256", "0" * 64)])
def test_rejects_stale_path_identity(
    repository: Path, field: str, value: object
) -> None:
    payload = _inventory(repository)
    payload[field] = value
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match=field):
        check_report_ownership(repository)


@pytest.mark.parametrize("field", ["producer_inputs", "producer_paths"])
def test_rejects_self_fed_generated_output(repository: Path, field: str) -> None:
    payload = _inventory(repository)
    _owner(payload, "analysis/result")[field] = ["docs/report/analysis/result.json"]
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match="feeds its own output"):
        check_report_ownership(repository)


@pytest.mark.parametrize("field", ["producer_inputs", "producer_paths"])
def test_rejects_indirect_generated_output_feedback(
    repository: Path, field: str
) -> None:
    payload = _inventory(repository)
    downstream = _owner(payload, "open-evidence")
    downstream.update(
        role="generated_owner",
        producer_paths=["packages/report_producer.py"],
        producer_inputs=["docs/report/analysis/result.json"],
    )
    _owner(payload, "analysis/result")[field] = ["docs/report/pending.json"]
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match="generated owner dependency cycle"):
        check_report_ownership(repository)


def test_allows_generated_chain_with_shared_retained_input(repository: Path) -> None:
    payload = _inventory(repository)
    _owner(payload, "open-evidence").update(
        role="generated_owner",
        producer_paths=["packages/report_producer.py"],
        producer_inputs=["docs/report/source/seed.csv"],
    )
    _owner(payload, "analysis/result")["producer_inputs"] = [
        "docs/report/pending.json",
        "docs/report/source/seed.csv",
    ]
    _write_inventory(repository, payload)
    result = check_report_ownership(repository, require_resolved=True)
    assert result.role_counts["generated_owner"] == 2
    assert result.unresolved_path_count == 0


def test_rejects_symlinked_source_and_ancestor(repository: Path) -> None:
    source = repository / "data/source.csv"
    source.unlink()
    source.symlink_to(repository / "docs/report/analysis/result.json")
    with pytest.raises(ReportOwnershipError, match="not a real regular file"):
        check_report_ownership(repository)
    source.unlink()
    source.write_text("id\na\n", encoding="utf-8")

    outside = repository.parent / f"{repository.name}-outside-data"
    (repository / "data").rename(outside)
    (repository / "data").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ReportOwnershipError, match="non-real directory"):
        check_report_ownership(repository)


def test_rejects_missing_tracked_file(repository: Path) -> None:
    (repository / "docs/report/guide.md").unlink()
    with pytest.raises(ReportOwnershipError, match="tracked report path is missing"):
        check_report_ownership(repository)


@pytest.mark.parametrize(
    "owner_id,field,value,message",
    [
        ("open-evidence", "role", "unknown", "invalid role"),
        ("reader-pages", "paths", ["docs/report/pending.json"], "non-Markdown"),
        ("analysis/code", "paths", ["docs/report/pending.json"], "non-code"),
        ("analysis/result", "producer_paths", [], "needs producer paths"),
        ("analysis/result", "producer_inputs", ["../outside.csv"], "not a canonical"),
        (
            "analysis/result",
            "producer_inputs",
            ["packages/report_producer.py", "data/source.csv"],
            "sorted and unique",
        ),
        ("source/reference", "verification", "", "verification is missing"),
    ],
)
def test_rejects_invalid_owner_role_or_source(
    repository: Path, owner_id: str, field: str, value: object, message: str
) -> None:
    payload = _inventory(repository)
    _owner(payload, owner_id)[field] = value
    _write_inventory(repository, payload)
    with pytest.raises(ReportOwnershipError, match=message):
        check_report_ownership(repository)

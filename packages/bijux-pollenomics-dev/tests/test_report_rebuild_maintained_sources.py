"""Candidate-byte and role guards for checked-in report sources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import (
    InventoryEntry,
    inventory_reports,
    repository_identity,
)
from bijux_pollenomics_dev.ci.report_rebuild import maintained_sources as sources
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    ReportRebuildError,
    canonical_json_sha256,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import INVENTORY_SCOPE


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        timeout=30,
    )


def _commit(root: Path) -> None:
    _git(
        root,
        "add",
        "--",
        "docs/report",
        "configs/ci/report-ownership.json",
        "producer.py",
        "input.csv",
    )
    _git(
        root,
        "-c",
        "user.name=Bijux Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-q",
        "-m",
        "bind report source fixture",
    )


def _inventory(root: Path, owners: list[dict[str, Any]]) -> None:
    paths = sorted(path for row in owners for path in row["paths"])
    document = {
        "schema_version": "report-output-ownership.v1",
        "root": "docs/report",
        "inventory_scope": INVENTORY_SCOPE,
        "path_count": len(paths),
        "paths_sha256": hashlib.sha256(
            json.dumps(paths, separators=(",", ":")).encode()
        ).hexdigest(),
        "owners": owners,
    }
    path = root / "configs/ci/report-ownership.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def _fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, list[dict[str, Any]]]:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "-q")
    files = {
        "docs/report/source/replay.py": "VALUE = 1\n",
        "docs/report/source/README.md": "# Checked-in account\n",
        "docs/report/source/config.json": '{"bounds": [1, 2], "enabled": true}\n',
        "docs/report/generated/result.md": "generated\n",
        "docs/report/generated/report.json": "{}\n",
        "docs/report/publisher/report.json": "{}\n",
        "docs/report/publisher/README.md": "# Publisher output\n",
        "docs/report/retained/certificate.json": "{}\n",
        "docs/report/method-certification/original-r-reference/reference-bundle/oracle.R": "x <- 1\n",
        "docs/report/unresolved/missing.csv": "missing\n",
        "docs/report/unresolved/README.md": "# Unresolved account\n",
        "producer.py": "VALUE = 1\n",
        "input.csv": "a\n1\n",
    }
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    owners: list[dict[str, Any]] = []

    def owner(identity: str, role: str, paths: list[str]) -> None:
        owners.append(
            {
                "owner_id": identity,
                "role": role,
                "paths": sorted(paths),
                "producer_paths": ["producer.py"] if role == "generated_owner" else [],
                "producer_inputs": ["input.csv"] if role == "generated_owner" else [],
                "verification": "fixture role and source check",
            }
        )

    owner("source-code", "maintained_code", ["docs/report/source/replay.py"])
    owner("source-account", "maintained_editorial", ["docs/report/source/README.md"])
    owner(
        "study-design", "maintained_configuration", ["docs/report/source/config.json"]
    )
    owner(
        "generated",
        "generated_owner",
        ["docs/report/generated/report.json", "docs/report/generated/result.md"],
    )
    owner(
        "publisher",
        "publisher_partition",
        ["docs/report/publisher/README.md", "docs/report/publisher/report.json"],
    )
    owner(
        "retained",
        "retained_source",
        [
            "docs/report/method-certification/original-r-reference/reference-bundle/oracle.R",
            "docs/report/retained/certificate.json",
        ],
    )
    owner(
        "unresolved",
        "unresolved",
        ["docs/report/unresolved/README.md", "docs/report/unresolved/missing.csv"],
    )
    _inventory(root, owners)
    _commit(root)
    monkeypatch.setattr(
        sources,
        "MAINTAINED_ROLE_PATHS",
        {
            "maintained_code": (
                1,
                canonical_json_sha256(["docs/report/source/replay.py"]),
            ),
            "maintained_editorial": (
                1,
                canonical_json_sha256(["docs/report/source/README.md"]),
            ),
            "maintained_configuration": (
                1,
                canonical_json_sha256(["docs/report/source/config.json"]),
            ),
        },
    )
    return root, owners


def _validate(root: Path) -> tuple[tuple[InventoryEntry, ...], dict[str, Any]]:
    tracked = inventory_reports(root / "docs/report", {"volatile_text_rules": []})
    return cast(
        tuple[tuple[InventoryEntry, ...], dict[str, Any]],
        sources.validated_maintained_report_sources(
            root, tracked, expected_repository=repository_identity(root, required=True)
        ),
    )


def test_only_reviewed_maintained_paths_are_candidate_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    entries, evidence = _validate(root)
    assert {entry.path for entry in entries} == {
        "source/replay.py",
        "source/README.md",
        "source/config.json",
    }
    assert len(evidence["inventory"]) == 3
    assert evidence["roles"]["maintained_code"]["path_count"] == 1
    assert evidence["roles"]["maintained_editorial"]["path_count"] == 1
    assert evidence["roles"]["maintained_configuration"]["path_count"] == 1
    assert (
        evidence["repository"]["head_commit"]
        == subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
    )


@pytest.mark.parametrize(
    ("foreign_role", "foreign_path", "maintained_role", "maintained_path"),
    [
        (
            "generated_owner",
            "docs/report/generated/result.md",
            "maintained_editorial",
            "docs/report/source/README.md",
        ),
        (
            "publisher_partition",
            "docs/report/publisher/README.md",
            "maintained_editorial",
            "docs/report/source/README.md",
        ),
        (
            "retained_source",
            "docs/report/method-certification/original-r-reference/reference-bundle/oracle.R",
            "maintained_code",
            "docs/report/source/replay.py",
        ),
        (
            "unresolved",
            "docs/report/unresolved/README.md",
            "maintained_editorial",
            "docs/report/source/README.md",
        ),
        (
            "generated_owner",
            "docs/report/generated/report.json",
            "maintained_configuration",
            "docs/report/source/config.json",
        ),
        (
            "publisher_partition",
            "docs/report/publisher/report.json",
            "maintained_configuration",
            "docs/report/source/config.json",
        ),
        (
            "retained_source",
            "docs/report/retained/certificate.json",
            "maintained_configuration",
            "docs/report/source/config.json",
        ),
    ],
)
def test_other_roles_cannot_be_relabelled_as_maintained(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    foreign_role: str,
    foreign_path: str,
    maintained_role: str,
    maintained_path: str,
) -> None:
    root, owners = _fixture(tmp_path, monkeypatch)
    maintained = next(row for row in owners if row["role"] == maintained_role)
    foreign = next(row for row in owners if row["role"] == foreign_role)
    maintained["paths"] = sorted(
        [
            foreign_path if path == maintained_path else path
            for path in maintained["paths"]
        ]
    )
    foreign["paths"] = sorted(
        [maintained_path if path == foreign_path else path for path in foreign["paths"]]
    )
    _inventory(root, owners)
    _commit(root)
    with pytest.raises(
        ReportRebuildError, match=f"reviewed {maintained_role} path set changed"
    ):
        _validate(root)


def test_uncommitted_edit_and_symlink_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    tracked = inventory_reports(root / "docs/report", {"volatile_text_rules": []})
    identity = repository_identity(root, required=True)
    source = root / "docs/report/source/README.md"
    source.write_text("# Changed account\n", encoding="utf-8")
    with pytest.raises(ReportRebuildError, match="ownership or Git identity failed"):
        sources.validated_maintained_report_sources(
            root, tracked, expected_repository=identity
        )
    source.unlink()
    source.symlink_to(root / "input.csv")
    with pytest.raises(ReportRebuildError, match="ownership or Git identity failed"):
        sources.validated_maintained_report_sources(
            root, tracked, expected_repository=identity
        )


def test_authored_configuration_cannot_revert_to_unresolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, owners = _fixture(tmp_path, monkeypatch)
    next(row for row in owners if row["owner_id"] == "study-design")["role"] = (
        "unresolved"
    )
    _inventory(root, owners)
    _commit(root)
    with pytest.raises(
        ReportRebuildError, match="reviewed maintained_configuration path set changed"
    ):
        _validate(root)


@pytest.mark.parametrize(
    "payload",
    [
        "[]\n",
        "null\n",
        '{"limit": NaN}\n',
        '{"limit": 1e400}\n',
        '{"nested": {"limit": Infinity}}\n',
        '{"nested": {"limit": 1, "limit": 2}}\n',
        '{"broken": true\n',
    ],
)
def test_malformed_maintained_configuration_is_refused_after_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: str
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    (root / "docs/report/source/config.json").write_text(payload, encoding="utf-8")
    _commit(root)
    with pytest.raises(
        ReportRebuildError, match="maintained configuration|format invalid"
    ):
        _validate(root)


def test_unsupported_shell_script_is_not_a_reviewed_code_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, owners = _fixture(tmp_path, monkeypatch)
    path = root / "docs/report/source/script.sh"
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    code = next(row for row in owners if row["role"] == "maintained_code")
    code["paths"] = ["docs/report/source/script.sh"]
    other = next(row for row in owners if row["role"] == "unresolved")
    other["paths"] = sorted(
        [
            "docs/report/source/replay.py",
            "docs/report/unresolved/README.md",
            "docs/report/unresolved/missing.csv",
        ]
    )
    _inventory(root, owners)
    _git(root, "add", "--", "docs/report/source/script.sh")
    _commit(root)
    monkeypatch.setattr(
        sources,
        "MAINTAINED_ROLE_PATHS",
        {
            "maintained_code": (
                1,
                canonical_json_sha256(["docs/report/source/script.sh"]),
            ),
            "maintained_editorial": (
                1,
                canonical_json_sha256(["docs/report/source/README.md"]),
            ),
        },
    )
    with pytest.raises(
        ReportRebuildError, match="unsupported maintained_code source format"
    ):
        _validate(root)


def test_incomplete_tracked_inventory_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    tracked = inventory_reports(root / "docs/report", {"volatile_text_rules": []})
    incomplete = tuple(entry for entry in tracked if entry.path != "source/README.md")
    with pytest.raises(ReportRebuildError, match="maintained source inventory differs"):
        sources.validated_maintained_report_sources(
            root,
            incomplete,
            expected_repository=repository_identity(root, required=True),
        )


def test_wrong_git_candidate_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    tracked = inventory_reports(root / "docs/report", {"volatile_text_rules": []})
    with pytest.raises(ReportRebuildError, match="Git candidate changed"):
        sources.validated_maintained_report_sources(
            root, tracked, expected_repository={"mode": "git", "head_commit": "wrong"}
        )


def test_reviewed_source_path_sets_match_the_current_repository() -> None:
    repository = Path(__file__).resolve().parents[3]
    inventory = json.loads(
        (repository / "configs/ci/report-ownership.json").read_text(encoding="utf-8")
    )
    for role, (count, digest) in sources.MAINTAINED_ROLE_PATHS.items():
        paths = sorted(
            path
            for owner in inventory["owners"]
            if owner["role"] == role
            for path in owner["paths"]
        )
        assert len(paths) == count, role
        assert canonical_json_sha256(paths) == digest, role

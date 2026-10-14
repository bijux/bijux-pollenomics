"""Guard the portal namespace and Markdown identity against stale publication."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.presentation import publish_report_portal
from bijux_pollenomics_dev.docs.report_portal_check import (
    ReportPortalCheckError,
    check_report_portal,
    main,
)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    report_root = tmp_path / "docs/report"
    (report_root / "regional-account").mkdir(parents=True)
    (report_root / "regional-account/README.md").write_text(
        "# Regional account\n\nA bounded description of this report surface.\n",
        encoding="utf-8",
    )
    (report_root / "machine.csv").write_text("id,value\na,1\n", encoding="utf-8")
    publish_report_portal(report_root)
    return tmp_path


def _payload(repository: Path, name: str) -> dict[str, object]:
    value: object = json.loads(
        (repository / "docs/report" / name).read_text(encoding="utf-8")
    )
    assert isinstance(value, dict)
    return value


def _write_payload(repository: Path, name: str, payload: dict[str, object]) -> None:
    (repository / "docs/report" / name).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def test_checks_real_producer_population_and_cli(
    repository: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = check_report_portal(repository)
    assert result.report_file_count == result.registered_surface_count + 4
    assert result.excluded_metadata_count == 4
    assert result.markdown_page_count > 1
    assert main(["--repository", str(repository)]) == 0
    emitted = json.loads(capsys.readouterr().out)
    assert emitted["registered_surface_count"] == result.registered_surface_count


def test_rejects_modified_markdown(repository: Path) -> None:
    with (repository / "docs/report/regional-account/README.md").open(
        "a", encoding="utf-8"
    ) as stream:
        stream.write("A changed interpretation.\n")
    with pytest.raises(
        ReportPortalCheckError, match="registry content_sha256 is stale"
    ):
        check_report_portal(repository)


def test_rejects_unregistered_and_missing_files(repository: Path) -> None:
    extra = repository / "docs/report/unregistered.json"
    extra.write_text("{}", encoding="utf-8")
    with pytest.raises(ReportPortalCheckError, match="registry population differs"):
        check_report_portal(repository)
    extra.unlink()
    (repository / "docs/report/machine.csv").unlink()
    with pytest.raises(ReportPortalCheckError, match="registry path is missing"):
        check_report_portal(repository)


def test_rejects_duplicate_registry_path(repository: Path) -> None:
    payload = _payload(repository, "report_surface_registry.json")
    rows = payload["rows"]
    assert isinstance(rows, list)
    rows.append(dict(rows[0]))
    payload["surface_count"] = len(rows)
    _write_payload(repository, "report_surface_registry.json", payload)
    with pytest.raises(ReportPortalCheckError, match="duplicate registry path"):
        check_report_portal(repository)


def test_rejects_incomplete_or_stale_quality_coverage(repository: Path) -> None:
    payload = _payload(repository, "report_narrative_quality_review.json")
    rows = payload["rows"]
    assert isinstance(rows, list)
    row = rows.pop()
    assert isinstance(row, dict)
    payload["page_count"] = len(rows)
    _write_payload(repository, "report_narrative_quality_review.json", payload)
    with pytest.raises(
        ReportPortalCheckError, match="quality Markdown coverage is incomplete"
    ):
        check_report_portal(repository)

    rows.append(row)
    row["content_sha256"] = "0" * 64
    payload["page_count"] = len(rows)
    _write_payload(repository, "report_narrative_quality_review.json", payload)
    with pytest.raises(ReportPortalCheckError, match="quality content_sha256 is stale"):
        check_report_portal(repository)


def test_rejects_wrong_exclusion_and_aggregate_count(repository: Path) -> None:
    payload = _payload(repository, "report_surface_registry.json")
    payload["excluded_metadata_paths"] = ["docs/report/report_surface_registry.json"]
    _write_payload(repository, "report_surface_registry.json", payload)
    with pytest.raises(ReportPortalCheckError, match="four exact portal metadata"):
        check_report_portal(repository)

    payload["excluded_metadata_paths"] = sorted(
        [
            "docs/report/report_narrative_quality_review.json",
            "docs/report/report_narrative_quality_review.md",
            "docs/report/report_surface_registry.json",
            "docs/report/report_surface_registry.md",
        ]
    )
    payload["surface_count"] = -1
    _write_payload(repository, "report_surface_registry.json", payload)
    with pytest.raises(ReportPortalCheckError, match="non-negative integer"):
        check_report_portal(repository)


def test_rejects_hash_ownership_on_machine_output(repository: Path) -> None:
    payload = _payload(repository, "report_surface_registry.json")
    rows = payload["rows"]
    assert isinstance(rows, list)
    machine = next(
        row for row in rows if row["repository_path"].endswith("machine.csv")
    )
    machine["content_sha256"] = "0" * 64
    _write_payload(repository, "report_surface_registry.json", payload)
    with pytest.raises(
        ReportPortalCheckError, match="non-Markdown registry row owns content hash"
    ):
        check_report_portal(repository)


def test_rejects_symlink_and_path_escape(repository: Path) -> None:
    outside = repository / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    link = repository / "docs/report/outside.md"
    link.symlink_to(outside)
    with pytest.raises(ReportPortalCheckError, match="not regular"):
        check_report_portal(repository)
    link.unlink()

    payload = _payload(repository, "report_surface_registry.json")
    rows = payload["rows"]
    assert isinstance(rows, list)
    rows[0]["repository_path"] = "docs/report/../outside.md"
    _write_payload(repository, "report_surface_registry.json", payload)
    with pytest.raises(ReportPortalCheckError, match="not canonical"):
        check_report_portal(repository)


def test_rejects_symlinked_docs_ancestor_outside_repository(repository: Path) -> None:
    outside = repository.parent / f"{repository.name}-outside-docs"
    (repository / "docs").rename(outside)
    (repository / "docs").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ReportPortalCheckError, match="report root escapes repository"):
        check_report_portal(repository)


def test_rejects_symlinked_docs_ancestor_within_repository(repository: Path) -> None:
    relocated = repository / "relocated-docs"
    (repository / "docs").rename(relocated)
    (repository / "docs").symlink_to(relocated, target_is_directory=True)

    with pytest.raises(
        ReportPortalCheckError, match="ancestor is not a real directory"
    ):
        check_report_portal(repository)

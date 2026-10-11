"""Exercise deterministic ESSD intake, discrepancy, and refusal behavior."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import stat
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest

from bijux_pollenomics_dev.essd_reproduction import (
    build_reconciliation,
    publish_reconciliation,
)
from bijux_pollenomics_dev.essd_reproduction import (
    reconcile as reconciliation,
)

_EXAMPLE_SITES = {
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


def _json(value: object) -> bytes:
    return json.dumps(value).encode()


def _candidate(
    path: Path,
    *,
    corrupt: bool = False,
    unlisted: bool = False,
    unsafe: bool = False,
    duplicate: bool = False,
    encrypted: bool = False,
    high_ratio: bool = False,
    symlink: bool = False,
    actual_r_parity_executed: bool = False,
    original_1128_raw_records_collected: bool = False,
) -> None:
    members = {
        "docs/SCIENTIFIC_AUDIT.md": b"The paper/Table 1 uses 12 PFTs. The PANGAEA description states 11.\n",
        "docs/INTEGRATION.md": b"Keep this candidate standalone pending gates.\n",
        "verification/delivery-scope.json": _json(
            {
                "offline_tests": {"passed": 87, "skipped": 1},
                "actual_R_parity_executed": actual_r_parity_executed,
                "original_1128_raw_records_collected": (
                    original_1128_raw_records_collected
                ),
            }
        ),
        "verification/environment.json": _json(
            {"packages": {"pytest": "9.0.2"}, "Rscript_path": None}
        ),
        "pyproject.toml": b'[project]\n[project.optional-dependencies]\ntest=["pytest>=8,<9"]\n',
        "tests/test_science.py": b"def test_table1_inventory(): pass\n",
        "tests/test_products.py": (
            b"import pytest\n@pytest.mark.integration\n"
            b"def test_actual_R_parity_optional(): pass\n"
            b"def test_published_25_windows(): pass\n"
        ),
    }
    if high_ratio:
        members["payload/high-ratio.txt"] = b"x" * 100_000
    if symlink:
        members["payload/link"] = b"../../outside"
    if unsafe:
        members["../outside.txt"] = b"unsafe\n"
    sums = "".join(
        f"{hashlib.sha256(content).hexdigest()}  {name}\n"
        for name, content in sorted(members.items())
    ).encode()
    members["SHA256SUMS"] = sums
    if corrupt:
        members["tests/test_science.py"] += b"# changed after manifest\n"
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, content in members.items():
            info = ZipInfo(f"candidate/{name}")
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            file_type = stat.S_IFLNK if name == "payload/link" else stat.S_IFREG
            info.external_attr = (file_type | 0o600) << 16
            archive.writestr(info, content)
        if unlisted:
            info = ZipInfo("candidate/unlisted.txt")
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(info, b"not in SHA256SUMS\n")
        if duplicate:
            info = ZipInfo("candidate/tests/test_science.py")
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(info, b"duplicate\n")
    if encrypted:
        archive_content = bytearray(path.read_bytes())
        for signature, flag_offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            offset = archive_content.find(signature)
            assert offset >= 0
            start = offset + flag_offset
            flags = int.from_bytes(archive_content[start : start + 2], "little") | 0x1
            archive_content[start : start + 2] = flags.to_bytes(2, "little")
        path.write_bytes(archive_content)


def _repository(
    root: Path,
    *,
    trailing_header: str | None = None,
    vegetation_accuracy: str = "not_evaluated",
) -> None:
    method_profile = root / "docs/report/publication-replay/landclim-method-profile"
    comparison = method_profile / "reference"
    comparison.mkdir(parents=True)
    (comparison / "report.json").write_text(
        json.dumps(
            {
                "profile": "landclimii-2016-release-source-v1",
                "coverage": "two_author_example_grids_only_not_full_1128_record_study",
                "independent_measured_vegetation_accuracy": vegetation_accuracy,
                "grids": [
                    {
                        "grid_id": grid_id,
                        "sites": len(site_ids),
                        "bins": 25,
                        "taxa": 31,
                        "passed": True,
                        "checks": {
                            "regional_cover": {"passed": True},
                            "regional_se": {"passed": True},
                            "site_counts_equal": True,
                            "sites": [
                                {
                                    "site_id": site_id,
                                    "cover": {"passed": True},
                                    "se": {"passed": True},
                                }
                                for site_id in site_ids
                            ],
                        },
                    }
                    for grid_id, site_ids in _EXAMPLE_SITES.items()
                ],
            }
        )
    )
    (method_profile / "report.json").write_text(
        json.dumps(
            {
                "scope": "two_retained_author_example_grids_method_and_input_identity",
                "example_grid_sites": {"512": 9, "562": 8},
                "inputs": [
                    {
                        "path": "docs/report/publication-replay/landclim-method-profile/reference/report.json",
                        "sha256": hashlib.sha256(
                            (comparison / "report.json").read_bytes()
                        ).hexdigest(),
                    }
                ],
                "pft_evidence": {
                    "paper_prose_claim": 12,
                    "parameter_table_nonblank_codes": 12,
                },
                "admission": {
                    "private_input_redistribution_rights_cleared": False,
                    "whole_paper_reproduction": False,
                },
            }
        )
    )
    reexecution = root / "docs/report/publication-replay/landclim-example-reexecution"
    reexecution.mkdir(parents=True)
    (reexecution / "report.json").write_text(
        json.dumps(
            {
                "passed": True,
                "native_comparison": json.loads(
                    (comparison / "report.json").read_text()
                ),
                "admission": {
                    "private_input_redistribution_rights_cleared": False,
                    "full_study_reproduction": False,
                },
            }
        )
    )
    raw = root / "data/landclim/raw"
    raw.mkdir(parents=True)
    taxonomy_pfts = [
        "TBE1",
        "TBE2",
        "IBE",
        "MTBE",
        "TSE",
        "MTSE",
        "IBS",
        "TBS",
        "TSD",
        "LSE",
        "GL",
        "AL",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=[
            "Land-cover types (LCTs)",
            "PFT",
            "PFT definition",
            "",
            "Plant taxa/Pollen-morphological types",
            "FSP (m/s)",
            "PPE (SD)",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    taxa = [f"taxon_{index:02d}" for index in range(31)]
    for index, taxon in enumerate(taxa):
        pft = taxonomy_pfts[index % len(taxonomy_pfts)]
        writer.writerow(
            {
                "Land-cover types (LCTs)": "Evergreen trees (ET)" if index == 0 else "",
                "PFT": pft,
                "PFT definition": f"definition {pft}",
                "Plant taxa/Pollen-morphological types": taxon,
                "FSP (m/s)": "0.1",
                "PPE (SD)": "1 (0.1)",
            }
        )
    (raw / "landclim_ii_taxa_pft_ppe_fsp_values.csv").write_text(stream.getvalue())
    output_header = [
        "LCGRID_ID",
        "lonDD",
        "latDD",
        *taxa,
        *taxonomy_pfts,
        "ISTS",
        "ET",
    ]
    if trailing_header is not None:
        output_header.append(trailing_header)
    with ZipFile(raw / "landclim_ii_reveals_results.zip", "w") as archive:
        for name in ("means/TW1.csv", "standarderrors/TW1.csv"):
            archive.writestr(name, ",".join(output_header) + "\n")


def test_reconciliation_preserves_bounded_truth(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate)
    _repository(repository)

    products = build_reconciliation(candidate, repository)

    receipt = products["archive-receipt.json"]
    assert isinstance(receipt, dict)
    assert receipt["internal_checksums_match"] is True
    envelope = receipt["archive_envelope"]
    assert isinstance(envelope, dict)
    assert envelope["regular_file_members_only"] is True
    assert envelope["encrypted_members_allowed"] is False
    discrepancy = products["pft-discrepancy.json"]
    assert isinstance(discrepancy, dict)
    assert discrepancy["resolution_status"].startswith("unresolved_")
    observations = discrepancy["observations"]
    assert isinstance(observations, list)
    assert [row["pft_count"] for row in observations] == [12, 11, 12, 13]
    assert (
        observations[0]["source_status"] == "candidate_prose_not_pinned_primary_source"
    )
    assert (
        observations[1]["source_status"] == "candidate_prose_not_pinned_primary_source"
    )
    assert observations[-1]["unmatched_headers"] == ["ISTS"]
    profiles = products["publication-profile-crosswalk.json"]
    assert isinstance(profiles, dict)
    assert profiles["whole_paper_reproduction_certified"] is False
    report = products["scientific-scope-report.md"]
    assert isinstance(report, bytes)
    assert b"original 1,128 pollen records" in report
    assert b"not an exhaustive repository-wide absence proof" in report
    assert b"actual-R parity was not executed" in report
    assert b"Rights remain component-specific" in report


def test_publication_is_deterministic_and_refuses_replacement(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate)
    _repository(repository)
    first = tmp_path / "first"
    second = tmp_path / "second"

    publish_reconciliation(candidate, repository, first)
    publish_reconciliation(candidate, repository, second)

    assert sorted(path.name for path in first.iterdir()) == [
        "archive-receipt.json",
        "candidate-test-inventory.json",
        "input-availability.csv",
        "pft-discrepancy.json",
        "publication-profile-crosswalk.json",
        "scientific-scope-report.md",
    ]
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    with pytest.raises(FileExistsError, match="Refusing to replace"):
        publish_reconciliation(candidate, repository, first)


def test_tampered_candidate_is_rejected(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate, corrupt=True)
    _repository(repository)

    with pytest.raises(ValueError, match="checksum failure"):
        build_reconciliation(candidate, repository)


def test_unlisted_candidate_member_is_rejected(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate, unlisted=True)
    _repository(repository)

    with pytest.raises(ValueError, match="manifest does not cover archive exactly"):
        build_reconciliation(candidate, repository)


def test_unsafe_and_duplicate_candidate_members_are_rejected(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _repository(repository)
    unsafe = tmp_path / "unsafe.zip"
    _candidate(unsafe, unsafe=True)
    with pytest.raises(ValueError, match="unsafe member names"):
        build_reconciliation(unsafe, repository)

    duplicate = tmp_path / "duplicate.zip"
    with pytest.warns(UserWarning, match="Duplicate name"):
        _candidate(duplicate, duplicate=True)
    with pytest.raises(ValueError, match="duplicate member names"):
        build_reconciliation(duplicate, repository)


def test_candidate_archive_bounds_are_enforced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate)
    _repository(repository)
    limits = [
        ("_MAX_ARCHIVE_BYTES", "archive byte limit"),
        ("_MAX_MEMBER_COUNT", "member count limit"),
        ("_MAX_MEMBER_BYTES", "member exceeds byte limit"),
        ("_MAX_EXPANDED_BYTES", "total expanded byte limit"),
    ]
    for limit_name, message in limits:
        with monkeypatch.context() as patch:
            patch.setattr(reconciliation, limit_name, 1)
            with pytest.raises(ValueError, match=message):
                build_reconciliation(candidate, repository)


def test_high_ratio_encrypted_and_nonregular_members_are_rejected(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    _repository(repository)

    high_ratio = tmp_path / "high-ratio.zip"
    _candidate(high_ratio, high_ratio=True)
    with pytest.raises(ValueError, match="compression ratio limit"):
        build_reconciliation(high_ratio, repository)

    encrypted = tmp_path / "encrypted.zip"
    _candidate(encrypted, encrypted=True)
    with pytest.raises(ValueError, match="encrypted"):
        build_reconciliation(encrypted, repository)

    symlink = tmp_path / "symlink.zip"
    _candidate(symlink, symlink=True)
    with pytest.raises(ValueError, match="not_regular_file"):
        build_reconciliation(symlink, repository)


def test_example_grid_scope_is_fail_closed(
    tmp_path: Path,
) -> None:
    mutations = [
        ("extra_grid", "exactly two grid objects"),
        ("wrong_count", "wrong site count"),
        ("wrong_dimensions", "wrong dimensions"),
        ("grid_failed", "did not pass"),
        ("counts_differ", "site counts differ"),
        ("wrong_identity", "site identity differs"),
        ("regional_failed", "regional_cover did not pass"),
        ("site_failed", "site check did not pass"),
    ]
    for mutation, message in mutations:
        case = tmp_path / mutation
        candidate = case / "candidate.zip"
        repository = case / "repository"
        case.mkdir()
        _candidate(candidate)
        _repository(repository)
        report_path = (
            repository
            / "docs/report/publication-replay/landclim-method-profile/reference/report.json"
        )
        report = json.loads(report_path.read_text())
        first = report["grids"][0]
        if mutation == "extra_grid":
            report["grids"].append(dict(first))
        elif mutation == "wrong_count":
            first["sites"] = 10
        elif mutation == "wrong_dimensions":
            first["bins"] = 24
        elif mutation == "grid_failed":
            first["passed"] = False
        elif mutation == "counts_differ":
            first["checks"]["site_counts_equal"] = False
        elif mutation == "wrong_identity":
            first["checks"]["sites"][0]["site_id"] = "NOT_BROADOWN"
        elif mutation == "regional_failed":
            first["checks"]["regional_cover"]["passed"] = False
        elif mutation == "site_failed":
            first["checks"]["sites"][0]["cover"]["passed"] = False
        else:
            raise AssertionError(f"Unhandled mutation: {mutation}")
        report_path.write_text(json.dumps(report))
        method_path = (
            repository
            / "docs/report/publication-replay/landclim-method-profile/report.json"
        )
        method_report = json.loads(method_path.read_text())
        method_report["inputs"][0]["sha256"] = hashlib.sha256(
            report_path.read_bytes()
        ).hexdigest()
        method_path.write_text(json.dumps(method_report))

        with pytest.raises(ValueError, match=message):
            build_reconciliation(candidate, repository)


def test_unknown_trailing_published_header_is_not_classified_as_pft(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate)
    _repository(repository, trailing_header="UNKNOWN_GROUP")

    with pytest.raises(ValueError, match="unknown trailing grouped headers"):
        build_reconciliation(candidate, repository)


def test_unsupported_candidate_completion_claim_is_rejected(
    tmp_path: Path,
) -> None:
    for name, actual_r, original_records in (
        ("actual-r", True, False),
        ("original-records", False, True),
    ):
        case = tmp_path / name
        candidate = case / "candidate.zip"
        repository = case / "repository"
        case.mkdir()
        _candidate(
            candidate,
            actual_r_parity_executed=actual_r,
            original_1128_raw_records_collected=original_records,
        )
        _repository(repository)

        with pytest.raises(ValueError, match="lacks independently pinned evidence"):
            build_reconciliation(candidate, repository)


def test_independent_vegetation_accuracy_overclaim_is_rejected(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate)
    _repository(repository, vegetation_accuracy="passed")

    with pytest.raises(ValueError, match="must not claim independent measured"):
        build_reconciliation(candidate, repository)


def test_governed_redistribution_claim_cannot_be_promoted(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate)
    _repository(repository)
    method_report = (
        repository
        / "docs/report/publication-replay/landclim-method-profile/report.json"
    )
    report = json.loads(method_report.read_text())
    report["admission"]["private_input_redistribution_rights_cleared"] = True
    method_report.write_text(json.dumps(report))

    with pytest.raises(ValueError, match="Governed source rights"):
        build_reconciliation(candidate, repository)


def test_governed_comparison_must_match_method_and_fresh_replay(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.zip"
    repository = tmp_path / "repository"
    _candidate(candidate)
    _repository(repository)
    method_path = (
        repository
        / "docs/report/publication-replay/landclim-method-profile/report.json"
    )
    original_method = method_path.read_text()
    method_report = json.loads(original_method)
    method_report["inputs"][0]["sha256"] = "0" * 64
    method_path.write_text(json.dumps(method_report))
    with pytest.raises(ValueError, match="bind its comparison bytes"):
        build_reconciliation(candidate, repository)

    method_path.write_text(original_method)
    replay_path = (
        repository
        / "docs/report/publication-replay/landclim-example-reexecution/report.json"
    )
    replay = json.loads(replay_path.read_text())
    replay["native_comparison"]["grids"][0]["available_site_bins"] = 0
    replay_path.write_text(json.dumps(replay))
    with pytest.raises(ValueError, match="comparison grids disagree"):
        build_reconciliation(candidate, repository)

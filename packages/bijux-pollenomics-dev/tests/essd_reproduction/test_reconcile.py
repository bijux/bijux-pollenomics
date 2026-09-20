"""Exercise deterministic ESSD intake, discrepancy, and refusal behavior."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from bijux_pollenomics_dev.essd_reproduction import (
    build_reconciliation,
    publish_reconciliation,
)


def _json(value: object) -> bytes:
    return json.dumps(value).encode()


def _candidate(
    path: Path,
    *,
    corrupt: bool = False,
    unlisted: bool = False,
    unsafe: bool = False,
    duplicate: bool = False,
) -> None:
    members = {
        "docs/SCIENTIFIC_AUDIT.md": b"The paper/Table 1 uses 12 PFTs. The PANGAEA description states 11.\n",
        "docs/INTEGRATION.md": b"Keep this candidate standalone pending gates.\n",
        "verification/delivery-scope.json": _json(
            {
                "offline_tests": {"passed": 87, "skipped": 1},
                "actual_R_parity_executed": False,
                "original_1128_raw_records_collected": False,
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
            archive.writestr(f"candidate/{name}", content)
        if unlisted:
            archive.writestr("candidate/unlisted.txt", b"not in SHA256SUMS\n")
        if duplicate:
            archive.writestr("candidate/tests/test_science.py", b"duplicate\n")


def _repository(root: Path) -> None:
    comparison = root / "artifacts/v2/engine/publication-check-004/comparison"
    comparison.mkdir(parents=True)
    (comparison / "report.json").write_text(
        json.dumps(
            {
                "profile": "landclimii-2016-release-source-v1",
                "coverage": "two_author_example_grids_only_not_full_1128_record_study",
                "independent_measured_vegetation_accuracy": "not_evaluated",
                "grids": [
                    {"grid_id": "512", "sites": 9},
                    {"grid_id": "562", "sites": 8},
                ],
            }
        )
    )
    design = root / "artifacts/v2/engine/multisite-audit"
    design.mkdir(parents=True)
    (design / "IMPLEMENTATION-DESIGN.md").write_text(
        "The article reports 1128 pollen records, 31 taxa, 12 PFTs.\n"
    )
    rights = root / "artifacts/v2/engine/publication-license-audit"
    rights.mkdir(parents=True)
    (rights / "DISPOSITION.md").write_text(
        "release and host redistribution are **not cleared**\n"
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
    for index, pft in enumerate(taxonomy_pfts):
        writer.writerow(
            {
                "Land-cover types (LCTs)": "Evergreen trees (ET)" if index == 0 else "",
                "PFT": pft,
                "PFT definition": f"definition {pft}",
                "Plant taxa/Pollen-morphological types": f"taxon {pft}",
                "FSP (m/s)": "0.1",
                "PPE (SD)": "1 (0.1)",
            }
        )
    (raw / "landclim_ii_taxa_pft_ppe_fsp_values.csv").write_text(stream.getvalue())
    output_header = ["LCGRID_ID", "lonDD", "latDD", *taxonomy_pfts, "ISTS", "ET"]
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
    discrepancy = products["pft-discrepancy.json"]
    assert isinstance(discrepancy, dict)
    assert discrepancy["resolution_status"].startswith("unresolved_")
    observations = discrepancy["observations"]
    assert isinstance(observations, list)
    assert [row["pft_count"] for row in observations] == [12, 11, 12, 13]
    assert observations[-1]["unmatched_headers"] == ["ISTS"]
    profiles = products["publication-profile-crosswalk.json"]
    assert isinstance(profiles, dict)
    assert profiles["whole_paper_reproduction_certified"] is False
    report = products["scientific-scope-report.md"]
    assert isinstance(report, bytes)
    assert b"original 1,128 pollen records" in report
    assert b"actual-R parity was not executed" in report
    assert b"redistribution rights remain unresolved" in report


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
    assert {
        path.name: path.read_bytes() for path in first.iterdir()
    } == {path.name: path.read_bytes() for path in second.iterdir()}
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

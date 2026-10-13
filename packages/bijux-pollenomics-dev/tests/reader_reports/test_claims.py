import copy
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize(
    "corruption", ["missing", "duplicate", "hash", "category", "evidence", "packet"]
)
def test_claim_accounting_refuses_incomplete_or_stale_evidence(corruption: str) -> None:
    spec = importlib.util.spec_from_file_location(
        "scientific_claims", ROOT / "reports/needed/verify-claims.py"
    )
    assert spec is not None and spec.loader is not None
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    with (ROOT / "reports/needed/report-claims.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    with (ROOT / "reports/needed/source-requests.csv").open() as handle:
        packets = {r["packet_id"] for r in csv.DictReader(handle)}
    verifier.validate(ROOT, rows, packets)
    rows = copy.deepcopy(rows)
    if corruption == "missing":
        rows.pop()
    elif corruption == "duplicate":
        rows[0] = rows[1]
    elif corruption == "hash":
        rows[0]["source_report_sha256"] = "0" * 64
    elif corruption == "category":
        rows[0]["cause_categories"] = "none within stated scope|qualified review"
    elif corruption == "evidence":
        rows[0]["retained_evidence_paths"] = "../outside-evidence"
    else:
        rows[0]["packet_reference"] = "unknown-request"
    with pytest.raises(ValueError):
        verifier.validate(ROOT, rows, packets)


@pytest.mark.parametrize(
    "corruption", ["duplicate", "missing", "escape", "non_markdown", "foreign_surface"]
)
def test_supplemental_account_authority_refuses_unowned_sources(
    tmp_path: Path, corruption: str
) -> None:
    import json

    spec = importlib.util.spec_from_file_location(
        "scientific_account_authority", ROOT / "reports/needed/verify-claims.py"
    )
    assert spec is not None and spec.loader is not None
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    primary = tmp_path / "reports/science/primary.md"
    primary.parent.mkdir(parents=True)
    primary.write_text("Primary research account")
    supplemental = tmp_path / "docs/report/aggregate/README.md"
    supplemental.parent.mkdir(parents=True)
    supplemental.write_text("Supplemental primary scientific account")
    authority = tmp_path / "reports/needed/claim-account-sources.json"
    authority.parent.mkdir(parents=True)
    source = "docs/report/aggregate/README.md"

    def save(paths: list[str]) -> None:
        authority.write_text(
            json.dumps({"schema_version": 1, "supplemental_report_paths": paths})
        )

    save([source])
    assert verifier.expected_report_paths(tmp_path) == {
        "reports/science/primary.md",
        source,
    }
    if corruption == "duplicate":
        paths = [source, source]
    elif corruption == "missing":
        paths = ["docs/report/missing.md"]
    elif corruption == "escape":
        paths = ["docs/report/../../../outside.md"]
    elif corruption == "non_markdown":
        other = tmp_path / "docs/report/aggregate/report.json"
        other.write_text("{}")
        paths = ["docs/report/aggregate/report.json"]
    else:
        paths = ["reports/science/primary.md"]
    save(paths)
    with pytest.raises(ValueError):
        verifier.expected_report_paths(tmp_path)

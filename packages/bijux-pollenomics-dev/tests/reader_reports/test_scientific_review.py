import copy
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize(
    "corruption",
    ["duplicate", "source", "register", "qualification", "packet", "decision"],
)
def test_review_matrix_refuses_stale_or_unsupported_records(corruption: str) -> None:
    spec = importlib.util.spec_from_file_location(
        "scientific_review", ROOT / "reports/needed/verify-review.py"
    )
    assert spec is not None and spec.loader is not None
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    with (ROOT / "reports/needed/scientific-review.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    with (ROOT / "reports/needed/source-requests.csv").open() as handle:
        packets = {r["packet_id"] for r in csv.DictReader(handle)}
    verifier.validate(ROOT, rows, packets)
    rows = copy.deepcopy(rows)
    if corruption == "duplicate":
        rows.append(rows[0])
    elif corruption == "source":
        rows[0]["claim_report_sha256"] = "0" * 64
    elif corruption == "register":
        rows[0]["claim_register_sha256"] = "0" * 64
    elif corruption == "qualification":
        rows[0].pop("qualification_and_independence")
    elif corruption == "packet":
        rows[0]["source_request_ids"] = "unknown-packet"
    else:
        rows[0]["review_decision"] = "accepted_scoped"
    with pytest.raises(ValueError):
        verifier.validate(ROOT, rows, packets)

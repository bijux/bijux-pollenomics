"""Check that SEAD handoff summaries retain relation and country identities."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPOSITORY = Path(__file__).resolve().parents[5]
SOURCE = REPOSITORY / "docs/report/source-relations/sead/verify_handoff_accounting.py"
RUN = "sead-full-evidence-39bfff6a-ce80714e"
JOINS = REPOSITORY / f"data/sead/raw/acquisitions/{RUN}/reconciliation/joins.json"
REPORT = REPOSITORY / "docs/report/source-relations/sead"


def _verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sead_handoff_verifier", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_source_handoff_retains_refused_admission() -> None:
    result = _verifier().verify(REPOSITORY)
    assert result["join_edges"] == 86
    assert result["assigned_sites"] == {"DK": 59, "FI": 40, "NO": 45, "SE": 1925}
    assert result["eligible_ecological_events"] == 0
    assert result["release_status"] == "refused"


def test_join_projection_matches_original_capture_and_refuses_edge_substitution() -> (
    None
):
    verifier = _verifier()
    source = json.loads(JOINS.read_bytes())
    public = json.loads((REPORT / "public-custody/report.json").read_bytes())
    assert verifier._source_join_projection(source) == public["join_edges"]

    changed = [dict(row) for row in public["join_edges"]]
    changed[1]["edge"] = changed[0]["edge"]
    assert changed != verifier._source_join_projection(source)
    changed_source = {"edges": [dict(row) for row in source["edges"]]}
    changed_source["edges"][1]["edge"] = changed_source["edges"][0]["edge"]
    with pytest.raises(ValueError, match="join identities"):
        verifier._source_join_projection(changed_source)


def test_verify_refuses_rebound_public_join_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _verifier()
    public_path = "docs/report/source-relations/sead/public-custody/report.json"
    chronology_path = (
        "docs/report/source-relations/sead/chronology-country-accounting/report.json"
    )
    map_path = "docs/report/source-relations/sead/map-candidate/report.json"
    documents: dict[str, dict[str, Any]] = {
        path: json.loads((REPOSITORY / path).read_bytes())
        for path in (public_path, chronology_path, map_path)
    }
    public = documents[public_path]
    public["join_edges"][1]["edge"] = public["join_edges"][0]["edge"]

    def digest(path: str) -> str:
        return hashlib.sha256(
            json.dumps(documents[path], sort_keys=True).encode()
        ).hexdigest()

    documents[chronology_path]["input_sha256"][public_path] = digest(public_path)
    documents[map_path]["source_sha256"][chronology_path] = digest(chronology_path)
    original_document: Callable[[Path, str], dict[str, Any]] = verifier._document
    original_sha: Callable[[Path], str] = verifier._sha

    def document(root: Path, relative: str) -> dict[str, Any]:
        if relative in documents:
            return documents[relative]
        return original_document(root, relative)

    def sha(path: Path) -> str:
        relative = path.relative_to(REPOSITORY).as_posix()
        if relative in (public_path, chronology_path):
            return digest(relative)
        return original_sha(path)

    monkeypatch.setattr(verifier, "_document", document)
    monkeypatch.setattr(verifier, "_sha", sha)
    with pytest.raises(ValueError, match="source join projection"):
        verifier.verify(REPOSITORY)


def test_country_rows_refuse_duplicate_missing_and_boolean_count() -> None:
    verifier = _verifier()
    report = json.loads((REPORT / "country-coverage/report.json").read_bytes())
    rows = report["country_rows"]
    assert set(
        verifier._checked_country_rows(rows, set(verifier.COUNTRIES), "coverage")
    ) == set(verifier.COUNTRIES)
    for changed in (rows + [dict(rows[0])], rows[:-1], rows[:-1] + [dict(rows[0])]):
        with pytest.raises(
            ValueError, match="country (population differs|identities differ)"
        ):
            verifier._checked_country_rows(changed, set(verifier.COUNTRIES), "coverage")
    with pytest.raises(ValueError, match="nonnegative integer"):
        verifier._count(True, "assigned sites")


def test_chronology_country_denominators_reconcile_current_source() -> None:
    verifier = _verifier()
    report = json.loads(
        (REPORT / "chronology-country-accounting/report.json").read_bytes()
    )
    rows = verifier._checked_country_rows(
        report["country_site_denominators"], set(verifier.COUNTRIES), "chronology"
    )
    for code, row in rows.items():
        assert row["claim_count"] == report["country_counts"][code]
        assert (
            row["claim_count"] == report["propagation_refusal_counts_by_country"][code]
        )
        assert (
            row["claim_site_count"] + row["assigned_sites_without_claim_count"]
            == row["assigned_site_count"]
        )
    assert (
        sum(row["claim_site_count"] for row in rows.values())
        == report["claim_site_count"]
    )

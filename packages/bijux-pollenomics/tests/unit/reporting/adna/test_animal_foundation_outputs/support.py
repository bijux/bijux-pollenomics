"""Shared repository paths for animal foundation reporting tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.support.repository import REPOSITORY_ROOT


class AnimalFoundationOutputsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = REPOSITORY_ROOT
        self.data_root = self.repo_root / "data"
        self.report_root = self.repo_root / "docs" / "report"
        self.docs_root = self.repo_root / "docs"


def sample_row(
    *,
    stable_token: str,
    locality_token: str,
    locality_text: str,
    project_accession: str,
    master_id: str | None = None,
) -> dict[str, object]:
    return {
        "identity": {"stable_token": stable_token},
        "master_id": stable_token if master_id is None else master_id,
        "locality_identity": {
            "stable_token": locality_token,
            "locality_text": locality_text,
        },
        "project_accession": project_accession,
        "paper_doi": "10.1000/test",
        "paper_url": "https://doi.org/10.1000/test",
        "supplementary_source": "supplementary/test.csv",
        "sample_basis": "project_accession_anchor",
        "inclusion_status": "site_curated",
        "chronology": {
            "original_text": "1000-1200 BP",
            "time_start_bp": 1000,
            "time_end_bp": 1200,
        },
        "coordinates": {
            "latitude_text": "59.0",
            "longitude_text": "18.0",
            "confidence": "approximate",
        },
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from bijux_pollenomics.cli import main
from bijux_pollenomics.config import DEFAULT_AADR_VERSION
from tests.support.aadr import AADR_HEADER


def test_report_multi_country_map_emits_mixed_species_scientific_review_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "data" / "aadr" / DEFAULT_AADR_VERSION / "ho"
        root.mkdir(parents=True, exist_ok=True)
        (root / f"{DEFAULT_AADR_VERSION}_HO_public.anno").write_text(
            "\n".join(
                [
                    AADR_HEADER,
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tHO\tF",
                    "NO1\tNO1\tNorway_Group\tOslo\tNorway\t59.9139\t10.7522\tPaperB\t2021\t600 BCE\t2550\tHO\tM",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        exit_code = main(
            [
                "report-multi-country-map",
                "Sweden",
                "Norway",
                "--aadr-root",
                str(Path(tmp) / "data" / "aadr"),
                "--output-root",
                str(Path(tmp) / "docs" / "report"),
                "--context-root",
                str(Path(tmp) / "data"),
            ]
        )

        atlas_root = Path(tmp) / "docs" / "report" / "nordic-atlas"
        payload = json.loads(
            (atlas_root / "nordic-atlas_scientific_review.json").read_text(
                encoding="utf-8"
            )
        )

    species_rows = {row["species_latin_name"] for row in payload["country_coverage"]}
    assert exit_code == 0
    assert payload["schema_version"] == "scientific-review-surface.v3"
    assert "Homo sapiens" in species_rows
    assert "Ovis aries" in species_rows
    assert "animal_coordinate_review" in payload

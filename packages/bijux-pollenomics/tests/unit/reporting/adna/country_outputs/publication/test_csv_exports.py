from __future__ import annotations

import csv
from pathlib import Path

from bijux_pollenomics.reporting.adna.country_outputs.models import (
    CountryAnimalOutputBundle,
)
from bijux_pollenomics.reporting.adna.country_outputs.publication.csv_exports import (
    write_country_animal_samples_csv,
)


def test_animal_sample_csv_preserves_product_scope(tmp_path: Path) -> None:
    output = tmp_path / "animal-samples.csv"
    bundle = CountryAnimalOutputBundle(
        country="Sweden",
        version="v66",
        generated_on="2026-09-06",
        sample_rows=(
            {
                "country": "Sweden",
                "species_latin_name": "Bos primigenius",
                "species_common_name": "aurochs",
                "animal_scope": "wild_or_progenitor_context",
            },
        ),
        species_rows=(),
        localities=(),
        citations=(),
        warnings=(),
        evidence_quality_summary={},
        traceability_summary={},
    )

    write_country_animal_samples_csv(output, bundle)

    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["animal_scope"] == "wild_or_progenitor_context"

"""Regenerate the actual Nordic human and animal country data contracts."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from bijux_pollenomics.reporting.aadr.samples import load_country_samples
from bijux_pollenomics.reporting.adna.country_outputs.publication.csv_exports import (
    write_country_animal_samples_csv,
)
from bijux_pollenomics.reporting.adna.country_outputs.service import (
    build_country_animal_output_bundle,
)
from bijux_pollenomics.reporting.rendering.record_exports import write_samples_csv


def main() -> None:
    source, output = map(Path, sys.argv[1:])
    if output.exists():
        raise ValueError("Preserve existing actual lifecycle output")
    output.mkdir(parents=True)
    record: list[dict[str, Any]] = []
    for country in ("Denmark", "Finland", "Norway", "Sweden"):
        slug = country.lower()
        expected_dir = source / "docs/report/countries" / slug
        samples, dataset_counts = load_country_samples(
            source / "data/aadr/v66", country
        )
        write_samples_csv(output / f"{slug}_aadr.csv", samples)
        expected: dict[str, Any] = json.loads(
            (expected_dir / f"{slug}_animal_adna_v66_summary.json").read_text()
        )
        bundle = build_country_animal_output_bundle(
            data_root=source / "data",
            country=country,
            version="v66",
            generated_on=expected["generated_on"],
        )
        write_country_animal_samples_csv(output / f"{slug}_animal.csv", bundle)
        (output / f"{slug}_animal.json").write_text(
            json.dumps(bundle.as_dict(), ensure_ascii=False, indent=2) + "\n"
        )
        record.append(
            {
                "country": country,
                "human_samples": len(samples),
                "human_dataset_row_counts": dict(dataset_counts),
                "animal_samples": len(bundle.sample_rows),
                "animal_localities": len(bundle.localities),
                "animal_warnings": len(bundle.warnings),
            }
        )
    (output / "producer-account.json").write_text(
        json.dumps(
            {
                "countries": record,
                "scope": "Actual source normalization and country data publication contracts; no map, browser, LRA, genotype or propagation network inference.",
                "scientific_admission": False,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()

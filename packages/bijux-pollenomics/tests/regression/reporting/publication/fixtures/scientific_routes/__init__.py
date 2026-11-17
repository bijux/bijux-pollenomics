"""Bind generated publication mechanics to independently frozen fixture bytes."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    Route,
    parse_routes,
)

PACKET = Path(__file__).parent
SCOPE = "publication-fixture-scope.md"
EXPECTED = {
    "animal_atlas_exclusion_report.json": "029f8d5d4bda59c8eb3cf30205388c211accc3725eba0aa128a4b5aa2a295da7",
    "animal_output_honesty.json": "79b6881cad2baa56c2278427765b766b6f85655c49db9d58a64c0cf0e7503132",
}


def expected_bytes(name: str) -> bytes:
    """Read a declared fixture, never infer authority from a publication candidate."""
    if name not in EXPECTED:
        raise ValueError("Unknown generated evidence fixture")
    raw = (PACKET / name).read_bytes()
    if sha256(raw).hexdigest() != EXPECTED[name]:
        raise ValueError("Frozen generated evidence fixture changed")
    return raw


def frozen_routes() -> dict[str, Route]:
    """Declare two mechanical routes without inheriting production scientific claims."""
    fields = {
        "supported_claim": "The declared synthetic release can publish its owned files.",
        "unsupported_claim": "No animal coverage, empirical or scientific qualification.",
        "actual_verification_performed": "Real route validation against frozen fixture bytes.",
        "remaining_input_or_review": "Actual source review and production routes are separate.",
        "cause_category": "Generated mechanical publication fixture only.",
        "consequence": "Only this declared synthetic evidence epoch may pass these routes.",
        "precise_next_acceptance_route": "Validate the unchanged fixture authority and ownership.",
        "negative_or_refused_result": "Changed bytes and foreign owner paths must refuse.",
        "matched_denominator": "Declared synthetic annotation inputs; no actual animal evidence.",
    }
    rows = []
    for name, digest in EXPECTED.items():
        expected_bytes(name)
        rows.append(
            {
                "reader_path": "docs/report/" + name.removesuffix(".json") + ".md",
                "canonical_accounts": [{"report_path": "docs/report/" + SCOPE}],
                "scope_reason": "Generated publication mechanics, not production route coverage.",
                "qualification": {
                    "fields": fields,
                    "evidence_pins": [
                        {"path": "docs/report/" + name, "sha256": digest}
                    ],
                },
            }
        )
    return parse_routes(json.dumps({"schema_version": 2, "routes": rows}))


@contextmanager
def generated_route_authority(output_root: Path) -> Iterator[dict[str, Route]]:
    """Freeze the fixture authority before invoking the tested publisher."""
    routes = frozen_routes()
    scope = output_root / SCOPE
    scope.parent.mkdir(parents=True, exist_ok=True)
    scope.write_bytes((PACKET / "scope.md").read_bytes())
    with patch(
        "bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts.load_routes",
        return_value=routes,
    ):
        yield routes


def write_generated_readers(root: Path) -> None:
    """Build only the declared synthetic route inputs inside an owned test root."""
    scope = root / SCOPE
    scope.parent.mkdir(parents=True, exist_ok=True)
    scope.write_bytes((PACKET / "scope.md").read_bytes())
    for name in EXPECTED:
        (root / name).write_bytes(expected_bytes(name))
        (root / (name.removesuffix(".json") + ".md")).write_text(
            "# Generated mechanical publication reader\n", encoding="utf-8"
        )


def assert_generated_route_views(root: Path) -> None:
    """Check both actual rendered fixture routes and their fixed evidence bytes."""
    for name, digest in EXPECTED.items():
        assert (root / name).read_bytes() == expected_bytes(name)
        reader = root / (name.removesuffix(".json") + ".md")
        rendered = reader.read_text(encoding="utf-8")
        assert (
            "Generated publication mechanics, not production route coverage."
            in rendered
        )
        assert f"SHA-256 `{digest}`" in rendered

"""Compare authored products only after authenticating their managed reader scope."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    parse_routes,
    render_route,
)
from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
    FIELDS,
)

ROOT = Path(__file__).resolve().parents[5]
FAMILY = Path("docs/report/pollen-reconstruction/author-buffered-pollen")


def load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "buffered_reader_comparison", ROOT / FAMILY / "replay.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def example(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[ModuleType, Path, dict[str, Any], Path, Path]:
    module = load()
    repository = tmp_path / "repo"
    family = repository / FAMILY
    family.mkdir(parents=True)
    generated = tmp_path / "generated"
    generated.mkdir()
    prose = b"# Conditional fixture\n\nRetained140/184 bins.\n"
    payload = b'{"scored":140,"observed":184}\n'
    for base in (family, generated):
        (base / "report.json").write_bytes(payload)
    account = repository / "reports/science/account.md"
    account.parent.mkdir(parents=True)
    account.write_bytes(b"# Source-free primary fixture\n")
    record: dict[str, Any] = {
        "reader_path": (FAMILY / "REPORT.md").as_posix(),
        "scope_reason": "Source-free custody fixture with no new fits.",
        "canonical_accounts": [
            {
                "report_path": "reports/science/account.md",
            }
        ],
        "qualification": {
            "fields": {key: f"Scoped fixture {label}." for key, label in FIELDS},
            "evidence_pins": [
                {
                    "path": (FAMILY / "report.json").as_posix(),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            ],
        },
    }
    routes = parse_routes(json.dumps({"schema_version": 2, "routes": [record]}))
    tracked = family / "REPORT.md"
    tracked.write_bytes(render_route(prose, routes[record["reader_path"]]))
    (generated / "REPORT.md").write_bytes(prose)
    monkeypatch.setattr(module, "FAMILY", family)
    monkeypatch.setattr(module, "REPOSITORY", repository)
    monkeypatch.setattr(module, "load_routes", lambda: routes)
    manifest = {
        "files": [
            {"path": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for rel, raw in [("REPORT.md", prose), ("report.json", payload)]
        ]
    }
    return module, generated, manifest, tracked, family / "report.json"


def test_source_produced_prose_matches_verified_tracked_reader(
    example: tuple[ModuleType, Path, dict[str, Any], Path, Path],
) -> None:
    module, generated, manifest, _, _ = example
    assert module._compare(generated, manifest) == []


@pytest.mark.parametrize(
    "change", ["managed_claim", "trailing_html", "malformed", "evidence"]
)
def test_malformed_or_changed_reader_cannot_be_peeled(
    example: tuple[ModuleType, Path, dict[str, Any], Path, Path], change: str
) -> None:
    module, generated, manifest, tracked, evidence = example
    if change == "managed_claim":
        tracked.write_bytes(
            tracked.read_bytes().replace(b"Scoped fixture", b"Approved")
        )
    elif change == "trailing_html":
        tracked.write_bytes(tracked.read_bytes() + b"<script>unqualified</script>")
    elif change == "malformed":
        tracked.write_bytes(tracked.read_bytes().replace(b"route:end", b"missing:end"))
    else:
        evidence.write_bytes(b'{"scored":184,"observed":184}\n')
    with pytest.raises(ValueError):
        module._compare(generated, manifest)


def test_numeric_payload_changes_stay_in_the_comparison(
    example: tuple[ModuleType, Path, dict[str, Any], Path, Path],
) -> None:
    module, generated, manifest, _, _ = example
    (generated / "report.json").write_bytes(b'{"scored":141,"observed":184}\n')
    differences = module._compare(generated, manifest)
    assert any("manifest hash differs: report.json" in value for value in differences)
    assert "tracked bytes differ: report.json" in differences


def test_undeclared_managed_reader_refuses(
    example: tuple[ModuleType, Path, dict[str, Any], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module, generated, manifest, _, _ = example
    monkeypatch.setattr(module, "load_routes", dict)
    with pytest.raises(ValueError, match="undeclared managed account"):
        module._compare(generated, manifest)


def test_changed_authored_reader_stays_in_the_raw_comparison(
    example: tuple[ModuleType, Path, dict[str, Any], Path, Path],
) -> None:
    module, generated, manifest, tracked, _ = example
    tracked.write_bytes(tracked.read_bytes().replace(b"140/184", b"184/184"))
    assert module._compare(generated, manifest) == ["tracked bytes differ: REPORT.md"]


@pytest.mark.parametrize(
    "mutation",
    [
        "old_schema",
        "account_hash",
        "authored_hash",
        "reader_escape",
        "account_escape",
        "duplicate_route",
        "duplicate_account",
        "self_account",
        "evidence_escape",
        "self_evidence",
        "missing_field",
        "missing_raw_hash",
    ],
)
def test_core_authority_parser_retains_scope_and_identity_refusals(
    mutation: str,
) -> None:
    reader = "docs/report/fixture/README.md"
    record: dict[str, Any] = {
        "reader_path": reader,
        "scope_reason": "Explicit constructed reader scope.",
        "canonical_accounts": [{"report_path": "reports/science/fixture.md"}],
        "qualification": {
            "fields": {key: f"Constructed {label}." for key, label in FIELDS},
            "evidence_pins": [
                {"path": "docs/report/fixture/report.json", "sha256": "a" * 64}
            ],
        },
    }
    authority: dict[str, Any] = {"schema_version": 2, "routes": [record]}
    if mutation == "old_schema":
        authority["schema_version"] = 1
    elif mutation == "account_hash":
        record["canonical_accounts"][0]["source_sha256"] = "a" * 64
    elif mutation == "authored_hash":
        record["qualification"]["authored_reader_sha256"] = "a" * 64
    elif mutation == "reader_escape":
        record["reader_path"] = "docs/report/../outside.md"
    elif mutation == "account_escape":
        record["canonical_accounts"][0]["report_path"] = "../outside.md"
    elif mutation == "duplicate_route":
        authority["routes"].append(record)
    elif mutation == "duplicate_account":
        record["canonical_accounts"].append(record["canonical_accounts"][0])
    elif mutation == "self_account":
        record["canonical_accounts"][0]["report_path"] = reader
    elif mutation == "evidence_escape":
        record["qualification"]["evidence_pins"][0]["path"] = "../outside.json"
    elif mutation == "self_evidence":
        record["qualification"]["evidence_pins"] = [{"path": reader}]
    elif mutation == "missing_field":
        record["qualification"]["fields"].pop(FIELDS[0][0])
    else:
        record["qualification"]["evidence_pins"][0].pop("sha256")
    with pytest.raises(ValueError):
        parse_routes(json.dumps(authority))

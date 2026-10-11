"""Bind original Nordic count accounting to qualified custody and absent outputs."""

from __future__ import annotations

from collections.abc import Callable
import csv
from dataclasses import dataclass, replace
import hashlib
import io
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import (
    SCHEMA as AUTHOR_SCHEMA,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
    require_mapping,
)
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import LOOKUP
from bijux_pollenomics_dev.source_completion.pollen_taxonomy import (
    author_nordic_mass as account,
)
from bijux_pollenomics_dev.source_completion.pollen_taxonomy.author_mass import (
    DESCRIPTOR,
    SOURCE_ID,
)


@dataclass
class Packet:
    repository: Path
    root: Path
    output: Path
    qualified: QualifiedReportSources
    report: JsonObject
    calls: list[str]
    publish: Callable[[Path, Path, Path], JsonObject]


def _sites(report: JsonObject) -> list[JsonObject]:
    value = report["sites"]
    assert isinstance(value, list)
    return [require_mapping(row, "site fixture") for row in value]


def _write(report: JsonObject, output: Path) -> None:
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    stream = io.StringIO(newline="")
    sites = _sites(report) if isinstance(report.get("sites"), list) else []
    fields = list(sites[0]) if sites else ["country"]
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(sites)
    (output / "sites.csv").write_bytes(stream.getvalue().encode("utf-8"))


@pytest.fixture
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Packet:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    descriptor = repository / DESCRIPTOR
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text(
        json.dumps({"schema_version": AUTHOR_SCHEMA, "source_id": SOURCE_ID}),
        encoding="utf-8",
    )
    for relative in account.REPOSITORY_INPUTS:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"repository fixture source\n")
    root = tmp_path / "store"
    directory = root / SOURCE_ID
    lookup = directory / LOOKUP
    lookup.parent.mkdir(parents=True)
    lookup.write_bytes(b"qualified fixture lookup\n")
    inputs = {
        DESCRIPTOR.as_posix(): descriptor,
        f"external/{SOURCE_ID}/{LOOKUP}": lookup,
    }
    qualified = QualifiedReportSources(
        directory, inputs, hashlib.sha256(descriptor.read_bytes()).hexdigest()
    )
    retained = (
        Path(__file__).resolve().parents[5]
        / "docs/report/regions/nordic/author-taxonomy-mass/report.json"
    )
    report = require_mapping(
        json.loads(retained.read_bytes()), "retained Nordic count fixture"
    )
    calls: list[str] = []

    def qualify(
        repo: Path, source_root: Path, source_descriptor: Path
    ) -> QualifiedReportSources:
        assert (repo, source_root, source_descriptor) == (repository, root, DESCRIPTOR)
        calls.append("qualify")
        return qualified

    def publish(repo: Path, source_directory: Path, output: Path) -> JsonObject:
        assert repo == repository and source_directory == directory
        assert (
            output.parent == repository / "artifacts"
            and output != repository / "artifacts/result"
        )
        calls.append("produce")
        _write(report, output)
        return report

    monkeypatch.setattr(account, "validated_external_report_sources", qualify)
    monkeypatch.setattr(account, "publish", publish)
    return Packet(
        repository,
        root,
        repository / "artifacts/result",
        qualified,
        report,
        calls,
        publish,
    )


def _run(packet: Packet) -> JsonObject:
    return account.run(packet.repository, packet.root, DESCRIPTOR, packet.output)


def _unpublished(packet: Packet) -> None:
    assert not packet.output.exists()
    assert list((packet.repository / "artifacts").iterdir()) == []


def test_original_source_account_bytes_publish_after_two_qualifications(
    packet: Packet,
) -> None:
    before = {name: path.read_bytes() for name, path in packet.qualified.inputs.items()}
    assert _run(packet) == packet.report
    assert packet.calls == ["qualify", "produce", "qualify"]
    assert {path.name for path in packet.output.iterdir()} == {
        "report.json",
        "sites.csv",
    }
    assert {
        name: path.read_bytes() for name, path in packet.qualified.inputs.items()
    } == before
    retained = (
        Path(__file__).resolve().parents[5]
        / "docs/report/regions/nordic/author-taxonomy-mass"
    )
    for name in ("report.json", "sites.csv"):
        assert (packet.output / name).read_bytes() == (retained / name).read_bytes()
    assert packet.report["selected_site_count"] == 81
    assert packet.report["selected_sample_count"] == 5432
    assert packet.report["selected_pollen_observation_rows"] == 116727
    assert packet.report["lra_admitted_samples"] == 0


@pytest.mark.parametrize(
    "placement", ["existing", "escape", "traversal", "symlink-leaf", "symlink-parent"]
)
def test_occupied_or_unconfined_output_refuses_before_source(
    packet: Packet, placement: str
) -> None:
    output = packet.output
    if placement == "existing":
        output.mkdir()
        (output / "user.txt").write_bytes(b"preserve")
    elif placement == "escape":
        packet.output = packet.repository.parent / "escaped"
    elif placement == "traversal":
        packet.output = output.parent / ".." / "artifacts/result"
    elif placement == "symlink-leaf":
        output.symlink_to(packet.root, target_is_directory=True)
    else:
        parent = output.parent / "linked"
        parent.symlink_to(packet.root, target_is_directory=True)
        packet.output = parent / "result"
    with pytest.raises(ReportRebuildError):
        _run(packet)
    assert packet.calls == []
    if placement == "existing":
        assert (output / "user.txt").read_bytes() == b"preserve"


@pytest.mark.parametrize("index", range(32))
@pytest.mark.parametrize("failure", ["missing", "symlink"])
def test_every_repository_input_refuses_missing_or_linked_before_producer(
    packet: Packet, index: int, failure: str
) -> None:
    source = packet.repository / account.REPOSITORY_INPUTS[index]
    source.unlink()
    if failure == "symlink":
        source.symlink_to(packet.qualified.directory / LOOKUP)
    with pytest.raises(ReportRebuildError):
        _run(packet)
    assert packet.calls == ["qualify"]
    _unpublished(packet)


@pytest.mark.parametrize("failure", ["schema", "source-id", "descriptor", "lookup"])
def test_wrong_snapshot_contract_refuses_before_producer(
    packet: Packet, failure: str
) -> None:
    if failure in {"schema", "source-id"}:
        descriptor = packet.repository / DESCRIPTOR
        value = require_mapping(
            json.loads(descriptor.read_bytes()), "descriptor fixture"
        )
        value["schema_version" if failure == "schema" else "source_id"] = "wrong"
        descriptor.write_text(json.dumps(value), encoding="utf-8")
    else:
        name = (
            DESCRIPTOR.as_posix()
            if failure == "descriptor"
            else f"external/{SOURCE_ID}/{LOOKUP}"
        )
        packet.qualified.inputs.pop(name)
    with pytest.raises(ReportRebuildError):
        _run(packet)
    assert packet.calls == ["qualify"]
    _unpublished(packet)


def test_full_qualifier_refusal_never_runs_original_consumer(
    packet: Packet, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_args: object) -> QualifiedReportSources:
        raise ReportRebuildError("pinned author snapshot differs")

    monkeypatch.setattr(account, "validated_external_report_sources", refuse)
    with pytest.raises(ReportRebuildError, match="pinned author snapshot differs"):
        _run(packet)
    assert packet.calls == []
    _unpublished(packet)


@pytest.mark.parametrize("index", range(34))
def test_every_input_mutation_during_consumer_refuses_publication(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, index: int
) -> None:
    inputs = [
        *packet.qualified.inputs.values(),
        *(packet.repository / p for p in account.REPOSITORY_INPUTS),
    ]

    def mutate(repo: Path, directory: Path, output: Path) -> JsonObject:
        result = packet.publish(repo, directory, output)
        with inputs[index].open("ab") as stream:
            stream.write(b" ")
        return result

    monkeypatch.setattr(account, "publish", mutate)
    with pytest.raises(ReportRebuildError, match="inputs changed"):
        _run(packet)
    _unpublished(packet)


@pytest.mark.parametrize("field", ["directory", "inputs", "descriptor_sha256"])
def test_qualified_declaration_mutation_refuses_publication(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    count = 0

    def qualify(*_args: object) -> QualifiedReportSources:
        nonlocal count
        count += 1
        if count == 1:
            return packet.qualified
        if field == "directory":
            return replace(packet.qualified, directory=packet.root)
        if field == "inputs":
            return replace(packet.qualified, inputs={})
        return replace(packet.qualified, descriptor_sha256="0" * 64)

    monkeypatch.setattr(account, "validated_external_report_sources", qualify)
    with pytest.raises(ReportRebuildError, match="inputs changed"):
        _run(packet)
    _unpublished(packet)


@pytest.mark.parametrize(
    "failure",
    [
        "exception",
        "extra",
        "missing",
        "json-drift",
        "csv-drift",
        "linked-json",
        "linked-csv",
        "appeared",
    ],
)
def test_bad_products_or_occupied_destination_preserve_user_output(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    def mutate(repo: Path, directory: Path, output: Path) -> JsonObject:
        report = packet.publish(repo, directory, output)
        if failure == "exception":
            raise ValueError("original producer refused")
        if failure == "extra":
            (output / "extra.json").write_bytes(b"{}")
        elif failure == "missing":
            (output / "sites.csv").unlink()
        elif failure.endswith("drift"):
            (
                output / ("report.json" if failure == "json-drift" else "sites.csv")
            ).write_bytes(b"different")
        elif failure.startswith("linked"):
            target = output / (
                "report.json" if failure == "linked-json" else "sites.csv"
            )
            target.unlink()
            target.symlink_to(packet.qualified.directory / LOOKUP)
        else:
            packet.output.mkdir()
            (packet.output / "user.txt").write_bytes(b"preserve")
        return report

    monkeypatch.setattr(account, "publish", mutate)
    with pytest.raises((ValueError, ReportRebuildError)):
        _run(packet)
    if failure == "appeared":
        assert (packet.output / "user.txt").read_bytes() == b"preserve"
        assert {p.name for p in packet.output.parent.iterdir()} == {"result"}
    else:
        _unpublished(packet)


@pytest.mark.parametrize(
    "failure",
    [
        "schema",
        "scope",
        "interpretation",
        "samples",
        "observations",
        "admission",
        "bool-admission",
        "missing-samples",
        "non-list-sites",
        "site-coverage",
        "site-order",
        "site-identity",
        "site-fields",
        "negative-mass",
        "mass",
        "site-admission",
        "targets",
        "fraction",
        "country-order",
        "country-mass",
        "variants",
    ],
)
def test_scope_mass_and_admission_drift_refuse_original_account(
    packet: Packet, failure: str
) -> None:
    sites = _sites(packet.report)
    countries_value = packet.report["countries"]
    assert isinstance(countries_value, list)
    countries = [require_mapping(row, "country fixture") for row in countries_value]
    if failure in {"schema", "scope", "interpretation"}:
        packet.report[
            {
                "schema": "schema_version",
                "scope": "scope",
                "interpretation": "interpretation",
            }[failure]
        ] = "wrong"
    elif failure in {"samples", "observations"}:
        packet.report[
            "selected_sample_count"
            if failure == "samples"
            else "selected_pollen_observation_rows"
        ] = 1
    elif failure in {"admission", "bool-admission"}:
        packet.report["lra_admitted_samples"] = 1 if failure == "admission" else False
    elif failure == "missing-samples":
        packet.report.pop("selected_sample_count")
    elif failure == "non-list-sites":
        packet.report["sites"] = {}
    elif failure == "site-coverage":
        sites.pop()
    elif failure == "site-order":
        sites.reverse()
    elif failure == "site-identity":
        sites[1]["country"] = sites[0]["country"]
        sites[1]["site_id"] = sites[0]["site_id"]
    elif failure == "site-fields":
        sites[0]["extra"] = 1
    elif failure in {"negative-mass", "mass"}:
        sites[0]["all_native_nisp"] = -1 if failure == "negative-mass" else 1
    elif failure == "site-admission":
        sites[0]["lra_admitted_samples"] = 1
    elif failure == "targets":
        sites[0]["author_targets_present"] = 32
    elif failure == "fraction":
        sites[0]["assigned_fraction"] = 0
    elif failure == "country-order":
        countries.reverse()
    elif failure == "country-mass":
        countries[0]["unmapped_nisp"] = 0
    else:
        countries[0]["size_variant_candidate_nisp"] = 1
    if failure != "non-list-sites":
        packet.report["sites"] = sites
    packet.report["countries"] = countries
    with pytest.raises(ReportRebuildError):
        _run(packet)
    _unpublished(packet)


def test_cli_passes_explicit_qualified_source_and_confined_destination(
    packet: Packet,
) -> None:
    assert (
        account.main(
            [
                "--repository",
                str(packet.repository),
                "--source-root",
                str(packet.root),
                "--source-descriptor",
                DESCRIPTOR.as_posix(),
                "--output",
                str(packet.output),
            ]
        )
        == 0
    )
    assert packet.calls == ["qualify", "produce", "qualify"]

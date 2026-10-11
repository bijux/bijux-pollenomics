"""Own retained matrices and fixture-only preparation/qualification callbacks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import (
    SCHEMA as AUTHOR_SCHEMA,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    require_mapping,
)
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import LOOKUP
from bijux_pollenomics_dev.source_completion.nordic import (
    author_target_preparation as account,
)
from bijux_pollenomics_dev.source_completion.nordic_author_target_pollen import (
    AUTHOR_MASS,
    NORDIC,
)
from bijux_pollenomics_dev.source_completion.pollen_taxonomy.author_mass import (
    DESCRIPTOR,
    SOURCE_ID,
)


@dataclass
class Packet:
    """Own source identities and callbacks for one author-preparation fixture."""

    repository: Path
    root: Path
    output: Path
    qualified: QualifiedReportSources
    manifest: JsonObject
    products: dict[str, bytes]
    calls: list[str]
    prepare: Callable[[Path, Path, Path], None]


def _write_manifest(manifest: JsonObject, output: Path) -> None:
    (output / "input-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Packet:
    """Build a qualified author-preparation fixture with retained products."""
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
        path.write_bytes(b"repository preparation fixture\n")
    root = tmp_path / "store"
    directory = root / SOURCE_ID
    lookup = directory / LOOKUP
    lookup.parent.mkdir(parents=True)
    lookup.write_bytes(b"qualified fixture source lookup\n")
    qualified = QualifiedReportSources(
        directory,
        {DESCRIPTOR.as_posix(): descriptor, f"external/{SOURCE_ID}/{LOOKUP}": lookup},
        hashlib.sha256(descriptor.read_bytes()).hexdigest(),
    )
    retained = (
        Path(__file__).resolve().parents[6]
        / "docs/report/regions/nordic/author-target-pollen"
    )
    manifest = require_mapping(
        json.loads((retained / "input-manifest.json").read_bytes()),
        "retained source receipt fixture",
    )
    for field, path in (
        ("direct_manifest_sha256", repository / NORDIC / "manifest.json"),
        ("author_mass_report_sha256", repository / AUTHOR_MASS),
        ("author_lookup_sha256", lookup),
    ):
        manifest[field] = hashlib.sha256(path.read_bytes()).hexdigest()
    products = {
        relative: (retained / relative).read_bytes() for relative in account.PRODUCTS
    }
    calls: list[str] = []

    def qualify(
        repo: Path, source_root: Path, source_descriptor: Path
    ) -> QualifiedReportSources:
        assert (repo, source_root, source_descriptor) == (repository, root, DESCRIPTOR)
        calls.append("qualify")
        return qualified

    def prepare(repo: Path, source_directory: Path, output: Path) -> None:
        assert repo == repository and source_directory == directory
        assert (
            not output.exists()
            and output.name == "source-products"
            and output.parent.name.startswith(".result.")
        )
        calls.append("prepare")
        output.mkdir()
        for relative, data in products.items():
            path = output / relative
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
        _write_manifest(manifest, output)

    monkeypatch.setattr(account, "validated_external_report_sources", qualify)
    monkeypatch.setattr(account, "prepare", prepare)
    return Packet(
        repository,
        root,
        repository / "artifacts/result",
        qualified,
        manifest,
        products,
        calls,
        prepare,
    )


def _run(packet: Packet) -> JsonObject:
    return account.run(packet.repository, packet.root, DESCRIPTOR, packet.output)


def _unpublished(packet: Packet) -> None:
    assert not packet.output.exists()
    assert list((packet.repository / "artifacts").iterdir()) == []


def _mutate_product(
    packet: Packet, relative: str, mutate: Callable[[JsonObject], None]
) -> None:
    payload = require_mapping(
        json.loads(gzip.decompress(packet.products[relative])), "source product fixture"
    )
    mutate(payload)
    data = gzip.compress(
        (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
        mtime=0,
    )
    packet.products[relative] = data
    hashes = require_mapping(
        packet.manifest["produced_file_sha256"], "fixture product hashes"
    )
    hashes[relative] = hashlib.sha256(data).hexdigest()

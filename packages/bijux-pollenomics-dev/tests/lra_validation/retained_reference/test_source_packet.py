"""Qualify exact retained source bytes without building cases or running native R."""

import json
import os
from pathlib import Path
import shutil
import sys

import pytest

from bijux_pollenomics_dev.lra_validation.retained_reference import source_packet
from bijux_pollenomics_dev.lra_validation.retained_reference.identity import (
    authenticate_bundle,
)

_REPOSITORY = Path(__file__).resolve().parents[5]


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    destination = root / source_packet.PACKET
    destination.parent.mkdir(parents=True)
    shutil.copytree(_REPOSITORY / source_packet.PACKET, destination)
    return root


def test_exact_recovered_source_packet_has_distinct_executed_authority(
    repository: Path,
) -> None:
    accepted = source_packet.authenticate_repository_reference(repository)
    assert accepted["certificate_sha256"] == (
        "9560a9eb36259a4f665f61ba18de108193eb1d4e864f751640a392737501410e"
    )
    assert accepted["source_commit"] == "10fe3c1ed008651ad843e9dc42a31241fd16b2ed"
    assert len(accepted["files"]) == 143
    assert accepted["required_profiles"] == {
        "core_source_compatibility": 25,
        "prospective_optimized_love": 18,
        "source_domains_corrected_forward": 23,
    }
    assert accepted["retained_qualification"]["current_linux_or_R_execution"] is False
    assert (
        accepted["retained_qualification"]["original_host_supervision_restored"]
        is False
    )
    assert accepted["historical_boundary"]["historical_products_reclassified"] is False
    assert accepted["historical_boundary"]["numerical_parity_claim"] is False
    bundle = source_packet.repository_reference_bundle(repository)
    certificate = json.loads((bundle / "certificate.json").read_bytes())
    assert len(certificate["source_files"]) == 1925
    assert len(certificate["tracked_git_blobs"]) == 1925
    assert set(certificate["source_files"]) == set(certificate["tracked_git_blobs"])
    assert len(certificate["generated_source_files"]) == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "vector",
        "certificate",
        "missing",
        "extra",
        "manifest",
        "recovery",
        "extra-packet",
    ],
)
def test_unqualified_packet_refuses(repository: Path, mutation: str) -> None:
    packet = repository / source_packet.PACKET
    bundle = packet / "reference-bundle"
    selected = bundle / "oracle/C0007.csv"
    if mutation == "vector":
        selected.write_bytes(selected.read_bytes() + b"numeric,9\n")
    elif mutation == "certificate":
        (bundle / "certificate.json").write_text("{}")
    elif mutation == "missing":
        selected.unlink()
    elif mutation == "extra":
        (bundle / "unqualified.csv").write_text("kind,value\nnumeric,1\n")
    elif mutation == "manifest":
        (packet / "source.json").write_text("{}")
    elif mutation == "recovery":
        (packet / "recovery.json").write_text("{}")
    else:
        (packet / "unqualified.json").write_text("{}")
    with pytest.raises((ValueError, FileNotFoundError)):
        source_packet.authenticate_repository_reference(repository)


@pytest.mark.parametrize("alias", ["root", "bundle", "member", "hardlink"])
def test_packet_physical_aliases_refuse(repository: Path, alias: str) -> None:
    packet = repository / source_packet.PACKET
    bundle = packet / "reference-bundle"
    selected = bundle / "oracle/C0007.csv"
    if alias == "hardlink":
        os.link(selected, repository / "shared-inode")
    else:
        path = packet if alias == "root" else bundle if alias == "bundle" else selected
        moved = repository / "unqualified-storage"
        path.rename(moved)
        path.symlink_to(moved, target_is_directory=moved.is_dir())
    with pytest.raises(ValueError, match="regular|confined|independent"):
        source_packet.authenticate_repository_reference(repository)


def test_historical_distinction_never_becomes_parity(repository: Path) -> None:
    packet = repository / source_packet.PACKET
    distinction = json.loads((packet / "historical-distinction.json").read_bytes())
    assert distinction["historical_owned_count"] == 137
    assert distinction["comparison_counts"] == {
        "EQUAL": 112,
        "DIFFERENT": 23,
        "ABSENT_IN_RECOVERED": 2,
    }
    changed = [r for r in distinction["members"] if r["comparison"] == "DIFFERENT"]
    native = [r for r in changed if r["relative"].endswith(".csv")]
    assert len(native) == 14
    assert all(
        r["csv_semantics"]["historical_rows_including_header"]
        == r["csv_semantics"]["recovered_rows_including_header"]
        and r["csv_semantics"]["changed_row_count"] > 0
        for r in native
    )
    assert len([r for r in changed if r["relative"].endswith((".npy", ".npz"))]) == 3
    assert len(changed) - len(native) - 3 == 6


def test_cli_default_selection_preserves_explicit_bundle_override(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.lra_validation.retained_reference import __main__ as cli

    observed: list[tuple[Path, Path, Path]] = []

    def observe_replay(root: Path, bundle: Path, output: Path) -> dict[str, str]:
        observed.append((root, bundle, output))
        return {"status": "passed"}

    monkeypatch.setattr(cli, "replay", observe_replay)
    output = repository / "never-written.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "retained-reference",
            "--repository",
            str(repository),
            "--output",
            str(output),
        ],
    )
    assert cli.main() == 0
    assert observed[-1][1] == repository / source_packet.PACKET / "reference-bundle"
    explicit = repository / "explicit"
    monkeypatch.setattr(sys, "argv", [*sys.argv, "--bundle", str(explicit)])
    assert cli.main() == 0
    assert observed[-1][1] == explicit
    assert not output.exists()


@pytest.mark.parametrize("mutation", ["authority", "vector", "hardlink"])
def test_packet_change_during_authentication_refuses(
    repository: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    original = authenticate_bundle
    calls = 0

    def captured_then_changed(bundle: Path) -> dict[str, object]:
        nonlocal calls
        accepted = original(bundle)
        calls += 1
        if calls == 1:
            if mutation == "authority":
                (bundle.parent / "recovery.json").write_text("{}")
            elif mutation == "vector":
                with (bundle / "oracle/C0007.csv").open("ab") as stream:
                    stream.write(b"numeric,9\n")
            else:
                os.link(bundle / "oracle/C0007.csv", repository / "shared-inode")
        return accepted

    monkeypatch.setattr(source_packet, "authenticate_bundle", captured_then_changed)
    with pytest.raises(ValueError):
        source_packet.authenticate_repository_reference(repository)

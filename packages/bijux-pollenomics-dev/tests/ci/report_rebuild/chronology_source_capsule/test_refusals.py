"""Keep descriptor, physical, Git and generated-byte refusals in maintained APIs."""

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

from .fixtures import RUNTIME_MEMBER, Catalogue, write
from .fixtures import catalogue as catalogue


@pytest.mark.parametrize(
    "fault",
    [
        "revision",
        "ancestor",
        "mode",
        "kind",
        "missing_member",
        "extra_member",
        "duplicate_member",
        "body",
        "terminator",
    ],
)
def test_external_git_faults_refuse(catalogue: Catalogue, fault: str) -> None:
    catalogue.state.fault = fault
    with pytest.raises((ReportRebuildError, ValueError)):
        catalogue.validate()


@pytest.mark.parametrize(
    "damage",
    [
        "group_count",
        "group_epoch",
        "unknown_role",
        "path_escape",
        "duplicate_generated",
        "missing_generated",
        "relabel_native_epoch",
    ],
)
def test_declared_population_role_and_path_refusals(
    catalogue: Catalogue, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    group = catalogue.descriptor["git_groups"][0]
    if damage == "group_count":
        group["member_count"] -= 1
    elif damage == "group_epoch":
        group["historical_source_commit"] = "0" * 40
    elif damage == "unknown_role":
        group["storage_role"] = "current_reader"
    elif damage == "path_escape":
        group["prefixes"]["repository_prefix"] = "../packages/"
    elif damage == "duplicate_generated":
        catalogue.descriptor["generated_members"] *= 2
    elif damage == "missing_generated":
        catalogue.descriptor["generated_members"] = []
    else:
        catalogue.descriptor["rewritten_source_epoch_executed"] = True
    catalogue.refresh(monkeypatch)
    with pytest.raises(ReportRebuildError):
        catalogue.validate()


@pytest.mark.parametrize(
    "damage", ["duplicate_member", "path_escape", "boolean_size", "empty_role"]
)
def test_original_catalogue_schema_refusals(
    catalogue: Catalogue, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    rows = catalogue.document["files"]
    if damage == "duplicate_member":
        rows.append(dict(rows[0]))
    elif damage == "path_escape":
        rows[0]["path"] = "../source.py"
    elif damage == "boolean_size":
        rows[0]["bytes"] = True
    else:
        rows[0]["kind"] = ""
    catalogue.refresh(monkeypatch)
    with pytest.raises(ReportRebuildError):
        catalogue.validate()


@pytest.mark.parametrize(
    "damage",
    ["provider", "genesis", "version_derivation", "scalars", "node", "identity"],
)
def test_generation_provider_and_exact_body_refusals(
    catalogue: Catalogue, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    row = catalogue.descriptor["generated_members"][0]
    if damage == "provider":
        row["generator"]["sha256"] = "0" * 64
    elif damage == "genesis":
        row["original_generator_execution_claimed"] = True
    elif damage == "version_derivation":
        row["original_version_derivation_claimed"] = True
    elif damage == "scalars":
        row["scalars"]["version"] = "1.0.0.other00"
    elif damage == "node":
        row["scalars"]["short_node"] = "c" * 7
    else:
        next(x for x in catalogue.document["files"] if x["path"] == RUNTIME_MEMBER)[
            "sha256"
        ] = "0" * 64
    catalogue.refresh(monkeypatch)
    with pytest.raises(ReportRebuildError):
        catalogue.validate()


@pytest.mark.parametrize(
    "damage",
    ["missing", "changed", "extra", "symlink", "hardlink", "materialized_source"],
)
def test_physical_projection_is_complete_and_source_free(
    catalogue: Catalogue, damage: str
) -> None:
    path = catalogue.directory / "source/data/own/source_000.json"
    if damage == "missing":
        path.unlink()
    elif damage == "changed":
        path.write_bytes(path.read_bytes().replace(b"0", b"9"))
    elif damage == "extra":
        write(catalogue.directory / "extra.json", b"{}")
    elif damage in {"symlink", "hardlink"}:
        reference = catalogue.repository / "own-payload.json"
        reference.write_bytes(path.read_bytes())
        path.unlink()
        if damage == "symlink":
            path.symlink_to(reference)
        else:
            path.hardlink_to(reference)
    else:
        write(
            catalogue.directory / "source/packages/own/chronology_0000.py",
            catalogue.state.bodies["packages/own/chronology_0000.py"],
        )
    with pytest.raises(ReportRebuildError):
        catalogue.validate()


@pytest.mark.parametrize("damage", ["head", "capture", "descriptor"])
def test_closed_reader_refuses_epoch_or_metadata_movement(
    catalogue: Catalogue, damage: str
) -> None:
    capsule = catalogue.validate()
    path = (
        catalogue.repository / ".git/HEAD"
        if damage == "head"
        else catalogue.directory
        / ("capture.json" if damage == "capture" else "source-transport.json")
    )
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ReportRebuildError, match="context changed"):
        capsule.read_source(RUNTIME_MEMBER)

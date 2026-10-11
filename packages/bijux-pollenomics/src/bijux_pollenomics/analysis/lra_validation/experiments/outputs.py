"""Owned publication and strict inventory reopening for experiment phases."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile

from ....core.owned_tree import publish_new_output_tree
from ..channels import (
    ObservationChannels,
    ObservedPollenAdmission,
    PollenChannel,
    assert_channel_inputs,
)
from ..contracts import (
    Fold,
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ..metrics import closed_composition
from .configuration import (
    BLOCK_LOCAL_PROFILE,
    BLOCK_PROFILE,
    FITTED_PROFILE,
    LOCAL_METHOD,
    LOCAL_PROFILE,
    PROFILE,
    SOURCE_PROFILE,
    TEMPORAL_PROFILE,
    identity,
    object_list,
    object_mapping,
)
from .configuration import LOCAL_EVALUATION_ROLES as ROLES
from .inputs import _unique_pairs


@dataclass(frozen=True)
class ExperimentProduct:
    """One byte-bound phase, explicitly without scientific acceptance."""

    directory: Path
    manifest_sha256: str
    scientific_content_sha256: str


def stage_directory(destination: Path) -> Path:
    """Create one new diagnostic stage; existing products are never replaced."""
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValidationRefusal("experiment_output_exists", str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    return Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.pending-", dir=destination.parent)
    )


def write_json(stage: Path, name: str, value: object) -> None:
    """Write a fixed producer-owned JSON member, preserving finite values."""
    if Path(name).name != name or not name.endswith(".json"):
        raise ValidationRefusal("invalid_experiment_output_name", name)
    (stage / name).write_text(canonical_json(value) + "\n")


def _inventory(directory: Path) -> dict[str, str]:
    result = {}
    if directory.is_symlink():
        raise ValidationRefusal("invalid_experiment_product", "Symlink root")
    for path in directory.rglob("*"):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise ValidationRefusal("invalid_experiment_product", "Nonregular output")
        if path.is_file() and path != directory / "manifest.json":
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return result


def publish_phase(
    stage: Path,
    destination: Path,
    *,
    phase: str,
    scientific: dict[str, object],
    profile: str = PROFILE,
) -> ExperimentProduct:
    """Publish only an enumerated phase; failures must already be accounted for."""
    if profile not in {
        PROFILE,
        SOURCE_PROFILE,
        LOCAL_PROFILE,
        FITTED_PROFILE,
        BLOCK_PROFILE,
        BLOCK_LOCAL_PROFILE,
        TEMPORAL_PROFILE,
    }:
        raise ValidationRefusal("unsupported_experiment_profile", profile)
    scientific_digest = manifest_sha256(scientific)
    manifest = {
        "schema_version": "lra-experiment-product.v1",
        "profile": profile,
        "phase": phase,
        "status": "generated_exploratory",
        "scientific_acceptance": "not_evaluated",
        "scientific_content_sha256": scientific_digest,
        "scientific_payload": scientific,
        "files": _inventory(stage),
    }
    write_json(stage, "manifest.json", manifest)
    digest = hashlib.sha256((stage / "manifest.json").read_bytes()).hexdigest()
    try:
        publish_new_output_tree(
            final_output_root=destination.absolute(), staging_output_root=stage
        )
    except OSError as exc:
        raise ValidationRefusal("experiment_publication_failed", str(exc)) from exc
    return ExperimentProduct(destination.absolute(), digest, scientific_digest)


def read_experiment_product(
    directory: Path, *, expected_manifest_sha256: str
) -> tuple[ExperimentProduct, dict[str, object]]:
    """Authenticate the caller's exact expected inventory before opening outcomes."""
    directory = directory.absolute()
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Expected a nonsymlink product directory")
        content = (directory / "manifest.json").read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != expected_manifest_sha256:
            raise ValueError(
                "Manifest differs from the independently retained identity"
            )
        manifest = object_mapping(
            json.loads(content, object_pairs_hook=_unique_pairs), "manifest"
        )
        canonical_json(manifest)
        if (
            manifest.get("schema_version") != "lra-experiment-product.v1"
            or manifest.get("profile")
            not in {
                PROFILE,
                SOURCE_PROFILE,
                LOCAL_PROFILE,
                FITTED_PROFILE,
                BLOCK_PROFILE,
                BLOCK_LOCAL_PROFILE,
                TEMPORAL_PROFILE,
            }
            or manifest.get("status") != "generated_exploratory"
            or manifest.get("scientific_acceptance") != "not_evaluated"
        ):
            raise ValueError("Unsupported experimental posture")
        if manifest.get("files") != _inventory(directory):
            raise ValueError("Product byte inventory changed")
        scientific = object_mapping(
            manifest["scientific_payload"], "scientific_payload"
        )
        identity = manifest_sha256(scientific)
        if identity != manifest.get("scientific_content_sha256"):
            raise ValueError("Scientific identity differs from its payload")
        return ExperimentProduct(directory, digest, identity), manifest
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValidationRefusal("invalid_experiment_product", str(exc)) from exc


def read_member(product: ExperimentProduct, name: str) -> object:
    """Read one already inventoried JSON member and recheck complete ownership."""
    _, manifest = read_experiment_product(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    member = Path(name)
    if (
        member.is_absolute()
        or member.as_posix() != name
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or not name.endswith(".json")
        or name == "manifest.json"
        or name not in object_mapping(manifest["files"], "files")
    ):
        raise ValidationRefusal("invalid_experiment_output_name", name)
    try:
        data = json.loads(
            (product.directory / name).read_bytes(), object_pairs_hook=_unique_pairs
        )
        canonical_json(data)
    except (OSError, ValueError, TypeError) as exc:
        raise ValidationRefusal("invalid_experiment_member", name) from exc
    read_experiment_product(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    return data


def _local_prediction_rows(
    manifest: dict[str, object], values: object, catalogue: object
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    scientific = object_mapping(manifest["scientific_payload"], "scientific_payload")
    if (
        manifest["profile"] != LOCAL_PROFILE
        or manifest["phase"] != "predictions"
        or values != scientific["predictions"]
        or scientific.get("evaluation_roles") != ROLES
        or scientific.get("pollen_eligible_for_heldout_acceptance") is not False
    ):
        raise ValidationRefusal(
            "local_prediction_role_mismatch",
            "An explicit local-pollen profile and diagnostic role are required",
        )
    folds = {
        identity(row["fold_id"]): row
        for value in object_list(scientific["folds"], "folds")
        if (row := object_mapping(value, "fold"))
    }
    if len(folds) != len(object_list(scientific["folds"], "folds")) or not folds:
        raise ValidationRefusal(
            "local_prediction_accounting_mismatch",
            "Fold IDs must be nonempty and unique",
        )
    rows = {}
    for value in object_list(values, "predictions"):
        row = object_mapping(value, "prediction")
        key = identity(row["fold_id"])
        if (
            key in rows
            or key not in folds
            or row.get("profile") != LOCAL_PROFILE
            or row.get("method") != LOCAL_METHOD
            or row.get("method_kind") != "local_pollen_assimilation"
            or row.get("evaluation_roles") != ROLES
            or row.get("pollen_eligible_for_heldout_acceptance") is not False
            or row.get("outer_fold") != folds[key]
            or folds[key]["test_record_ids"] != [row["record_id"]]
            or manifest_sha256(
                {k: v for k, v in row.items() if k != "prediction_manifest_sha256"}
            )
            != row["prediction_manifest_sha256"]
        ):
            raise ValidationRefusal("local_prediction_identity_mismatch", key)
        local_source = object_mapping(
            row["observed_local_pollen_source"], "local_pollen_source"
        )
        regional_source = object_mapping(
            row["regional_pollen_source"], "regional_pollen_source"
        )
        if (
            local_source["record_id"] != row["record_id"]
            or local_source["role"] != "observed_local_pollen"
            or folds[key]["test_group_ids"] != [row["group_id"]]
            or local_source["group_id"] != row["group_id"]
            or regional_source["record_id"]
            not in object_list(folds[key]["train_record_ids"], "train_record_ids")
            or regional_source["role"] != "training_regional_pollen"
            or row["observed_pollen_unit"] != "count"
        ):
            raise ValidationRefusal("local_prediction_channel_mismatch", key)
        vegetation = closed_composition(
            {
                taxon: finite_number(value)
                for taxon, value in object_mapping(
                    row["vegetation_fraction"], "vegetation_fraction"
                ).items()
            }
        )
        pollen = closed_composition(
            {
                taxon: finite_number(value)
                for taxon, value in object_mapping(
                    row["pollen_fraction"], "pollen_fraction"
                ).items()
            }
        )
        counts = object_mapping(row["observed_pollen_count"], "observed_pollen_count")
        if (
            set(vegetation) != set(pollen)
            or set(pollen) != set(counts)
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in counts.values()
            )
        ):
            raise ValidationRefusal("local_prediction_denominator_mismatch", key)
        _validate_channel_receipt(row, catalogue)
        rows[key] = row
    failures = object_list(scientific["failures"], "failures")
    failed = {
        identity(object_mapping(value, "failure")["fold_id"]) for value in failures
    }
    if (
        len(failed) != len(failures)
        or failed & set(rows)
        or failed | set(rows) != set(folds)
    ):
        raise ValidationRefusal(
            "local_prediction_accounting_mismatch",
            "Every fold must be predicted or refused exactly once",
        )
    return folds, rows


def local_prediction_rows(
    manifest: dict[str, object], values: object, catalogue: object
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    """Refuse malformed channel/shape identities before any vegetation access."""
    try:
        return _local_prediction_rows(manifest, values, catalogue)
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationRefusal("invalid_local_prediction_product", str(exc)) from exc


def _pollen_channels(values: object) -> tuple[PollenChannel, ...]:
    rows = [
        object_mapping(value, "pollen_channel")
        for value in object_list(values, "pollen_channels")
    ]
    return tuple(
        PollenChannel(identity(row["input_id"]), identity(row["source_sha256"]))
        for row in rows
    )


def _validate_channel_receipt(row: dict[str, object], catalogue: object) -> None:
    """Reconstitute the recorded original Fold and recheck shared channel admission."""
    records = [
        object_mapping(value, "channel_owner")
        for value in object_list(catalogue, "observation_channels")
    ]
    channels = tuple(
        ObservationChannels(
            identity(value["record_id"]),
            identity(value["group_id"]),
            _pollen_channels(value["pollen_channels"]),
            tuple(
                identity(key)
                for key in object_list(
                    value["vegetation_input_ids"], "vegetation_input_ids"
                )
            ),
        )
        for value in records
    )
    outer = object_mapping(row["outer_fold"], "outer_fold")
    fold = Fold(
        identity(outer["fold_id"]),
        tuple(
            identity(key)
            for key in object_list(outer["train_record_ids"], "train_record_ids")
        ),
        tuple(
            identity(key)
            for key in object_list(outer["test_record_ids"], "test_record_ids")
        ),
        tuple(
            identity(key)
            for key in object_list(outer["train_group_ids"], "train_group_ids")
        ),
        tuple(
            identity(key)
            for key in object_list(outer["test_group_ids"], "test_group_ids")
        ),
    )
    evidence = object_mapping(row["channel_admission"], "channel_admission")
    declared = object_mapping(evidence["observed_pollen"], "observed_pollen")
    observed = ObservedPollenAdmission(
        identity(declared["record_id"]),
        identity(declared["group_id"]),
        _pollen_channels(declared["pollen_channels"]),
    )
    graph = {
        key: tuple(identity(value) for value in object_list(parents, "parents"))
        for key, parents in object_mapping(
            evidence["quantitative_lineage"], "quantitative_lineage"
        ).items()
    }
    inputs = tuple(
        identity(key)
        for key in object_list(evidence["pollen_input_ids"], "pollen_input_ids")
    )
    closure = assert_channel_inputs(
        fold, inputs, graph, channels=channels, observed_pollen=observed
    )
    local = object_mapping(row["observed_local_pollen_source"], "local_pollen_source")
    regional = object_mapping(row["regional_pollen_source"], "regional_pollen_source")
    expected = {
        "raw:" + identity(local["record_id"]),
        "raw:" + identity(regional["record_id"]),
    }
    consumed = [
        {
            "record_id": owner.record_id,
            "group_id": owner.group_id,
            "input_id": source.input_id,
            "source_sha256": source.source_sha256,
        }
        for owner in channels
        for source in owner.pollen_channels
        if source.input_id in closure
    ]
    hashes = {value["input_id"]: value["source_sha256"] for value in consumed}
    if (
        evidence["schema_version"] != "lra-local-pollen-channel-admission.v1"
        or set(inputs) != expected
        or evidence["original_fold_sha256"] != manifest_sha256(fold.as_dict())
        or list(closure) != evidence["pollen_channel_closure"]
        or consumed != evidence["consumed_pollen_sources"]
        or observed.record_id != row["record_id"]
        or observed.group_id != row["group_id"]
        or len(observed.pollen_channels) != 1
        or observed.pollen_channels[0].input_id != "raw:" + identity(row["record_id"])
        or hashes.get("raw:" + identity(local["record_id"])) != local["sha256"]
        or hashes.get("raw:" + identity(regional["record_id"])) != regional["sha256"]
    ):
        raise ValidationRefusal(
            "local_channel_receipt_mismatch",
            "Channel evidence differs from actual sources and original Fold",
        )


def validate_fitted_preparation(row: dict[str, object], fit: dict[str, object]) -> None:
    """Validate retained forward units, dimensions and declared support without a new solver."""
    prepared = object_mapping(row["forward_preparation"], "forward_preparation")
    support = object_mapping(row["support"], "support")
    taxa = tuple(identity(value) for value in object_list(prepared["taxa"], "taxa"))
    vegetation = object_mapping(row["vegetation_fraction"], "vegetation_fraction")
    pollen = object_mapping(row["pollen_fraction"], "pollen_fraction")
    if (
        not taxa
        or len(set(taxa)) != len(taxa)
        or set(taxa) != set(vegetation)
        or set(taxa) != set(pollen)
        or list(taxa) != support["taxa"]
        or set(taxa) != set(object_list(fit["taxa"], "taxa"))
        or prepared["target_geometry_sha256"] != row["target_geometry_sha256"]
        or prepared["deposition_units"] != "relative-kernel-mass"
        or prepared["forward_method_profile"]
        != "disqover-0.9.14-homogeneous-local-forward"
        or prepared["preparation_profile"]
        != "disqover-0.9.14-corrected-matrix-homogeneous-v1"
        or prepared["geometry_profile"] != "circular-shore-contiguous-v1"
    ):
        raise ValidationRefusal(
            "fitted_forward_contract_mismatch",
            "Taxa, target identity or units/profile differ",
        )
    kernels = [
        tuple(finite_number(value) for value in object_list(ring, "local_k"))
        for ring in object_list(prepared["local_k"], "local_k")
    ]
    terrestrial = tuple(
        finite_number(value)
        for value in object_list(
            prepared["terrestrial_fraction"], "terrestrial_fraction"
        )
    )
    if (
        not kernels
        or len(kernels) != len(terrestrial)
        or any(
            len(ring) != len(taxa) or any(value < 0 for value in ring)
            for ring in kernels
        )
        or any(not 0 <= value <= 1 for value in terrestrial)
    ):
        raise ValidationRefusal(
            "fitted_forward_shape_mismatch",
            "Require nonempty finite nonnegative ring/taxon support",
        )
    for field in ("ppe", "regional_deposition", "regional_cover"):
        values = tuple(
            finite_number(value) for value in object_list(prepared[field], field)
        )
        if len(values) != len(taxa) or any(
            value <= 0 if field == "ppe" else value < 0 for value in values
        ):
            raise ValidationRefusal("fitted_forward_shape_mismatch", field)
    bounds = [
        tuple(finite_number(value) for value in object_list(ring, "ring_bounds_m"))
        for ring in object_list(prepared["ring_bounds_m"], "ring_bounds_m")
    ]
    declared = [
        object_mapping(ring, "forward_ring")
        for ring in object_list(
            prepared["declared_target_forward_rings"], "forward_rings"
        )
    ]
    inversion = [
        object_mapping(ring, "inversion_ring")
        for ring in object_list(
            prepared["declared_target_inversion_rings"], "inversion_rings"
        )
    ]
    radius = finite_number(support["local_support_radius_m"])
    if (
        len(bounds) < len(kernels)
        or len(bounds) != len(declared)
        or not inversion
        or any(len(ring) != 2 or not 0 <= ring[0] < ring[1] for ring in bounds)
        or any(
            left[1] != right[0]
            for left, right in zip(bounds[:-1], bounds[1:], strict=True)
        )
        or bounds
        != [
            (finite_number(ring["inner_m"]), finite_number(ring["outer_m"]))
            for ring in declared
        ]
        or bounds[len(kernels) - 1][1] != radius
        or finite_number(inversion[-1]["outer_m"]) != radius
        or finite_number(prepared["regional_cutoff_m"]) != bounds[-1][1]
    ):
        raise ValidationRefusal(
            "fitted_forward_support_mismatch",
            "Prepared rings differ from declared target support",
        )

"""Count-free primary membership and complete-footprint input controls."""

from __future__ import annotations

import csv
import hashlib
from io import StringIO
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.blocks import inputs

_NAMES = [
    "BECKHAM",
    "BROADOWN",
    "COMERSLA",
    "CUTHILL2",
    "GOURTEMIRES",
    "HANGINGS",
    "HARESDOWN",
    "LARKBARR",
    "LOBBSBOG",
    "LONGBREACH",
    "MOLECHAM",
    "NTWITCHEN",
    "WHH05",
    "WINDMILL",
    "WINNEYS",
]
_BLOCK_512 = {
    "BROADOWN",
    "CUTHILL2",
    "HANGINGS",
    "HARESDOWN",
    "LOBBSBOG",
    "WHH05",
    "WINDMILL",
    "WINNEYS",
}


def _encoded(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_encoded(value)).hexdigest()


def _fixture(root: Path, mutation: str = "") -> tuple[Path, Path, Path, dict[str, Any]]:
    repository, archive, data = root / "repository", root / "archive", root / "data"
    for path in (repository, archive, data):
        path.mkdir(parents=True)

    def store(name: str, value: Any, *, cas: bool = False) -> dict[str, Any]:
        raw = _encoded(value)
        sha = hashlib.sha256(raw).hexdigest()
        path = archive / "objects" / sha[:2] / sha if cas else repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {"path": name, "bytes": len(raw), "sha256": sha}

    taxa = [f"taxon-{index}" for index in range(30)]
    records = ["author:" + name for name in _NAMES]
    groups = {record: "site-group:" + _sha([record]) for record in records}
    source_sites: list[dict[str, Any]] = []
    author_pins: list[dict[str, Any]] = []
    geometry_pins: dict[str, dict[str, Any]] = {}
    csv_rows = []
    for index, name in enumerate(_NAMES):
        record = "author:" + name
        radius = 25 + index
        latitude, longitude = 50.0 + index / 20, -4.0 + index / 100
        geometry = {
            "latitude": latitude,
            "longitude": longitude,
            "basin": {"diameter_m": 2.0 * radius, "site_type": "lake"},
            "sample_metadata": {
                "site_id": name,
                "bin_id": "author-TW5",
                "age_type": "calendar_bp",
                "age_support_bp": [[1250, 1750]],
            },
            "inversion_rings": [{"outer_m": 500}, {"outer_m": 10000}],
            "forward_rings": [
                {"outer_m": 1000},
                {"outer_m": 150000 if mutation == "wider_ring" else 100000},
            ],
        }
        pin = store(name + "-geometry.json", geometry, cas=True)
        geometry_pins[record] = pin
        raw_pin = {
            "path": name + "-raw.json",
            "bytes": 3,
            "sha256": _sha(["UNOPENED", name]),
        }
        # No raw observation object is created: any attempted open must fail.
        author_pins.extend((pin, raw_pin))
        source_sites.append(
            {
                "record_id": record,
                "site_id": name,
                "identity_keys": [],
                "geometry": {key: pin[key] for key in ("path", "sha256")},
                "raw": {key: raw_pin[key] for key in ("path", "sha256")},
            }
        )
        csv_rows.append(
            {
                "metadata": "TRUE",
                "filename": name,
                "SiteName": name,
                "model": "2",
                "radius": str(radius),
                "londd": str(longitude),
                "latdd": str(latitude),
                "LCGRID_ID": "512" if name in _BLOCK_512 else "562",
            }
        )
    for name, block in (("EXEBRID", "562"), ("WHH11", "512")):
        csv_rows.append(
            {
                "metadata": "TRUE",
                "filename": name,
                "SiteName": name,
                "model": "2",
                "radius": "25",
                "londd": "-4.0",
                "latdd": "51.0",
                "LCGRID_ID": block,
            }
        )
    if mutation == "duplicate_csv_owner":
        csv_rows[-1]["filename"] = _NAMES[0]
    elif mutation == "foreign_exclusion":
        csv_rows[-1]["filename"] = "FOREIGN"
    elif mutation == "wrong_block":
        csv_rows[0]["LCGRID_ID"] = "512"
    elif mutation == "csv_coordinates":
        csv_rows[0]["latdd"] = "51.1234"
    elif mutation == "csv_radius":
        csv_rows[0]["radius"] = "35"
    metadata = StringIO()
    writer = csv.DictWriter(
        metadata,
        fieldnames=[
            "metadata",
            "filename",
            "SiteName",
            "model",
            "radius",
            "londd",
            "latdd",
            "LCGRID_ID",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(csv_rows)
    raw_metadata = metadata.getvalue().encode()
    metadata_name = "landclim/author-reference/author/site.metadata.csv"
    metadata_path = data / metadata_name
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_bytes(raw_metadata)
    metadata_pin = {
        "path": metadata_name,
        "bytes": len(raw_metadata),
        "sha256": hashlib.sha256(raw_metadata).hexdigest(),
    }
    experiment: dict[str, Any] = {
        "sites": source_sites,
        "regional_priority": records,
        "local_support_radius_m": 1000,
        "request_template": {"taxa": taxa, "configuration": {"reveals": {}}},
    }
    if mutation == "explicit_larger_cutoff":
        experiment["request_template"]["configuration"]["reveals"][
            "region_cutoff_m"
        ] = 120000
    author_pins.append(store("experiment.json", experiment, cas=True))
    for name in (
        "chronology",
        "decision",
        "dependency-lock",
        "parameters",
        "source-report",
        "taxa",
    ):
        author_pins.append(
            {"path": name + ".json", "bytes": 3, "sha256": _sha(["UNOPENED", name])}
        )
    parent_pin = store(
        "parent.json",
        {"nominal_transport": "gpm neutral", "author_inputs": author_pins},
    )
    contexts: list[dict[str, Any]] = []
    for outer in records:
        for target in records:
            training = sorted(set(records) - {outer, target})
            anchor = next(record for record in records if record in training)
            contexts.append(
                {
                    "outer_target": outer,
                    "target": target,
                    "kind": "outer" if outer == target else "inner",
                    "fold": {"train_record_ids": training},
                    "anchor": anchor,
                    "predictors": [
                        {
                            "record_id": local,
                            "group_id": groups[local],
                            "request_sha256": _sha([local, anchor]),
                            "covers_by_ring": "FORECAST MUST NOT BE USED",
                        }
                        for local in sorted(set(training) - {anchor})
                    ],
                    "forward": {
                        "regional_cutoff_m": 100000.0,
                        "target_geometry_sha256": geometry_pins[target]["sha256"],
                        "regional_deposition": "DO NOT CONSUME",
                    },
                    "reference_baselines": "NOT A FORECAST CONSUMER",
                }
            )
    if mutation == "inconsistent_pair":
        contexts[0]["predictors"][0]["request_sha256"] = "e" * 64
    elif mutation == "noninjective_pair":
        contexts[0]["predictors"][0]["request_sha256"] = contexts[0]["predictors"][1][
            "request_sha256"
        ]
    elif mutation == "predictor_group":
        contexts[0]["predictors"][0]["group_id"] = "wrong-group"
    elif mutation == "regional_cutoff":
        contexts[-1]["forward"]["regional_cutoff_m"] = 99999.0
    elif mutation == "boolean_cutoff":
        contexts[0]["forward"]["regional_cutoff_m"] = True
    elif mutation == "geometry_epoch":
        contexts[0]["forward"]["target_geometry_sha256"] = "e" * 64
    elif mutation == "context_missing":
        contexts.pop()
    nominal_pin = store(
        "nominal-inputs.json",
        {
            "schema_version": "author-lra-spatial-inputs.v1",
            "groups": groups,
            "taxa": taxa,
            "contexts": contexts,
        },
    )
    protocol = {
        "schema_version": "author-lra-block-support-protocol.v1",
        "sources": {
            "parent_protocol": parent_pin,
            "nominal_inputs": nominal_pin,
            "site_metadata": metadata_pin,
        },
        "expected": {
            "sites": 15,
            "blocks": ["512", "562"],
            "saved_pairs": 39,
            "cross_block_comparisons": 112,
        },
        "policy": {
            "minimum_buffer_m": 20000.0,
            "coordinate_uncertainty_m": 0.0,
            "uncertainty_scope": "optimistic_zero_lower_bound_not_empirical_precision",
            "support_scope": "declared_finite_cutoff_synthetic_not_empirical_independence",
        },
    }
    return repository, archive, data, protocol


def test_only_primary_metadata_and_geometry_open_and_saved_pairs_are_exact(
    tmp_path: Path,
) -> None:
    args = _fixture(tmp_path)
    packet = inputs.load_block_inputs(*args)
    assert packet["summary"]["blocks"] == {"512": 8, "562": 7}
    assert len(packet["sites"]) == 15 and len(packet["saved_pairs"]) == 39
    assert packet["summary"]["raw_outcomes_opened"] == 0
    assert packet["summary"]["prediction_values_consumed"] == 0
    assert len(packet["sources"]) == 19
    assert all(not row["path"].endswith("-raw.json") for row in packet["sources"])
    assert all(
        row["source_radius_m"] == 100000
        and row["target_radius_m"] == 1000
        and row["coordinate_uncertainty_m"] == 0
        for row in packet["sites"]
    )
    assert packet["excluded_source_block_ids"] == ["EXEBRID", "WHH11"]
    inputs.check_block_sources(*args[:3], packet)


@pytest.mark.parametrize(
    "mutation,expected_radius",
    [("wider_ring", 150000), ("explicit_larger_cutoff", 120000)],
)
def test_source_footprint_covers_every_declared_support(
    tmp_path: Path, mutation: str, expected_radius: int
) -> None:
    packet = inputs.load_block_inputs(*_fixture(tmp_path, mutation))
    assert all(
        row["source_radius_m"] == expected_radius
        and row["basin_shoreline_radius_m"] < row["target_radius_m"]
        for row in packet["sites"]
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_csv_owner",
        "foreign_exclusion",
        "wrong_block",
        "csv_coordinates",
        "csv_radius",
        "inconsistent_pair",
        "noninjective_pair",
        "predictor_group",
        "regional_cutoff",
        "boolean_cutoff",
        "geometry_epoch",
        "context_missing",
    ],
)
def test_source_identity_membership_and_pair_conflicts_refuse(
    tmp_path: Path, mutation: str
) -> None:
    with pytest.raises(ValueError):
        inputs.load_block_inputs(*_fixture(tmp_path, mutation))


def test_optimistic_zero_uncertainty_cannot_be_relabelled_empirical(
    tmp_path: Path,
) -> None:
    args = _fixture(tmp_path)
    args[3]["policy"]["uncertainty_scope"] = "observed_precision"
    with pytest.raises(ValueError, match="conditional support"):
        inputs.load_block_inputs(*args)
    args[3]["policy"]["uncertainty_scope"] = (
        "optimistic_zero_lower_bound_not_empirical_precision"
    )
    args[3]["policy"]["coordinate_uncertainty_m"] = False
    with pytest.raises(ValueError, match="strict numerical"):
        inputs.load_block_inputs(*args)


def test_postguard_streams_all_sources_without_decoding_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _fixture(tmp_path)
    packet = inputs.load_block_inputs(*args)

    def forbidden(_: bytes) -> Any:
        raise AssertionError("Postguard must not decode JSON")

    monkeypatch.setattr(inputs, "_decode", forbidden)
    inputs.check_block_sources(*args[:3], packet)
    pin = args[3]["sources"]["site_metadata"]
    path = args[2] / pin["path"]
    changed = bytearray(path.read_bytes())
    changed[0] = ord("M")
    path.write_bytes(changed)
    with pytest.raises(ValueError, match="source guard bytes changed"):
        inputs.check_block_sources(*args[:3], packet)


def test_primary_path_cannot_escape_or_redirect(tmp_path: Path) -> None:
    args = _fixture(tmp_path)
    pin = args[3]["sources"]["site_metadata"]
    original_name = pin["path"]
    pin["path"] = "../site.metadata.csv"
    with pytest.raises(ValueError, match="shared metadata path"):
        inputs.load_block_inputs(*args)
    pin["path"] = original_name
    path = args[2] / original_name
    payload = path.read_bytes()
    path.unlink()
    alternate = args[2] / "same-source.csv"
    alternate.write_bytes(payload)
    path.symlink_to(alternate)
    with pytest.raises(ValueError, match="ordinary original"):
        inputs.load_block_inputs(*args)

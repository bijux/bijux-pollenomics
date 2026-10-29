"""Use one fixed illustrative paired law through the canonical validation API."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from math import exp
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.analysis.lra.uncertainty.projection import project
from bijux_pollenomics.analysis.lra_validation.contracts import (
    SiteRecord,
    site_group_id,
)
from bijux_pollenomics.analysis.lra_validation.prediction import ForwardInputs
from bijux_pollenomics.analysis.lra_validation.spatial import (
    JointSpatialDraw,
    SiteCoordinate,
    SpatialConfig,
    UnavailableSpatialDraw,
    propagate_withheld_spatial_draws,
)
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km
from bijux_pollenomics.analysis.lra_validation.spatial.uncertainty.contracts import (
    CONDITIONED_SOURCES,
    UPSTREAM_SOURCES,
)
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition

Json = dict[str, Any]


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def _read_example(path: Path, expected_sha256: str) -> tuple[Json, str]:
    """Read this fixed example's fields; this is not a general joint-law loader."""
    _require(
        path.is_file() and path.stat().st_nlink == 1, "Independent law file required"
    )
    _require(path.stat().st_size <= 32768, "Bounded example law required")
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    _require(actual == expected_sha256, "Example law SHA-256 differs")

    def unique(pairs: list[tuple[str, Any]]) -> Json:
        result: Json = {}
        for key, value in pairs:
            _require(key not in result, "Duplicate example law member")
            result[key] = value
        return result

    def invalid(value: str) -> None:
        raise ValueError("Nonfinite example value: " + value)

    law: Json = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)
    _require(
        set(law)
        == {
            "schema_version",
            "kind",
            "taxa",
            "records",
            "coordinates",
            "support_id",
            "temporal_support_id",
            "length_scale_km",
            "ridge_rule",
            "atoms",
        },
        "Exact example fields required; no target outcomes",
    )
    _require(
        law["schema_version"] == "predictive-uncertainty-usage-law.v1"
        and law["kind"] == "constructed_example_not_field_law",
        "Constructed example only",
    )
    _require(
        law["taxa"] == ["a", "b"]
        and law["ridge_rule"] == "squared_one_minus_offdiagonal",
        "Fixed example axis and rule required",
    )
    _require(
        len(law["records"]) == 4
        and [r["record_id"] for r in law["records"]]
        == ["r1", "r2", "p10", "p10-alias"],
        "Complete four-record example axis required",
    )
    for row in law["records"]:
        _require(
            set(row) == {"record_id", "site_id", "identity_keys"},
            "Outcome-free records required",
        )
    _require(
        set(law["coordinates"]) == {"r1", "r2", "p10"},
        "Exact example coordinates required",
    )
    _require(
        len(law["atoms"]) == 2 and [a["draw_id"] for a in law["atoms"]] == ["d0", "d1"],
        "Frozen paired draw order required",
    )
    for row in law["atoms"]:
        _require(
            set(row)
            == {
                "draw_id",
                "mass",
                "training_compositions",
                "regional_deposition",
                "local_k",
                "terrestrial_fraction",
                "ppe",
            },
            "Exact paired example atom required",
        )
        _require(
            set(row["mass"]) == {"numerator", "denominator"}
            and all(type(v) is int for v in row["mass"].values()),
            "Exact integer mass required",
        )
        _require(
            set(row["training_compositions"]) == {"r1", "r2"}
            and all(
                list(values) == law["taxa"]
                for values in row["training_compositions"].values()
            ),
            "Exact ordered training/taxon axes required",
        )
    return law, actual


def run_example(
    *, repository: Path, law_path: Path, expected_sha256: str, output: Path
) -> Json:
    """Write three illustrative pushforwards, never a field uncertainty certificate.

    All cases are supplied before fitting. No target pollen, observed total,
    observation scoring or scientific-law approval is accepted by this example.
    """
    repository, law_path, output = (
        p.absolute() for p in (repository, law_path, output)
    )
    _require(
        all(
            ".." not in p.parts and not any(a.is_symlink() for a in (p, *p.parents))
            for p in (repository, law_path, output)
        ),
        "Normalized nonsymlinked paths required",
    )
    _require(
        law_path.is_relative_to(repository)
        and output.is_relative_to(repository / "artifacts")
        and not output.exists(),
        "Law inside repository and absent artifacts output required",
    )
    law, source_sha = _read_example(law_path, expected_sha256)
    records = tuple(
        SiteRecord(row["record_id"], row["site_id"], tuple(row["identity_keys"]))
        for row in law["records"]
    )
    fold = next(f for f in grouped_leave_one_out(records) if "p10" in f.test_record_ids)
    groups = {name: site_group_id((name,)) for name in ("r1", "r2")}
    coordinates = {
        name: SiteCoordinate(*values) for name, values in law["coordinates"].items()
    }
    decay = exp(
        -0.5
        * (distance_km(coordinates["r1"], coordinates["r2"]) / law["length_scale_km"])
        ** 2
    )
    config = SpatialConfig(law["length_scale_km"], (1 - decay) ** 2, law["support_id"])
    temporal = law["temporal_support_id"]
    forward_source_sha = hashlib.sha256(
        Path(forward_deposition.__code__.co_filename).read_bytes()
    ).hexdigest()
    atoms = []
    refused = []
    for item in law["atoms"]:
        weight = Fraction(item["mass"]["numerator"], item["mass"]["denominator"])
        identities = tuple(
            "example:" + item["draw_id"] + ":" + role
            for role in ("geometry", "parameters", "regional")
        )
        graph = {
            "r1": (),
            "r2": (),
            temporal: (),
            identities[0]: (),
            identities[1]: (),
            identities[2]: ("r1", "r2"),
        }
        context = ForwardInputs(
            tuple(law["taxa"]),
            tuple(item["regional_deposition"]),
            tuple(tuple(r) for r in item["local_k"]),
            tuple(item["terrestrial_fraction"]),
            tuple(item["ppe"]),
            (identities[2],),
            (identities[1],),
            (identities[0],),
            temporal,
            "disqover-0.9.14-homogeneous-local-forward",
            "source:" + forward_source_sha,
        )
        atoms.append(
            JointSpatialDraw(
                item["draw_id"],
                weight,
                source_sha,
                tuple(
                    sorted(
                        (groups[name], tuple(values.items()))
                        for name, values in item["training_compositions"].items()
                    )
                ),
                tuple(sorted((groups[name], coordinates[name]) for name in groups)),
                context,
                ("r1", "r2"),
                tuple(sorted(graph.items())),
                (*identities, temporal),
            )
        )
        # The deliberately missing regional role returns before a child request
        # or any admitted-plan fields are accessed. It is not upstream admission.
        upstream, request, files = project(
            cast(Any, None),
            {"regional": {"samples": []}, "local": {"samples": [{"sample_id": "r1"}]}},
            {
                "draw_id": item["draw_id"],
                "mass": item["mass"],
                "ages_by_sample_id": {"r1": 100},
            },
            {"bin_id": temporal, "younger_bp": 0, "older_bp": 200},
        )
        _require(
            request is None
            and not files
            and upstream["reason_code"] == "missing_role_in_bin",
            "Expected original upstream refusal",
        )
        encoded = json.dumps(upstream, sort_keys=True, separators=(",", ":"))
        refused.append(
            UnavailableSpatialDraw(
                encoded,
                hashlib.sha256(encoded.encode()).hexdigest(),
                temporal,
                ("r1", "r2"),
                tuple(sorted((("r1", ()), ("r2", ()), (temporal, ())))),
                (temporal,),
            )
        )
    populations: dict[str, tuple[JointSpatialDraw | UnavailableSpatialDraw, ...]] = {
        "complete": tuple(atoms),
        "mixed-refusal": (atoms[0], refused[1]),
        "all-unavailable": tuple(refused),
    }
    results = {}
    for name, draws in populations.items():
        results[name] = propagate_withheld_spatial_draws(
            fold,
            fold.test_group_ids[0],
            coordinates["p10"],
            support_id=config.support_id,
            temporal_support_id=temporal,
            site_records=records,
            config=config,
            predictor_group_ids=tuple(sorted(groups.values())),
            draw_ids=tuple(a.draw_id for a in draws),
            draws=draws,
            law_evidence_sha256=source_sha,
            upstream_sources=tuple(sorted(UPSTREAM_SOURCES)),
            omitted_sources=tuple(sorted(CONDITIONED_SOURCES)),
            forward_model=forward_deposition,
        )
    output.mkdir(parents=True, exist_ok=False)
    for name, result in results.items():
        (output / (name + ".json")).write_text(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    return {
        "law_sha256": source_sha,
        "output": str(output),
        "cases": {name: result["summary"] for name, result in results.items()},
        "law_authenticity_verified": False,
        "field_coverage_verified": False,
        "scope": "Constructed supplied-law usage only; no observed target outcomes, new law estimation or field uncertainty claim.",
    }

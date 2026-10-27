"""Independent raw-source, captured-law and literal radial-edge admission."""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
import math
from pathlib import PurePosixPath
from typing import Any, cast

from .contracts import (
    OWNERS,
    RULE,
    _same_json,
    finite,
    identity,
    parse,
    require,
)
from .geometry import Geometry
from .sources import _captured

BASE = "reports/science/pollen-reconstruction/spatial-field-forward/"
CAPTURE = "artifacts/physical-core/spatial-field-forward/continuous-receiver/study/input-freeze.json"
RADIAL_PROTOCOL = BASE + "radial-envelope/protocol.json"
CONTINUOUS_PROTOCOL = BASE + "continuous-receiver/protocol.json"
CORES = ("BOKE", "BUS", "SOLSOE83")
AXIS = ("Betula", "Ulmus")


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    require(
        protocol.get("schema_version") == "continuous-receiver-monotone-rings.v1"
        and protocol.get("cases") == [{"core": c, "taxon": t} for c, t in OWNERS],
        "Ring protocol population differs",
    )
    contract = {
        "endpoint_full_width_exact": "1/10000000000",
        "coefficient_full_width_exact": "1/1000000000",
        "arithmetic_bits": 96,
        "rule": RULE,
        "endpoint_population": 774,
        "coefficient_population": 18,
        "prediction_contexts": 18,
        "family_slots": 54,
        "all_initial_endpoints_before_refinement": True,
    }
    require(
        _same_json(protocol.get("numerical_contract"), contract),
        "Typed ring contract differs",
    )
    resources = {
        "wall_seconds": 180,
        "integration_work_seconds": 160,
        "peak_rss_bytes_posthoc": 805306368,
        "all_output_bytes": 5000000,
        "per_case_maximum_leaves": 4096,
        "per_case_maximum_attempted_panels": 8191,
        "per_case_maximum_node_evaluations": 73719,
        "per_case_maximum_live_queue": 4096,
    }
    observer = {
        "wall_seconds": 180,
        "replay_work_seconds": 160,
        "peak_rss_bytes_posthoc": 805306368,
        "all_output_bytes": 5000000,
    }
    require(
        _same_json(protocol.get("resources"), resources)
        and _same_json(protocol.get("independent_resources"), observer),
        "Ring resource ceilings differ",
    )
    require(
        all(
            protocol.get(k) is True
            for k in (
                "no_new_fits",
                "no_new_point_forecasts",
                "no_parameter_or_score_tuning",
                "retain_all_refusals",
            )
        )
        and protocol.get("unchanged_rerun_permitted") is False,
        "Ring scientific/refusal scope differs",
    )


def bind_raw_inputs(
    protocol: Mapping[str, Any], raw_inputs: Mapping[str, bytes]
) -> dict[str, dict[str, Any]]:
    """Authenticate the complete scientific inventory before interpreting fields."""
    validate_protocol(protocol)
    pins = protocol.get("input_files")
    require(
        isinstance(pins, dict) and set(pins) == set(raw_inputs),
        "Raw input inventory differs",
    )
    pins = cast(dict[str, Any], pins)
    decoded = {}
    for name, raw in raw_inputs.items():
        path = PurePosixPath(name)
        require(
            isinstance(name, str)
            and not path.is_absolute()
            and ".." not in path.parts
            and str(path) == name
            and type(raw) is bytes
            and 0 < len(raw) <= 1_000_000,
            "Unsafe or oversized scientific input",
        )
        require(_same_json(pins[name], identity(raw)), "Raw source identity differs")
        decoded[name] = parse(raw)
    require(RADIAL_PROTOCOL in decoded, "Qualified radial source declaration missing")
    radial = decoded[RADIAL_PROTOCOL]
    qualified = radial.get("repository_inputs")
    require(isinstance(qualified, dict), "Qualified study pins missing")
    qualified = cast(dict[str, Any], qualified)
    require(
        set(decoded)
        == {
            BASE + "protocol.json",
            BASE + "result.json",
            RADIAL_PROTOCOL,
            CONTINUOUS_PROTOCOL,
            CAPTURE,
            *qualified,
        },
        "Undeclared scientific source population",
    )
    for name, pin in qualified.items():
        require(_same_json(pins[name], pin), "Prior qualified source identity replaced")
    freeze = decoded[CAPTURE]
    require(
        _same_json(
            freeze.get("input_files"),
            {
                name: pins[name]
                for name in (BASE + "result.json", BASE + "protocol.json")
            },
        )
        and _same_json(
            freeze.get("protocol_file"),
            {"path": CONTINUOUS_PROTOCOL, **pins[CONTINUOUS_PROTOCOL]},
        ),
        "Captured law belongs to different scientific input bytes",
    )
    prediction = decoded[radial["source_prediction"]]
    execution = decoded[radial["source_execution"]]
    verification = decoded[radial["source_verification"]]
    require(
        prediction.get("source_commit") == radial["prior_producer_source_commit"]
        and execution.get("source_commit") == radial["prior_observer_source_commit"]
        and type(execution.get("exit_code")) is int
        and execution["exit_code"] == 0
        and type(execution.get("pytest_passed")) is int
        and execution["pytest_passed"] == 1
        and verification["predictions_sha256"]
        == execution["source_results"]["predictions_sha256"]
        == qualified[radial["source_prediction"]]["sha256"]
        and verification["result_sha256"]
        == execution["source_results"]["result_sha256"]
        == qualified[radial["source_result"]]["sha256"],
        "Prior independent qualification linkage differs",
    )
    require(
        _same_json(
            [
                verification.get("source_rows"),
                verification.get("selected_samples"),
                verification.get("source_contexts"),
                verification["scores"].get("scored_rows"),
                verification["scores"].get("refused_rows"),
            ],
            [147, 59, 18, 54, 0],
        ),
        "Qualified source/score support differs",
    )
    return decoded


def nested_edges(
    saved: Mapping[str, Any], receiver: Fraction, outer: Fraction
) -> tuple[Fraction, ...]:
    """Reconstruct the prescribed binary64 constructor from the eight old annuli."""
    taxa = saved.get("taxa")
    require(
        isinstance(taxa, list) and len(taxa) == 2, "Saved geometry taxon axis differs"
    )
    taxa = cast(list[dict[str, Any]], taxa)
    annuli = taxa[0]["step_bounds"]["annuli"]
    require(
        isinstance(annuli, list) and len(annuli) == 8, "Eight original annuli required"
    )
    coarse = [annuli[0]["inner_radius_m"], *[row["outer_radius_m"] for row in annuli]]
    exact = tuple(finite(x) for x in coarse)
    require(
        exact[0] == receiver
        and exact[-1] == outer
        and finite(saved["radius_m"]) == receiver
        and all(a < b for a, b in zip(exact, exact[1:], strict=False))
        and all(
            finite(row["inner_radius_m"]) == exact[i] for i, row in enumerate(annuli)
        ),
        "Original annulus coverage differs",
    )
    for taxon in taxa:
        other = taxon["step_bounds"]["annuli"]
        require(
            isinstance(other, list)
            and len(other) == 8
            and all(
                finite(row["inner_radius_m"]) == exact[i]
                and finite(row["outer_radius_m"]) == exact[i + 1]
                for i, row in enumerate(other)
            ),
            "Cross-taxon original annulus boundaries differ",
        )
    values = [exact[0]]
    for left, right in zip(coarse, coarse[1:], strict=False):
        for j in range(1, 16):
            native = math.exp(
                math.log(left) + (math.log(right) - math.log(left)) * j / 16
            )
            values.append(finite(native))
        values.append(finite(right))
    require(
        len(values) == 129
        and all(a < b for a, b in zip(values, values[1:], strict=False)),
        "Unresolved nested edges",
    )
    return tuple(values)


def select_sources(
    protocol: Mapping[str, Any],
    public: Mapping[str, Any],
    original: Mapping[str, Any],
    freeze: Mapping[str, Any],
    prediction: Mapping[str, Any],
) -> tuple[tuple[Geometry, ...], tuple[tuple[Fraction, ...], ...]]:
    validate_protocol(protocol)
    require(
        public.get("schema_version") == "spatial-field-forward-account.v1"
        and original.get("schema_version") == "spatial-field-forward-protocol.v1"
        and prediction.get("schema_version") == "spatial-field-forward-predictions.v1"
        and freeze.get("schema_version") == "continuous-receiver-input-freeze.v1"
        and freeze.get("historical_A_authenticated") is False
        and freeze.get("source_commit") == protocol.get("captured_law_source_commit"),
        "Scientific source/captured-law identity differs",
    )
    require(
        public.get("axis")
        == prediction.get("axis")
        == original.get("projected_axis")
        == list(AXIS)
        and [(r.get("core"), r.get("taxon")) for r in public["geometry"]]
        == list(OWNERS)
        and [(r.get("core"), r.get("taxon")) for r in freeze["cases"]] == list(OWNERS)
        and [r.get("core") for r in prediction["geometry"]] == list(CORES)
        and [r.get("id") for r in original["cores"]] == list(CORES),
        "Scientific source owner/axis order differs",
    )
    physical = original["physical"]
    require(
        finite(physical["turbulence_parameter"]) / 2 == Fraction(1, 8),
        "Survival exponent differs",
    )
    require(
        all(
            finite(physical[k]) > 0
            for k in ("diffusion_coefficient", "wind_speed_m_s", "regional_extent_m")
        )
        and len(public["fall_speed_m_s"]) == 2
        and all(finite(x) > 0 for x in public["fall_speed_m_s"]),
        "Positive physical source parameters required",
    )
    prefixes = freeze["native_prefix"]
    require(
        [r.get("taxon") for r in prefixes] == list(AXIS), "Captured prefix axis differs"
    )
    coefficients = []
    for i, row in enumerate(prefixes):
        expected = {
            name: float(physical[name])
            for name in (
                "diffusion_coefficient",
                "turbulence_parameter",
                "wind_speed_m_s",
            )
        }
        expected["fall_speed_m_s"] = float(public["fall_speed_m_s"][i])
        require(
            _same_json(row.get("parameters"), expected),
            "Captured native parameters differ",
        )
        s1, survival = _captured(row.get("S1"), "S1")
        a, coefficient = _captured(row.get("A"), "A")
        require(
            0 < survival < 1 and coefficient > 0 and (-math.log(s1)).hex() == a.hex(),
            "Captured A/S1 arithmetic differs",
        )
        coefficients.append(coefficient)
    geometries, edges = [], []
    for i, (core, _) in enumerate(OWNERS):
        row, saved, captured = (
            public["geometry"][i],
            prediction["geometry"][i // 2],
            freeze["cases"][i],
        )
        order = [c for c in CORES if c != core]
        require(
            row.get("anchor_order")
            == saved.get("anchor_order")
            == captured.get("anchor_order")
            == order
            and _same_json(row.get("anchor_xy_m"), saved.get("anchor_xy_m")),
            "Original anchor ownership/order differs",
        )
        xy = row["anchor_xy_m"]
        require(
            isinstance(xy, list)
            and len(xy) == 2
            and all(isinstance(p, list) and len(p) == 2 for p in xy),
            "Two original anchors required",
        )
        geometry = Geometry(
            coefficients[i % 2],
            finite(original["cores"][i // 2]["radius_m"]),
            finite(physical["regional_extent_m"]),
            (finite(xy[0][0]), finite(xy[0][1])),
            (finite(xy[1][0]), finite(xy[1][1])),
        )
        require(
            _same_json(captured.get("geometry"), geometry.encoded()),
            "Captured geometry drift",
        )
        selected = nested_edges(saved, geometry.receiver, geometry.outer)
        require(
            protocol.get("edges_exact", {}).get(core) == [str(x) for x in selected],
            "Declared exact nested edges differ",
        )
        geometries.append(geometry)
        edges.append(selected)
    return tuple(geometries), tuple(edges)

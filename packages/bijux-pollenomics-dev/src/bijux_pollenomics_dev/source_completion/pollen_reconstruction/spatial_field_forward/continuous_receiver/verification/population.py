"""Audit complete case accounting separately from independent precision acceptance."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from .certificates import verify_certificate
from .contracts import (
    OWNERS,
    RESOURCE_LIMITS,
    Clock,
    _same_json,
    bounds,
    finite,
    integer,
    require,
)
from .sources import reference_checks, select_sources, validate_protocol


def audit(
    protocol: Mapping[str, Any],
    source: Mapping[str, Any],
    original: Mapping[str, Any],
    freeze: Mapping[str, Any],
    result: Mapping[str, Any],
    certificates: list[dict[str, Any]],
    clock: Clock,
) -> dict[str, Any]:
    """Check every case disposition and its saved coefficient certificates."""
    validate_protocol(protocol)
    require(
        result.get("schema_version") == "continuous-receiver-study-result.v1"
        and freeze.get("schema_version") == "continuous-receiver-input-freeze.v1",
        "Unknown study packet",
    )
    revision = result.get("source_commit")
    require(
        isinstance(revision, str)
        and len(revision) == 40
        and set(revision) <= set("0123456789abcdef")
        and freeze.get("source_commit") == revision,
        "Source commit differs",
    )
    require(
        result.get("input_files")
        == freeze.get("input_files")
        == protocol["input_files"],
        "Public input pins differ",
    )
    require(
        result.get("protocol_file") == freeze.get("protocol_file"),
        "Protocol byte receipt differs",
    )
    cases = select_sources(source, original, freeze)
    rows = cast(list[dict[str, Any]], result.get("cases"))
    require(
        isinstance(rows, list)
        and [
            (
                integer(row.get("case_index"), "case index", 5),
                row.get("core"),
                row.get("taxon"),
            )
            for row in rows
        ]
        == [(i, *owner) for i, owner in enumerate(OWNERS)],
        "Missing/doubled/foreign result owner",
    )
    closed = result.get("certificate_closed")
    require(type(closed) is bool, "Certificate closure flag missing")
    mapping = cast(list[dict[str, Any]], result.get("certificate_cases"))
    require(
        isinstance(mapping, list) and len(mapping) == len(certificates),
        "Certificate population mismatch",
    )
    require(
        [
            integer(row.get("certificate_index"), "certificate index", 5)
            for row in mapping
        ]
        == list(range(len(certificates))),
        "Certificate index missing/doubled/reordered",
    )
    indices = [
        integer(row.get("case_index"), "certificate owner index", 5) for row in mapping
    ]
    require(indices == sorted(set(indices)), "Certificate owner repeated/reordered")
    require(
        all(
            (row.get("core"), row.get("taxon")) == OWNERS[index]
            for row, index in zip(mapping, indices, strict=True)
        ),
        "Foreign certificate owner",
    )
    require(closed or not mapping, "Unclosed proof mapped as available")
    require(
        result.get("source_guards_pass") is True
        and result.get("resource_guards_pass") is True,
        "Producer source/resource refusal",
    )
    require(
        _same_json(result.get("resource_limits"), RESOURCE_LIMITS),
        "Producer limits differ",
    )
    elapsed = float(finite(result.get("elapsed_seconds")))
    integration_elapsed = float(finite(result.get("integration_elapsed_seconds")))
    require(
        0 <= elapsed < 180 and 0 <= integration_elapsed <= elapsed,
        "Producer elapsed accounting differs",
    )
    require(
        integer(result.get("peak_rss_bytes"), "producer RSS", 805306368) > 0,
        "Producer RSS missing",
    )
    accounting = []
    all_widths = True
    all_complete = True
    work_totals = dict.fromkeys(
        (
            "attempted_panels",
            "reserved_node_evaluations",
            "completed_node_evaluations",
            "derivative_boxes",
            "leaf_reservations",
        ),
        0,
    )
    indexed = dict(zip(indices, range(len(certificates)), strict=True))
    for i, (case, row) in enumerate(zip(cases, rows, strict=True)):
        clock.current_case = (case["core"], case["taxon"])
        clock.check()
        work = cast(dict[str, Any], row.get("work"))
        require(
            isinstance(work, dict) and set(work) == set(work_totals),
            "Case work fields differ",
        )
        for name, maximum in (
            ("attempted_panels", 8191),
            ("reserved_node_evaluations", 73719),
            ("completed_node_evaluations", 73719),
            ("derivative_boxes", 16382),
            ("leaf_reservations", 4096),
        ):
            work_totals[name] += integer(work[name], name, maximum)
        require(
            work["completed_node_evaluations"] <= work["reserved_node_evaluations"]
            and work["derivative_boxes"] <= 2 * work["attempted_panels"],
            "Work reservation accounting differs",
        )
        if i not in indexed:
            all_complete = False
            all_widths = False
            if not closed:
                require(
                    row.get("complete_geometry_certificate") is False
                    and row.get("all_final_widths_pass") is False
                    and row.get("positive_bounds_usable") is False
                    and row.get("references") is None,
                    "Unavailable proof promoted",
                )
                require(
                    isinstance(result.get("certificate_refusal"), str)
                    and bool(result["certificate_refusal"]),
                    "Unavailable proof lacks refusal",
                )
                if row.get("math_bounds") is not None:
                    native_bounds = row["math_bounds"]
                    require(
                        set(native_bounds) == {"K", "B1", "B2"}
                        and row.get("widths_exact")
                        == {
                            name: str(bounds(value).width)
                            for name, value in native_bounds.items()
                        },
                        "Unavailable numerical metadata falsified",
                    )
                    require(
                        row.get("backend_status")
                        in ("certified_width", "refuse_unresolved"),
                        "Unavailable backend status differs",
                    )
                else:
                    require(
                        row.get("backend_status") is None
                        and row.get("widths_exact") is None,
                        "Unavailable case metadata differs",
                    )
                accounting.append(
                    {
                        "core": case["core"],
                        "taxon": case["taxon"],
                        "status": "aggregate_certificate_unavailable",
                        "refusal": result["certificate_refusal"],
                        "backend_status": row.get("backend_status"),
                        "backend_refusal": row.get("backend_refusal"),
                    }
                )
                continue
            require(
                row.get("complete_geometry_certificate") is False
                and row.get("backend_status") is None,
                "Incomplete case promoted",
            )
            require(
                row.get("math_bounds") is None
                and row.get("widths_exact") is None
                and row.get("references") is None,
                "Incomplete case supplied fabricated numerical result",
            )
            require(
                all(
                    row.get(name) is False
                    for name in (
                        "all_final_widths_pass",
                        "positive_bounds_usable",
                        "local_integral_allocations_pass",
                        "endpoint_product_allocations_pass",
                        "local_allocations_pass",
                    )
                ),
                "Incomplete case promoted an acceptance flag",
            )
            require(
                isinstance(row.get("backend_refusal"), str)
                and bool(row["backend_refusal"]),
                "Incomplete owner lacks refusal",
            )
            accounting.append(
                {
                    "core": case["core"],
                    "taxon": case["taxon"],
                    "status": "incomplete_source_geometry",
                    "refusal": row["backend_refusal"],
                }
            )
            continue
        require(
            row.get("complete_geometry_certificate") is True,
            "Closed available case mislabeled",
        )
        checked = verify_certificate(certificates[indexed[i]], case["geometry"], clock)
        native = checked["saved_bounds"]
        require(row.get("math_bounds") == native, "Result/certificate bounds differ")
        widths = {
            name: str(bounds(interval).width) for name, interval in native.items()
        }
        require(row.get("widths_exact") == widths, "Result width falsified")
        require(
            row.get("all_final_widths_pass") is checked["all_final_widths_pass"],
            "Final acceptance flag falsified",
        )
        require(
            row.get("backend_status")
            == (
                "certified_width"
                if checked["all_final_widths_pass"]
                else "refuse_unresolved"
            ),
            "Backend status falsified",
        )
        require(
            row.get("positive_bounds_usable") is checked["positive_bounds_usable"],
            "Positive lower-bound flag falsified",
        )
        require(
            row.get("local_integral_allocations_pass")
            is checked["local_integral_allocations_pass"]
            and row.get("endpoint_product_allocations_pass")
            is checked["endpoint_product_allocations_pass"]
            and row.get("local_allocations_pass") is checked["local_allocations_pass"],
            "Auxiliary allocation diagnostic falsified",
        )
        require(
            _same_json(
                row.get("references"), reference_checks(case["references"], native)
            ),
            "Saved reference comparison falsified",
        )
        require(
            work["leaf_reservations"] >= checked["leaves"], "Uncharged saved leaves"
        )
        require(
            work["completed_node_evaluations"] >= checked["minimum_completed_nodes"]
            and work["attempted_panels"] >= checked["minimum_attempted_panels"]
            and work["derivative_boxes"] >= checked["minimum_derivative_boxes"],
            "Uncharged closed ancestor/node population",
        )
        all_widths = all_widths and checked["independent_all_final_widths_pass"]
        accounting.append(
            {
                "core": case["core"],
                "taxon": case["taxon"],
                "status": "independently_certified_width"
                if checked["independent_all_final_widths_pass"]
                else "independent_width_unresolved",
                "backend_refusal": row.get("backend_refusal"),
                **checked,
                "independent_references": reference_checks(
                    case["references"], checked["independent_bounds"]
                ),
            }
        )
    require(
        work_totals["attempted_panels"] <= 49146
        and work_totals["reserved_node_evaluations"] <= 442314
        and work_totals["leaf_reservations"] <= 24576,
        "Global work cap exceeded",
    )
    require(
        result.get("all_population_complete") is all_complete,
        "Complete population flag falsified",
    )
    saved_all = all_complete and all(row["all_final_widths_pass"] for row in rows)
    require(
        result.get("status")
        == ("all_coefficients_certified" if saved_all else "refuse_unresolved"),
        "Overall result status falsified",
    )
    return {
        "schema_version": "continuous-receiver-independent-check.v1",
        "status": "passed" if all_complete and all_widths else "refuse_unresolved",
        "accounting_verified": True,
        "all_population_complete": all_complete,
        "independent_all_18_widths_pass": all_complete and all_widths,
        "producer_all_18_widths_pass": saved_all,
        "producer_source_commit": revision,
        "cases": accounting,
        "work_totals": work_totals,
        "limits": "Conditional ideal newly captured-A law on saved finite static geometry. Independent fixed-leaf formulas and assembly reuse the separately controlled Interval/Jet elementary library. No adaptive integration, raw counts, forecasts, field/vegetation accuracy or historical-A authentication. Producer interval overlap is correspondence; independently recomputed enclosures carry the independent mathematical claim.",
    }

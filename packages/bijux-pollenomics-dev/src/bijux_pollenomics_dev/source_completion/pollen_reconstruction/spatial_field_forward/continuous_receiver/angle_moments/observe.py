"""Independently replay the saved fixed leaves without adaptive reintegration."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import signal
import time
from typing import Any, cast

from ..verification.contracts import (
    EPSILON,
    OWNERS,
    RESOURCE_LIMITS,
    Clock,
    _same_json,
    bounds,
    integer,
    rational,
)
from ..verification.geometry import Geometry
from ..verification.receiver_angles import verify_angle_certificate
from . import METHOD
from .inputs import decode, identity, read_inputs, read_regular, require
from .transport import (
    check_terminal,
    environment,
    fresh_output,
    source_guard,
    write_json,
)


def _deadline(_number: int, _frame: object) -> None:
    raise TimeoutError("Original observer 180-second process ceiling reached")


def _producer(
    root: Path, directory: Path
) -> tuple[dict[str, Any], dict[str, Any], list[Any], dict[str, Any]]:
    """Bind all three immutable producer products before reading any certificate."""
    relative = directory.relative_to(root).as_posix()
    bodies = {
        name: read_regular(root, relative + "/" + name, 5_000_000)
        for name in ("execution-context.json", "result.json", "certificates.json")
    }
    require(
        sum(len(raw) for raw in bodies.values()) <= 5_000_000,
        "Producer products exceed original byte ceiling",
    )
    context, result = (
        decode(bodies[name]) for name in ("execution-context.json", "result.json")
    )
    certificates = decode(b'{"certificates":' + bodies["certificates.json"] + b"}")[
        "certificates"
    ]
    require(
        type(certificates) is list and len(certificates) <= 6,
        "Invalid certificate population",
    )
    require(
        result.get("certificate_identity") == identity(bodies["certificates.json"]),
        "Producer certificate identity differs",
    )
    return (
        context,
        result,
        certificates,
        {name: identity(raw) for name, raw in bodies.items()},
    )


def _geometry(values: dict[str, Any]) -> Geometry:
    """Construct independent geometry directly from original rational strings."""
    first = tuple(rational(x) for x in values["first_anchor_xy_m"])
    second = tuple(rational(x) for x in values["second_anchor_xy_m"])
    require(len(first) == len(second) == 2, "Independent planar anchors required")
    return Geometry(
        rational(values["coefficient_A"]),
        rational(values["receiver_radius_m"]),
        rational(values["outer_radius_m"]),
        (first[0], first[1]),
        (second[0], second[1]),
    )


def _work(row: dict[str, Any], replay: dict[str, Any] | None) -> dict[str, int]:
    """Check observed reservations and independently derived saved-forest minima."""
    work = row.get("work")
    require(
        type(work) is dict
        and set(work)
        == {
            "attempted_panels",
            "reserved_node_evaluations",
            "completed_node_evaluations",
            "derivative_boxes",
            "leaf_reservations",
        },
        "Producer work fields differ",
    )
    caps = {
        "attempted_panels": 8191,
        "reserved_node_evaluations": 73719,
        "completed_node_evaluations": 73719,
        "derivative_boxes": 8191,
        "leaf_reservations": 4096,
    }
    counts = {
        name: integer(cast(dict[str, Any], work)[name], name, cap)
        for name, cap in caps.items()
    }
    require(
        counts["completed_node_evaluations"] <= counts["reserved_node_evaluations"]
        and counts["reserved_node_evaluations"] == 7 * counts["attempted_panels"]
        and counts["derivative_boxes"] <= counts["attempted_panels"],
        "Impossible one-dimensional work accounting",
    )
    if replay is not None:
        for name, minimum in (
            ("attempted_panels", "minimum_attempted_panels"),
            ("completed_node_evaluations", "minimum_completed_nodes"),
            ("derivative_boxes", "minimum_derivative_boxes"),
            ("leaf_reservations", "leaves"),
        ):
            require(
                counts[name] >= replay[minimum],
                "Saved forest exceeds producer work accounting",
            )
    return counts


def run_observer(
    root: Path, protocol: Path, producer: Path, output: Path
) -> dict[str, Any]:
    """Retain six owners and report own mathematical ranges, never overlap as precision."""
    started = time.monotonic()
    root, protocol, producer, output = (
        root.resolve(),
        protocol.resolve(),
        producer.absolute(),
        output.absolute(),
    )
    require(
        protocol.is_relative_to(root) and producer.is_relative_to(root / "artifacts"),
        "Observer input escaped source/artifact owner",
    )
    destination = fresh_output(root, output)
    report: dict[str, Any] = {
        "schema_version": "continuous-receiver-angle-moments-observer.v1",
        "method": METHOD,
        "status": "failed",
        "cases": [
            {"case_index": i, "core": core, "taxon": taxon, "status": "not_replayed"}
            for i, (core, taxon) in enumerate(OWNERS)
        ],
    }
    clock: Clock | None = None
    previous = signal.signal(signal.SIGALRM, _deadline)
    signal.setitimer(signal.ITIMER_REAL, 180)
    try:
        inputs = read_inputs(root, protocol)
        runtime = environment(root)
        before = source_guard(root, inputs)
        context, result, certificates, pins = _producer(root, producer)
        require(
            _same_json(context.get("source"), asdict(before))
            and result.get("source_commit") == before.head
            and result.get("method") == context.get("method") == METHOD
            and result.get("schema_version")
            == "continuous-receiver-angle-moments-result.v1"
            and result.get("status")
            in ("producer_precision_usable", "refuse_unresolved")
            and result.get("native_prefix_recaptured") is False,
            "Producer source/method/result scope differs",
        )
        require(
            _same_json(context.get("inputs"), inputs.identities)
            and _same_json(result.get("input_identities"), inputs.identities)
            and _same_json(context.get("law"), inputs.protocol["law"])
            and _same_json(context.get("resources"), RESOURCE_LIMITS)
            and _same_json(result.get("resource_limits"), RESOURCE_LIMITS),
            "Producer law/input/resource identity differs",
        )
        require(
            result["terminal"]["source_and_index_unchanged"] is True
            and result["terminal"]["inputs_unchanged"] is True
            and 0 <= result["terminal"]["elapsed_seconds"] < 180
            and result["terminal"]["peak_rss_bytes"] <= 805306368,
            "Producer terminal source/resource qualification differs",
        )
        write_json(
            destination,
            "execution-context.json",
            {
                "source": asdict(before),
                "inputs": inputs.identities,
                "environment": runtime,
                "producer_products": pins,
                "resources": inputs.protocol["independent_resources"],
            },
        )
        rows = result.get("cases")
        require(
            type(rows) is list and len(rows) == 6,
            "Producer six-owner disposition incomplete",
        )
        clock = Clock(160)
        observed = cast(list[dict[str, Any]], report["cases"])
        report.update(source_commit=before.head, producer_products=pins)
        certificate_index = 0
        width_count = positive_count = saved_width_count = saved_positive_count = 0
        for index, (frozen, row) in enumerate(
            zip(inputs.freeze["cases"], cast(list[dict[str, Any]], rows), strict=True)
        ):
            core, taxon = OWNERS[index]
            require(
                type(row) is dict
                and type(row.get("case_index")) is int
                and row["case_index"] == index
                and (row.get("core"), row.get("taxon")) == (core, taxon)
                and _same_json(row.get("geometry"), frozen["geometry"])
                and type(row.get("complete")) is bool,
                "Producer owner/geometry disposition differs",
            )
            clock.current_case = (core, taxon)
            own: dict[str, Any] = {
                "case_index": index,
                "core": core,
                "taxon": taxon,
                "complete": row["complete"],
            }
            own["status"] = "replay_started"
            observed[index] = own
            replay = None
            if row["complete"]:
                require(
                    type(row.get("certificate_index")) is int
                    and row["certificate_index"] == certificate_index
                    and certificate_index < len(certificates),
                    "Missing/duplicate/foreign certificate",
                )
                replay = verify_angle_certificate(
                    certificates[certificate_index],
                    _geometry(frozen["geometry"]),
                    clock,
                )
                own.update(status="fixed_leaf_replayed", **replay)
                certificate_index += 1
                saved = replay["saved_bounds"]
                widths = {
                    name: str(bounds(saved[name]).width) for name in ("K", "B1", "B2")
                }
                saved_widths = [
                    bounds(saved[name]).width <= EPSILON for name in ("K", "B1", "B2")
                ]
                saved_positive = [
                    bounds(saved[name]).lower > 0 for name in ("K", "B1", "B2")
                ]
                require(
                    row.get("status") == certificates[certificate_index - 1]["status"]
                    and row.get("q_bound")
                    == certificates[certificate_index - 1]["approximation"]["q_bound"]
                    and row.get("global_series_remainder_radius")
                    == certificates[certificate_index - 1]["approximation"][
                        "remainder_radius"
                    ]
                    and _same_json(row.get("coefficient_bounds"), saved)
                    and _same_json(row.get("widths"), widths)
                    and _same_json(row.get("width_pass"), saved_widths)
                    and _same_json(row.get("positive_bounds"), saved_positive)
                    and row.get("saved_leaves") == replay["leaves"]
                    and row.get("complete_domains") == replay["initial_domains"],
                    "Producer reported mathematical flags differ",
                )
                width_count += sum(
                    rational(value) <= EPSILON
                    for value in replay["independent_widths"].values()
                )
                positive_count += sum(
                    bounds(value).lower > 0
                    for value in replay["independent_bounds"].values()
                )
                saved_width_count += sum(saved_widths)
                saved_positive_count += sum(saved_positive)
            else:
                require(
                    "certificate_index" not in row, "Incomplete owner has a certificate"
                )
                own.update(
                    status="producer_initial_coverage_incomplete",
                    backend_refusal=row.get("backend_refusal"),
                )
            own["producer_work"] = _work(row, replay)
            report.update(
                complete_cases=certificate_index,
                independent_certified_widths=width_count,
                independent_positive_bounds=positive_count,
                producer_certified_widths=saved_width_count,
                producer_positive_bounds=saved_positive_count,
                completed_leaves=clock.completed_leaves,
            )
        require(
            certificate_index
            == len(certificates)
            == integer(result.get("complete_cases"), "complete cases", 6),
            "Certificate-owner bijection differs",
        )
        require(
            integer(result.get("certified_widths"), "producer width count", 18)
            == saved_width_count
            and integer(result.get("positive_bounds"), "producer positivity count", 18)
            == saved_positive_count,
            "Producer final precision counts differ",
        )
        require(
            _producer(root, producer)[3] == pins,
            "Producer products changed during replay",
        )
        terminal = check_terminal(root, protocol, before, inputs, started, destination)
        passed = (
            certificate_index == 6
            and width_count
            == positive_count
            == saved_width_count
            == saved_positive_count
            == 18
        )
        require(
            result["status"]
            == (
                "producer_precision_usable"
                if saved_width_count == saved_positive_count == 18
                else "refuse_unresolved"
            ),
            "Producer final precision status differs",
        )
        report.update(
            status="precision_usable" if passed else "refuse_unresolved",
            accounting_verified=True,
            source_commit=before.head,
            producer_products=pins,
            cases=observed,
            terminal=terminal,
            complete_cases=certificate_index,
            independent_certified_widths=width_count,
            independent_positive_bounds=positive_count,
            producer_certified_widths=saved_width_count,
            producer_positive_bounds=saved_positive_count,
            completed_leaves=clock.completed_leaves,
            scope="Independent fixed-leaf mathematics; overlap is consistency only; no adaptive replay, target inspection, A recapture, refit, prediction, score or field claim",
        )
    except Exception as error:
        if clock is not None:
            report["progress"] = {
                "current_case": clock.current_case,
                "current_domain": clock.current_domain,
                "completed_leaves": clock.completed_leaves,
            }
        report["error"] = str(error)
        report["elapsed_seconds_at_failure"] = time.monotonic() - started
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        write_json(destination, "independent-check.json", report)
    return report


def main() -> None:
    """Read one committed producer run into a distinct fresh artifact directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--producer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_observer(args.repository, args.protocol, args.producer, args.output)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "source_commit",
                    "complete_cases",
                    "independent_certified_widths",
                    "independent_positive_bounds",
                )
            }
        )
    )


if __name__ == "__main__":
    main()

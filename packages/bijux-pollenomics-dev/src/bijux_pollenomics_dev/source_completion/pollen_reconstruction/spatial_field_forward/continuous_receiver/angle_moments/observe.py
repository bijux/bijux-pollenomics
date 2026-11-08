"""Independently replay the saved fixed leaves without adaptive reintegration."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import signal
import subprocess
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
    SourceGuard,
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


_SOURCE_OWNER = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_reconstruction/spatial_field_forward/continuous_receiver/"
_OBSERVER_ONLY = frozenset(
    (
        _SOURCE_OWNER + "verification/receiver_angles.py",
        _SOURCE_OWNER + "angle_moments/observe.py",
    )
)


def _external_receipts(
    root: Path, producer: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Bind the original completed-process supervision and its small logs."""
    parent = producer.parent
    relative = parent.relative_to(root).as_posix()
    expected = {
        "supervision-context.json",
        "supervision-terminal.json",
        "stdout.log",
        "stderr-time.log",
        *(
            "products/" + name
            for name in ("execution-context.json", "result.json", "certificates.json")
        ),
    }
    paths = list(parent.rglob("*"))
    require(
        len(paths) <= 16 and not any(path.is_symlink() for path in paths),
        "Unexpected producer output tree",
    )
    files = {path.relative_to(parent).as_posix() for path in paths if path.is_file()}
    require(
        files == expected and producer.name == "products",
        "Original producer output members differ",
    )
    total = sum(path.stat().st_size for path in paths if path.is_file())
    require(total <= 5_000_000, "Original producer all-output ceiling exceeded")
    bodies = {
        name: read_regular(root, relative + "/" + name, 150_000)
        for name in (
            "supervision-context.json",
            "supervision-terminal.json",
            "stdout.log",
            "stderr-time.log",
        )
    }
    context, terminal = (
        decode(bodies[name])
        for name in ("supervision-context.json", "supervision-terminal.json")
    )
    require(
        type(terminal.get("returncode")) is int
        and terminal["returncode"] == 0
        and terminal.get("timed_out") is False
        and terminal.get("source_head_and_index_unchanged") is True
        and terminal.get("process_cap_pass") is True
        and terminal.get("rss_cap_pass") is True
        and terminal.get("output_cap_pass") is True,
        "Original producer supervision failed",
    )
    require(
        type(terminal.get("elapsed_seconds")) in (int, float)
        and 0 <= terminal["elapsed_seconds"] < 180
        and integer(terminal.get("peak_rss_bytes"), "producer peak RSS", 805306368) > 0
        and integer(
            terminal.get("all_output_bytes"), "producer all-output bytes", 5_000_000
        )
        == total,
        "Original producer external resource receipt differs",
    )
    require(
        context.get("whole_process_limit_seconds") == 180
        and context.get("original_integration_work_seconds") == 160
        and context.get("peak_rss_posthoc_maximum_bytes") == 805306368
        and context.get("all_output_maximum_bytes") == 5_000_000,
        "Original producer supervision ceilings differ",
    )
    return context, terminal, {name: identity(raw) for name, raw in bodies.items()}


def _producer_source(
    root: Path,
    producer: Path,
    context: dict[str, Any],
    result: dict[str, Any],
    before: SourceGuard,
) -> dict[str, Any]:
    """Authenticate historical producer bytes while allowing only observer equations to change."""
    original = context.get("source")
    if _same_json(original, asdict(before)):
        require(
            result.get("source_commit") == before.head, "Producer source claim differs"
        )
        return {
            "kind": "same_committed_source",
            "producer_source_commit": before.head,
            "observer_source_commit": before.head,
            "observer_only_differences": [],
        }
    require(
        type(original) is dict and set(original) == {"head", "index_sha256", "files"},
        "Historical producer source guard malformed",
    )
    original = cast(dict[str, Any], original)
    head = original["head"]
    require(
        type(head) is str
        and len(head) == 40
        and all(c in "0123456789abcdef" for c in head)
        and result.get("source_commit") == head,
        "Historical producer revision/claim differs",
    )
    git = ["git", "--no-optional-locks", "--no-replace-objects", "-C", str(root)]
    ancestor = subprocess.run(
        [*git, "merge-base", "--is-ancestor", head, before.head],
        capture_output=True,
        timeout=30,
        check=False,
    )
    require(ancestor.returncode == 0, "Producer source is not a committed ancestor")
    rows = original["files"]
    current = dict(before.files)
    require(
        type(rows) is list and len(rows) == len(current),
        "Historical source closure path count differs",
    )
    historical = {}
    for row in rows:
        require(
            type(row) is list
            and len(row) == 2
            and type(row[0]) is str
            and type(row[1]) is str
            and len(row[1]) == 64
            and all(c in "0123456789abcdef" for c in row[1])
            and row[0] not in historical,
            "Historical source closure entry malformed",
        )
        historical[row[0]] = row[1]
    require(set(historical) == set(current), "Historical source closure paths differ")
    total = 0
    changes = []
    for name, digest in historical.items():
        object_name = head + ":" + name
        size = int(
            subprocess.check_output([*git, "cat-file", "-s", object_name], timeout=30)
        )
        total += size
        require(
            0 <= size <= 5_000_000 and total <= 5_000_000,
            "Historical source closure byte cap exceeded",
        )
        raw = subprocess.check_output(
            [*git, "cat-file", "blob", object_name], timeout=30
        )
        require(
            len(raw) == size and hashlib.sha256(raw).hexdigest() == digest,
            "Historical source does not match its committed Git blob",
        )
        if current[name] != digest:
            require(name in _OBSERVER_ONLY, "Protected producer source changed")
            changes.append(
                {
                    "path": name,
                    "producer_sha256": digest,
                    "observer_sha256": current[name],
                }
            )
    external_context, external_terminal, external_pins = _external_receipts(
        root, producer
    )
    require(
        external_context.get("source_commit")
        == external_terminal.get("source_commit")
        == head
        and external_context.get("index_sha256_before") == original["index_sha256"],
        "Original producer external source/index identity differs",
    )
    return {
        "kind": "historical_producer_unchanged_equations",
        "producer_source_commit": head,
        "observer_source_commit": before.head,
        "historical_git_blobs_authenticated": True,
        "unchanged_producer_source_files": len(current) - len(changes),
        "observer_only_differences": changes,
        "external_receipts": external_pins,
        "producer_external_terminal": external_terminal,
    }


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
        bridge = _producer_source(root, producer, context, result, before)
        require(
            result.get("method") == context.get("method") == METHOD
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
                "producer_source_bridge": bridge,
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
        report.update(
            source_commit=before.head,
            producer_products=pins,
            producer_source_bridge=bridge,
        )
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
        if "external_receipts" in bridge:
            require(
                _external_receipts(root, producer)[2] == bridge["external_receipts"],
                "Original producer external receipts changed during replay",
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

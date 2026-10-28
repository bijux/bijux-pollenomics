"""Close all conditional forecasts before opening their source-window outcomes."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ...author_lra_spatial.products import (
    code_state,
    file_sha,
    reopen,
    resources,
    write,
)
from ...nordic_coupled.literal_window_support.study import read_pin
from ..inputs import decode, physical, require
from .evaluation import score_closed, summarize
from .inputs import load_inputs
from .prediction import predict_all
from .responses import build_responses


def source_state(repository: Path) -> dict[str, Any]:
    """Guard maintained Python and R without publishing a code hash registry."""
    state = code_state(repository)
    names = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "--", "packages"], cwd=repository
        )
        .decode()
        .split("\0")
    )
    state["r_files"] = {
        name: file_sha(repository / name)
        for name in names
        if name.lower().endswith(".r")
    }
    return state


def produce(
    repository: Path,
    protocol_path: Path,
    output: Path,
    *,
    compute_response: Callable[..., Any] | None = None,
    inverse: Callable[..., tuple[float, ...]] | None = None,
    forward: Callable[..., tuple[float, ...]] | None = None,
) -> dict[str, Any]:
    """Use injected numerical operators only in source-free controlled fixtures."""
    started = time.monotonic()
    physical(repository)
    physical(protocol_path)
    output = require_absent_artifact_output(repository, output)
    before = source_state(repository)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    require(
        protocol_path.is_relative_to(repository),
        "Repository-owned prospective protocol required",
    )
    protocol_pin = {
        "path": str(protocol_path.relative_to(repository)),
        "bytes": len(raw_protocol),
        "sha256": hashlib.sha256(raw_protocol).hexdigest(),
    }
    packet = load_inputs(repository, protocol)
    response = build_responses(
        protocol,
        **({"compute": compute_response} if compute_response is not None else {}),
    )
    output.mkdir()
    maximum = protocol["limits"]["max_output_bytes"]
    products = {"responses": write(output, "responses.json", response, maximum)}
    resources(started, output, protocol["limits"])
    callbacks = {}
    if inverse is not None:
        callbacks["inverse"] = inverse
    if forward is not None:
        callbacks["forward"] = forward
    contexts = predict_all(packet, protocol, response, **callbacks)
    freeze = {
        "schema_version": "nordic-physical-predictions.v1",
        "source_commit": before["head"],
        "protocol": protocol_pin,
        "response_file": products["responses"],
        "contexts": contexts,
    }
    products["prediction_freeze"] = write(
        output, "prediction-freeze.json", freeze, maximum
    )
    resources(started, output, protocol["limits"])
    # Score ownership starts only after ALL prediction and response bytes close.
    scores = score_closed(
        output, products["prediction_freeze"], products["responses"], packet, protocol
    )
    products["scores"] = write(
        output,
        "scores.json",
        {
            "schema_version": "nordic-physical-scores.v1",
            "prediction_file": products["prediction_freeze"],
            "rows": scores,
        },
        maximum,
    )
    products["summary"] = write(
        output, "summary.json", summarize(scores, protocol), maximum
    )
    for pin in products.values():
        reopen(output, pin)
    require(
        {p.name for p in output.iterdir()} == {p["path"] for p in products.values()},
        "Unowned file in closed producer inventory",
    )
    for pin in packet["sourcepins"]:
        read_pin(repository, pin, protocol["source_max_bytes"])
    require(
        protocol_path.read_bytes() == raw_protocol
        and source_state(repository) == before,
        "Consumed sources, protocol, Python/R, HEAD or index changed",
    )
    result = {
        "schema_version": "nordic-physical-transfer-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": before["head"],
        "index_sha256": before["index_sha256"],
        "protocol": protocol_pin,
        "sourcepins": packet["sourcepins"],
        "products": products,
        "source_guards_passed": True,
        "resources": resources(started, output, protocol["limits"]),
        "scope": protocol["claim"],
        "previously_exposed_development": True,
        "uncertainty_evaluated": False,
        "scientific_or_field_admission": False,
    }
    write(output, "result.json", result, maximum)
    require(
        {p.name for p in output.iterdir()}
        == {p["path"] for p in products.values()} | {"result.json"},
        "Closed five-product inventory required",
    )
    resources(started, output, protocol["limits"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("repository", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()

    def timeout(*_: object) -> None:
        raise TimeoutError("180 second conditional physical transfer ceiling")

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(180)
    try:
        result = produce(
            args.repository.absolute(), args.protocol.absolute(), args.output.absolute()
        )
        print(
            json.dumps({"status": result["status"], "resources": result["resources"]})
        )
    finally:
        signal.alarm(0)

"""Load closed scientific packets and run the bounded independent observer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import time
from typing import Any, cast

from .contracts import (
    INPUT_NAMES,
    MAX_BYTES,
    Clock,
    VerificationError,
    _rss,
    _unique,
    bound_file,
    identity,
    integer,
    parse,
    require,
)
from .population import audit
from .sources import validate_protocol


def _pin_file(pin: object, name: str) -> dict[str, Any]:
    require(
        isinstance(pin, dict)
        and set(pin) == {"path", "bytes", "sha256"}
        and pin.get("path") == name,
        "Foreign scientific file locator",
    )
    row = cast(dict[str, Any], pin)
    integer(row["bytes"], "scientific file bytes", MAX_BYTES)
    require(
        type(row["sha256"]) is str
        and len(row["sha256"]) == 64
        and set(row["sha256"]) <= set("0123456789abcdef"),
        "Invalid scientific SHA",
    )
    return {"bytes": row["bytes"], "sha256": row["sha256"]}


def _owned(repository: Path, path: Path) -> Path:
    absolute = path.absolute() if path.is_absolute() else repository / path
    require(
        ".." not in absolute.parts and absolute.is_relative_to(repository),
        "Scientific locator escapes repository",
    )
    current = repository
    for part in absolute.relative_to(repository).parts:
        current = current / part
        require(not current.is_symlink(), "Symlink scientific locator")
    require(
        absolute.resolve().is_relative_to(repository),
        "Scientific locator resolves outside repository",
    )
    return absolute


def load_packet(
    repository: Path, protocol_path: Path, study_output: Path
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    repository = repository.resolve()
    protocol_path = _owned(repository, protocol_path)
    study_output = _owned(repository, study_output)
    require(
        not protocol_path.is_symlink()
        and protocol_path.resolve().is_relative_to(repository),
        "Foreign protocol path",
    )
    require(protocol_path.stat().st_size <= 1_000_000, "Protocol byte cap exceeded")
    protocol_raw = protocol_path.read_bytes()
    require(len(protocol_raw) <= 1_000_000, "Protocol byte cap exceeded")
    protocol = parse(protocol_raw)
    validate_protocol(protocol)
    require(
        not study_output.is_symlink()
        and study_output.resolve().is_relative_to(repository / "artifacts"),
        "Study output must be repository-owned artifacts",
    )
    allowed = {"result.json", "input-freeze.json", "certificates.json"}
    files = list(study_output.iterdir())
    require(
        all(
            path.name in allowed and path.is_file() and not path.is_symlink()
            for path in files
        ),
        "Undeclared/unsafe study output member",
    )
    require(
        sum(path.stat().st_size for path in files) <= MAX_BYTES,
        "Study byte cap exceeded",
    )
    result = parse((study_output / "result.json").read_bytes())
    name = str(protocol_path.resolve().relative_to(repository))
    require(
        _pin_file(result.get("protocol_file"), name) == identity(protocol_raw),
        "Protocol file identity differs",
    )
    require(
        result.get("input_freeze") == "input-freeze.json",
        "Input freeze locator differs",
    )
    freeze_raw = bound_file(
        study_output / "input-freeze.json",
        _pin_file(result.get("input_freeze_file"), "input-freeze.json"),
    )
    freeze = parse(freeze_raw)
    require(
        freeze.get("protocol_file") == result["protocol_file"],
        "Frozen protocol identity differs",
    )
    inputs = []
    for input_name in INPUT_NAMES:
        path = repository / input_name
        require(
            path.resolve().is_relative_to(repository) and not path.is_symlink(),
            "Public input escapes owner",
        )
        inputs.append(parse(bound_file(path, protocol["input_files"][input_name])))
    if result.get("certificate_closed") is True:
        require(
            result.get("certificate_file") == "certificates.json",
            "Certificate locator differs",
        )
        raw = bound_file(
            study_output / "certificates.json",
            _pin_file(result.get("certificate_identity"), "certificates.json"),
        )
        certificates = json.loads(
            raw,
            object_pairs_hook=_unique,
            parse_constant=lambda x: (_ for _ in ()).throw(VerificationError(x)),
        )
        require(
            isinstance(certificates, list)
            and all(isinstance(row, dict) for row in certificates),
            "Invalid certificate array",
        )
    else:
        require(
            result.get("certificate_file") is None
            and result.get("certificate_identity") is None,
            "Unavailable proof locator promoted",
        )
        certificates = []
    return protocol, inputs[0], inputs[1], freeze, result, certificates


def _guard(
    repository: Path, protocol: Path
) -> tuple[str, str, tuple[tuple[str, str], ...]]:
    import inspect

    from bijux_pollenomics_lra.dispersal.kernels import gpm_values

    from ... import radial_envelope

    command = ["git", "--no-optional-locks", "-C", str(repository)]
    revision = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True
    ).strip()
    index = Path(
        subprocess.check_output(
            [*command, "rev-parse", "--git-path", "index"], text=True
        ).strip()
    )
    if not index.is_absolute():
        index = repository / index
    paths = [
        *Path(__file__).parent.rglob("*.py"),
        Path(__file__).parent.parent / "arithmetic.py",
        Path(radial_envelope.__file__),
        Path(inspect.getfile(gpm_values)),
        protocol,
        *(repository / name for name in INPUT_NAMES),
    ]
    relative = sorted({str(path.resolve().relative_to(repository)) for path in paths})
    subprocess.run(
        [*command, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*command, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
    )
    return (
        revision,
        hashlib.sha256(index.read_bytes()).hexdigest(),
        tuple(
            (name, hashlib.sha256((repository / name).read_bytes()).hexdigest())
            for name in relative
        ),
    )


def run_verification(
    repository: Path, protocol_path: Path, study_output: Path, output: Path
) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.resolve()
    protocol_path = _owned(repository, protocol_path)
    study_output = _owned(repository, study_output)
    destination = _owned(repository, output)
    require(
        not destination.exists()
        and not destination.is_symlink()
        and destination.resolve().is_relative_to(repository / "artifacts"),
        "Fresh repository-owned artifact output required",
    )
    before = _guard(repository, protocol_path)
    clock = Clock()
    packet = None
    proof_snapshot: dict[str, dict[str, Any]] = {}
    try:
        packet = load_packet(repository, protocol_path, study_output)
        proof_snapshot = {
            path.name: identity(path.read_bytes()) for path in study_output.iterdir()
        }
        require(
            packet[4].get("source_commit") == before[0],
            "Producer/observer committed source differs",
        )
        result = audit(*packet, clock)
    except (
        VerificationError,
        ValueError,
        ArithmeticError,
        KeyError,
        TypeError,
        IndexError,
        OSError,
    ) as error:
        result = {
            "schema_version": "continuous-receiver-independent-check.v1",
            "status": "failed",
            "accounting_verified": False,
            "producer_source_commit": packet[4].get("source_commit")
            if packet is not None
            else None,
            "reason": f"{type(error).__name__}: {error}",
            "current_case": clock.current_case,
            "current_domain": clock.current_domain,
            "completed_leaf_replays": clock.completed_leaves,
            "case_statuses": [
                {
                    key: row.get(key)
                    for key in ("core", "taxon", "backend_status", "backend_refusal")
                }
                for row in (packet[4].get("cases", []) if packet is not None else [])
            ],
            "limits": "No full continuous coefficient acceptance follows from a failed/incomplete independent replay.",
        }
    require(
        _guard(repository, protocol_path) == before,
        "Consumed source/index changed during verification",
    )
    if proof_snapshot:
        require(
            proof_snapshot
            == {
                path.name: identity(path.read_bytes())
                for path in study_output.iterdir()
            },
            "Closed study files changed during observation",
        )
    result["observer_source_commit"] = before[0]
    result["study_result_identity"] = identity(
        (study_output / "result.json").read_bytes()
    )
    result["elapsed_seconds"] = time.monotonic() - started
    result["peak_rss_bytes"] = _rss()
    require(
        result["elapsed_seconds"] < 180 and result["peak_rss_bytes"] <= 805306368,
        "Observer final resource cap exceeded",
    )
    raw = (
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    require(len(raw) <= 4_850_000, "Observer output cap exceeded")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--study-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    signal.alarm(180)
    result = run_verification(
        args.repository, args.protocol, args.study_output, args.output
    )
    signal.alarm(0)
    print(
        json.dumps(
            {
                "status": result["status"],
                "accounting_verified": result["accounting_verified"],
            }
        )
    )
    if result["status"] != "passed":
        raise SystemExit(1)

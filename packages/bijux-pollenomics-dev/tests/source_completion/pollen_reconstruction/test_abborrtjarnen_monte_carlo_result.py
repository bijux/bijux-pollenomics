"""Observe saved mean MCSE without fitting, drawing or reusing producer algebra."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

from .abborrtjarnen_monte_carlo.independent_result import verify_result
from .abborrtjarnen_monte_carlo.independent_sources import PROTOCOL


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "result", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    entry = Path(__file__).resolve()
    helpers = entry.parent / "abborrtjarnen_monte_carlo"
    common = entry.parent / "abborrtjarnen_age_ppe_dependence"
    files = [
        entry,
        *sorted(helpers.glob("independent_*.py")),
        common / "independent_sources.py",
        common / "independent_quadratic_forms.py",
    ]
    relative = [str(p.relative_to(repository)) for p in files]
    relative += [
        str(PROTOCOL),
        "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/common-covariance/protocol.json",
    ]
    git = ["git", "-C", str(repository)]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    for command in (
        [*git, "ls-files", "--error-unmatch", "--", *relative],
        [*git, "diff", "--exit-code", revision, "--", *relative],
    ):
        subprocess.run(command, check=True, capture_output=True)
    output = args.output.absolute()
    if (
        output.exists()
        or not output.resolve().is_relative_to(repository / "artifacts")
        or any(p.is_symlink() for p in (output, *output.parents))
    ):
        raise ValueError("Independent output must be absent under repository artifacts")
    started = time.monotonic()
    checked = verify_result(repository, args.result.resolve(strict=True))
    checked.update(
        observer_source_commit=revision, elapsed_seconds=time.monotonic() - started
    )
    subprocess.run(
        [*git, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
    )
    if (
        subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
        != revision
    ):
        raise ValueError("Independent observer HEAD changed during verification")
    body = json.dumps(checked, indent=2, allow_nan=False) + "\n"
    if len(body.encode()) > 5_000_000 or checked["elapsed_seconds"] > 120:
        raise ValueError("Independent runtime/output bound exceeded")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body)
    print(json.dumps(checked, sort_keys=True))


if __name__ == "__main__":
    main()

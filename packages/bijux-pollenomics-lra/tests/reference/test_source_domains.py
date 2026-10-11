"""The boundary suite has its own case denominator and preparation status."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from .lra_oracle.run_source_domains import cases


def test_source_domains_have_separate_semantics_and_stable_ids() -> None:
    specs = cases()
    assert len(specs) == 23
    assert len({case.id for case in specs}) == 23
    assert sum(case.kind == "forward" for case in specs) == 13
    assert sum(case.kind == "wrapper_refusal" for case in specs) == 2
    assert sum(case.kind == "ring_refusal" for case in specs) == 2


def test_source_domain_preparation_does_not_claim_live_reference(
    project_root: Path, tmp_path: Path
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(project_root / "tests/reference/lra_oracle/run_source_domains.py"),
            "--output",
            str(tmp_path / "domains"),
            "--prepare-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "domains/report.json").read_text())
    assert report["status"] == "prepared_not_executed"
    assert report["live_R_executed"] is False
    assert report["profile"] == "disqover-source-domains-and-corrected-forward-v1"
    assert report["prepared_cases"] == 23

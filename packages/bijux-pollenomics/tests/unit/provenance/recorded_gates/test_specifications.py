from __future__ import annotations

import os
import re
import subprocess

from bijux_pollenomics.governance.country_coverage import INPUT_PATHS
from bijux_pollenomics.provenance import gates as gate_module
from bijux_pollenomics.provenance.gates import build_product_gate_specification
from tests.support.repository import REPOSITORY_ROOT


def test_product_map_gate_binds_generated_report_tree() -> None:
    repository_root = REPOSITORY_ROOT

    specification = build_product_gate_specification(repository_root, "map")

    assert "docs/report" in specification.input_paths
    reporting_tests = "packages/bijux-pollenomics/tests/unit/reporting"
    assert reporting_tests in specification.argv
    assert reporting_tests in specification.input_paths
    assert specification.timeout_seconds == 540.0
    runtime_identity = dict(specification.runtime_identity)
    assert runtime_identity["command_executable_path"].endswith("/pytest")
    if os.path.isfile(runtime_identity["command_executable_path"]):
        assert runtime_identity["command_executable_sha256"].startswith("sha256:")
    else:
        assert runtime_identity["command_executable_sha256"] == "unavailable"
    assert runtime_identity["runner_python"]
    assert runtime_identity["python_implementation"]
    assert runtime_identity["python_version"]


def test_doc_count_gate_attests_exact_shard_receipt_reconciliation() -> None:
    specification = build_product_gate_specification(REPOSITORY_ROOT, "doc-counts")

    assert specification.argv[1:3] == (
        "-m",
        "bijux_pollenomics_dev.ci.test_shards",
    )
    assert "--expected-universe-file" in specification.argv
    assert "--junit-output" in specification.argv
    assert specification.argv[specification.argv.index("--count") + 1] == "2"
    assert specification.argv[specification.argv.index("--revision") + 1] == (
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    assert {
        ".github/workflows/scientific-verification.yml",
        "artifacts/execution-control/doc-count-plan",
        "artifacts/execution-control/doc-count-shards",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/test_shards",
    } <= set(specification.input_paths)
    assert dict(specification.environment)["PYTHONPATH"].endswith(
        "/packages/bijux-pollenomics-dev/src"
    )
    assert specification.timeout_seconds == 120.0


def test_make_gate_inputs_and_timeout_match_product_specifications() -> None:
    repository_root = REPOSITORY_ROOT
    environment = {
        key: value
        for key, value in os.environ.items()
        if key != "POLLENOMICS_GATE_TIMEOUT_SECONDS"
    }
    completed = subprocess.run(
        ["make", "-pn"],
        cwd=repository_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    prefixes = {
        "science": "SCIENCE",
        "data": "DATA",
        "map": "MAP",
        "provenance": "PROVENANCE",
        "doc-counts": "DOC_COUNT",
    }
    for gate_id, prefix in prefixes.items():
        match = re.search(
            rf"^POLLENOMICS_{prefix}_INPUTS := (.*)$",
            completed.stdout,
            flags=re.MULTILINE,
        )
        assert match is not None
        make_inputs = tuple(sorted(match.group(1).split()))
        specification = build_product_gate_specification(repository_root, gate_id)
        assert make_inputs == specification.input_paths
        expected_timeout = 120.0 if gate_id == "doc-counts" else 540.0
        assert specification.timeout_seconds == expected_timeout
        assert {
            "Makefile",
            "makes/pollenomics-verification.mk",
            "packages/bijux-pollenomics/pyproject.toml",
            "pyproject.toml",
            "uv.lock",
        } <= set(specification.input_paths)
        if gate_id == "doc-counts":
            assert set(INPUT_PATHS) <= set(specification.input_paths)

        for test_name in gate_module._GATE_TESTS[gate_id]:
            test_path = (
                repository_root
                / "packages/bijux-pollenomics/tests/regression/test_docs_breadth.py"
                if test_name.startswith("../regression/")
                else repository_root
                / "packages/bijux-pollenomics/tests/unit"
                / test_name
            )
            assert test_path.exists(), test_path

    assert re.search(
        r"^POLLENOMICS_GATE_TIMEOUT_SECONDS = 540$",
        completed.stdout,
        flags=re.MULTILINE,
    )
    assert re.search(
        r"^POLLENOMICS_DOC_COUNT_REDUCER_TIMEOUT_SECONDS := 120$",
        completed.stdout,
        flags=re.MULTILINE,
    )


def test_gate_inputs_recursively_bind_owned_python_sources() -> None:
    source_root = REPOSITORY_ROOT / "packages/bijux-pollenomics/src/bijux_pollenomics"
    owned_roots = {
        "science": ("analysis", "core", "evidence"),
        "data": ("adna", "collection"),
        "map": ("evidence", "reporting"),
        "provenance": (
            "analysis/propagation",
            "core",
            "evidence/classification",
            "evidence/sources/neotoma",
            "provenance",
        ),
        "doc-counts": ("governance", "reporting/review"),
    }

    for gate_id, relative_roots in owned_roots.items():
        specification = build_product_gate_specification(REPOSITORY_ROOT, gate_id)
        expected = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for relative_root in relative_roots
            for path in (source_root / relative_root).rglob("*.py")
        }
        assert expected <= set(specification.input_paths)


def test_make_release_evidence_does_not_rerun_recorded_gates() -> None:
    repository_root = REPOSITORY_ROOT

    completed = subprocess.run(
        ["make", "-n", "release-evidence"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert " -m pytest" not in completed.stdout
    assert "provenance.gates" not in completed.stdout
    assert "provenance request" in completed.stdout
    assert "provenance write" in completed.stdout


def test_make_has_explicit_gate_refresh_and_candidate_addressed_outputs() -> None:
    repository_root = REPOSITORY_ROOT
    makefile = (repository_root / "makes/pollenomics-verification.mk").read_text(
        encoding="utf-8"
    )

    assert (
        "refresh-release-gates: verify-science verify-data verify-map "
        "verify-provenance verify-doc-counts"
    ) in makefile
    assert "release-evidence: release-evidence-request" in makefile
    assert "release-evidence: verify-science" not in makefile
    assert "release-evidence/$(POLLENOMICS_RELEASE_CANDIDATE_ID)" in makefile

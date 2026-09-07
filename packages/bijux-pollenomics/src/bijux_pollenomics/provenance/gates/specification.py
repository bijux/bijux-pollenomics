"""Repository-owned release-gate specification construction."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess  # nosec B404

from ..release_evidence import ReleaseEvidenceError
from .catalog import _GATE_FIXED_INPUTS, _GATE_GLOBS, _GATE_TESTS
from .model import RecordedGateSpecification
from .producer import _runtime_identity
from .repository import _repository_root

_DOC_COUNT_SHARD_COUNT = 2
_DOC_COUNT_REDUCER_TIMEOUT_SECONDS = 120.0
_PYTEST_GATE_TIMEOUT_SECONDS = 540.0


def _head_revision(root: Path) -> str:
    """Return the exact commit identity bound into shard receipts."""
    try:
        completed = subprocess.run(  # nosec B603
            ("git", "-C", str(root), "rev-parse", "HEAD"),
            check=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            shell=False,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ReleaseEvidenceError(
            "doc-count shard evidence requires an inspectable Git revision"
        ) from error
    revision = completed.stdout.strip()
    if len(revision) != 40 or any(
        character not in "0123456789abcdef" for character in revision
    ):
        raise ReleaseEvidenceError("doc-count shard revision is not a full Git commit")
    return revision


def _doc_count_specification(
    root: Path, *, inputs: set[str], artifacts_directory: str, junit_path: str
) -> RecordedGateSpecification:
    """Specify the exact reducer that attests complete doc-count shard execution."""
    python_path = root / "artifacts/root/check-venv/bin/python"
    receipt_root = root / "artifacts/execution-control/doc-count-shards"
    collection_plan = (
        root / "artifacts/execution-control/doc-count-plan/collection-plan.json"
    )
    argv = (
        str(python_path),
        "-m",
        "bijux_pollenomics_dev.ci.test_shards",
        "--receipt-root",
        str(receipt_root),
        "--count",
        str(_DOC_COUNT_SHARD_COUNT),
        "--revision",
        _head_revision(root),
        "--expected-universe-file",
        str(collection_plan),
        "--junit-output",
        str(root / junit_path),
    )
    node_path = shutil.which("node")
    path_parts = [str(root / "artifacts/root/check-venv/bin")]
    if node_path is not None:
        path_parts.append(str(Path(node_path).parent))
    path_parts.extend(("/usr/bin", "/bin"))
    environment = {
        "PATH": ":".join(path_parts),
        "PYTHONPATH": str(root / "packages/bijux-pollenomics-dev/src"),
        "PYTHONPYCACHEPREFIX": str(root / f"{artifacts_directory}/pycache/doc-counts"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "LANG": "C",
        "LC_ALL": "C",
    }
    return RecordedGateSpecification(
        gate_id="doc-counts",
        required=True,
        argv=argv,
        environment=tuple(sorted(environment.items())),
        input_paths=tuple(sorted(inputs)),
        artifacts_directory=artifacts_directory,
        junit_path=junit_path,
        timeout_seconds=_DOC_COUNT_REDUCER_TIMEOUT_SECONDS,
        runtime_identity=_runtime_identity(str(python_path), node_path),
    )


def build_product_gate_specification(
    repository_root: Path, gate_id: str
) -> RecordedGateSpecification:
    """Return the repository-owned exact specification for a release gate."""
    root = _repository_root(repository_root)
    try:
        test_names = _GATE_TESTS[gate_id]
    except KeyError as error:
        raise ReleaseEvidenceError(
            f"unknown product verification gate: {gate_id}"
        ) from error
    test_root = "packages/bijux-pollenomics/tests/unit"
    tests = tuple(
        (
            "packages/bijux-pollenomics/tests/regression/test_docs_breadth.py"
            if name.startswith("../regression/")
            else f"{test_root}/{name}"
        )
        for name in test_names
    )
    inputs = set(_GATE_FIXED_INPUTS[gate_id])
    inputs.update(tests)
    for pattern in _GATE_GLOBS[gate_id]:
        inputs.update(path.relative_to(root).as_posix() for path in root.glob(pattern))
    artifacts_directory = "artifacts/execution-control/gates"
    junit_path = f"{artifacts_directory}/{gate_id}.junit.xml"
    if gate_id == "doc-counts":
        return _doc_count_specification(
            root,
            inputs=inputs,
            artifacts_directory=artifacts_directory,
            junit_path=junit_path,
        )
    pytest_path = root / "artifacts/root/check-venv/bin/pytest"
    argv = (
        str(pytest_path),
        "--rootdir",
        str(root),
        "-c",
        str(root / "configs/pytest.ini"),
        "-q",
        "-o",
        f"cache_dir={root}/{artifacts_directory}/pytest-cache/{gate_id}",
        f"--junitxml={root}/{junit_path}",
        *tests,
    )
    node_path = shutil.which("node")
    path_parts = [str(root / "artifacts/root/check-venv/bin")]
    if node_path is not None:
        path_parts.append(str(Path(node_path).parent))
    path_parts.extend(("/usr/bin", "/bin"))
    environment = {
        "PATH": ":".join(path_parts),
        "PYTHONPATH": str(root / "packages/bijux-pollenomics/src"),
        "PYTHONPYCACHEPREFIX": str(root / f"{artifacts_directory}/pycache/{gate_id}"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "HYPOTHESIS_DATABASE_DIRECTORY": str(
            root / f"{artifacts_directory}/hypothesis/{gate_id}"
        ),
        "LANG": "C",
        "LC_ALL": "C",
    }
    return RecordedGateSpecification(
        gate_id=gate_id,
        required=True,
        argv=argv,
        environment=tuple(sorted(environment.items())),
        input_paths=tuple(sorted(inputs)),
        artifacts_directory=artifacts_directory,
        junit_path=junit_path,
        timeout_seconds=_PYTEST_GATE_TIMEOUT_SECONDS,
        runtime_identity=_runtime_identity(str(pytest_path), node_path),
    )

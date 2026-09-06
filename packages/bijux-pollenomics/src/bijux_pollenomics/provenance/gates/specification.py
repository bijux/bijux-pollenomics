"""Repository-owned release-gate specification construction."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..release_evidence import ReleaseEvidenceError
from .catalog import _GATE_FIXED_INPUTS, _GATE_GLOBS, _GATE_TESTS
from .model import RecordedGateSpecification
from .producer import _runtime_identity
from .repository import _repository_root


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
        timeout_seconds=900.0,
        runtime_identity=_runtime_identity(str(pytest_path), node_path),
    )

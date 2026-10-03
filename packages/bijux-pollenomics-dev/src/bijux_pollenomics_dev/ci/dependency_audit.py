"""Export locked public dependencies and account for repository workspace sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from typing import Literal, TypedDict


class DependencyAuditReceipt(TypedDict):
    """Separate vulnerability-service public pins from exact local source custody."""

    schema: str
    distribution: str
    extras: list[str]
    exported_pin_count_including_target_markers: int
    requirements_sha256: str
    source_sha256: dict[str, str]
    workspace_distributions: dict[str, str]
    uv_executable: str
    uv_executable_sha256: str
    argv: list[str]
    scope: str
    vulnerability_assessment_performed: Literal[False]


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("expected a TOML table")
    return dict(value)


def _items(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("expected a TOML array")
    return list(value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("expected nonempty TOML text")
    return value


def _sha(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("source is not a regular file: " + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _confined(root: Path, path: Path) -> Path:
    absolute = path.absolute()
    if not absolute.is_relative_to(root) or ".." in absolute.parts:
        raise ValueError("path is outside its owned root")
    if any(parent.is_symlink() for parent in (absolute, *absolute.parents)):
        raise ValueError("symbolic path custody is forbidden")
    return absolute


def workspace_sources(repository: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Record declared workspace metadata and Python sources without a CVE claim."""
    root = _mapping(tomllib.loads((repository / "pyproject.toml").read_text()))
    tool = _mapping(root["tool"])
    configured = _mapping(tool["bijux_pollenomics"])
    members = [_text(item) for item in _items(configured["packages"])]
    declared: dict[str, str] = {}
    identities = {
        "pyproject.toml": _sha(repository / "pyproject.toml"),
        "uv.lock": _sha(repository / "uv.lock"),
    }
    for member in members:
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", member) is None:
            raise ValueError("workspace member name is not a distribution name")
        base = _confined(repository, repository / "packages" / member)
        project_path = base / "pyproject.toml"
        project = _mapping(_mapping(tomllib.loads(project_path.read_text()))["project"])
        name = _text(project["name"])
        if name != member or name in declared:
            raise ValueError("declared workspace distribution identity differs")
        declared[name] = str(base.relative_to(repository))
        paths = [project_path, *sorted((base / "src").rglob("*.py"))]
        if len(paths) == 1:
            raise ValueError("workspace distribution has no Python source")
        for path in paths:
            _confined(repository, path)
            identities[str(path.relative_to(repository))] = _sha(path)
    return declared, identities


def registry_identities(
    lock: dict[str, object], workspace: dict[str, str]
) -> set[tuple[str, str]]:
    """Refuse undeclared local sources and non-PyPI public-package attribution."""
    public: set[tuple[str, str]] = set()
    observed: dict[str, str] = {}
    for item in _items(lock["package"]):
        package = _mapping(item)
        name = _text(package["name"])
        source = _mapping(package["source"])
        if source == {"registry": "https://pypi.org/simple"}:
            public.add((name, _text(package["version"])))
        elif source == {"editable": "."}:
            if name != "bijux-pollenomics-repository":
                raise ValueError("workspace root identity differs")
        elif source == {"editable": workspace.get(name)} and name in workspace:
            observed[name] = _text(source["editable"])
        else:
            raise ValueError("unsupported or undeclared dependency source: " + name)
    if observed != workspace:
        raise ValueError(
            "lock does not account for all declared workspace distributions"
        )
    return public


def validate_export(
    text: str, public: set[tuple[str, str]], workspace: dict[str, str]
) -> int:
    """Require complete exact public pins while preserving uv's target markers."""
    count = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        pin, separator, marker = line.partition(" ; ")
        match = re.fullmatch(r"([a-z0-9]+(?:-[a-z0-9]+)*)==([a-zA-Z0-9.!+_-]+)", pin)
        if match is None or (separator and not marker):
            raise ValueError("audit export is not an exact locked public pin")
        identity = match.group(1), match.group(2)
        if identity[0] in workspace or identity not in public:
            raise ValueError("audit export identity is outside public lock custody")
        count += 1
    if not count:
        raise ValueError("locked dependency audit export is empty")
    return count


def prepare(
    repository: Path,
    distribution: str,
    extras: list[str],
    output: Path,
    account: Path,
    uv: str,
) -> DependencyAuditReceipt:
    """Publish exact uv export and workspace custody for the package security gate."""
    repository = repository.absolute()
    if repository.is_symlink():
        raise ValueError("repository source is symbolic")
    output = _confined(repository / "artifacts", output)
    account = _confined(repository / "artifacts", account)
    if output == account or any(
        path.exists() and not path.is_file() for path in (output, account)
    ):
        raise ValueError("audit outputs must be distinct regular artifact paths")
    workspace, before = workspace_sources(repository)
    if distribution not in workspace:
        raise ValueError("audit distribution is not a declared workspace member")
    project = _mapping(
        _mapping(
            tomllib.loads(
                (repository / workspace[distribution] / "pyproject.toml").read_text()
            )
        )["project"]
    )
    optional = _mapping(project.get("optional-dependencies", {}))
    if len(extras) != len(set(extras)) or any(
        extra not in optional for extra in extras
    ):
        raise ValueError("audit extras are not declared by the selected distribution")
    public = registry_identities(
        _mapping(tomllib.loads((repository / "uv.lock").read_text())), workspace
    )
    executable = shutil.which(uv)
    if executable is None:
        raise ValueError("uv exporter executable unavailable")
    output.parent.mkdir(parents=True, exist_ok=True)
    account.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="dependency-export-", dir=output.parent
    ) as directory:
        scratch = Path(directory)
        exported = scratch / "requirements.txt"
        argv = [
            executable,
            "export",
            "--locked",
            "--offline",
            "--no-config",
            "--python",
            sys.executable,
            "--no-default-groups",
            "--package",
            distribution,
            "--no-emit-workspace",
            "--no-annotate",
            "--no-header",
            "--no-hashes",
            "--format",
            "requirements.txt",
            "--output-file",
            str(exported),
        ]
        for extra in extras:
            argv.extend(["--extra", extra])
        environment = {
            "PATH": os.defpath,
            "HOME": str(scratch),
            "UV_CACHE_DIR": str(scratch / "cache"),
            "UV_PYTHON_DOWNLOADS": "never",
            "UV_OFFLINE": "1",
            "UV_NO_CONFIG": "1",
            "LANG": "C.UTF-8",
        }
        subprocess.run(
            argv,
            cwd=repository,
            env=environment,
            check=True,
            timeout=120,
            stdout=subprocess.DEVNULL,
        )
        text = exported.read_text()
        if len(text.encode()) > 1024 * 1024:
            raise ValueError("audit export exceeds its finite size bound")
        count = validate_export(text, public, workspace)
        if workspace_sources(repository) != (workspace, before):
            raise ValueError("workspace inputs mutated during dependency export")
        receipt: DependencyAuditReceipt = {
            "schema": "pollenomics-workspace-dependency-audit/v1",
            "distribution": distribution,
            "extras": extras,
            "exported_pin_count_including_target_markers": count,
            "requirements_sha256": _sha(exported),
            "source_sha256": before,
            "workspace_distributions": workspace,
            "uv_executable": executable,
            "uv_executable_sha256": _sha(Path(executable).resolve()),
            "argv": argv,
            "scope": "Exact locked public third-party dependency pins, with target markers evaluated by pip-audit on its runtime. Workspace sources have separate SHA custody and remain subject to their owned static-analysis gates; no public vulnerability-service assessment of those local distributions is claimed.",
            "vulnerability_assessment_performed": False,
        }
        staged_account = scratch / "workspace-account.json"
        staged_account.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        _confined(repository / "artifacts", output)
        _confined(repository / "artifacts", account)
        os.replace(exported, output)
        os.replace(staged_account, account)
    return receipt


def main() -> int:
    """Prepare package security inputs; pip-audit remains the strict audit owner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--distribution", required=True)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--account", type=Path, required=True)
    parser.add_argument("--uv", default="uv")
    args = parser.parse_args()
    receipt = prepare(
        args.repository,
        args.distribution,
        args.extra,
        args.output,
        args.account,
        args.uv,
    )
    print(
        json.dumps(
            {
                "requirements_sha256": receipt["requirements_sha256"],
                "pin_count": receipt["exported_pin_count_including_target_markers"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

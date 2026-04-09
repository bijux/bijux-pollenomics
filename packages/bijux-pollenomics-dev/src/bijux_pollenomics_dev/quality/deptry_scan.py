"""Run deptry with repository-owned configuration merged into a package scan."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deptry with repository-owned config merged into a package pyproject.toml.",
    )
    parser.add_argument(
        "--config", required=True, help="Path to the repo-owned deptry TOML file."
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Path to the package root containing pyproject.toml.",
    )
    parser.add_argument(
        "--deptry-bin", default="", help="Deptry executable to invoke."
    )
    parser.add_argument(
        "roots",
        nargs="*",
        default=["."],
        help="Roots to scan, relative to the project dir.",
    )
    return parser.parse_args()


def resolve_deptry_command(deptry_bin: str) -> list[str]:
    deptry_command = shlex.split(deptry_bin)
    if not deptry_command:
        return [sys.executable, "-m", "deptry"]

    deptry_bin_arg = Path(deptry_command[0]).expanduser()
    if deptry_bin_arg.is_absolute() or len(deptry_bin_arg.parts) > 1:
        if not deptry_bin_arg.absolute().is_file():
            raise SystemExit(f"deptry executable not found: {deptry_bin}")
        return [os.fspath(deptry_bin_arg.absolute()), *deptry_command[1:]]

    resolved_deptry = shutil.which(deptry_command[0])
    if resolved_deptry is None:
        raise SystemExit(f"deptry executable not found: {deptry_bin}")
    return [resolved_deptry, *deptry_command[1:]]


def merge_deptry_config(
    config_path: Path, package_slug: str, package_pyproject: dict[str, object]
) -> dict[str, object]:
    root_config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    base_config = root_config.get("tool", {}).get("deptry", {})
    package_configs = (
        root_config.get("tool", {}).get("repo_deptry", {}).get("packages", {})
    )
    package_override = package_configs.get(package_slug, {})

    merged_config: dict[str, object] = dict(base_config)
    for key, value in package_override.items():
        current = merged_config.get(key)
        if isinstance(current, list) and isinstance(value, list):
            merged_config[key] = list(dict.fromkeys([*current, *value]))
        elif isinstance(current, dict) and isinstance(value, dict):
            merged_config[key] = {**current, **value}
        else:
            merged_config[key] = value

    if "known_first_party" not in merged_config:
        merged_config["known_first_party"] = [package_slug.replace("-", "_")]
    optional_dependencies = (
        package_pyproject.get("project", {}).get("optional-dependencies", {})
    )
    available_groups = set(optional_dependencies)
    dev_groups = merged_config.get("optional_dependencies_dev_groups")
    if isinstance(dev_groups, list):
        filtered_groups = [group for group in dev_groups if group in available_groups]
        if filtered_groups:
            merged_config["optional_dependencies_dev_groups"] = filtered_groups
        else:
            merged_config.pop("optional_dependencies_dev_groups", None)
    return merged_config


def render_deptry_config(config: dict[str, object]) -> str:
    lines = ["[tool.deptry]"]
    config_copy = dict(config)
    package_module_name_map = config_copy.pop("package_module_name_map", None)
    for key, value in config_copy.items():
        lines.append(f"{key} = {render_toml_value(value)}")
    if isinstance(package_module_name_map, dict) and package_module_name_map:
        lines.append("")
        lines.append("[tool.deptry.package_module_name_map]")
        for key, value in package_module_name_map.items():
            lines.append(f"{json.dumps(str(key))} = {json.dumps(str(value))}")
    return "\n".join(lines)


def render_toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(render_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        items = ", ".join(
            f"{key} = {render_toml_value(item)}" for key, item in value.items()
        )
        return "{ " + items + " }"
    return str(value)


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
    config_path = Path(args.config).resolve()
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.is_file():
        raise SystemExit(f"pyproject.toml not found in {project_dir}")
    if not config_path.is_file():
        raise SystemExit(f"deptry config not found at {config_path}")

    deptry_command = resolve_deptry_command(args.deptry_bin)
    pyproject_text = pyproject_path.read_text(encoding="utf-8").rstrip()
    package_pyproject = tomllib.loads(pyproject_text)
    config_text = render_deptry_config(
        merge_deptry_config(config_path, project_dir.name, package_pyproject)
    )
    merged_text = f"{pyproject_text}\n\n{config_text}\n"

    with tempfile.TemporaryDirectory(prefix="deptry-") as tmpdir:
        merged_pyproject = Path(tmpdir) / "pyproject.toml"
        merged_pyproject.write_text(merged_text, encoding="utf-8")
        completed = subprocess.run(
            [*deptry_command, "--config", os.fspath(merged_pyproject), *args.roots],
            cwd=project_dir,
            check=False,
        )
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

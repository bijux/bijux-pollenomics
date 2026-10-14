"""Physical source closure observed by maintained atlas candidate generators."""

from __future__ import annotations

from collections.abc import Iterable
import hashlib
from pathlib import Path
import sys


def _owned_source_inputs(
    repository: Path, modules: Iterable[tuple[str, object]]
) -> dict[str, str]:
    repository = repository.absolute()
    inputs: dict[str, str] = {}
    for name, source in modules:
        if not (
            name
            in {
                "pollenomics",
                "bijux_pollenomics",
                "bijux_pollenomics_lra",
                "bijux_pollenomics_dev",
            }
            or name.startswith(
                (
                    "pollenomics.",
                    "bijux_pollenomics.",
                    "bijux_pollenomics_lra.",
                    "bijux_pollenomics_dev.",
                )
            )
        ):
            continue
        if source is None:
            continue
        if not isinstance(source, str):
            raise ValueError("Atlas owned module source path must be text")
        path = Path(source).absolute()
        if not path.is_relative_to(repository / "packages"):
            raise ValueError(
                "Atlas loaded an owned module outside its frozen source repository"
            )
        if path.suffix != ".py" or not path.is_file() or path.stat().st_nlink != 1:
            raise ValueError(
                "Atlas owned module requires one regular physical Python source"
            )
        if any(
            parent.is_symlink()
            for parent in (path, *path.parents)
            if parent.is_relative_to(repository)
        ):
            raise ValueError("Atlas owned module source cannot traverse a symlink")
        inputs[path.relative_to(repository).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return dict(sorted(inputs.items()))


def observed_source_inputs(repository: Path) -> dict[str, str]:
    """Bind all loaded product modules as well as each generator's declared assets.

    This observes imported source bytes. It does not assert that every imported
    function executed, and third-party runtime custody is qualified separately.
    """
    return _owned_source_inputs(
        repository,
        (
            (name, getattr(module, "__file__", None))
            for name, module in tuple(sys.modules.items())
        ),
    )

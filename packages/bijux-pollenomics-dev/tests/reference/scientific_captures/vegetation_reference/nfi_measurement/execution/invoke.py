"""Invoke the unchanged maintained metadata CLI after authenticating its exact source origin."""

from __future__ import annotations
import argparse
import importlib
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import dump, pin, read, require


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.plan)
    original = importlib.import_module(plan["maintained_module"])
    filename = original.__file__
    require(isinstance(filename, str), "Maintained producer has no physical origin")
    assert isinstance(filename, str)
    require(
        pin(Path(filename)) == plan["maintained_producer"],
        "Maintained metadata producer origin differs",
    )
    sys.argv = [
        filename,
        "--private-source-store",
        plan["private_source_store"],
        "--output",
        plan["metadata_output"],
    ]
    dump(
        Path(plan["output"]) / "producer-origin.json",
        {
            "candidate": plan["candidate"],
            "actual_wrapper_argv": [sys.executable, *sys.orig_argv[1:]],
            "maintained_producer": pin(Path(filename)),
            "maintained_main_argv": sys.argv,
            "semantic_scope": "Only unchanged source dictionary/header/D-G-H metadata main; tree outcomes stay unselected",
        },
    )
    original.main()
    origins: dict[str, Any] = {}
    roots = [Path(r) for r in plan["source_roots"]]
    for name, module in sorted(sys.modules.items()):
        if name.startswith(
            (
                "bijux_pollenomics.",
                "bijux_pollenomics_dev.",
                "bijux_pollenomics_lra.",
                "pollenomics.",
            )
        ):
            filename = getattr(module, "__file__", None)
            if filename:
                path = Path(filename).resolve()
                require(
                    any(path.is_relative_to(r) for r in roots),
                    "Loaded first-party source escaped full pinned roots",
                )
                origins[name] = pin(path)
    dump(Path(plan["output"]) / "loaded-source-origins.json", origins)


if __name__ == "__main__":
    main()

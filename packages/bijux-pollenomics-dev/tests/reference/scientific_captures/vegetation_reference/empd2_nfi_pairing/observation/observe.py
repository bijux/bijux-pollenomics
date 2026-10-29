"""Observe source provenance, sixteen metadata joins and complete outcome-blind refusals."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import sys
from typing import cast

_entry_directory = Path(__file__).resolve().parent
_expected_python = {
    "contracts.py",
    "metadata.py",
    "execute_source.py",
    "observe.py",
    "prepare.py",
    "run.py",
    "check_contracts.py",
    "source_runtime.py",
    "runtime_contracts.py",
    "runtime_guarded_runner.py",
    "common_runner.py",
}
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _expected_python:
        raise ValueError("Unexpected controller import")
sys.path.insert(0, str(_entry_directory))
from contracts import (  # noqa: E402 - authenticate the local import namespace first.
    INPUTS,
    PACKAGE_ROOTS,
    PRODUCER,
    REPORT,
    ROOT,
    dump,
    exact,
    load,
    pin,
    require,
    sha,
    verify_inputs,
)
from metadata import (  # noqa: E402 - authenticate the local import namespace first.
    checked_leads,
    expected_rows,
    nfi_metadata,
    source_metadata,
    validate_products,
)

PROJ_USER_DATA_GETTER = "get_user_data_dir"
PROJ_NETWORK_GETTER = "is_network_enabled"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = load(args.plan)
    verify_inputs(plan)
    output = Path(plan["output"])
    progress = json.loads((output / "stage-progress.json").read_bytes())
    require(len(progress) == 1, "Exactly one producer stage must precede observer")
    stage = progress[0]
    require(
        stage["id"] == plan["stages"][0]["id"]
        and stage["argv"] == plan["stages"][0]["argv"]
        and (type(stage["actual_exit"]) is int)
        and (stage["actual_exit"] == 0)
        and (stage["timed_out"] is False),
        "Actual producer stage differs",
    )
    for key in ("stdout", "stderr"):
        require(
            sha(Path(stage[key])) == stage[key + "_sha256"],
            "Actual producer log changed",
        )
    execution = load(output / "source-execution.json")
    emitted = json.loads(Path(stage["stdout"]).read_text().splitlines()[-1])
    require(
        exact(emitted["source_execution"], pin(output / "source-execution.json")),
        "Source execution receipt lacks native stdout hash join",
    )
    require(
        execution["candidate"] == plan["candidate"]
        and exact(execution["plan"], pin(args.plan))
        and exact(execution["source"], plan["maintained_source"]),
        "Producer source/plan/candidate join differs",
    )
    require(
        type(execution["source_exit"]) is int
        and execution["source_exit"] == 0
        and (type(execution["metadata_exit"]) is int)
        and (execution["metadata_exit"] == 0),
        "Source and metadata exits differ",
    )
    require(
        execution["metadata_error"] is None
        and execution["counters"]
        == {
            "selected_NFI_cells": (43892 + 1) * 6,
            "selected_NFI_rows": 43892 + 1,
            "outcome_cell_decode_attempts": 0,
            "LRA_implementation_function_calls": 0,
        },
        "Outcome-blind source telemetry differs",
    )
    require(
        execution["executed_source_argv"]
        == [
            str(ROOT / PRODUCER),
            "--repository",
            str(ROOT),
            "--private-source-store",
            plan["private_source_store"],
            "--output",
            str(output / "producer"),
        ],
        "Actual maintained CLI argv differs",
    )
    sys.path[:0] = [str(p) for p in PACKAGE_ROOTS]
    from pyproj import Geod, Transformer, datadir, network

    require(
        Path(datadir.get_data_dir()) == Path(plan["PROJ_data_directory"])
        and Path(
            cast(Callable[[bool], str], getattr(datadir, PROJ_USER_DATA_GETTER))(False)
        )
        == Path(plan["PROJ_user_directory"])
        and (
            cast(Callable[[], bool], getattr(network, PROJ_NETWORK_GETTER))() is False
        ),
        "Observer PROJ context differs",
    )
    protected = {r["path"]: r for r in plan["input_pins"]}
    require(
        execution["PROJ"]["network_enabled"] is False
        and execution["PROJ"]["data_directory"] == plan["PROJ_data_directory"]
        and exact(
            execution["PROJ"]["proj_db"],
            pin(Path(plan["PROJ_data_directory"]) / "proj.db"),
        ),
        "Producer PROJ resource context differs",
    )
    for row in [
        *execution["first_party_origins"],
        *execution["PROJ"]["module_origins"],
    ]:
        require(
            exact(
                protected.get(row["path"]),
                {k: row[k] for k in ("path", "sha256", "bytes")},
            ),
            "Observed source/native-extension origin changed",
        )
    dossier = load(INPUTS["dossier"][0])
    spatial = load(INPUTS["spatial"][0])
    nfi, cells = nfi_metadata(INPUTS["workbook"][0])
    require(
        len(nfi) == 43892 and len({(r[1], r[2]) for r in nfi}) == 6018,
        "Complete native NFI metadata denominator differs",
    )
    names = [r["spatial_lead"]["pollen_sample"] for r in dossier["rows"]]
    records, ages, citations = source_metadata(INPUTS["sqlite"][0], names)
    items = checked_leads(dossier, spatial, records, ages, citations)
    rows = expected_rows(
        items,
        nfi,
        Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True),
        Geod(ellps="WGS84"),
    )
    tracked = load(ROOT / REPORT / "report.json")
    require(
        tracked["input_sha256"]["producer"] == plan["maintained_source"]["sha256"],
        "Tracked static report producer scope differs",
    )
    result = validate_products(output / "producer", rows, tracked)
    require(
        not any(
            name.startswith(("bijux_pollenomics", "pollenomics"))
            for name in sys.modules
        ),
        "Independent observer imported the first-party producer/projection",
    )
    verify_inputs(plan)
    dump(
        output / "independent-pairing-review.json",
        {
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "plan": pin(args.plan),
            "actual_producer_stage": stage,
            "source_execution": pin(output / "source-execution.json"),
            "current_private_source_identities": plan["source_input_records"],
            "all_native_NFI_metadata_rows": len(nfi),
            "distinct_native_NFI_tract_plot_pairs": 6018,
            "native_pollen_records_rejoined": len(records),
            "age_codes_and_citations_rejoined": True,
            "workbook_access": cells,
            **result,
            "current_refusals_are_not_vegetation_validation": True,
            "no_fresh_source_rights_or_human_review_claimed": True,
        },
    )
    print(
        json.dumps(
            {
                "independent_review": pin(output / "independent-pairing-review.json"),
                "refusals": 16,
                "admitted": 0,
            }
        )
    )


if __name__ == "__main__":
    main()

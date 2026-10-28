"""Exercise only synthetic/source metadata guards; never import xlrd or decode XLS."""

from __future__ import annotations

import ast
from collections.abc import Callable
from copy import deepcopy
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cache_contract import inventory, safe_member, validate_cache
import contracts as c
from contracts import (
    CACHE,
    SOURCE,
    confined_output,
    dump,
    frozen_pin_union,
    load,
    output_products,
    physical_pin,
    pin,
    verify_frozen_pins,
)
from independent import (
    count_status,
    endpoints,
    neotoma_findings,
    number,
    workbook_age_findings,
)
from runtime import (
    absent_path,
    dependency_load_names,
    expand_dependency,
    qualify_process_snapshot,
    require_environment,
)


def entrypoint_import_guards(root: Path) -> int:
    """Exercise real entrypoint refusal before a poisoned local helper could run."""
    total = 0
    for name in ("prepare.py", "execute_source.py", "observe.py", "run.py"):
        source = (SOURCE / name).read_text()
        parsed = ast.parse(source)
        insertion = next(
            i
            for i, node in enumerate(parsed.body)
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "insert"
        )
        prefix = ast.Module(body=parsed.body[:insertion], type_ignores=[])
        boundary = root / name.removesuffix(".py")
        boundary.mkdir()
        target = boundary / name
        target.write_text(source)
        namespace: dict[str, Any] = {"__file__": str(target)}
        exec(compile(prefix, str(target), "exec"), namespace)
        total += 1
        marker = boundary / "import-executed.json"
        poison = boundary / "contracts.py"
        poison.write_text(
            "from pathlib import Path\nPath("
            + repr(str(marker))
            + ").write_text('unsafe')\n"
        )
        for bad_name, kind in (
            ("contracts.cpython-311-darwin.so", "file"),
            ("unselected.pyc", "file"),
            ("unselected.py", "file"),
            ("unselected-package", "directory"),
            ("unselected-link", "symlink"),
            ("unselected-fifo", "fifo"),
        ):
            bad = boundary / bad_name
            if kind == "file":
                bad.write_bytes(b"unselected import shadow")
            elif kind == "directory":
                bad.mkdir()
            elif kind == "symlink":
                bad.symlink_to(poison)
            else:
                os.mkfifo(bad)
            try:
                refused(runpy.run_path, str(target))
                assert not marker.exists(), "Local helper ran before namespace refusal"
            finally:
                if kind == "directory":
                    bad.rmdir()
                else:
                    bad.unlink()
            total += 1
        alias = root / (name + "-alias")
        alias.symlink_to(boundary, target_is_directory=True)
        with_alias: dict[str, Any] = {"__file__": str(alias / name)}
        refused(exec, compile(prefix, str(target), "exec"), with_alias)
        alias.unlink()
        assert not marker.exists()
        total += 1
    return total


def refused(function: Callable[..., Any], *args: Any) -> None:
    try:
        function(*args)
    except (ValueError, OSError, KeyError):
        return
    raise AssertionError("Expected guard refusal")


class Cell:
    def __init__(self, value: Any) -> None:
        self.value = value
        self.ctype = 2 if type(value) in (int, float) else 1


class Sheet:
    name = "Synthetic source-only control"

    def __init__(self, rows: list[list[Any]]) -> None:
        self.rows = rows
        self.nrows = len(rows)
        self.ncols = max(map(len, rows))

    def cell_value(self, row: int, column: int) -> Any:
        return self.rows[row][column]

    def row_values(self, row: int) -> list[Any]:
        return self.rows[row]

    def cell(self, row: int, column: int) -> Cell:
        return Cell(self.cell_value(row, column))


def fixture() -> tuple[dict[str, Any], dict[str, dict[str, str]], dict[str, Any]]:
    sheets = {
        "FLINK": Sheet(
            [
                [
                    "Sample",
                    "Sample age (cal AD/BC)",
                    "\\iBetula\\i count",
                    "\\iPinus\\i count",
                    "\\iPopulus\\i count",
                ],
                [0.01, 1900.0, 1.0, 0.0, 0.0],
                [0.02, 1800.0, 2.0, 0.0, 0.0],
            ]
        ),
        "HOLK": Sheet(
            [["Sample", "Sample age (cal AD/BC)"], [1.0, 1900.0], [2.0, 1800.0]]
        ),
        "RANV": Sheet([["Sample", "SALIX"], [1.0, 2.0], [2.0, 3.0]]),
        "STAV": Sheet(
            [["", ""], ["", ""], ["Sample", "Betula"], ["", ""], [1.0, 1.0], [2.0, 2.0]]
        ),
    }
    ledger = {
        seq: {
            "typed_workbook_member": "rootsi/" + seq + ".xls",
            "typed_workbook_sha256": "a" * 64,
            "site_samples": "2",
            "source_top_bp": "50",
            "source_bottom_bp": "150",
        }
        for seq in sheets
    }
    sites = []
    for _sequence, dataset, site, chronology in [
        ("FLINK", 54024, 28889, 38438),
        ("STAV", 54003, 28873, 38423),
    ]:
        samples = [
            {
                "depth": float(i),
                "sampleid": dataset * 10 + i,
                "ages": [
                    {
                        "chronologyid": chronology,
                        "agetype": "Calibrated radiocarbon years BP",
                        "ageolder": None,
                        "ageyounger": None,
                        "age": 50.0 if i == 1 else 150.0,
                    }
                ],
                "datum": [
                    {
                        "units": "NISP",
                        "element": "pollen",
                        "variablename": "Betula",
                        "value": float(i),
                    }
                ],
            }
            for i in (1, 2)
        ]
        sites.append(
            {
                "site": {
                    "dataset": {"datasetid": dataset},
                    "siteid": site,
                    "collectionunit": {
                        "defaultchronology": chronology,
                        "dataset": {"samples": samples},
                        "chronologies": [
                            {
                                "chronology": {
                                    "chronology": {
                                        "notes": "Synthetic source-only note"
                                    }
                                }
                            }
                        ],
                    },
                }
            }
        )
    return sheets, ledger, {"part_number": 8, "rows": sites}


def main() -> None:
    assert "xlrd" not in sys.modules
    catalog = load(SOURCE / "xlrd-cache-contract.json")
    count = 0
    with tempfile.TemporaryDirectory(dir=SOURCE / "preflight") as name:
        root = Path(name)
        cache = root / "cache"
        shutil.copytree(CACHE, cache)
        assert len(validate_cache(cache, catalog)) == 16
        count += 1
        target = cache / "xlrd/info.py"
        original = target.read_bytes()
        target.write_bytes(original + b"\n")
        refused(validate_cache, cache, catalog)
        target.write_bytes(original)
        count += 1
        extra = cache / "unexpected.py"
        extra.write_text("")
        refused(validate_cache, cache, catalog)
        extra.unlink()
        count += 1
        extra.mkdir()
        refused(validate_cache, cache, catalog)
        extra.rmdir()
        count += 1
        os.mkfifo(extra)
        try:
            refused(inventory, cache)
        finally:
            extra.unlink()
        count += 1
        extra.symlink_to(cache / "xlrd/info.py")
        try:
            refused(inventory, cache)
        finally:
            extra.unlink()
        count += 1
        for unsafe_path in (
            "../escape",
            "/escape",
            "xlrd//module.py",
            "xlrd/./module.py",
            "xlrd/../module.py",
            "xlrd\\module.py",
        ):
            refused(safe_member, unsafe_path)
            count += 1
        for member, old_value, new_value in [
            (
                "xlrd-2.0.2.dist-info/WHEEL",
                "Root-Is-Purelib: true",
                "Root-Is-Purelib: false",
            ),
            (
                "xlrd-2.0.2.dist-info/WHEEL",
                "Tag: py3-none-any",
                "Tag: cp311-cp311-macosx_11_0_arm64",
            ),
            (
                "xlrd-2.0.2.dist-info/METADATA",
                "Version: 2.0.2",
                "Version: 2.0.2\nRequires-Dist: unselected-runtime",
            ),
            (
                "xlrd-2.0.2.dist-info/RECORD",
                "xlrd/__init__.py,sha256=kmuIEz8cutatGjjW3EmaApTEgcHmcsYo0CcWH_th2P0,7320",
                "xlrd/__init__.py,sha256=wrong,7320",
            ),
        ]:
            path = cache / member
            original = path.read_bytes()
            assert old_value in original.decode()
            path.write_text(original.decode().replace(old_value, new_value))
            altered = deepcopy(catalog)
            altered["entries"] = inventory(cache)
            try:
                refused(validate_cache, cache, altered)
            finally:
                path.write_bytes(original)
            count += 1
        controller = root / "controller"
        controller.mkdir()
        original_source = c.SOURCE
        c.SOURCE = controller
        try:
            c.source_namespace()
            for kind in ("module", "directory", "fifo", "alias"):
                path = controller / (
                    "unexpected.py" if kind == "module" else "unexpected"
                )
                if kind == "module":
                    path.write_text("")
                elif kind == "directory":
                    path.mkdir()
                elif kind == "fifo":
                    os.mkfifo(path)
                else:
                    path.symlink_to(cache / "xlrd/info.py")
                try:
                    refused(c.source_namespace)
                finally:
                    if path.is_dir() and not path.is_symlink():
                        path.rmdir()
                    else:
                        path.unlink()
                count += 1
        finally:
            c.SOURCE = original_source
        input_file = root / "input"
        input_file.write_text("old")
        frozen = frozen_pin_union([pin(input_file), pin(input_file)])
        assert len(frozen) == 1
        count += 1
        input_file.write_text("changed")
        refused(verify_frozen_pins, frozen)
        count += 1
        refused(
            qualify_process_snapshot,
            {
                "native_images": [],
                "namespace": [
                    {"module": "unselected", "file": "/unselected/module.py"}
                ],
            },
            [],
            SOURCE,
        )
        count += 1
        outputs = root / "outputs"
        outputs.mkdir()
        (outputs / "regular").write_text("")
        assert len(output_products(outputs)) == 1
        os.mkfifo(outputs / "fifo")
        try:
            refused(output_products, outputs)
        finally:
            (outputs / "fifo").unlink()
        count += 1
        output_alias = root / "alias-directory"
        output_alias.symlink_to(outputs, target_is_directory=True)
        refused(confined_output, output_alias / "future.json")
        count += 1
        refused(physical_pin, output_alias / "regular")
        count += 1
        special = outputs / "refused-receipt"
        os.mkfifo(special)
        try:
            refused(dump, special, {})
        finally:
            special.unlink()
        count += 1
        zip_path = root / "python311.zip"
        zip_path.symlink_to(root / "missing")
        assert not absent_path(zip_path)
        zip_path.unlink()
        count += 1
    refused(confined_output, SOURCE / "../escape")
    count += 1
    for env in (
        {"DYLD_INSERT_LIBRARIES": ""},
        {"LD_PRELOAD": ""},
        {"__PYVENV_LAUNCHER__": ""},
    ):
        refused(require_environment, env)
        count += 1
    assert expand_dependency(
        "@loader_path", Path("/owner/lib"), Path("/bin/python")
    ) == Path("/owner")
    count += 1
    assert expand_dependency(
        "/opt/openssl@3/lib/crypto", Path("/owner/lib"), Path("/bin/python")
    ) == Path("/opt/openssl@3/lib/crypto")
    count += 1
    refused(expand_dependency, "@unknown/lib", Path("/owner/lib"), Path("/bin/python"))
    count += 1
    refused(dependency_load_names, "wrong header", Path("/owner/lib"))
    count += 1
    for value in (True, None, float("nan"), float("inf")):
        refused(number, value)
        count += 1
    assert [
        count_status(0, []),
        count_status(1, []),
        count_status(1, [1]),
        count_status(1, [2]),
        count_status(1, [1, 1]),
    ] == [
        "absent_source_zero",
        "absent_source_positive",
        "explicit_agreement",
        "explicit_difference",
        "ambiguous_source_name",
    ]
    count += 1
    assert endpoints([2000.0, -100.0]) == [-50, 2050]
    count += 1
    sheets, ledger, raw = fixture()
    finding = workbook_age_findings(sheets, ledger)
    assert (
        all(row["dated_event_admitted"] is False for row in finding)
        and finding[2]["source_age_basis"] is None
        and finding[3]["numeric_source_ages"] == 0
    )
    count += 1
    bad = deepcopy(sheets)
    bad["FLINK"].rows[1][1] = "1900"
    refused(workbook_age_findings, bad, ledger)
    count += 1
    bad = deepcopy(sheets)
    bad["STAV"].rows[3][0] = "not empty"
    refused(workbook_age_findings, bad, ledger)
    count += 1
    findings, joins = neotoma_findings(sheets, ledger, raw)
    assert (
        findings[0]["selected_count_cell_status"]
        == {"absent_source_zero": 4, "explicit_agreement": 2}
        and findings[1]["neotoma_age_vector_transfer"]
        == "candidate_only_no_workbook_age_field"
        and joins["FLINK"]["matched_depth_rows"] == 2
    )
    count += 1
    bad = deepcopy(raw)
    bad["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][0]["ages"][0][
        "ageolder"
    ] = 0
    refused(neotoma_findings, sheets, ledger, bad)
    count += 1
    bad = deepcopy(raw)
    bad["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][1]["depth"] = 1.0
    refused(neotoma_findings, sheets, ledger, bad)
    count += 1
    bad = deepcopy(sheets)
    bad["FLINK"].rows[0][2] = "other taxon"
    refused(neotoma_findings, bad, ledger, raw)
    count += 1
    with tempfile.TemporaryDirectory(dir=SOURCE / "preflight") as boundary_root:
        count += entrypoint_import_guards(Path(boundary_root))
    assert "xlrd" not in sys.modules
    print(
        json.dumps(
            {
                "source_only_actual_exit": 0,
                "meaningful_guard_groups": count,
                "xlrd_imports": 0,
                "XLS_decodes_or_actual_replay_or_native_runtime_preparation": 0,
            }
        )
    )


if __name__ == "__main__":
    main()

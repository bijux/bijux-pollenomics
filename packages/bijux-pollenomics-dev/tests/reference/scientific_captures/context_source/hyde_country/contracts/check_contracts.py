"""Exercise independent HYDE source arithmetic and fail-closed custody on synthetic data."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from copy import deepcopy
from decimal import Decimal
from io import BytesIO
import os
from pathlib import Path
import sys
import tempfile
from typing import Any
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contracts as c
import metadata as m
from runtime import absent_path, dependency_load_names


def refuses(function: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    try:
        function(*args, **kwargs)
    except (ValueError, OSError, KeyError, TypeError):
        return
    raise AssertionError("Unsafe source/custody case accepted")


def workbook(names: list[tuple[str, str]]) -> bytes:
    strings = (
        '<sst xmlns="'
        + m.NS[1:-1]
        + '">'
        + "".join("<si><t>" + name + "</t></si>" for name, _ in names)
        + "</sst>"
    )
    sheet = (
        '<worksheet xmlns="'
        + m.NS[1:-1]
        + '"><sheetData>'
        + "".join(
            '<row><c r="A'
            + str(i + 1)
            + '"><v>'
            + iso
            + '</v></c><c r="B'
            + str(i + 1)
            + '" t="s"><v>'
            + str(i)
            + "</v></c></row>"
            for i, (_, iso) in enumerate(names)
        )
        + "</sheetData></worksheet>"
    )
    inner = BytesIO()
    with ZipFile(inner, "w") as zipped:
        zipped.writestr("xl/sharedStrings.xml", strings)
        zipped.writestr("xl/worksheets/sheet1.xml", sheet)
    outer = BytesIO()
    with ZipFile(outer, "w") as zipped:
        zipped.writestr("HYDE_country_codes.xlsx", inner.getvalue())
    return outer.getvalue()


def country_table(value: str = "1.00") -> bytes:
    return (
        "region "
        + " ".join(map(str, m.YEARS))
        + "\n"
        + "".join(
            iso + " " + " ".join([value] * 7) + "\n"
            for _, iso in m.COUNTRY_NAMES.values()
        )
    ).encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=c.SOURCE / "preflight/qualified-source-controls"
    )
    output = c.confined_output(parser.parse_args().output, absent=True)
    output.mkdir()
    cases = []
    report = c.load(
        c.ROOT / "docs/report/regions/nordic/hyde-country-cropland/report.json"
    )
    c.validate_scope(report)
    cases.append("complete-84-28-4-source-report-and-unresolved-rights-contract")
    for key, value in [
        ("rows", 84.0),
        ("country_years", True),
        ("measure", "independent observed vegetation"),
        ("scenarios", ["base", "lower"]),
        ("source_year_ce_labels", [1450, 950, 450, 250, 50, -50, -75]),
        ("remaining", []),
    ]:
        bad = deepcopy(report)
        bad[key] = value
        refuses(c.validate_scope, bad)
    cases.append("typed-population-calendar-observation-and-limits-refusals")
    bad = deepcopy(report)
    bad["inputs"][1], bad["inputs"][2] = bad["inputs"][2], bad["inputs"][1]
    refuses(c.validate_scope, bad)
    cases.append("ordered-complete-four-source-identities")
    names = [(name, iso) for name, (_, iso) in m.COUNTRY_NAMES.items()]
    mapping = m.country_mapping(workbook(names))
    assert mapping == {"DK": "208", "FI": "246", "NO": "578", "SE": "752"}
    cases.append("synthetic-native-nested-XML-four-country-ISO-positive")
    refuses(m.country_mapping, workbook(names[:-1]))
    refuses(m.country_mapping, workbook([*names, names[0]]))
    refuses(m.country_mapping, workbook([("Denmark", "999"), *names[1:]]))
    cases.append("missing-duplicate-wrong-source-ISO-refusals")
    values = m.values(country_table(), mapping)
    assert len(values) == 28 and all(x == Decimal("1.00") for x in values.values())
    cases.append("synthetic-source-28-exact-Decimal-values")
    for token in ["NaN", "Infinity", "-0.1", "not-a-number"]:
        refuses(m.values, country_table(token), mapping)
    cases.append("nonfinite-negative-and-nonnumeric-native-value-refusals")
    refuses(m.values, country_table().replace(b"2025", b"2024"), mapping)
    refuses(m.values, country_table().replace(b"2000", b"1900"), mapping)
    cases.append("missing-or-duplicated-lexical-CE-column-refusals")
    refuses(
        m.values, country_table() + country_table().splitlines()[1] + b"\n", mapping
    )
    refuses(m.values, b"\n".join(country_table().splitlines()[:-1]), mapping)
    cases.append("duplicate-and-missing-native-country-refusals")
    scenarios = {
        name: {key: value + Decimal(offset) for key, value in values.items()}
        for name, offset in [("base", 0), ("lower", 2), ("upper", -1)]
    }
    rows = m.joined_rows(mapping, scenarios)
    assert (
        len(rows) == 84
        and rows[1]["difference_from_base_km2"] == "2.00"
        and rows[2]["difference_from_base_km2"] == "-1.00"
    )
    assert rows[0]["difference_from_base_km2"] == "0"
    assert len(m.csv_bytes(rows).splitlines()) == 85
    cases.append(
        "84-source-scenario-rows-Decimal-base-difference-no-interval-inference"
    )
    refuses(m.joined_rows, mapping, dict(reversed(list(scenarios.items()))))
    badscenarios = deepcopy(scenarios)
    del badscenarios["base"][("DK", 500)]
    refuses(m.joined_rows, mapping, badscenarios)
    cases.append("incomplete-or-permuted-scenario-population-refusals")
    assert not c.exact({"rows": 84}, {"rows": 84.0}) and not c.exact([0], [False])
    cases.append("typed-equality-no-bool-number-coercion")
    with tempfile.TemporaryDirectory(dir=output) as directory:
        root = Path(directory)
        file = root / "source"
        file.write_text("original")
        row = c.pin(file)
        assert c.frozen_pin_union([row, row]) == [row]
        refuses(c.frozen_pin_union, [row, {**row, "bytes": 1}])
        file.write_text("changed")
        refuses(c.verify_frozen_pins, [row])
        cases.append("frozen-source-census-race-and-conflicting-duplicate-refusals")
        file.write_text("original")
        alias = root / "alias"
        alias.symlink_to(file)
        refuses(c.pin, alias)
        refuses(c.output_products, root)
        alias.unlink()
        special = root / "named-pipe"
        os.mkfifo(special)
        refuses(c.output_products, root)
        special.unlink()
        cases.append("output-alias-and-FIFO-total-traversal-refusals")
        alias.symlink_to(root, target_is_directory=True)
        refuses(c.confined_output, alias / "future", absent=True)
        alias.unlink()
        refuses(c.confined_output, root / "child/../../escape", absent=True)
        refuses(c.confined_output, root, absent=True)
        cases.append("output-ancestor-traversal-existing-root-refusals")
        absent = root / "python311.zip"
        assert absent_path(absent)
        absent.symlink_to(root / "missing")
        assert not absent_path(absent)
        cases.append("dangling-stdlib-ZIP-not-absent")
    assert dependency_load_names(
        "/fake (architecture arm64):\n\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1.0.0)\n",
        Path("/fake"),
    ) == ["/usr/lib/libSystem.B.dylib"]
    cases.append("qualified-native-inspector-ARM64-header-parser")
    expected_csv = m.csv_bytes(rows)
    c.validate_products(
        report, expected_csv, report, expected_csv, report, expected_csv
    )
    refuses(
        c.validate_products,
        report,
        expected_csv.replace(b"2.00", b"2.01", 1),
        report,
        expected_csv,
        report,
        expected_csv,
    )
    refuses(
        c.validate_products,
        report,
        expected_csv.replace(b"\n", b"\r\n"),
        report,
        expected_csv,
        report,
        expected_csv,
    )
    cases.append("all84-output-values-and-exact-CSV-serialization-refusals")
    bad = deepcopy(report)
    bad["inputs"][0]["sha256"] = "0" * 64
    refuses(
        c.validate_products,
        bad,
        expected_csv,
        report,
        expected_csv,
        report,
        expected_csv,
    )
    cases.append("stale-source-identity-not-a-new-output-baseline")
    bad = deepcopy(report)
    bad["rows"] = 84.0
    refuses(
        c.validate_products,
        bad,
        expected_csv,
        report,
        expected_csv,
        report,
        expected_csv,
    )
    cases.append("typed-complete-report-output-refusal")
    # No runtime_inputs/inspector/preparer, private source reads or maintained CLI calls.
    c.dump(
        output / "receipt.json",
        {
            "actual_exit": 0,
            "groups": cases,
            "count": len(cases),
            "private_source_or_producer_calls": 0,
        },
    )
    print(__import__("json").dumps({"actual_exit": 0, "groups": len(cases)}))


if __name__ == "__main__":
    main()

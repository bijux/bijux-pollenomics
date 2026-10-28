"""Exercise Swedish metadata refusals and custody using bounded synthetic fixtures."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contracts as c
from custody import RETAINED, retained_contract, validate_launch_log
from metadata import (
    PROFILES,
    age_events,
    dataset_sites,
    profile_handle,
    retained_identities,
    table,
    title,
    title_screen,
)
from runtime import dependency_load_names, expand_dependency


def refuses(function: Callable[..., Any], *args: Any) -> None:
    try:
        function(*args)
    except (ValueError, OSError, KeyError, TypeError):
        return
    raise AssertionError("Unsafe metadata/custody scope accepted")


def hit(identifier: int, label: str) -> dict[str, Any]:
    return {
        "_id": str(identifier),
        "_source": {
            "xml-thumb": '<MetaData xmlns="http://www.pangaea.de/MetaData"><title>'
            + label
            + "</title></MetaData>"
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=c.SOURCE / "preflight/source-controls"
    )
    output = c.confined_output(parser.parse_args().output, absent=True)
    output.mkdir()
    cases = []
    mutate: Callable[[dict[str, Any]], Any]
    current = c.load(
        c.ROOT
        / "docs/report/source-relations/neotoma/swedish-cohort-availability/report.json"
    )
    c.validate_scope(current)
    cases.append("complete-current-metadata102-99-206-66-62-37-refusal-scope")
    for key, value in (
        ("records", 102.0),
        ("unique_site_ids", True),
        ("retained_site_ids", 199),
        ("site_ids_outside_retained_snapshot", [123]),
    ):
        changed = deepcopy(current)
        changed["neotoma_inventory"][key] = value
        refuses(c.validate_scope, changed)
    cases.append("dataset-site-count-type-and-outside-site-refusals")
    records: list[dict[str, Any]] = [
        {"site": {"siteid": index % 99, "datasets": [{"datasetid": index}]}}
        for index in range(102)
    ]
    assert len(dataset_sites(records)) == 99
    records[-1]["site"]["datasets"][0]["datasetid"] = records[0]["site"]["datasets"][0][
        "datasetid"
    ]
    refuses(dataset_sites, records)
    records[-1]["site"]["datasets"][0]["datasetid"] = 101
    records[-1]["site"]["siteid"] = True
    refuses(dataset_sites, records)
    cases.append(
        "complete102-unique-native-datasets99sites-duplicate-and-boolean-refusals"
    )
    for mutate in (
        lambda x: x[-1].update(datasetid=101),
        lambda x: x[-1]["site"].pop("datasets"),
        lambda x: x[-1]["site"].update(datasets=[]),
        lambda x: x[-1]["site"]["datasets"].append({"datasetid": 200}),
        lambda x: x[-1]["site"]["datasets"][0].update(datasetid=True),
        lambda x: x[-1]["site"]["datasets"][0].update(datasetid=101.0),
        lambda x: x[-1]["site"].update(siteid="2"),
    ):
        nested = [
            {"site": {"siteid": index % 99, "datasets": [{"datasetid": index}]}}
            for index in range(102)
        ]
        mutate(nested)
        refuses(dataset_sites, nested)
    cases.append(
        "actual-declared-nested-schema-missing-multiple-flattened-and-ID-type-refusals"
    )
    for key, value in (
        ("retained_neotoma_all_country_core_handles", 203),
        ("search_hits_matching_retained_handles", 63),
        ("pangaea_metadata_search_hits", 65),
        ("unmatched_named_core_handles", False),
        ("checked_epd_final_age_swedish_events", 38),
    ):
        changed = deepcopy(current)
        changed["epd_metadata_screen"][key] = value
        refuses(c.validate_scope, changed)
    cases.append("whole-country-unassigned-and-title-age-population-refusals")
    for mutate in (
        lambda x: x.update(result="fresh_cohort_qualified"),
        lambda x: x["cross_archive_leads"][0].update(
            selected_calibrated_age_model_in_checked_pangaea_metadata=True
        ),
        lambda x: x["epd_metadata_screen"]["named_leads"][2].update(
            selected_sample_age_sequence_identified=True
        ),
        lambda x: x["epd_metadata_screen"]["named_leads"][2][
            "retained_neotoma_identity"
        ].update(retained_country_code="SE"),
        lambda x: x["epd_metadata_screen"]["named_leads"].pop(),
        lambda x: x["epd_metadata_screen"]["hakulla5_chronology_reference"].update(
            selected_sample_age_sequence_in_table=True
        ),
    ):
        changed = deepcopy(current)
        mutate(changed)
        refuses(c.validate_scope, changed)
    cases.append("fresh-cohort-selected-age-country-filter-and-complete-lead-refusals")
    assert (
        profile_handle("Pollen profile of sediment core HAKULLA5, source metadata")
        == "HAKULLA5"
    )
    assert profile_handle("Pollen profile ADRAN, source metadata") == "ADRAN"
    assert profile_handle("Pollen profile of Schonen, generic metadata") is None
    assert profile_handle("Age determination of sediment core ADRAN, metadata") is None
    cases.append("metadata-title-handle-vocabulary-and-generic-unbound")
    assert (
        title(hit(1, "Pollen profile ADRAN, metadata"))
        == "Pollen profile ADRAN, metadata"
    )
    refuses(title, {"_source": {"xml-thumb": "<root/>"}})
    cases.append("source-namespace-title-parser-and-missing-title-refusal")
    identities: dict[str, dict[str, Any]] = {"H" + str(i): {} for i in range(59)}
    identities.update({name: {} for name in ("HAKULLA5", "NDRAKET", "VUOLEPAL")})
    hits = [
        hit(10000 + i, "Pollen profile H" + str(i) + ", metadata") for i in range(59)
    ]
    hits.extend(
        hit(PROFILES[name], "Pollen profile " + name + ", metadata")
        for name in ("HAKULLA5", "NDRAKET", "VUOLEPAL", "ADRAN", "GARASEL", "LEVEANIE")
    )
    hits.append(hit(761854, "Pollen profile of Schonen, generic metadata"))
    search = {"timed_out": False, "hits": {"total": 66, "hits": hits}}
    matched, unmatched, named, generic = title_screen(search, identities)
    assert matched == 62 and len(unmatched) == len(named) == 3 and generic == [761854]
    cases.append("complete-synthetic66-metadata-62-retained3-unmatched1-generic")
    for mutate in (
        lambda x: x.update(timed_out=True),
        lambda x: x["hits"].update(total=66.0),
        lambda x: x["hits"]["hits"].pop(),
        lambda x: x["hits"]["hits"][0].update(_id=str(761854)),
    ):
        changed = deepcopy(search)
        mutate(changed)
        refuses(title_screen, changed, identities)
    cases.append("truncated-timedout-typed-total-duplicate-DOI-refusals")
    filtered = {name: row for name, row in identities.items() if name != "HAKULLA5"}
    refuses(title_screen, search, filtered)
    cases.append("all-country-retained-handle-cannot-be-filtered-out")
    sites = [
        {
            "site_id": "site1",
            "source_site_id": 3138,
            "country_code": "UNASSIGNED",
            "source_payload": {"geopolitical": ["Sweden"]},
        }
    ]
    units = [
        {
            "site_id": "site1",
            "source_collection_unit_id": 3955,
            "collection_unit_id": "unit1",
            "source_payload": {"handle": "hakulla5"},
        }
    ]
    datasets = [{"collection_unit_id": "unit1", "source_dataset_id": 4082}]
    joined = retained_identities(sites, units, datasets)
    assert joined["HAKULLA5"]["retained_country_code"] == "UNASSIGNED" and joined[
        "HAKULLA5"
    ]["neotoma_pollen_dataset_ids"] == [4082]
    refuses(retained_identities, sites, units + units, datasets)
    refuses(
        retained_identities, sites, units, [{**datasets[0], "source_dataset_id": True}]
    )
    cases.append("site-core-dataset-all-country-join-and-duplicate-typed-ID-refusals")
    assert age_events(
        "Event(s):\nHAKULLA5 (abc) * LOCATION: Sweden\nNORWAY (abc) * LOCATION: Norway\n*/\nOTHER * LOCATION: Sweden"
    ) == {"HAKULLA5"}
    assert table("metadata\n*/\nEvent\tReference\nHAKULLA5\tEPD chron2\n") == [
        {"Event": "HAKULLA5", "Reference": "EPD chron2"}
    ]
    refuses(table, "Event\tReference\nHAKULLA5\tEPD chron2")
    cases.append(
        "event-header-only-and-chronology-reference-table-no-pollen-count-parsing"
    )
    with tempfile.TemporaryDirectory(dir=output) as name:
        root = Path(name)
        path = root / "input"
        path.write_bytes(b"reviewed")
        frozen = c.frozen_pin_union([c.pin(path), c.pin(path)])
        assert len(frozen) == 1
        changed = dict(frozen[0])
        changed["sha256"] = "0" * 64
        refuses(c.frozen_pin_union, [frozen[0], changed])
        path.write_bytes(b"tampered")
        refuses(c.verify_frozen_pins, frozen)
        cases.append(
            "frozen-union-identical-overlap-conflicting-role-and-pre-mkdir-drift-refusals"
        )
        document = root / "duplicate.json"
        document.write_text('{"key":1,"key":2}')
        refuses(c.load, document)
        document.write_text('{"key":NaN}')
        refuses(c.load, document)
        assert not c.exact({"count": 1}, {"count": True}) and not c.exact([1], [1.0])
        cases.append("duplicate-nonfinite-JSON-and-complete-typed-numeric-equality")
        original = c.SOURCE
        c.SOURCE = root
        try:
            c.source_namespace()
            for kind in ("module", "directory", "alias", "special"):
                p = root / ("shadow.py" if kind == "module" else "shadow")
                if kind == "module":
                    p.write_text("")
                elif kind == "directory":
                    p.mkdir()
                elif kind == "alias":
                    p.symlink_to(path)
                else:
                    os.mkfifo(p)
                refuses(c.source_namespace)
                p.rmdir() if kind == "directory" else p.unlink()
        finally:
            c.SOURCE = original
        cases.append("closed-helper-namespace-shadow-directory-alias-special-refusals")
        refuses(c.confined_output, c.ROOT / "artifacts/../escape")
        alias = root / "alias"
        alias.symlink_to(root, target_is_directory=True)
        refuses(c.confined_output, alias / "output")
        products = root / "products"
        products.mkdir()
        (products / "report.json").write_text("{}")
        assert len(c.output_products(products)) == 1
        special = products / "special"
        os.mkfifo(special)
        refuses(c.output_products, products)
        special.unlink()
        special.symlink_to(path)
        refuses(c.output_products, products)
        cases.append("artifact-confinement-and-inclusive-output-alias-special-refusals")
    assert expand_dependency(
        "/opt/homebrew/opt/openssl@3/lib/crypto", Path("/lib/loader"), c.BASE
    ) == Path("/opt/homebrew/opt/openssl@3/lib/crypto")
    refuses(expand_dependency, "@unsupported/x", Path("/lib/loader"), c.BASE)
    refuses(dependency_load_names, "not an image", Path("/image"))
    cases.append("inherited-native-loader-prefix-and-malformed-header-refusals")
    with tempfile.TemporaryDirectory(dir=output) as name:
        root = Path(name)
        for script in ("prepare.py", "run.py", "execute_source.py", "observe.py"):
            prefix = (c.SOURCE / script).read_text().split("sys.path.insert", 1)[0]
            code = compile(prefix, "controlled-native-entry-prefix", "exec")
            namespace: dict[str, Any] = {"__file__": str(root / script)}
            exec(code, namespace)
            assert namespace["_expected_python"] == c.MODULES
            shadow = root / "contracts.cpython-311-darwin.so"
            shadow.write_bytes(b"must not load")
            refuses(exec, code, {"__file__": str(root / script)})
            shadow.unlink()
    cases.append(
        "all-four-native-entrypoints-refuse-compiled-helper-shadow-before-import"
    )
    stdout_prefix = b"original stage summaries\n"
    original_log = {
        "bytes": len(stdout_prefix),
        "sha256": __import__("hashlib").sha256(stdout_prefix).hexdigest(),
    }
    common_pin = {"path": "/retained/terminal.json", "sha256": "a" * 64, "bytes": 10}
    outer_pin = {"path": "/retained/outer.json", "sha256": "b" * 64, "bytes": 11}
    tail = (
        json.dumps(
            {
                "terminal": common_pin["path"],
                "sha256": common_pin["sha256"],
                "status": "failed",
            }
        )
        + "\n"
        + json.dumps({"terminal": outer_pin, "actual_exit": 1})
        + "\n"
    ).encode()
    validate_launch_log(
        stdout_prefix + tail, original_log, common_pin, outer_pin, "failed"
    )
    for content in (
        b"X" + stdout_prefix[1:] + tail,
        stdout_prefix + tail[:-1],
        stdout_prefix + tail + b"unrecorded",
    ):
        refuses(
            validate_launch_log, content, original_log, common_pin, outer_pin, "failed"
        )
    refuses(
        validate_launch_log,
        stdout_prefix + tail,
        original_log,
        common_pin,
        outer_pin,
        "passed",
    )
    cases.append(
        "original-stdout-stdout_prefix-and-only-source-defined-failed-terminal-tails"
    )
    original = c.load(RETAINED / "plan.json")
    common = c.load(RETAINED / "terminal.json")
    outer = c.load(RETAINED / "swedish-cohort-terminal.json")
    retained_contract(original, common, outer)
    cases.append("genuine-original-plan3537-source0-observer1-whole1-declared-contract")
    for mutate in (
        lambda x: x.update(actual_exit=0),
        lambda x: x["stages"][0].update(actual_exit=1),
        lambda x: x["stages"][1].update(actual_exit=0),
        lambda x: x["stages"][0].update(timed_out=True),
        lambda x: x["stages"][0]["argv"].append("unregistered"),
        lambda x: x["stages"].pop(),
        lambda x: x["after_pin_mismatches"].append("changed input"),
    ):
        altered = deepcopy(common)
        mutate(altered)
        refuses(retained_contract, original, altered, outer)
    cases.append("original-native-exit-command-timeout-membership-and-custody-refusals")
    for value in (0, True):
        altered = deepcopy(outer)
        altered["actual_exit"] = value
        refuses(retained_contract, original, common, altered)
    altered = deepcopy(original)
    altered["input_pins"][-1] = altered["input_pins"][0]
    refuses(retained_contract, altered, common, outer)
    cases.append("no-relabelling-original-whole-failure-or-duplicate-original-pin")
    c.dump(
        output / "receipt.json",
        {
            "source_only_actual_exit": 0,
            "meaningful_guard_groups": len(cases),
            "cases": cases,
            "actual_source_metadata_producer_parser_join_preparer_native_or_inspector_calls": 0,
            "fixture_scope": "Synthetic metadata plus current public report scope only; no actual26 private metadata joins.",
        },
    )
    print(
        json.dumps(
            {"source_only_actual_exit": 0, "meaningful_guard_groups": len(cases)}
        )
    )


if __name__ == "__main__":
    main()

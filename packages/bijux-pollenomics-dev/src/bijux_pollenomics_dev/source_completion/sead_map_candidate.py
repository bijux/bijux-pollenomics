"""Audit the built Nordic SEAD map against its governed source and browser replay."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, cast

from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics_dev.docs.sead_evidence_sync import synchronize_sead_evidence

COUNTRIES = {"Denmark": "DK", "Finland": "FI", "Norway": "NO", "Sweden": "SE"}
SITE_LAYER = "sead-sites"
RECORD_LAYER = "sweden-archaeology-site-discovery"
REPORT = Path("docs/report/source-relations/sead/map-candidate")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _chunk(directory: Path, row: dict[str, Any]) -> dict[str, Any]:
    path = directory / row["path"]
    payload = path.read_bytes()
    if _sha(payload) != row["sha256"]:
        raise ValueError(f"Built atlas chunk hash changed: {row['path']}")
    return decode_chunk_script(
        payload,
        expected_asset_key=row["asset_key"],
        expected_payload_sha256=row["payload_sha256"],
        expected_payload_encoding=row["payload_encoding"],
        expected_decoded_byte_count=row.get("decoded_byte_count"),
    )


def _built_layers(
    repository: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, list[dict[str, Any]]], int]:
    directory = repository / "docs/report/regions/nordic"
    html = (directory / "nordic_map.html").read_text()
    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    if match is None:
        raise ValueError("Built Nordic map has no static bootstrap")
    manifest = json.loads(match.group(1))
    inventory = normalize_asset_inventory(manifest["assets"])
    provenance = _chunk(
        directory, next(row for row in inventory if row["domain"] == "provenance")
    )
    layers = {
        entry["layer"]["key"]: entry["layer"]
        for entry in provenance["layers"]
        if entry["layer"]["key"] in {SITE_LAYER, RECORD_LAYER}
    }
    if set(layers) != {SITE_LAYER, RECORD_LAYER}:
        raise ValueError("Built SEAD layers are missing")
    features: dict[str, list[dict[str, Any]]] = {key: [] for key in layers}
    for row in inventory:
        layer_key = row.get("layer_key")
        if (
            row["domain"] == "nodes"
            and isinstance(layer_key, str)
            and layer_key in features
        ):
            nodes = _chunk(directory, row)["features"]
            if len(nodes) != row["record_count"]:
                raise ValueError("Built SEAD node count differs from manifest")
            features[layer_key].extend(nodes)
    edge_row = next(row for row in inventory if row["domain"] == "edges")
    edge_count = len(_chunk(directory, edge_row)["records"])
    return manifest, layers, features, edge_count


def _run_time_filter(
    repository: Path, features: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    html = (
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html"
    ).read_text()
    start = html.index("function finiteTimeValue")
    end = html.index("function pointFeatureInTimeWindow", start)
    helpers = html[start:end]
    site = next(
        feature
        for feature in features[SITE_LAYER]
        if feature["record_id"] == "sead:site:3840"
    )
    unresolved = next(
        feature
        for feature in features[SITE_LAYER]
        if feature["record_id"] == "sead:site:6468"
    )
    zero = next(
        feature for feature in features[SITE_LAYER] if feature.get("time_start_bp") == 0
    )
    records = [
        feature
        for feature in features[RECORD_LAYER]
        if feature["record_id"] == "sead:site:3840"
    ]
    if len(records) != 11:
        raise ValueError("Disjoint-site regression no longer has 11 source records")
    js = (
        "const TIME_HAS_DATA=true; let timeStartBp=84,timeIntervalYears=20;\n"
        "function timeWindowEndBp(){return timeStartBp+timeIntervalYears}\n"
        "function timeFilterUsesFullExtent(){return false}\n"
        + helpers
        + "\nconst input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));\n"
        "const recordLayer={applies_time_filter:true,semantic_role:'source_chronology_context'};\n"
        "const siteLayer={applies_time_filter:false};\n"
        "const gap=input.records.filter(x=>featureInTimeWindow(recordLayer,x));\n"
        "timeStartBp=82;timeIntervalYears=0;\n"
        "const dated=input.records.filter(x=>featureInTimeWindow(recordLayer,x));\n"
        "timeStartBp=0;timeIntervalYears=0;\n"
        "console.log(JSON.stringify({gap_record_count:gap.length,at_82_record_count:dated.length,"
        "zero_site_status:featureTimeAdmission(input.zero).status,"
        "zero_site_in_test_window:featureInTimeWindow(recordLayer,input.zero),"
        "unresolved_site_status:featureTimeAdmission(input.unresolved).status,"
        "unresolved_site_in_test_window:featureInTimeWindow(recordLayer,input.unresolved),"
        "site_layer_applies_time_filter:siteLayer.applies_time_filter,"
        "site_hull_visible_as_context:featureInTimeWindow(siteLayer,input.site)}));\n"
    )
    result = subprocess.run(
        ["node", "-e", js],
        input=json.dumps(
            {"site": site, "unresolved": unresolved, "zero": zero, "records": records}
        ),
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    observed = cast(dict[str, Any], json.loads(result.stdout))
    expected = {
        "gap_record_count": 0,
        "at_82_record_count": 2,
        "zero_site_status": "valid",
        "zero_site_in_test_window": True,
        "unresolved_site_status": "contextual",
        "unresolved_site_in_test_window": False,
        "site_layer_applies_time_filter": False,
        "site_hull_visible_as_context": True,
    }
    if observed != expected:
        raise ValueError(f"Built SEAD time-filter behavior differs: {observed}")
    return observed


def audit(repository: Path, candidate: Path, browser_receipt: Path) -> dict[str, Any]:
    """Check exact built payloads, governed denominators and browser detail outcome."""
    repository = repository.resolve()
    manifest, layers, features, edge_count = _built_layers(repository)
    site_features, record_features = features[SITE_LAYER], features[RECORD_LAYER]
    source = repository / "docs/report/source-relations/sead"
    country = _read_json(source / "country-coverage/report.json")
    claims = _read_json(source / "chronology-country-accounting/report.json")
    intervals = _read_json(source / "interval-sets/report.json")
    contract = _read_json(
        repository / "docs/report/regions/nordic/nordic_map_publication_contract.json"
    )
    synchronize_sead_evidence(repository, check=True)
    map_prose = (
        repository / "docs/report/regions/nordic/nordic_map_publication_contract.md"
    ).read_text()
    handbook = (
        repository / "docs/public/pollenomics-data/sources/sead-handbook.md"
    ).read_text()
    if not all(
        phrase in map_prose
        for phrase in (
            "Site envelopes summarize source chronology and are not dated events or interval evidence.",
            "| `2069` |",
            "| `8799` |",
        )
    ) or not all(
        phrase in handbook
        for phrase in (
            "| assigned four-country sites | 2,069 |",
            "| Swedish numeric chronology features | 7,244 |",
            "| chronology claims | 25,109 |",
        )
    ):
        raise ValueError(
            "Public SEAD map narrative no longer matches governed counts or posture"
        )
    generation = _read_json(candidate / "generation.json")
    browser = _read_json(browser_receipt)
    source_id = country["source_run_id"]
    if {
        claims["source_run_id"],
        intervals["source_run_id"],
        contract["detail_projection"]["sources"]["sead"]["source_run_id"],
    } != {source_id}:
        raise ValueError("SEAD report and map source runs differ")
    counts = Counter(feature["country"] for feature in site_features)
    expected_counts = {
        next(
            name for name, code in COUNTRIES.items() if code == row["country_code"]
        ): row["governed_assigned_sites"]
        for row in country["country_rows"]
    }
    if (
        counts != expected_counts
        or len(site_features) != intervals["denominators"]["exported_sites"]
    ):
        raise ValueError("Built SEAD site and governed country counts differ")
    site_untimed = sum(
        feature.get("time_start_bp") is None and feature.get("time_end_bp") is None
        for feature in site_features
    )
    record_untimed = sum(
        feature.get("time_start_bp") is None and feature.get("time_end_bp") is None
        for feature in record_features
    )
    record_numeric = len(record_features) - record_untimed
    if (len(record_features), record_numeric, record_untimed, site_untimed) != (
        8799,
        intervals["denominators"]["exported_record_intervals"],
        1555,
        1219,
    ):
        raise ValueError("Built SEAD chronology display denominators differ")
    if any(feature["country"] != "Sweden" for feature in record_features):
        raise ValueError("Swedish discovery layer gained unsupported country scope")
    if (
        layers[SITE_LAYER]["applies_time_filter"]
        or layers[SITE_LAYER]["default_enabled"]
        or not layers[RECORD_LAYER]["applies_time_filter"]
    ):
        raise ValueError("Built SEAD layer visibility/time posture differs")
    rows_by_key = {row["key"]: row for row in contract["layer_rows"]}
    for key in (SITE_LAYER, RECORD_LAYER):
        if (
            layers[key]["coverage_label"] != rows_by_key[key]["coverage_label"]
            or layers[key]["count"] != rows_by_key[key]["count"]
        ):
            raise ValueError("Built SEAD layer and public contract prose/count differ")
    if (
        "not dated events or interval evidence"
        not in layers[SITE_LAYER]["coverage_label"]
    ):
        raise ValueError("Site hull is not explicitly identified as context")
    if (
        country["eligible_evidence_event_count"],
        contract["detail_projection"]["sources"]["sead"]["eligible_event_count"],
    ) != (0, 0):
        raise ValueError("SEAD ecological event count gained admission")
    if any(
        row["eligible_evidence_events"] or row["propagation_eligible_sites"]
        for row in country["country_rows"]
    ):
        raise ValueError("SEAD country event eligibility changed")
    if (
        contract["detail_projection"]["sources"]["sead"]["propagation_status"]
        != "refused"
        or edge_count != 0
    ):
        raise ValueError("Built map has accepted SEAD propagation")
    if (
        browser["status"] != "PASS"
        or browser["runtime_errors"]
        or len(browser["chronology_tables"]) != 16
    ):
        raise ValueError("Four-country browser detail replay did not pass")
    if (
        generation["source_atlas_build_id"] != manifest["build_id"]
        or not generation["selected_source_record_equality"]
    ):
        raise ValueError("Browser candidate does not match built Nordic map")
    if len(generation["source_records"]) != 8 or set(generation["countries"]) != set(
        COUNTRIES
    ):
        raise ValueError("Browser candidate lacks a four-country source detail pair")
    time_filter = _run_time_filter(repository, features)
    return {
        "schema_version": "sead-built-map-candidate-audit.v1",
        "status": "PASS",
        "source_run_id": source_id,
        "source_release_status": contract["detail_projection"]["sources"]["sead"][
            "acquisition_release_status"
        ],
        "published_atlas_build_id": manifest["build_id"],
        "browser_candidate_build_id": generation["candidate_build_id"],
        "browser_status": browser["status"],
        "browser_chronology_table_checks": len(browser["chronology_tables"]),
        "browser_runtime_error_count": len(browser["runtime_errors"]),
        "public_evidence_sync_status": "current",
        "site_count": len(site_features),
        "site_country_counts": dict(sorted(counts.items())),
        "site_untimed_count": site_untimed,
        "record_count": len(record_features),
        "record_numeric_count": record_numeric,
        "record_unresolved_count": record_untimed,
        "reviewed_claim_count": claims["claim_count"],
        "eligible_ecological_event_count": 0,
        "built_accepted_edge_count": edge_count,
        "cross_border_propagation_posture": "refused_zero_eligible_events_all_four_countries",
        "time_filter_regression": time_filter,
        "source_sha256": {
            str(path.relative_to(repository)): _sha(path.read_bytes())
            for path in (
                source / "country-coverage/report.json",
                source / "chronology-country-accounting/report.json",
                source / "interval-sets/report.json",
                repository / "docs/report/regions/nordic/nordic_map.html",
                repository
                / "docs/report/regions/nordic/nordic_map_publication_contract.json",
                repository
                / "docs/report/regions/nordic/nordic_map_publication_contract.md",
                repository / "docs/public/pollenomics-data/sources/sead.md",
                repository / "docs/public/pollenomics-data/sources/sead-handbook.md",
                repository
                / "docs/public/pollenomics-data/publications/sead-exports.md",
                repository
                / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html",
                Path(__file__).resolve(),
            )
        },
        "browser_receipt_sha256": _sha(browser_receipt.read_bytes()),
        "candidate_generation_sha256": _sha(
            (candidate / "generation.json").read_bytes()
        ),
    }


def main() -> None:
    """Write a governed result for an actual built and browser-checked candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--browser-receipt", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.repository, args.candidate, args.browser_receipt)
    output = args.output or args.repository / REPORT
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (output / "README.md").write_text(
        "# SEAD built map candidate\n\n"
        f"The published Nordic atlas build `{result['published_atlas_build_id']}` and the "
        f"browser candidate `{result['browser_candidate_build_id']}` agree on the "
        f"retained four-country SEAD source details. The browser replay checked "
        f"{result['browser_chronology_table_checks']} chronology tables at two widths "
        f"with {result['browser_runtime_error_count']} runtime errors. "
        "The public SEAD evidence blocks and map layer prose/counts match the "
        "governed sources. The [machine report](report.json) binds the checked "
        "source and map bytes.\n\n"
        f"The built site layer contains {result['site_count']:,} context points, including "
        f"{result['site_untimed_count']:,} without numeric site envelopes. "
        f"The Swedish discovery layer contains {result['record_count']:,} features: "
        f"{result['record_numeric_count']:,} numeric record intervals and "
        f"{result['record_unresolved_count']:,} unresolved context records. "
        "A live run of the map's time-filter functions excluded every site 3840 "
        "record from the 84–104 BP gap and admitted the two 82 BP records at 82 BP; "
        "a source-backed 0 BP site envelope remained numeric while an unresolved "
        "site remained outside the test time window. The optional site inventory "
        "ignores the time filter because its envelopes are display context.\n\n"
        f"The source review contains {result['reviewed_claim_count']:,} typed chronology "
        "claims and zero eligible ecological events across Denmark, Finland, Norway "
        "and Sweden. The built atlas contains zero accepted propagation edges. "
        "Cross-border candidate materialization is therefore refused for lack of "
        "admissible event endpoints; a national border is not a rejection rule. "
        f"The pinned acquisition release status is `{result['source_release_status']}`. "
        "Site envelopes do not establish occupation, arrival or propagation.\n\n"
        "## Reproduce\n\n"
        "From the repository root, run the existing retained-source candidate and "
        "browser verifier, then this audit with their output paths:\n\n"
        "```sh\n"
        "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m "
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_source_candidate "
        "--repository . --destination artifacts/sead-map-candidate/source-display\n"
        "node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic-country.mjs "
        "artifacts/sead-map-candidate/source-display artifacts/sead-map-candidate/browser "
        "'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'\n"
        "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m "
        "bijux_pollenomics_dev.source_completion.sead_map_candidate "
        "--repository . --candidate artifacts/sead-map-candidate/source-display "
        "--browser-receipt artifacts/sead-map-candidate/browser/receipt.json\n"
        "```\n\n"
        "Use absent artifact destinations for a replay. The browser result is a bounded "
        "retained-source detail check; it does not certify event-level ecology, "
        "source release, hosted deployment or all browser engines.\n"
    )
    print(
        json.dumps({"status": result["status"], "output": str(output / "report.json")})
    )


if __name__ == "__main__":
    main()

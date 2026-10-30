"""Read qualified saved covers without reopening source counts or model ages."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
import csv
import gzip
import io
import json
import math
from pathlib import Path
from typing import Any

from ..abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    TAXON_IDS,
    WINDOWS,
    bound_files,
    require,
)

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/common-covariance/protocol.json"
)


def load(repository: Path) -> dict[str, Any]:
    """Authenticate exactly three previously qualified scientific inputs."""
    protocol = json.loads((repository / PROTOCOL).read_bytes())
    require(
        protocol["window_ids"] == list(WINDOWS)
        and protocol["taxon_axis"] == list(TAXA),
        "Saved-cover study axes differ",
    )
    pins = protocol["repository_inputs"]
    require(
        set(pins)
        == {
            protocol[k]
            for k in ("source_result", "source_ledger", "source_verification")
        },
        "Saved-cover input population differs",
    )
    bodies = bound_files(repository, pins)
    result = json.loads(bodies[protocol["source_result"]])
    verified = json.loads(bodies[protocol["source_verification"]])
    require(
        result["source_commit"]
        == verified["producer_source_commit"]
        == protocol["producer_source_commit"]
        and verified["observer_source_commit"] == protocol["observer_source_commit"]
        and verified["status"] == "passed"
        and verified["result_sha256"] == pins[protocol["source_result"]]["sha256"]
        and result["count_profile"]
        == verified["count_profile"]
        == "pangaea_recorded_zeros_local_nc",
        "Qualified source-supported result identity differs",
    )
    for key, expected in {
        "native_samples_checked": 107,
        "saved_joint_age_rows_checked": 32000,
        "complete_rows": 31999,
        "undefined_rows": 1,
        "original_count_slots_checked": 535,
        "native_reported_count_pairs_checked": 527,
        "source_zero_slots_checked": 8,
        "covariance_entries_checked": 2400,
        "contrasts_checked": 30,
        "model_fits": 0,
    }.items():
        require(
            verified.get(key) == expected,
            "Saved-cover independent qualification is incomplete",
        )
    for key in (
        "maximum_ledger_cover_gap",
        "maximum_moment_gap",
        "common_native_maximum_moment_gap",
        "maximum_profile_difference_gap",
    ):
        value = verified[key]
        require(
            type(value) in (int, float)
            and math.isfinite(value)
            and 0 <= value <= 1e-12,
            "Saved-cover independent numerical qualification differs",
        )
    require(
        result["requested_draws"] == 32000
        and result["complete_draws"] == 31999
        and result["undefined_draws"] == 1,
        "Saved-cover conditioning population differs",
    )
    require(
        result["unconditional"]["status"] == "refused_undefined_mass"
        and result["conditional_on_complete"]["status"] == "conditional_on_complete",
        "Undefined saved mass was silently admitted",
    )
    ledger = result["draw_ledger"]
    require(
        ledger["path"] == Path(protocol["source_ledger"]).name
        and ledger["rows"] == 32000
        and all(
            ledger[k] == pins[protocol["source_ledger"]][k] for k in ("bytes", "sha256")
        ),
        "Qualified saved-cover ledger identity differs",
    )
    parameters = result["parameters"]
    require(
        len(parameters) == 5
        and [p["name"] for p in parameters] == list(TAXA)
        and [p["native_taxon_id"] for p in parameters] == list(TAXON_IDS),
        "Literal parameter axis differs",
    )
    require(
        all(
            type(p["ppe"]) in (int, float)
            and math.isfinite(p["ppe"])
            and p["ppe"] > 0
            and type(p["published_sd"]) in (int, float)
            and math.isfinite(p["published_sd"])
            and p["published_sd"] > 0
            for p in parameters[:4]
        ),
        "Four positive-SD parameter axes required",
    )
    require(
        parameters[4]["ppe"] == 1 and parameters[4]["published_sd"] == 0,
        "Poaceae relative reference differs",
    )
    return {
        "protocol": protocol,
        "source_result": result,
        "ledger_body": bodies[protocol["source_ledger"]],
        "parameters": parameters,
    }


def cover_rows(body: bytes, result: dict[str, Any]) -> Iterator[list[float] | None]:
    """Preserve all 32,000 iteration identities; only C_source contributes Q."""
    supports: dict[str, Counter[str]] = {str(b): Counter() for b in WINDOWS}
    count = complete = 0
    with (
        gzip.GzipFile(fileobj=io.BytesIO(body), mode="rb") as compressed,
        io.TextIOWrapper(compressed, newline="") as stream,
    ):
        rows = csv.DictReader(stream)
        require(
            rows.fieldnames is not None
            and len(rows.fieldnames) == len(set(rows.fieldnames)),
            "Saved-cover ledger header differs",
        )
        for index, row in enumerate(rows):
            require(index < 32000, "Extra saved-cover iteration")
            seed = (314159, 271828)[index // 16000]
            require(
                row["seed"] == str(seed)
                and row["native_row"] == str(3502 + index % 16000),
                "Saved-cover seed/native-row identity differs",
            )
            require(row["complete"] in {"0", "1"}, "Saved-cover complete flag differs")
            values: list[float] = []
            statuses = []
            for b in WINDOWS:
                status = row[f"bin_{b}_status"]
                require(
                    status
                    in {
                        "defined",
                        "empty_native_window",
                        "nonempty_zero_panel_mass",
                        "missing_explicit_five_taxon_member",
                    },
                    "Unknown saved-cover support status",
                )
                supports[str(b)][status] += 1
                statuses.append(status)
                cells = [row[f"cover_{b}_{taxon}"] for taxon in TAXON_IDS]
                if status != "defined":
                    require(
                        all(cell == "" for cell in cells),
                        "Undefined bin has saved covers",
                    )
                    continue
                cover = [float(cell) for cell in cells]
                require(
                    all(math.isfinite(v) and 0 <= v <= 1 for v in cover)
                    and abs(math.fsum(cover) - 1) <= 1e-12,
                    "Saved cover is not a finite closed composition",
                )
                values.extend(cover)
            defined = all(status == "defined" for status in statuses)
            require(
                int(row["complete"]) == int(defined),
                "Saved-cover conditioning event differs",
            )
            count += 1
            complete += int(defined)
            yield values if defined else None
    require(
        count == result["requested_draws"] == 32000
        and complete == result["complete_draws"] == 31999,
        "Saved-cover iteration/support totals differ",
    )
    require(
        all(
            dict(supports[str(b)])
            == result["support_by_window"][str(b)]["status_counts"]
            for b in WINDOWS
        ),
        "Saved-cover per-window support census differs",
    )

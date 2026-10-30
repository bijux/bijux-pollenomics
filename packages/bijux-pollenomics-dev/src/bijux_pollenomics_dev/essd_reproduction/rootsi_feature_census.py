"""Census unreviewed cached feature values in retained Rootsi workbooks."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Sequence
import csv
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from bijux_pollenomics.collection.sources.rootsi import authority
from bijux_pollenomics.collection.sources.rootsi.cells import decoding, inputs, models
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

CROSSWALK = "data/landclim/review/rootsi-candidate-inputs/rootsi-crosswalk.csv"
CROSSWALK_SHA256 = "ee76ac6af9d79ce4d81224a566e8edd7dc71eb940402b352fda809bba7e93588"
CROSSWALK_BYTES = 29508
WORKBOOK_COUNT = 79
WORKBOOK_BYTES = 4466176
PARTITIONS = (
    "complete_finite_nonnegative_positive",
    "complete_allzero",
    "numeric_with_negative",
    "incomplete_or_unsupported",
)
FLAGS = (
    "noninteger",
    "negative",
    "missing",
    "null",
    "text",
    "blank",
    "date",
    "boolean",
    "error",
    "nonfinite",
    "unsupported",
)


class CensusRefusal(ValueError):
    """A source header cannot support an unambiguous positional census."""


def roster(repository: Path, source: Path) -> list[dict[str, Any]]:
    """Bind the existing canonical candidate crosswalk to original workbook bytes."""
    raw = inputs.read_bytes(repository / CROSSWALK, CROSSWALK_SHA256, CROSSWALK_BYTES)
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    selected = [row for row in rows if row["typed_workbook_member"]]
    manifest_path = inputs.local_path(source / "manifest.json")
    if manifest_path.stat().st_size > 65536:
        raise ValueError("External workbook roster is unexpectedly large")
    manifest = models.object_value(models.decoded(manifest_path.read_bytes()), "roster")
    if manifest.get("archive_sha256") != authority.ARCHIVE_SHA256:
        raise ValueError("Retained original archive identity differs")
    members = manifest["members"]
    if not isinstance(members, list):
        raise ValueError("Workbook roster must be a list")
    expected = {
        row["typed_workbook_member"]: (
            row["typed_workbook_sha256"],
            int(row["typed_workbook_bytes"]),
        )
        for row in selected
    }
    observed = {row["archive_member"]: (row["sha256"], row["bytes"]) for row in members}
    if (
        len(selected) != len(expected)
        or len(members) != len(observed)
        or len(expected) != WORKBOOK_COUNT
        or observed != expected
        or sum(n for _, n in expected.values()) != WORKBOOK_BYTES
        or manifest.get("workbook_count") != WORKBOOK_COUNT
        or manifest.get("total_workbook_bytes") != WORKBOOK_BYTES
    ):
        raise ValueError(
            "Original workbook roster differs from canonical source candidates"
        )
    result = []
    for row in selected:
        member = inputs.member_name(row["typed_workbook_member"])
        digest, size = expected[member]
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None or not 0 < size <= 1024**2:
            raise ValueError("Invalid bounded workbook asset")
        result.append(
            {
                "archive_member": member,
                "sha256": digest,
                "bytes": size,
                "metadata_source_locator": row["rootsi_source_locator"],
                "metadata_sample_count_raw": row["rootsi_sample_count_raw"],
                "metadata_sample_count_claim": int(row["rootsi_sample_count_claim"]),
                "publication_candidate_status": row["publication_candidate_status"],
            }
        )
    return result


def nonempty(cell: decoding.Cell) -> bool:
    """Use the retained structural rule; a numeric zero is nonempty."""
    return cell.ctype not in (0, 6) and not (cell.ctype == 1 and cell.value == "")


def profile(book: decoding.Book) -> tuple[decoding.Sheet, int, list[int]]:
    """Reproduce the existing unique-text-maximum header and row selection."""
    active = []
    for sheet in book.sheets():
        if (
            not 0 <= sheet.nrows <= 65536
            or not 0 <= sheet.ncols <= 256
            or sheet.nrows * sheet.ncols > 1_000_000
        ):
            raise CensusRefusal("unsupported_sheet_extent")
        populated = []
        text_counts = []
        for row in range(sheet.nrows):
            cells = [sheet.cell(row, col) for col in range(sheet.ncols)]
            if any(nonempty(cell) for cell in cells):
                populated.append(row)
            text_counts.append(
                sum(cell.ctype == 1 and cell.value != "" for cell in cells)
            )
        if populated:
            active.append((sheet, populated, text_counts))
    if len(active) != 1:
        raise CensusRefusal("nonempty_sheet_count")
    sheet, populated, text_counts = active[0]
    maximum = max(text_counts)
    if maximum <= 0 or text_counts.count(maximum) != 1:
        raise CensusRefusal("ambiguous_header")
    header = text_counts.index(maximum)
    rows = [row for row in populated if row > header]
    if not rows or rows != list(range(rows[0], rows[-1] + 1)):
        raise CensusRefusal("noncontiguous_or_missing_data_rows")
    return sheet, header, rows


def role(label: str) -> str:
    """Declare lexical metadata exclusions without authenticating taxonomy."""
    label = " ".join(label.split()).casefold()
    if label.startswith(("sample age", "calibrated age", "age cal")):
        return "age_label"
    if label in {"sample", "provnummer", "provnivå"} or label.startswith(
        ("sample depth", "depth,")
    ):
        return "sample_or_depth_label"
    return "unreviewed_candidate_feature"


def flags(cell: decoding.Cell) -> tuple[float | None, set[str]]:
    """Preserve typed missingness and refuse numeric-looking text as a number."""
    found: set[str] = set()
    if cell.value is None:
        found.update(("null", "missing"))
    if cell.ctype in (0, 6):
        found.add("missing")
        if cell.ctype == 6:
            found.add("blank")
    elif cell.ctype == 1:
        found.add("text")
        if cell.value == "":
            found.add("missing")
    elif cell.ctype in (3, 4, 5):
        found.add({3: "date", 4: "boolean", 5: "error"}[cell.ctype])
    elif cell.ctype != 2:
        found.add("unsupported")
    value = cell.value
    if cell.ctype == 2 and (type(value) is int or type(value) is float):
        number = float(value)
        if math.isfinite(number):
            if number < 0:
                found.add("negative")
            if not number.is_integer():
                found.add("noninteger")
            return number, found
        found.add("nonfinite")
    if cell.ctype == 2:
        found.add("unsupported")
    return None, found


def summarize(book: decoding.Book) -> dict[str, Any]:
    """Partition source rows; orthogonal flags never become additive populations."""
    sheet, header, rows = profile(book)
    result: dict[str, Any] = {
        "sheet": sheet.name,
        "header_row_number": header + 1,
        "mechanical_row_count": len(rows),
        "first_data_row_number": rows[0] + 1,
        "last_data_row_number": rows[-1] + 1,
        "status": "computed",
        "value_origin": "decoded cached values; literal/formula origin unavailable",
        "excel_date_mode_raw": book.datemode,
    }
    metadata = []
    features = []
    ages = []
    unresolved = []
    for column in range(sheet.ncols):
        cell = sheet.cell(header, column)
        if cell.ctype != 1 or not isinstance(cell.value, str) or not cell.value.strip():
            unresolved.append(column + 1)
            continue
        kind = role(cell.value)
        if kind == "unreviewed_candidate_feature":
            features.append(column)
        else:
            metadata.append(
                {"column_number": column + 1, "source_label": cell.value, "role": kind}
            )
            if kind == "age_label":
                ages.append(column)
    result.update(
        candidate_feature_columns=len(features),
        excluded_metadata_columns=metadata,
        unresolved_header_columns=unresolved,
    )
    if unresolved or not features or not metadata:
        result.update(
            status="refused",
            reason="ambiguous_feature_header_roles",
            row_partition=None,
            anomaly_row_numbers=None,
        )
        return result
    partition: Counter[str] = Counter()
    anomalies: dict[str, list[int]] = {name: [] for name in (*PARTITIONS[1:], *FLAGS)}
    zero_ages: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        values = []
        row_flags: set[str] = set()
        for column in features:
            number, observed = flags(sheet.cell(row, column))
            values.append(number)
            row_flags.update(observed)
        complete = all(value is not None for value in values)
        if not complete:
            category = "incomplete_or_unsupported"
        elif "negative" in row_flags:
            category = "numeric_with_negative"
        elif all(value == 0 for value in values):
            category = "complete_allzero"
        else:
            category = "complete_finite_nonnegative_positive"
        partition[category] += 1
        number = row + 1
        if category in anomalies:
            anomalies[category].append(number)
        for flag in row_flags:
            anomalies[flag].append(number)
        if category == "complete_allzero":
            state = "not_single_explicit_age_column"
            if len(ages) == 1:
                value, observed = flags(sheet.cell(row, ages[0]))
                state = (
                    ("finite_zero" if value == 0 else "finite_nonzero")
                    if value is not None
                    else "missing_or_unsupported"
                )
            zero_ages[state].append(number)
    result.update(
        row_partition={name: partition[name] for name in PARTITIONS},
        anomaly_row_numbers=anomalies,
        orthogonal_flag_counts={name: len(anomalies[name]) for name in FLAGS},
        allzero_feature_rows_age_states=dict(zero_ages),
    )
    if sum(partition.values()) != len(rows):
        raise ValueError("Source row partition does not close")
    return result


def census(
    source: Path, records: Sequence[dict[str, Any]], decoder: decoding.Parser
) -> list[dict[str, Any]]:
    """Read and release one authenticated workbook at a time, preserving failures."""
    result = []
    fatal = False
    for record in records:
        row = {**record, "status": "not_run"}
        if not fatal:
            book = None
            try:
                path = source / record["archive_member"]
                raw = inputs.read_bytes(path, record["sha256"], record["bytes"])
                book = decoder.open_workbook(file_contents=raw, formatting_info=True)
                row.update(summarize(book))
                inputs.read_bytes(path, record["sha256"], record["bytes"])
                if "mechanical_row_count" in row:
                    row["metadata_claim_matches_mechanical_rows"] = (
                        record["metadata_sample_count_claim"]
                        == row["mechanical_row_count"]
                    )
                    row["metadata_claim_matches_positive_rows"] = (
                        record["metadata_sample_count_claim"]
                        == row["row_partition"]["complete_finite_nonnegative_positive"]
                        if row["status"] == "computed"
                        else None
                    )
            except CensusRefusal as error:
                row.update(status="refused", reason=str(error))
            except Exception as error:
                row.update(
                    status="fatal",
                    reason={"class": type(error).__name__, "detail": str(error)},
                )
                fatal = True
            finally:
                if book is not None:
                    book.release_resources()
        result.append(row)
    return result


def revision(repository: Path) -> str:
    """Require a stable committed repository source identity for the census."""
    prefix = (
        "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/rootsi"
    )
    modules = [
        (authority, f"{prefix}/authority.py"),
        (decoding, f"{prefix}/cells/decoding.py"),
        (inputs, f"{prefix}/cells/inputs.py"),
        (models, f"{prefix}/cells/models.py"),
        (
            sys.modules[__name__],
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/rootsi_feature_census.py",
        ),
    ]
    paths = [Path(module.__file__ or "") for module, _ in modules]
    if any(
        Path(module.__file__ or "").resolve(strict=True) != repository / relative
        or Path(module.__file__ or "") != repository / relative
        for module, relative in modules
    ):
        raise ValueError("Census modules must load from canonical repository packages")
    command = ["git", "-C", str(repository)]
    commit = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True, timeout=30
    ).strip()
    relative = [str(path.relative_to(repository)) for path in paths]
    subprocess.run(
        [*command, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        [*command, "diff", "--exit-code", commit, "--", *relative],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return commit


def main() -> None:
    """Parse arguments for the declared source-bound evidence writer."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = inputs.local_path(args.repository)
    output = require_absent_artifact_output(repository, args.output)
    commit = revision(repository)
    records = roster(repository, args.source_store)
    rows = census(args.source_store, records, decoding.parser())
    if revision(repository) != commit:
        raise ValueError("Consumed census source changed during execution")
    computed = [row for row in rows if row["status"] == "computed"]
    result = {
        "schema_version": "rootsi-cached-feature-census.v1",
        "source_commit": commit,
        "command": sys.orig_argv,
        "source_archive_sha256": authority.ARCHIVE_SHA256,
        "canonical_crosswalk": {"path": CROSSWALK, "sha256": CROSSWALK_SHA256},
        "workbooks": rows,
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "mechanical_rows": sum(row.get("mechanical_row_count", 0) for row in rows),
        "classified_rows": sum(row["mechanical_row_count"] for row in computed),
        "unclassified_mechanical_rows": sum(
            row.get("mechanical_row_count", 0)
            for row in rows
            if row["status"] != "computed"
        ),
        "retained_workbook_count": WORKBOOK_COUNT,
        "retained_workbook_bytes": WORKBOOK_BYTES,
        "exclusive_row_partition": {
            name: sum(row["row_partition"][name] for row in computed)
            for name in PARTITIONS
        },
        "orthogonal_row_flag_counts": {
            name: sum(row["orthogonal_flag_counts"][name] for row in computed)
            for name in FLAGS
        },
        "limits": [
            "Candidate feature columns are positional source values after explicit lexical sample/depth/age exclusions. Remaining labels are unreviewed; no taxonomy, pollen measurement or units are authenticated.",
            "Whole-row categories are exclusive; noninteger, negative and typed-missing flags overlap and must not be added as separate populations. Incomplete rows never become all-zero rows.",
            "The maintained decoder reads cached values. Literal versus formula origin is unavailable; formulas are neither executed nor reconstructed. Numeric-looking text, blanks, dates, booleans, errors and unsupported values are not grain counts.",
            "Age cells remain source-native cached values. Finite nonzero AGE in an all-zero-feature row does not establish chronology, sample authenticity or ecological absence. No calendar or epoch conversion is performed.",
            "Metadata candidate matches and mechanical sample-count correspondence do not authenticate historical LandClim membership, original publication inputs, analytical reuse rights or LRA readiness. No model, fit or numerical reconstruction is executed.",
        ],
    }
    raw = (
        json.dumps(result, indent=2, allow_nan=False, ensure_ascii=False) + "\n"
    ).encode()
    if len(raw) > 1024**2:
        raise ValueError("Census output exceeds one MiB")
    with output.open("xb") as stream:
        stream.write(raw)
    raise SystemExit(
        1 if any(row["status"] in {"fatal", "not_run"} for row in rows) else 0
    )


if __name__ == "__main__":
    main()

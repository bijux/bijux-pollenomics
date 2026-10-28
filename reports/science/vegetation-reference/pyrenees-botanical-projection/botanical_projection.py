"""Conditional botanical cover closure with explicit source association choices."""

from collections import Counter, defaultdict
import csv
import io
import math
from pathlib import PurePosixPath
import zipfile

AXES = (
    "Abies",
    "Betula",
    "Corylus",
    "Fagus",
    "Fraxinus",
    "Picea",
    "Pinus",
    "Quercus",
    "Salix",
    "Tilia",
    "Calluna vulgaris",
    "Ericaceae",
    "Juniperus",
    "Cyperaceae",
    "Plantago lanceolata",
    "Poaceae",
    "Potentilla",
)
VALUE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}value"
TYPE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}value-type"
MODES = ("source-code-authority", "exact-native-name-alternative")
PARENTS = (
    "declared-disjoint-residual-observations",
    "omit-inventory-parent-observations",
)
BLANKS = ("strict-unknown-blanks", "declared-exhaustive-survey-zero")


def integer(value):
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ValueError("Literal nonnegative native identifier required")
    return int(value)


def reference_lookup(path, version):
    member = {"3.00": "bdtfx_v3_00_ref.txt", "3.01": "bdtfx_v3_01/bdtfx_v3_01_ref.txt"}[
        version
    ]
    index = {}
    byname = defaultdict(list)
    with zipfile.ZipFile(path) as archive:
        total = 0
        seen = set()
        for info in archive.infolist():
            p = PurePosixPath(info.filename)
            if (
                info.filename in seen
                or p.is_absolute()
                or ".." in p.parts
                or "\\" in info.filename
                or info.flag_bits & 1
                or ((info.external_attr >> 16) & 0o170000) == 0o120000
            ):
                raise ValueError("Unsafe native archive member")
            seen.add(info.filename)
            total += info.file_size
            if info.file_size > 32 * 1024**2 or total > 48 * 1024**2:
                raise ValueError("Native archive size bound exceeded")
        with archive.open(member) as raw:
            reader = csv.DictReader(
                io.TextIOWrapper(raw, encoding="utf-8", newline=""), delimiter="\t"
            )
            for line, row in enumerate(reader, 2):
                key = integer(row["num_nom"])
                if key <= 0 or key in index:
                    raise ValueError("Nonunique native name identifier")
                projected = {
                    k: row[k]
                    for k in (
                        "num_nom",
                        "num_nom_retenu",
                        "num_tax_sup",
                        "nom_sci",
                        "rang",
                    )
                }
                projected["native_line"] = line
                index[key] = projected
                byname[row["nom_sci"]].append(key)
    return index, byname


def chain(index, start):
    path = []
    seen = set()
    aliases = []
    key = start
    for _ in range(64):
        if key in seen or key not in index:
            raise ValueError("Missing/cyclic retained or parent identity")
        seen.add(key)
        row = index[key]
        if not row["num_nom_retenu"]:
            raise ValueError("Unestablished retained name")
        retained = integer(row["num_nom_retenu"])
        if retained != key:
            aliases.append(key)
            key = retained
            continue
        path.append(row)
        if row["num_tax_sup"] == "0":
            return path, aliases
        if not row["num_tax_sup"]:
            raise ValueError("Accepted native name missing parent")
        key = integer(row["num_tax_sup"])
    raise ValueError("Native lineage bound exceeded")


def unique_literal(index, byname, labels, rank):
    targets = {}
    candidates = []
    for label in dict.fromkeys(labels):
        for key in byname.get(label, []):
            rows, aliases = chain(index, key)
            first = rows[0]
            if (
                rank in ("family", "genus")
                and first["rang"] != {"family": "180", "genus": "220"}[rank]
            ):
                raise ValueError("Native literal label rank differs")
            if rank == "species" and (
                not first["rang"].isdigit() or int(first["rang"]) < 290
            ):
                raise ValueError("Native label is not species or infraspecific")
            candidates.append(
                {
                    "literal_query": label,
                    "native_candidate": index[key],
                    "native_retained_id": first["num_nom"],
                    "alias_ids": aliases,
                }
            )
            targets[int(first["num_nom"])] = rows
    if len(targets) != 1:
        raise ValueError("Absent or ambiguous exact native retained-name association")
    return next(iter(targets.values())), candidates


def associate(saved, index, byname, mode, anchors):
    if mode not in MODES:
        raise ValueError("Undeclared source association mode")
    if any(len(anchors.get(axis, [])) != 1 for axis in AXES):
        raise ValueError("Missing or ambiguous declared botanical anchor")
    records = []
    for original in saved["records"]:
        s = original["source"]
        out = {
            "source": s,
            "retained_original_status": original["status"],
            "mode": mode,
            "original_code_remains": s["BDTFX_code"],
            "axis": None,
            "association_status": "unresolved",
            "assumption": None,
        }
        try:
            if s["BDTFX_code"] != "0" and (
                mode == MODES[0]
                or original["status"] != "code_lineage_label_mismatch_requires_review"
                or any(
                    r["nom_sci"]
                    in {s["source_name"], s["phytobase_name"], s["BDTFX_name"]}
                    for r in original["lineage"]["rows"][1:]
                )
            ):
                rows = [
                    {
                        k: r[k]
                        for k in (
                            "num_nom",
                            "num_nom_retenu",
                            "num_tax_sup",
                            "nom_sci",
                            "rang",
                            "native_line",
                        )
                    }
                    for r in original["lineage"]["rows"]
                ]
                out["assumption"] = (
                    "supplied-native-code-for-botanical-grouping; field infraspecific identity not asserted"
                )
                out["reused_completed_native_chain"] = True
            elif s["BDTFX_code"] != "0":
                labels = [
                    v
                    for v in (s["source_name"], s["BDTFX_name"], s["phytobase_name"])
                    if v
                ]
                rows, candidates = unique_literal(index, byname, labels, s["rank"])
                out["native_name_witnesses"] = candidates
                out["assumption"] = (
                    "exact-original-native-name-alternative; disagreement with supplied code retained"
                )
                out["supplied_code_accepted_id"] = original["lineage"]["accepted_id"]
                out["associated_id_differs_from_supplied_code"] = (
                    rows[0]["num_nom"] != original["lineage"]["accepted_id"]
                )
            else:
                if s["rank"] == "family":
                    labels = [s["source_name"]]
                    rank = "family"
                    assumption = "unique-literal-native-family-name association; originalcode0 retained"
                elif s["rank"] == "genus" and s["source_name"].endswith(" sp."):
                    labels = [s["source_name"][:-4]]
                    rank = "genus"
                    assumption = "source undetermined-species sp. label associated only with unique literal native genus; no species invented"
                else:
                    raise ValueError(
                        "Zero-code label lacks declared family/genus convention"
                    )
                rows, candidates = unique_literal(index, byname, labels, rank)
                out.update(native_name_witnesses=candidates, assumption=assumption)
            ids = {integer(r["num_nom"]) for r in rows}
            members = [
                name
                for name, keys in anchors.items()
                if name in AXES and len(keys) == 1 and keys[0] in ids
            ]
            if "Calluna vulgaris" in members and "Ericaceae" in members:
                members.remove("Ericaceae")
            if len(members) > 1:
                raise ValueError("Ambiguous multiple botanical panel axes")
            out.update(
                native_chain=rows,
                analyst_associated_native_id=rows[0]["num_nom"],
                association_status="associated",
                axis=members[0] if members else None,
                panel_status="mapped" if members else "outside-declared-panel",
            )
        except ValueError as error:
            out.update(
                refusal=str(error), panel_status="unresolved-taxonomic-association"
            )
        records.append(out)
    return records


def parent_mask(records):
    mapped = [
        r
        for r in records
        if r["axis"] is not None and r["association_status"] == "associated"
    ]
    omitted = {}
    overlaps = []
    for parent in mapped:
        pid = parent["analyst_associated_native_id"]
        for child in mapped:
            if parent["source"]["row"] == child["source"]["row"]:
                continue
            if pid in [r["num_nom"] for r in child["native_chain"][1:]]:
                overlaps.append(
                    {
                        "parent_source_row": parent["source"]["row"],
                        "child_source_row": child["source"]["row"],
                        "parent_native_id": pid,
                    }
                )
                omitted.setdefault(parent["source"]["row"], []).append(
                    child["source"]["row"]
                )
    return omitted, overlaps


def observed_matrix(census, taxa):
    table = next(s for s in census["sheets"] if s["name"] == "data")
    cells = {}
    for block in table["rows"]:
        start = block["row"]
        stop = min(213, start + block["row_repeat"] - 1)
        if stop < 2 or start > 213:
            continue
        for cell in block["cells"]:
            left = cell["column"]
            right = min(130, left + cell["column_repeat"] - 1)
            if left > 130:
                continue
            for row in range(max(2, start), stop + 1):
                for col in range(left, right + 1):
                    if (row, col) in cells:
                        raise ValueError("Overlapping stored source cells")
                    cells[row, col] = cell
    plots = {col: cells[2, col]["text"] for col in range(6, 131)}
    if len(set(plots.values())) != 125:
        raise ValueError("Original125 plot identities differ")
    matrix = {}
    positive = []
    for source in taxa:
        row = source["row"]
        if (
            cells[row, 1]["text"] != source["phytobase_name"]
            or cells[row, 3]["text"] != source["BDTFX_code"]
            or cells[row, 4]["text"] != source["rank"]
        ):
            raise ValueError("Original source label/code/rank differs")
        for col, plot in plots.items():
            cell = cells.get((row, col))
            raw = cell.get("attributes", {}).get(VALUE) if cell else None
            if raw is None:
                if cell is not None and cell["text"]:
                    raise ValueError("Non-numeric native cover cell")
                matrix[row, plot] = None
            else:
                number = float(raw)
                if (
                    not math.isfinite(number)
                    or number <= 0
                    or cell["attributes"].get(TYPE) != "float"
                    or cell["covered"]
                ):
                    raise ValueError("Native positive cover numeric contract differs")
                matrix[row, plot] = raw
                positive.append(
                    {"source_row": row, "plot": plot, "literal_cover_percent": raw}
                )
    if len(positive) != 1757:
        raise ValueError("Original1757 positive cover observations differ")
    return list(plots.values()), matrix, positive


def plot_metadata(source):
    events = {r["GBIF_eventID"]: r["cells"] for r in source["event_sheet_source_rows"]}
    if set(events) != set(source["classes"]):
        raise ValueError("Exact event/class identities differ")
    if any(
        events[plot][0] != plot
        or events[plot][1] not in ("2015", "2020")
        or events[plot][4] not in ("25", "100", "400")
        or events[plot][5] != "square_metre"
        for plot in events
    ):
        raise ValueError("Native year/area/unit metadata differs")
    return {
        plot: {
            **info,
            "event_year": events[plot][1],
            "area_m2": events[plot][4],
            "source_event_columns_preserved": True,
        }
        for plot, info in source["classes"].items()
    }


def close(values):
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("Invalid conditional cover values")
    total = math.fsum(values)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("No positive finite conditional panel total")
    return [v / total for v in values]


def project(records, plots, matrix, parent_rule, blank_rule):
    if parent_rule not in PARENTS or blank_rule not in BLANKS:
        raise ValueError("Undeclared parent/blank assumption")
    if len(set(plots)) != len(plots):
        raise ValueError("Duplicate plot identities")
    omitted, overlaps = parent_mask(records)
    selected = {
        r["source"]["row"]: r
        for r in records
        if r["axis"] is not None
        and not (parent_rule == PARENTS[1] and r["source"]["row"] in omitted)
    }
    unresolved = [
        r["source"]["row"] for r in records if r["association_status"] == "unresolved"
    ]
    axis_rows = {
        axis: [row for row, r in selected.items() if r["axis"] == axis] for axis in AXES
    }
    outcomes = []
    positive_ledger = []
    byrow = {r["source"]["row"]: r for r in records}
    for plot in plots:
        blanks = {
            axis: [row for row in rows if matrix[row, plot] is None]
            for axis, rows in axis_rows.items()
        }
        missing_axes = [axis for axis, rows in axis_rows.items() if not rows]
        unknown_positive = [row for row in unresolved if matrix[row, plot] is not None]
        raw = [
            math.fsum(
                float(matrix[row, plot])
                for row in rows
                if matrix[row, plot] is not None
            )
            for rows in axis_rows.values()
        ]
        reasons = []
        if unknown_positive:
            reasons.append("positive-source-cover-has-unresolved-taxonomic-association")
        if blank_rule == BLANKS[0] and (any(blanks.values()) or missing_axes):
            reasons.append("unknown-source-blanks-or-unrepresented-panel-axis")
        if math.fsum(raw) <= 0:
            reasons.append("no-positive-known-panel-cover")
        outcomes.append(
            {
                "plot": plot,
                "raw_cover_percent_by_axis": raw,
                "known_panel_cover_percent": math.fsum(raw),
                "closed_panel_fraction": close(raw) if not reasons else None,
                "status": "conditional-projection" if not reasons else "refused",
                "refusals": reasons,
                "unknown_positive_source_rows": unknown_positive,
                "source_blank_counts_by_axis": {k: len(v) for k, v in blanks.items()},
                "unrepresented_axes": missing_axes,
                "blank_zero_imputation_assumed": blank_rule == BLANKS[1],
            }
        )
        for row, r in byrow.items():
            quantity = matrix[row, plot]
            if quantity is None:
                continue
            status = (
                "unresolved-association"
                if r["association_status"] == "unresolved"
                else (
                    "outside-panel"
                    if r["axis"] is None
                    else (
                        "omitted-inventory-parent"
                        if row not in selected
                        else "included-panel-observation"
                    )
                )
            )
            positive_ledger.append(
                {
                    "plot": plot,
                    "source_row": row,
                    "literal_cover_percent": quantity,
                    "status": status,
                    "axis": r["axis"],
                }
            )
    if len(outcomes) != len(plots) or len(positive_ledger) != sum(
        matrix[r["source"]["row"], plot] is not None for r in records for plot in plots
    ):
        raise ValueError("Complete source observation accounting differs")
    return {
        "axis_order": AXES,
        "outcomes": outcomes,
        "positive_observation_loss_ledger": positive_ledger,
        "inventory_parent_mask": omitted if parent_rule == PARENTS[1] else {},
        "source_parent_child_overlaps": overlaps,
        "status_counts": dict(Counter(r["status"] for r in outcomes)),
        "observation_status_counts": dict(
            Counter(r["status"] for r in positive_ledger)
        ),
    }


def class_summaries(projection, metadata):
    groups = defaultdict(list)
    for row in projection["outcomes"]:
        m = metadata[row["plot"]]
        for source in ("map", "field"):
            groups[source, m[source + "_code"], "pooled-year-area"].append(row)
            groups[
                source, m[source + "_code"], m["event_year"] + "/" + m["area_m2"] + "m2"
            ].append(row)
    out = []
    for (source, code, stratum), rows in sorted(groups.items()):
        valid = [r for r in rows if r["closed_panel_fraction"] is not None]
        n = len(valid)
        mean_closed = (
            [
                math.fsum(r["closed_panel_fraction"][i] for r in valid) / n
                for i in range(len(AXES))
            ]
            if n
            else None
        )
        mean_raw = (
            [
                math.fsum(r["raw_cover_percent_by_axis"][i] for r in valid) / n
                for i in range(len(AXES))
            ]
            if n
            else None
        )
        out.append(
            {
                "class_source": source,
                "class_code": code,
                "stratum": stratum,
                "original_plot_denominator": len(rows),
                "conditional_projection_denominator": n,
                "refused_plot_denominator": len(rows) - n,
                "mean_of_closed_vectors": mean_closed,
                "closure_of_mean_raw_cover": close(mean_raw) if n else None,
                "equal_plot_weights": True,
                "not_independent_plots": True,
            }
        )
    return out

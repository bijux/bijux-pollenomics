"""Independent native-name and Decimal saved-vector account; no model or fitting."""

from collections import Counter, defaultdict
from decimal import Decimal, localcontext
import csv
import io
import json
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


def native_index(path, version):
    member = (
        "bdtfx_v3_00_ref.txt"
        if version == "3.00"
        else "bdtfx_v3_01/bdtfx_v3_01_ref.txt"
    )
    rows = {}
    names = defaultdict(list)
    with zipfile.ZipFile(path) as archive:
        with archive.open(member) as raw:
            for line, row in enumerate(
                csv.DictReader(
                    io.TextIOWrapper(raw, encoding="utf-8", newline=""), delimiter="\t"
                ),
                2,
            ):
                key = int(row["num_nom"])
                assert key not in rows
                rows[key] = (
                    row["num_nom_retenu"],
                    row["num_tax_sup"],
                    row["nom_sci"],
                    row["rang"],
                    line,
                )
                names[row["nom_sci"]].append(key)
    return rows, names


def native_route(rows, key):
    ancestors = []
    visited = set()
    for _ in range(64):
        assert key not in visited and key in rows, "invalid independent native route"
        visited.add(key)
        retained, parent, name, rank, line = rows[key]
        assert retained
        if int(retained) != key:
            key = int(retained)
            continue
        ancestors.append((key, name, rank, line, parent))
        if parent == "0":
            return ancestors
        assert parent
        key = int(parent)
    raise AssertionError("native route bound")


def named_route(rows, names, labels, rank):
    choices = {}
    for label in dict.fromkeys(labels):
        for key in names.get(label, []):
            ancestors = native_route(rows, key)
            r = ancestors[0][2]
            assert (
                (rank == "family" and r == "180")
                or (rank == "genus" and r == "220")
                or (rank == "species" and r.isdigit() and int(r) >= 290)
            ), "wrong independent rank"
            choices[ancestors[0][0]] = ancestors
    if len(choices) != 1:
        return None
    return next(iter(choices.values()))


def exact_inventory(records, key, expected, scope):
    assert len(records) == len(expected), scope + " population differs"
    indexed = {key(row): row for row in records}
    assert len(indexed) == len(records) and set(indexed) == set(expected), (
        scope + " duplicate/missing identity"
    )
    return indexed


def axis_vector(values, scope):
    assert isinstance(values, list) and len(values) == 17, scope + " requires17 axes"
    return values


def scenario_inventory(associations, contexts, summaries):
    versions = ("3.00", "3.01")
    modes = ("source-code-authority", "exact-native-name-alternative")
    parents = (
        "declared-disjoint-residual-observations",
        "omit-inventory-parent-observations",
    )
    blanks = ("strict-unknown-blanks", "declared-exhaustive-survey-zero")
    pairs = {(v, m) for v in versions for m in modes}
    exact_inventory(
        associations,
        lambda row: (row["version"], row["association_mode"]),
        pairs,
        "association scenarios",
    )
    expected = {
        "/".join((v, m, p, b)): (v, m, p, b)
        for v in versions
        for m in modes
        for p in parents
        for b in blanks
    }
    indexed = exact_inventory(
        contexts, lambda row: row["case_id"], expected, "plot scenarios"
    )
    for case_id, row in indexed.items():
        assert (
            row["version"],
            row["association_mode"],
            row["parent_assumption"],
            row["blank_assumption"],
        ) == expected[case_id], "scenario tuple/ID relation differs"
    exact_inventory(
        summaries, lambda row: row["case_id"], expected, "summary scenarios"
    )
    return indexed


def verify(job):
    def read(p):
        return json.loads(p.read_text())

    source = read(job / "inputs/original-taxa-classes.json")
    saved = {
        v: read(job / "inputs" / n)
        for v, n in [
            ("3.00", "lineage-three-zero.json"),
            ("3.01", "lineage-three-one.json"),
        ]
    }
    associations = read(job / "native/botanical-association-ledger.json")
    contexts = read(job / "native/conditional-panel-contexts.json")
    summaries = read(job / "native/source-class-comparisons.json")
    metadata = read(job / "native/source-plot-metadata.json")
    context_byid = scenario_inventory(associations, contexts, summaries)
    observed = {}
    columns = {}
    table = next(
        s
        for s in read(job / "inputs/stored-source-cells.json")["sheets"]
        if s["name"] == "data"
    )
    for block in table["rows"]:
        for cell in block["cells"]:
            value = cell["attributes"].get(
                "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}value"
            )
            for row in range(
                max(2, block["row"]),
                min(213, block["row"] + block["row_repeat"] - 1) + 1,
            ):
                for col in range(
                    max(6, cell["column"]),
                    min(130, cell["column"] + cell["column_repeat"] - 1) + 1,
                ):
                    if row == 2:
                        columns[col] = cell["text"]
                    elif row >= 6 and value is not None:
                        assert (row, col) not in observed
                        q = Decimal(value)
                        assert q.is_finite() and q > 0
                        observed[row, col] = q
    assert (
        len(columns) == 125
        and len(set(columns.values())) == 125
        and len(observed) == 1757
    )
    numbers = {(row, columns[col]): value for (row, col), value in observed.items()}
    plots = set(columns.values())
    source_byrow = {r["row"]: r for r in source["taxa"]}
    assert len(source_byrow) == 208 and len(plots) == 125
    metadata_expected = {}
    for event in source["event_sheet_source_rows"]:
        plot = event["GBIF_eventID"]
        cells = event["cells"]
        metadata_expected[plot] = {
            **source["classes"][plot],
            "event_year": cells[1],
            "area_m2": cells[4],
            "source_event_columns_preserved": True,
        }
    assert metadata == metadata_expected
    mapping = {}
    new_routes = 0
    reused_routes = 0
    nomenclature_conflicts = []
    for version in ("3.00", "3.01"):
        rows, names = native_index(
            job
            / "inputs"
            / ("bdtfx-three-zero.zip" if version == "3.00" else "bdtfx-three-one.zip"),
            version,
        )
        original = {r["source"]["row"]: r for r in saved[version]["records"]}
        anchors = saved[version]["native_anchors"]
        for item in [a for a in associations if a["version"] == version]:
            mode = item["association_mode"]
            exact_inventory(
                item["records"],
                lambda row: row["source"]["row"],
                source_byrow,
                "association source records",
            )
            derived = {}
            for record in item["records"]:
                s = source_byrow[record["source"]["row"]]
                assert (
                    record["source"] == s
                    and record["original_code_remains"] == s["BDTFX_code"]
                )
                old = original[s["row"]]
                labels = [
                    x
                    for x in (s["source_name"], s["BDTFX_name"], s["phytobase_name"])
                    if x
                ]
                reuse = s["BDTFX_code"] != "0" and (
                    mode == "source-code-authority"
                    or old["status"] != "code_lineage_label_mismatch_requires_review"
                    or any(r["nom_sci"] in labels for r in old["lineage"]["rows"][1:])
                )
                if reuse:
                    route = [
                        (
                            int(r["num_nom"]),
                            r["nom_sci"],
                            r["rang"],
                            r["native_line"],
                            r["num_tax_sup"],
                        )
                        for r in old["lineage"]["rows"]
                    ]
                    reused_routes += 1
                else:
                    query = (
                        [s["source_name"][:-4]]
                        if s["rank"] == "genus"
                        and s["BDTFX_code"] == "0"
                        and s["source_name"].endswith(" sp.")
                        else ([s["source_name"]] if s["BDTFX_code"] == "0" else labels)
                    )
                    try:
                        route = named_route(rows, names, query, s["rank"])
                    except AssertionError:
                        route = None
                    new_routes += 1
                if route is None:
                    assert (
                        record["association_status"] == "unresolved"
                        and record["axis"] is None
                    )
                    derived[s["row"]] = (None, None, None)
                    continue
                assert record["association_status"] == "associated"
                assert [
                    (
                        int(r["num_nom"]),
                        r["nom_sci"],
                        r["rang"],
                        r["native_line"],
                        r["num_tax_sup"],
                    )
                    for r in record["native_chain"]
                ] == route
                ids = {r[0] for r in route}
                axes = [
                    axis
                    for axis in AXES
                    if len(anchors[axis]) == 1 and anchors[axis][0] in ids
                ]
                if "Calluna vulgaris" in axes:
                    axes = [a for a in axes if a != "Ericaceae"]
                assert len(axes) <= 1
                axis = axes[0] if axes else None
                assert record["axis"] == axis and record[
                    "analyst_associated_native_id"
                ] == str(route[0][0])
                derived[s["row"]] = (axis, route[0][0], [r[0] for r in route[1:]])
                if (
                    not reuse
                    and s["BDTFX_code"] != "0"
                    and str(route[0][0]) != old["lineage"]["accepted_id"]
                ):
                    nomenclature_conflicts.append(
                        {
                            "version": version,
                            "row": s["row"],
                            "label": s["source_name"],
                            "code_accepted_id": old["lineage"]["accepted_id"],
                            "name_accepted_id": str(route[0][0]),
                        }
                    )
            mapping[version, mode] = derived
        del rows, names
    checked = 0
    maximum = Decimal(0)
    checked_raw = 0
    checked_closed = 0
    checked_means = 0
    full_loss_records = 0

    def equal(actual, expected):
        nonlocal checked, maximum
        error = abs(Decimal(str(actual)) - expected)
        assert error <= Decimal("2e-13"), (actual, str(expected), str(error))
        maximum = max(maximum, error)
        checked += 1

    with localcontext() as decimal_context:
        decimal_context.prec = 50
        for case in contexts:
            mode = case["association_mode"]
            version = case["version"]
            derived = mapping[version, mode]
            omit = set()
            for parent, (axis, pid, _) in derived.items():
                if axis is not None and any(
                    other != parent and caxis is not None and pid in ancestors
                    for other, (caxis, _, ancestors) in derived.items()
                    if ancestors is not None
                ):
                    omit.add(parent)
            if case["parent_assumption"] == "declared-disjoint-residual-observations":
                omit = set()
            assert set(map(int, case["inventory_parent_mask"])) == omit
            selected = {
                row: axis
                for row, (axis, _, _) in derived.items()
                if axis is not None and row not in omit
            }
            axis_rows = {
                a: [row for row, axis in selected.items() if axis == a] for a in AXES
            }
            unresolved = {
                row for row, (axis, pid, parents) in derived.items() if pid is None
            }
            assert (
                tuple(case["axis_order"]) == AXES
                and {r["plot"] for r in case["outcomes"]} == plots
            )
            outcome_byplot = exact_inventory(
                case["outcomes"], lambda row: row["plot"], plots, "plot outcomes"
            )
            loss = exact_inventory(
                case["positive_observation_loss_ledger"],
                lambda row: (row["source_row"], row["plot"]),
                numbers,
                "positive observation accounts",
            )
            full_loss_records += len(loss)
            for key, q in numbers.items():
                row, plot = key
                record = loss[key]
                axis, pid, _ = derived[row]
                expected_status = (
                    "unresolved-association"
                    if pid is None
                    else (
                        "outside-panel"
                        if axis is None
                        else (
                            "omitted-inventory-parent"
                            if row in omit
                            else "included-panel-observation"
                        )
                    )
                )
                assert (
                    record["status"] == expected_status
                    and record["axis"] == axis
                    and Decimal(record["literal_cover_percent"]) == q
                )
            for plot, actual in outcome_byplot.items():
                raw = [
                    sum(
                        (numbers[row, plot] for row in rows if (row, plot) in numbers),
                        Decimal(0),
                    )
                    for rows in axis_rows.values()
                ]
                total = sum(raw, Decimal(0))
                blank = {
                    axis: sum((row, plot) not in numbers for row in rows)
                    for axis, rows in axis_rows.items()
                }
                absent = [axis for axis, rows in axis_rows.items() if not rows]
                unknown = sorted(row for row in unresolved if (row, plot) in numbers)
                reasons = []
                if unknown:
                    reasons.append(
                        "positive-source-cover-has-unresolved-taxonomic-association"
                    )
                if case["blank_assumption"] == "strict-unknown-blanks" and (
                    any(blank.values()) or absent
                ):
                    reasons.append("unknown-source-blanks-or-unrepresented-panel-axis")
                if total <= 0:
                    reasons.append("no-positive-known-panel-cover")
                assert (
                    actual["refusals"] == reasons
                    and actual["source_blank_counts_by_axis"] == blank
                    and actual["unrepresented_axes"] == absent
                    and sorted(actual["unknown_positive_source_rows"]) == unknown
                )
                axis_vector(actual["raw_cover_percent_by_axis"], "raw plot vector")
                for x, y in zip(actual["raw_cover_percent_by_axis"], raw):
                    equal(x, y)
                    checked_raw += 1
                equal(actual["known_panel_cover_percent"], total)
                if reasons:
                    assert (
                        actual["closed_panel_fraction"] is None
                        and actual["status"] == "refused"
                    )
                else:
                    assert (
                        actual["status"] == "conditional-projection"
                        and len(actual["closed_panel_fraction"]) == 17
                    )
                    axis_vector(actual["closed_panel_fraction"], "closed plot vector")
                    for x, y in zip(actual["closed_panel_fraction"], raw):
                        equal(x, y / total)
                        checked_closed += 1
                    assert abs(
                        sum(Decimal(str(x)) for x in actual["closed_panel_fraction"])
                        - 1
                    ) < Decimal("2e-13")
            assert case["status_counts"] == dict(
                Counter(r["status"] for r in case["outcomes"])
            ) and case["observation_status_counts"] == dict(
                Counter(r["status"] for r in loss.values())
            )
        for entry in summaries:
            case = context_byid[entry["case_id"]]
            byplot = {r["plot"]: r for r in case["outcomes"]}
            groups = defaultdict(list)
            for plot in plots:
                m = metadata[plot]
                for origin in ("map", "field"):
                    groups[origin, m[origin + "_code"], "pooled-year-area"].append(plot)
                    groups[
                        origin,
                        m[origin + "_code"],
                        m["event_year"] + "/" + m["area_m2"] + "m2",
                    ].append(plot)
            summary_bykey = exact_inventory(
                entry["source_class_comparisons"],
                lambda row: (row["class_source"], row["class_code"], row["stratum"]),
                groups,
                "class rows",
            )
            for key, members in groups.items():
                row = summary_bykey[key]
                valid = [
                    byplot[p]
                    for p in members
                    if byplot[p]["status"] == "conditional-projection"
                ]
                n = len(valid)
                assert (
                    row["original_plot_denominator"] == len(members)
                    and row["conditional_projection_denominator"] == n
                    and row["refused_plot_denominator"] == len(members) - n
                )
                if not n:
                    assert (
                        row["mean_of_closed_vectors"] is None
                        and row["closure_of_mean_raw_cover"] is None
                    )
                    continue
                rawmeans = [
                    sum(
                        (
                            Decimal(str(v["raw_cover_percent_by_axis"][i]))
                            for v in valid
                        ),
                        Decimal(0),
                    )
                    / n
                    for i in range(17)
                ]
                closedmeans = [
                    sum(
                        (Decimal(str(v["closed_panel_fraction"][i])) for v in valid),
                        Decimal(0),
                    )
                    / n
                    for i in range(17)
                ]
                axis_vector(row["mean_of_closed_vectors"], "mean of closed vectors")
                axis_vector(
                    row["closure_of_mean_raw_cover"], "closure of mean raw cover"
                )
                for x, y in zip(row["mean_of_closed_vectors"], closedmeans):
                    equal(x, y)
                    checked_means += 1
                for x, y in zip(row["closure_of_mean_raw_cover"], rawmeans):
                    equal(x, y / sum(rawmeans, Decimal(0)))
                    checked_means += 1
    assert (
        checked_raw == 34000
        and full_loss_records == 28112
        and sum(len(c["outcomes"]) for c in contexts) == 2000
    ), "complete audit denominators differ"
    return {
        "approved_for_conditional_botanical_source_projection": True,
        "native_versions": 2,
        "source_records": 208,
        "reused_saved_native_routes": reused_routes,
        "new_name_association_routes": new_routes,
        "source_positive_observations": 1757,
        "complete_positive_loss_records": full_loss_records,
        "plot_contexts": 2000,
        "raw_axis_cells_verified": checked_raw,
        "closed_axis_cells_verified": checked_closed,
        "class_operator_cells_verified": checked_means,
        "total_decimal_comparisons": checked,
        "max_absolute_difference": str(maximum),
        "absolute_tolerance": "2e-13",
        "source_name_vs_code_accepted_id_disagreements": nomenclature_conflicts,
        "method": "Independent native CSV retained/parent route + saved183chain identity, independent original stored-cell projection and Decimal50 subset sums/closure/refusal/class operators. No shared producer association/projection functions.",
        "claims": "Conditional botanical source grouping only; no author116/full18/pollen matching or empirical model accuracy.",
    }

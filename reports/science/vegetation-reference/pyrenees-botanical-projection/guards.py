"""Meaningful source-code, nomenclature, observation and closure refusal guards."""

from collections import defaultdict
from copy import deepcopy
import json
import math


def check(m, consumer):
    results = []

    def positive(name, fn):
        assert fn(), name
        results.append({"name": name, "passed": True})

    def refused(name, fn, reason):
        try:
            fn()
        except (ValueError, KeyError) as error:
            assert reason in str(error), (name, str(error))
            results.append({"name": name, "passed": True, "actual_refusal": str(error)})
        else:
            raise AssertionError(name)

    def node(key, name, rank, parent):
        return {
            "num_nom": str(key),
            "num_nom_retenu": str(key),
            "num_tax_sup": str(parent),
            "nom_sci": name,
            "rang": rank,
            "native_line": key,
        }

    index = {
        1: node(1, "Calluna vulgaris", "290", 9),
        3: node(3, "Ericaceae", "180", 9),
        4: node(4, "Cyperaceae", "180", 9),
        9: node(9, "Plantae", "70", 0),
        10: node(10, "Carex nigra subsp. nigra", "310", 11),
        11: node(11, "Carex nigra", "290", 12),
        12: node(12, "Carex", "220", 4),
    }
    index[1]["num_tax_sup"] = "3"
    names = defaultdict(list)
    for key, row in index.items():
        names[row["nom_sci"]].append(key)
    anchors = {a: [1000 + i] for i, a in enumerate(m.AXES)}
    anchors.update({"Calluna vulgaris": [1], "Ericaceae": [3], "Cyperaceae": [4]})

    def source(row, label, code, rank="species"):
        return {
            "row": row,
            "phytobase_name": label,
            "source_name": label,
            "BDTFX_name": "",
            "BDTFX_code": str(code),
            "rank": rank,
        }

    def saved(s, ids, status):
        return {
            "source": s,
            "status": status,
            "lineage": {"rows": [index[i] for i in ids], "accepted_id": str(ids[0])},
        }

    broader = saved(
        source(6, "Carex nigra", 10),
        [10, 11, 12, 4, 9],
        "code_lineage_label_mismatch_requires_review",
    )
    calluna = saved(
        source(7, "Calluna vulgaris", 1), [1, 3, 9], "qualified_code_and_label"
    )
    parent = {
        "source": source(8, "Cyperaceae", 0, "family"),
        "status": "zero_code_unresolved",
    }
    genus = {
        "source": source(9, "Carex sp.", 0, "genus"),
        "status": "zero_code_unresolved",
    }
    original = {"records": [broader, calluna, parent, genus]}
    associated = m.associate(original, index, names, m.MODES[0], anchors)
    positive(
        "literal higher-rank name uses completed native family chain",
        lambda: (
            associated[0]["axis"] == "Cyperaceae"
            and associated[0]["reused_completed_native_chain"] is True
        ),
    )
    positive(
        "Calluna counted once outside Ericaceae parent",
        lambda: associated[1]["axis"] == "Calluna vulgaris",
    )
    positive(
        "code-zero family keeps original zero and distinct association",
        lambda: (
            associated[2]["original_code_remains"] == "0"
            and associated[2]["analyst_associated_native_id"] == "4"
        ),
    )
    positive(
        "genus sp. associated only to native genus",
        lambda: (
            associated[3]["native_chain"][0]["rang"] == "220"
            and associated[3]["analyst_associated_native_id"] == "12"
        ),
    )
    positive(
        "both authority modes retain source ancestor support",
        lambda: (
            m.associate(original, index, names, m.MODES[1], anchors)[0]["axis"]
            == "Cyperaceae"
        ),
    )
    refused(
        "foreign association mode",
        lambda: m.associate(original, index, names, "guessed", anchors),
        "Undeclared",
    )
    badanchors = {**anchors, "Poaceae": []}
    refused(
        "missing panel anchor",
        lambda: m.associate(original, index, names, m.MODES[0], badanchors),
        "Missing",
    )
    idx = deepcopy(index)
    idx[12]["num_tax_sup"] = "10"
    refused("parent cycle", lambda: m.chain(idx, 10), "cyclic")
    idx = deepcopy(index)
    idx[12]["num_tax_sup"] = "9999"
    refused("missing parent", lambda: m.chain(idx, 10), "Missing")
    idx = deepcopy(index)
    idx[12]["num_nom_retenu"] = ""
    refused("unestablished retained genus", lambda: m.chain(idx, 12), "Unestablished")
    idx = deepcopy(index)
    idx[12]["rang"] = "290"
    refused(
        "wrong literal genus rank",
        lambda: m.unique_literal(idx, names, ["Carex"], "genus"),
        "rank",
    )
    refused(
        "no literal native name",
        lambda: m.unique_literal(index, names, ["Guessed"], "genus"),
        "Absent",
    )
    idx = deepcopy(index)
    idx[20] = node(20, "Carex", "220", 4)
    amb = {**names, "Carex": [12, 20]}
    refused(
        "ambiguous same-name genus",
        lambda: m.unique_literal(idx, amb, ["Carex"], "genus"),
        "ambiguous",
    )
    source_wrong = source(10, "Carex thing", 0, "genus")
    positive(
        "zero genus without explicit sp. stays unresolved",
        lambda: (
            m.associate(
                {
                    "records": [
                        {"source": source_wrong, "status": "zero_code_unresolved"}
                    ]
                },
                index,
                names,
                m.MODES[0],
                anchors,
            )[0]["association_status"]
            == "unresolved"
        ),
    )
    idx = deepcopy(index)
    idx[30] = node(30, "Galium album", "290", 9)
    idx[31] = node(31, "Galium mollugo", "290", 9)
    names2 = {**names, "Galium album": [30], "Galium mollugo": [31]}
    mismatch = {
        "source": source(11, "Galium mollugo", 30),
        "status": "code_lineage_label_mismatch_requires_review",
        "lineage": {"rows": [idx[30], idx[9]], "accepted_id": "30"},
    }
    positive(
        "source code authority preserves conflicting original label",
        lambda: (
            m.associate({"records": [mismatch]}, idx, names2, m.MODES[0], anchors)[0][
                "analyst_associated_native_id"
            ]
            == "30"
        ),
    )
    positive(
        "exact name alternative records different accepted identity",
        lambda: (
            m.associate({"records": [mismatch]}, idx, names2, m.MODES[1], anchors)[0][
                "associated_id_differs_from_supplied_code"
            ]
            is True
        ),
    )
    positive(
        "native parent overlap sees both generic source rows",
        lambda: set(m.parent_mask(associated)[0]) == {8, 9},
    )
    plots = ["one", "two"]
    matrix = {(r["source"]["row"], p): None for r in associated for p in plots}
    matrix[6, "one"] = "14"
    matrix[7, "one"] = "3"
    matrix[8, "one"] = "32"
    matrix[9, "one"] = "0.3"
    matrix[6, "two"] = "90"
    matrix[7, "two"] = "14"
    full = m.project(associated, plots, matrix, m.PARENTS[0], m.BLANKS[1])
    omit = m.project(associated, plots, matrix, m.PARENTS[1], m.BLANKS[1])
    strict = m.project(associated, plots, matrix, m.PARENTS[0], m.BLANKS[0])
    positive(
        "declared residual sum retains generic native observations",
        lambda: math.isclose(full["outcomes"][0]["known_panel_cover_percent"], 49.3),
    )
    positive(
        "inventory parent omission has complete loss ledger",
        lambda: (
            omit["observation_status_counts"]["omitted-inventory-parent"] == 2
            and math.isclose(omit["outcomes"][0]["known_panel_cover_percent"], 17)
        ),
    )
    positive(
        "strict absent axes/blanks are refusal not zeros",
        lambda: all(r["closed_panel_fraction"] is None for r in strict["outcomes"]),
    )
    positive(
        "zero interpretation is flagged",
        lambda: all(
            r["blank_zero_imputation_assumed"] is True for r in full["outcomes"]
        ),
    )
    positive(
        "residual and omission masks independent of plot values",
        lambda: set(map(int, omit["inventory_parent_mask"])) == {8, 9},
    )
    refused(
        "foreign blank assumption",
        lambda: m.project(associated, plots, matrix, m.PARENTS[0], "invented"),
        "Undeclared",
    )
    refused(
        "foreign parent assumption",
        lambda: m.project(associated, plots, matrix, "invented", m.BLANKS[0]),
        "Undeclared",
    )
    refused(
        "duplicate plot identities",
        lambda: m.project(
            associated, ["one", "one"], matrix, m.PARENTS[0], m.BLANKS[1]
        ),
        "Duplicate",
    )
    unmapped = {
        "source": source(90, "Unknown", 0),
        "association_status": "unresolved",
        "axis": None,
    }
    copy = [*associated, unmapped]
    mat = {**matrix, (90, "one"): "57", (90, "two"): None}
    positive(
        "unknown positive taxonomy cannot be zero filled",
        lambda: (
            m.project(copy, plots, mat, m.PARENTS[0], m.BLANKS[1])["outcomes"][0][
                "refusals"
            ]
            == ["positive-source-cover-has-unresolved-taxonomic-association"]
        ),
    )
    for values in ([0, 0], [-1, 2], [float("nan"), 2], [float("inf"), 2]):
        refused(
            "invalid/zero closure " + repr(values),
            lambda v=values: m.close(v),
            "conditional" if values == [0, 0] else "Invalid",
        )
    positive(
        "positive subset closure simplex",
        lambda: m.close([14, 32]) == [14 / 46, 32 / 46],
    )
    metadata = {
        p: {"map_code": "BF", "field_code": "BF", "event_year": "2015", "area_m2": "25"}
        for p in plots
    }
    sums = m.class_summaries(full, metadata)
    positive(
        "both class operators and exact denominators retained",
        lambda: all(
            s["original_plot_denominator"] == 2
            and s["conditional_projection_denominator"] == 2
            and s["mean_of_closed_vectors"] != s["closure_of_mean_raw_cover"]
            for s in sums
        ),
    )
    inputs = consumer.JOB / "inputs"

    def read(n):
        return json.loads((inputs / n).read_text())

    native_args = [
        read(n)
        for n in (
            "lineage-terminal.json",
            "lineage-plan.json",
            "lineage-result.json",
            "stored-source-receipt.json",
            "literal-source-join-receipt.json",
        )
    ]
    consumer.authority(*native_args)
    positive("actual native authority original-shaped positive", lambda: True)
    for name, key, value, reason in [
        ("boolean exit", "native_exit_code", False, "authority"),
        ("changed custody", "custody_after_unchanged", False, "authority"),
        ("unsettled survivor", "owned_survivors", {"1": {}}, "authority"),
        ("resource violation", "resource_failure", "RSS", "authority"),
        ("wrong plan", "plan_sha256", "0" * 64, "binding"),
    ]:
        altered = [{**native_args[0], key: value}, *native_args[1:]]
        refused(name, lambda a=altered: consumer.authority(*a), reason)
    altered = list(native_args)
    altered[3] = {**native_args[3], "exit": False}
    refused("boolean source census exit", lambda: consumer.authority(*altered), "exit")
    source_native = read("original-taxa-classes.json")
    plots_native, matrix_native, positive_native = m.observed_matrix(
        read("stored-source-cells.json"), source_native["taxa"]
    )
    positive(
        "actual original matrix125 plots/1757 positives",
        lambda: (
            len(plots_native) == 125
            and len(positive_native) == 1757
            and len(matrix_native) == 26000
        ),
    )
    positive(
        "actual metadata keeps both epochs and three area types",
        lambda: (
            {r["event_year"] for r in m.plot_metadata(source_native).values()}
            == {"2015", "2020"}
            and {r["area_m2"] for r in m.plot_metadata(source_native).values()}
            == {"25", "100", "400"}
        ),
    )
    audit = consumer.load("independent")

    def coverage_refused(name, fn, reason):
        try:
            fn()
        except AssertionError as error:
            assert reason in str(error), (name, str(error))
            results.append({"name": name, "passed": True, "actual_refusal": str(error)})
        else:
            raise AssertionError(name)

    associations = [
        {"version": v, "association_mode": mode}
        for v in ("3.00", "3.01")
        for mode in m.MODES
    ]
    contexts = []
    for v in ("3.00", "3.01"):
        for mode in m.MODES:
            for parent in (
                "declared-disjoint-residual-observations",
                "omit-inventory-parent-observations",
            ):
                for blank in (
                    "strict-unknown-blanks",
                    "declared-exhaustive-survey-zero",
                ):
                    contexts.append(
                        {
                            "case_id": "/".join((v, mode, parent, blank)),
                            "version": v,
                            "association_mode": mode,
                            "parent_assumption": parent,
                            "blank_assumption": blank,
                        }
                    )
    summaries = [{"case_id": row["case_id"]} for row in contexts]
    positive(
        "exact Cartesian sixteen scenario inventory",
        lambda: len(audit.scenario_inventory(associations, contexts, summaries)) == 16,
    )
    duplicated = [*contexts[:-1], deepcopy(contexts[0])]
    coverage_refused(
        "duplicate context cannot hide missing Cartesian case",
        lambda: audit.scenario_inventory(associations, duplicated, summaries),
        "duplicate/missing",
    )
    wrong = deepcopy(contexts)
    wrong[0]["version"] = "3.01"
    coverage_refused(
        "scenario tuple must agree with joined identity",
        lambda: audit.scenario_inventory(associations, wrong, summaries),
        "tuple/ID",
    )
    coverage_refused(
        "duplicate summary cannot hide omitted scenario",
        lambda: audit.scenario_inventory(
            associations, contexts, [*summaries[:-1], summaries[0]]
        ),
        "duplicate/missing",
    )
    coverage_refused(
        "missing summary scenario",
        lambda: audit.scenario_inventory(associations, contexts, summaries[:-1]),
        "population",
    )
    rows = [{"key": "BF"}, {"key": "MF"}]
    coverage_refused(
        "duplicate class row cannot hide missing class",
        lambda: audit.exact_inventory(
            [rows[0], rows[0]], lambda row: row["key"], {"BF", "MF"}, "class"
        ),
        "duplicate/missing",
    )
    coverage_refused(
        "missing class row",
        lambda: audit.exact_inventory(
            rows[:-1], lambda row: row["key"], {"BF", "MF"}, "class"
        ),
        "population",
    )
    coverage_refused(
        "truncated raw axis refused before zip",
        lambda: audit.axis_vector([0] * 16, "raw"),
        "requires17",
    )
    coverage_refused(
        "extra raw axis refused before zip",
        lambda: audit.axis_vector([0] * 18, "raw"),
        "requires17",
    )
    coverage_refused(
        "truncated class axis refused before zip",
        lambda: audit.axis_vector([0] * 16, "class"),
        "requires17",
    )
    positive(
        "complete seventeen-axis vector",
        lambda: len(audit.axis_vector([0] * 17, "raw")) == 17,
    )
    coverage_refused(
        "duplicate plot row cannot hide missing plot",
        lambda: audit.exact_inventory(
            [{"plot_id": "PG1"}, {"plot_id": "PG1"}],
            lambda row: row["plot_id"],
            {"PG1", "PG2"},
            "plot",
        ),
        "duplicate/missing",
    )
    coverage_refused(
        "duplicate observation account cannot hide lost source",
        lambda: audit.exact_inventory(
            [{"key": (6, "PG1")}, {"key": (6, "PG1")}],
            lambda row: row["key"],
            {(6, "PG1"), (7, "PG1")},
            "loss",
        ),
        "duplicate/missing",
    )
    return results

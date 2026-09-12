"""Publication, parameter-resource and non-pollen source inventories."""

from __future__ import annotations

import ast
from collections import Counter
from typing import Any

from ..source_completion.evidence import EvidenceReader, digest
from ..source_completion.landclim import parse_taxonomy
from .rows import review_row


def landclim_rows(reader: EvidenceReader) -> list[dict[str, Any]]:
    path = "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
    content = reader.read_bytes(path)
    if content is None:
        raise ValueError("LandClim taxonomy authority is missing")
    rows = []
    for taxon in parse_taxonomy(content.decode("utf-8-sig")):
        row = review_row(
            row_id=f"landclim:937075:taxon-row:{taxon['source_row']}",
            source="landclim",
            native_id=None,
            label=taxon["source_taxon"],
            domain="published_modeled_taxon_parameter",
            evidence={"path": path, "doi": "10.1594/PANGAEA.937075", **taxon},
        )
        row.update(
            source_pft=taxon["source_pft"],
            source_lct=taxon["source_lct"],
            source_groups=[taxon["source_pft"], taxon["source_lct"]],
            parameter_candidates=[
                {
                    "ppe_sd_source_text": taxon["source_ppe_sd"],
                    "fall_speed_source_text": taxon["source_fall_speed"],
                    "fall_speed_units": "m/s",
                    "approval": "not_established",
                }
            ],
        )
        rows.append(row)
    return rows


def _resource_frames(
    value: object, locator: str = ""
) -> list[tuple[str, dict[str, Any]]]:
    frames = []
    if isinstance(value, dict):
        if value.get("__type__") == "dataframe":
            frames.append((locator, value))
        else:
            for key, child in sorted(value.items()):
                frames.extend(_resource_frames(child, f"{locator}/{key}"))
    return frames


def parameter_rows(reader: EvidenceReader) -> list[dict[str, Any]]:
    directory = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data"
    )
    rows = []
    declaration_path = directory.removesuffix("/data") + "/examples.py"
    declaration = reader.read_bytes(declaration_path)
    manifest = reader.json(directory + "/upstream_data_manifest.json")
    if declaration is None or manifest is None:
        raise ValueError(
            "Reference dataset declaration or upstream manifest is missing"
        )
    assignments = [
        node
        for node in ast.parse(declaration).body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "DATASETS"
    ]
    if len(assignments) != 1 or assignments[0].value is None:
        raise ValueError("Reference DATASETS declaration is unsupported")
    names = ast.literal_eval(assignments[0].value)
    if (
        not isinstance(names, tuple)
        or not names
        or any(
            not isinstance(name, str) or not name or "/" in name or "\\" in name
            for name in names
        )
        or len(set(names)) != len(names)
    ):
        raise ValueError("Reference DATASETS declaration is invalid")
    expected = {name + ".json" for name in names} | {"upstream_data_manifest.json"}
    actual = {path.name for path in reader.resolve(directory).glob("*.json")}
    if actual != expected:
        raise ValueError("Reference JSON inventory differs from declared DATASETS")
    for name in sorted(names):
        if name + ".rda" not in manifest:
            raise ValueError("Reference dataset has no upstream provenance entry")
        relative = directory + "/" + name + ".json"
        payload = reader.json(relative)
        if payload is None:
            raise ValueError("Declared reference dataset is missing")
        for locator, frame in _resource_frames(payload):
            columns = frame["columns"]
            label_column = next(
                (column for column in ("Taxon", "species") if column in columns), None
            )
            if label_column is not None:
                entries = [
                    (
                        values[columns.index(label_column)],
                        dict(zip(columns, values, strict=True)),
                    )
                    for values in frame["data"]
                ]
            else:
                entries = [
                    (
                        column,
                        {
                            "source_column": column,
                            "table_row_count": len(frame["data"]),
                        },
                    )
                    for column in columns
                ]
            for index, (label, evidence) in enumerate(entries):
                row = review_row(
                    row_id=f"lra-resource:{digest([relative, locator, index])[:24]}",
                    source="lra_reference_resources",
                    native_id=None,
                    label=label,
                    domain="reference_parameter_taxon"
                    if label_column
                    else "reference_table_column_needs_classification",
                    evidence={
                        "path": relative,
                        "locator": locator,
                        "entry_index": index,
                        **evidence,
                    },
                )
                if label_column:
                    row["parameter_candidates"] = [
                        {"source_values": evidence, "approval": "not_established"}
                    ]
                rows.append(row)
    return rows


def adna_rows(reader: EvidenceReader) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    dashboard_path = "data/adna/governance/cross_species_coverage_dashboard.json"
    dashboard = reader.json(dashboard_path)
    if dashboard is None:
        raise ValueError("Animal species dashboard authority is missing")
    rows = []
    for species in dashboard["rows"]:
        label = species["species_latin_name"]
        slug = label.lower().replace(" ", "_")
        path = f"data/adna/species/{slug}/normalized/sample_records.json"
        payload = reader.json(path)
        evidence: dict[str, Any] = {
            "dashboard_path": dashboard_path,
            "dashboard_row": species,
            "records_path": path,
        }
        row = review_row(
            row_id=f"animal-adna:species:{slug}",
            source="animal_adna",
            native_id=slug,
            label=label,
            domain="animal_ancient_dna_excluded_from_pollen",
            evidence=evidence,
        )
        row["current_mapping_status"] = "not_applicable_to_pollen"
        if payload is not None:
            if payload["species_latin_name"] != label:
                raise ValueError(f"Species authority disagreement: {path}")
            row["sample_count"] = len(payload["samples"])
            row["refused_sample_count"] = len(payload["sample_refusals"])
            row["country_counts"] = dict(
                sorted(
                    Counter(
                        sample.get("political_entity") or "UNASSIGNED"
                        for sample in payload["samples"]
                    ).items()
                )
            )
            row["country_dimension"] = "source_reported_political_entity"
        rows.append(row)
    human_path = (
        "data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json"
    )
    human = reader.json(human_path)
    if human is None:
        raise ValueError("Human source accountability authority is missing")
    row = review_row(
        row_id="aadr:human-source-taxonomy-scope",
        source="aadr",
        native_id=None,
        label=None,
        domain="human_ancient_dna_excluded_from_pollen",
        evidence={
            "path": human_path,
            "taxon_scope_status": human["taxon_scope_status"],
        },
    )
    row["current_mapping_status"] = "not_applicable_to_pollen"
    rows.append(row)
    return rows, {
        "animal_species_count": len(dashboard["rows"]),
        "human_taxon_scope_status": human["taxon_scope_status"],
        "human_accountability_denominators": human["accountability_projection"][
            "summary"
        ]["denominators"],
    }

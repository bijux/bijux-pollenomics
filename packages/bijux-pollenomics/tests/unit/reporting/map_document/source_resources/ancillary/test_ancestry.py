"""Explicit recorded ancestry targets reuse supporting metadata without body access."""

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document import source_resources as owner
from tests.unit.collection.sources.neotoma.acquisition.linked_resources.ancestry.chain.native_products import (
    capture_parent,
    publish_chain,
)
from tests.unit.collection.sources.neotoma.acquisition.linked_resources.ancestry.chain.native_products import (
    chain_products as chain_products,
)
from tests.unit.collection.sources.neotoma.acquisition.linked_resources.ancestry.native_products import (
    ancestry_products as ancestry_products,
)
from tests.unit.collection.sources.neotoma.ancillary_store.linked_evidence.native_products import (
    scoped_inputs as scoped_inputs,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from ...static_assets.source_resources.ancillary.native_metadata import (
    ancillary_sources as ancillary_sources,
)
from ...static_assets.source_resources.ancillary.native_metadata import (
    capsule_inputs as capsule_fixture,
)
from ...static_assets.source_resources.ancillary.native_metadata import (
    legacy_catalogue as legacy_catalogue,
)


@pytest.fixture
def capsule_inputs(tmp_path: Path) -> Any:
    root = tmp_path / "federation-inputs"
    root.mkdir()
    return capsule_fixture.__wrapped__(root)


def input_owner() -> Any:
    assert hasattr(owner, "AtlasTaxonAncestryArchiveInput"), (
        "Selected ancestry supporting input is missing"
    )
    return owner.AtlasTaxonAncestryArchiveInput


@pytest.mark.parametrize(
    "targets",
    [
        [("taxon", 1)],
        (("taxon", True),),
        (("taxon", 2**53),),
        (("contact", 1),),
        (("taxon", 1), ("taxon", 1)),
        (),
    ],
)
def test_targets_require_unique_immutable_literal_safe_identities(
    tmp_path: Path, targets: Any
) -> None:
    with pytest.raises(ValueError, match="target"):
        input_owner()(tmp_path, "1" * 64, {"2" * 64: tmp_path}, targets)


def test_resolver_is_detached_and_family_requires_exact_typed_input(
    tmp_path: Path,
) -> None:
    mapping = {"2" * 64: tmp_path}
    reference = input_owner()(tmp_path, "1" * 64, mapping, (("taxon", 1),))
    mapping.clear()
    assert dict(reference.chain_sources) == {"2" * 64: tmp_path}
    with pytest.raises(TypeError):
        reference.chain_sources["3" * 64] = tmp_path
    assert owner.AtlasAncillaryArchivesInput(
        taxon_ancestry=(reference,)
    ).taxon_ancestry == (reference,)
    with pytest.raises(ValueError):
        owner.AtlasAncillaryArchivesInput(
            taxon_ancestry=(owner.AtlasSourceArchiveInput(tmp_path, "1" * 64),)
        )


def test_real_chain_selected_projection_publishes_without_entity_bodies(
    chain_products: dict[str, Any],
    legacy_catalogue: Any,
    ancillary_sources: dict[str, Any],
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    from bijux_pollenomics.reporting.map_document.source_resources.ancillary.ancestry import (
        load_taxon_ancestry_metadata,
    )
    from bijux_pollenomics.reporting.map_document.static_assets import (
        write_static_atlas_assets,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.source_resources import (
        build_source_resource_payloads,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.source_resources.validation import (
        validate_source_resource_payloads,
    )

    sources, capture = capture_parent(chain_products, tmp_path / "captured")
    sources, pin, _ = publish_chain(
        tmp_path / "chain", sources=sources, captures=(capture,)
    )
    reference = input_owner()(
        tmp_path / "chain",
        pin,
        {
            **sources.chain_sources,
            chain_products["baseline_sha256"]: chain_products["baseline"],
        },
        (("taxon", 15), ("publication", 13)),
    )
    original, opened = capture_opening(), []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    from bijux_pollenomics.reporting.map_document.source_resources.ancillary.archives import (
        load_supporting_archive_metadata,
    )
    from tests.unit.reporting.map_document.source_resources.ancillary.native_federations import (
        source_input,
    )

    dependency = source_input(ancillary_sources)
    dependency = replace(
        dependency,
        ancillary=replace(
            dependency.ancillary,
            archives=owner.AtlasAncillaryArchivesInput(taxon_ancestry=(reference,)),
        ),
    )
    archive = load_supporting_archive_metadata(dependency)[0]
    assert opened == []
    assert archive["archive_kind"] == "taxon_ancestry"
    assert [row["target_key"] for row in archive["index"]["targets"]] == [
        "taxon-15",
        "publication-13",
    ]
    assert archive["integrity_scope"] == "SELECTED_RECORDED_TARGETS_ONLY"
    assert archive["current_roles_revalidated"] is False
    assert archive["native_source_fields_revalidated"] is False
    assert (
        archive["native_entity_bodies_opened"] == 0
        and archive["GET_authorized"] is False
    )
    assert str(tmp_path) not in json.dumps(archive)
    ancillary = legacy_catalogue.ancillary
    configured = replace(
        legacy_catalogue,
        ancillary=owner.AtlasAncillarySupportingMetadata(
            **{
                field: getattr(ancillary, field)
                for field in ancillary.__dataclass_fields__
                if field
                not in {
                    "integrity_scope",
                    "entity_body_hashes_verified",
                    "source_assessments_replayed",
                }
            },
            supporting_archives=(archive,),
        ),
    )
    before, after = (
        build_source_resource_payloads(legacy_catalogue),
        build_source_resource_payloads(configured),
    )
    for key in (
        "record_count",
        "site_count",
        "version_status_count",
        "ancillary_slot_count",
        "ancillary_observation_count",
        "ancillary_linked_occurrence_count",
    ):
        assert before.domain[key] == after.domain[key]
    assert (
        after.domain["supporting_archive_count"] == 1
        and after.domain["supporting_entry_count"] == 2
    )
    validate_source_resource_payloads(
        after,
        expected_catalogue_manifest_sha256=after.domain["catalogue_manifest_sha256"],
    )
    (tmp_path / "atlas").mkdir()
    written = write_static_atlas_assets(
        tmp_path / "atlas",
        slug="ancestry",
        version="recorded",
        point_layers=[],
        polygon_layers=[],
        source_resources=configured,
    )
    assert written.manifest["domains"]["resources"]["supporting_entry_count"] == 2
    from copy import deepcopy

    for field, value in (
        ("current_roles_revalidated", True),
        ("native_source_fields_revalidated", True),
        ("GET_authorized", True),
        ("native_entity_bodies_opened", 1),
    ):
        bad = deepcopy(after)
        for part in bad.payloads:
            if part["kind"] == "supporting_archives":
                part["records"][0][field] = value
        with pytest.raises(ValueError):
            validate_source_resource_payloads(
                bad,
                expected_catalogue_manifest_sha256=bad.domain[
                    "catalogue_manifest_sha256"
                ],
            )
    assert opened == []

    from tests.unit.reporting.map_document.browser_semantics.source_context.source_resources.ancillary.native_transport import (
        invoke,
        publish,
    )

    packet = publish(configured, tmp_path / "browser", countries=())
    observed = invoke(
        packet,
        """
(async()=>{const initial=calls.length,listed=await reader.search('taxon-15',{population:'supporting_entries'}),indexCalls=calls.length;
const selected=await reader.ancillary('supporting_entries',listed[0].record_id), exported=JSON.parse(JSON.stringify(selected));
selected.entry.recorded_node.native_id=999;
const reread=await reader.ancillary('supporting_entries',listed[0].record_id);
console.log(JSON.stringify({initial,indexCalls,listed,exported,reread,calls}));})().catch(e=>{console.error(e);process.exit(1)});
""",
    )
    assert observed["initial"] == 0
    assert observed["indexCalls"] == len(
        packet["manifest"]["domains"]["resources"]["index_asset_keys"]
    )
    assert len(observed["listed"]) == 1
    assert observed["listed"][0]["source_selectors"] == {
        "target_key": "taxon-15",
        "kind": "taxon",
        "native_id": 15,
    }
    assert (
        observed["exported"]["entry"]["recorded_node"]["native_id"]
        == observed["reread"]["entry"]["recorded_node"]["native_id"]
        == 15
    )
    assert observed["exported"]["entry"]["native_entity_bodies_opened"] == 0
    assert str(tmp_path) not in json.dumps(observed)
    assert not any(value.endswith(".body") for value in observed["calls"])
    assert opened == []
    from hashlib import sha256
    import shutil

    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    foreign = tmp_path / "foreign-locator"
    shutil.copytree(reference.directory, foreign)
    manifest = json.loads((foreign / "manifest.json").read_bytes())
    manifest["node_index"]["taxon-15"] = manifest["node_index"]["taxon-16"]
    raw = encoded_json(manifest)
    (foreign / "manifest.json").write_bytes(raw)
    with pytest.raises(ValueError, match="identity"):
        load_taxon_ancestry_metadata(
            replace(
                reference,
                directory=foreign,
                expected_manifest_sha256=sha256(raw).hexdigest(),
            )
        )
    assert opened == []
    for changes in (
        {"targets": (("taxon", 999999),)},
        {"chain_sources": {}},
        {"expected_manifest_sha256": "0" * 64},
    ):
        with pytest.raises(ValueError):
            load_taxon_ancestry_metadata(replace(reference, **changes))


def test_selected_target_wire_refuses_malformed_native_ids_and_upgraded_posture() -> (
    None
):
    from importlib.resources import files

    from tests.unit.reporting.map_document.browser_semantics.support import (
        run_node_json,
    )

    source = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/source-resources/ancillary.js")
        .read_text()
    )
    observed = run_node_json(
        source
        + """
const contract=createSourceResourceAncillaryContract({schema_version:'atlas-source-resources.v2'},message=>{throw Error(message)});
const base={archive_kind:'taxon_ancestry',archive_manifest_sha256:'a'.repeat(64),population:'targets',row_index:0,
entry:{target_key:'taxon-15',kind:'taxon',native_id:15,recorded_node:{target_key:'taxon-15',target_kind:'taxon',native_id:15},
integrity_scope:'anchored_selected_metadata_parts_only',current_roles_revalidated:false,native_source_fields_revalidated:false,native_entity_bodies_opened:0,GET_authorized:false,scientific_admission:'not_asserted'}};
let refused=[];
for(const [key,value] of [['native_id',true],['native_id',9007199254740992],['kind','contact'],['target_key','taxon-16'],['current_roles_revalidated',true],['native_source_fields_revalidated',true],['native_entity_bodies_opened',1],['GET_authorized',true]]){
const row=structuredClone(base);row.entry[key]=value;
try{contract.identity('supporting_entries',row);refused.push(false);}catch(error){refused.push(true);}}
const ordinals=[];
for(const row_index of [true,'0',-1,0.5,9007199254740992]){
const row={...base,entity_type:'supporting_entries',record_id:'taxon_ancestry:'+base.archive_manifest_sha256+':targets:0',row_index};
try{contract.index(row);ordinals.push(false);}catch(error){ordinals.push(true);}}
console.log(JSON.stringify({refused,ordinals,positive:contract.identity('supporting_entries',base)}));
"""
    )
    assert observed["refused"] == [True] * 8
    assert observed["ordinals"] == [True] * 5
    assert observed["positive"] == "taxon_ancestry:" + "a" * 64 + ":targets:0"


@pytest.mark.parametrize(
    "family,population",
    [
        ("unit_metadata", "units"),
        ("reference_tables", "tables"),
        ("context_resources", "resources"),
    ],
)
def test_existing_supporting_selector_bytes_do_not_gain_target_fields(
    family: str, population: str
) -> None:
    from bijux_pollenomics.reporting.map_document.static_assets.source_resources.ancillary.publication import (
        ancillary_index_entry,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.source_resources.ancillary.validation import (
        ancillary_record_id,
    )

    row = {
        "archive_kind": family,
        "archive_manifest_sha256": "a" * 64,
        "population": population,
        "row_index": 0,
        "entry": {
            "unit_key": "unit-a",
            "target_key": "taxon-15",
            "kind": "taxon",
            "native_id": 15,
        },
    }
    identity = ancillary_record_id("supporting_entries", row)
    indexed = ancillary_index_entry(
        "supporting_entries", row, "supporting_entries:0", identity
    )
    assert indexed["source_selectors"] == {"unit_key": "unit-a"}

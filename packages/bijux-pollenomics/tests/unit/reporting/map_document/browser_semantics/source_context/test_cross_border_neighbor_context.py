from __future__ import annotations

from ..support import run_node_json, template_block


def test_selected_country_retains_only_governed_cross_border_neighbors() -> None:
    helpers = template_block(
        "function atlasCountryPairKey(", "function atlasFilterStateSnapshot("
    )
    observed = run_node_json(
        helpers
        + """
const edge={source_record_id:'controlled:no:older',target_record_id:'controlled:se:younger',source_country:'Norway',target_country:'Sweden',signal_id:'fixture:whole'};
const domestic={...edge,target_record_id:'controlled:no:newer',target_country:'Norway'};
const selected=new Set(['Sweden']), signalIds=new Set(['fixture:whole']);
const visible=[edge,domestic].filter(row=>atlasEdgeVisible(row,selected,'all',false,signalIds));
const retained=atlasRetainedNeighborRecordCountries(visible,selected);
console.log(JSON.stringify({
  visible:visible.length,
  retained:[...retained],
  none:atlasEdgeVisible(edge,new Set(), 'all',false,signalIds),
  unrelated:atlasEdgeVisible(edge,new Set(['Denmark']),'all',false,signalIds),
  pairMismatch:atlasEdgeVisible(edge,selected,'Denmark|Sweden',false,signalIds),
  signalMismatch:atlasEdgeVisible(edge,selected,'all',false,new Set()),
  reverse:[...atlasRetainedNeighborRecordCountries([edge],new Set(['Norway']))],
  regional:[...atlasRetainedNeighborRecordCountries([edge],new Set(['Norway','Sweden']))],
}));
"""
    )
    assert observed == {
        "visible": 1,
        "retained": [["controlled:no:older", "Norway"]],
        "none": False,
        "unrelated": False,
        "pairMismatch": False,
        "signalMismatch": False,
        "reverse": [["controlled:se:younger", "Sweden"]],
        "regional": [],
    }


def test_country_partition_loader_requests_only_selected_or_retained_point_country() -> (
    None
):
    loader = template_block(
        "function staticAtlasCountryNeeded(", "function staticAtlasTimeNeeded("
    )
    observed = run_node_json(
        """
const activeCountries=new Set(['Sweden']);
const retainedNeighborRecordCountries=new Map([['controlled:no:older','Norway']]);
const animalSourceChronologyCountryFilterBypassed=()=>false;
"""
        + loader
        + """
const point={applies_country_filter:true}, polygon={applies_country_filter:true};
const row=(country,kind)=>({country_keys:[country],layer_kind:kind});
console.log(JSON.stringify({
  focal:staticAtlasCountryNeeded(row('Sweden','point'),point),
  retained:staticAtlasCountryNeeded(row('Norway','point'),point),
  unrelated:staticAtlasCountryNeeded(row('Finland','point'),point),
  neighborBoundary:staticAtlasCountryNeeded(row('Norway','polygon'),polygon),
  unfiltered:staticAtlasCountryNeeded(row('Finland','point'),{applies_country_filter:false}),
}));
"""
    )
    assert observed == {
        "focal": True,
        "retained": True,
        "unrelated": False,
        "neighborBoundary": False,
        "unfiltered": True,
    }


def test_country_only_view_labels_neighbor_without_changing_focal_counts() -> None:
    edge_helpers = template_block(
        "function atlasCountryPairKey(", "function atlasFilterStateSnapshot("
    )
    context_helper = template_block(
        "function isRetainedNeighborContext(", "function renderRelationControls("
    )
    visibility_helper = template_block(
        "function pointFeatureVisible(", "function polygonFeatureVisible("
    )
    country_controls = template_block(
        "function renderCountryControls(", "function renderScientificControls("
    )
    observed = run_node_json(
        """
const activeCountries = new Set(['Sweden']);
const signalIds = new Set(['fixture:whole']);
const edge = {
  source_record_id:'synthetic:no:older',target_record_id:'synthetic:se:younger',
  source_country:'Norway',target_country:'Sweden',signal_id:'fixture:whole'
};
const selectedEdges = [edge].filter(row => atlasEdgeVisible(row, activeCountries, 'all', false, signalIds));
const retainedNeighborRecordCountries = atlasRetainedNeighborRecordCountries(selectedEdges, activeCountries);
const layer = {key:'synthetic-pollen',semantic_role:'pollen',group:'pollen',applies_country_filter:true};
const activeLayerKeys = new Set([layer.key]);
const animalSourceChronologyCountryFilterBypassed = () => false;
const featureCoordinatePair = () => ({latitude:60,longitude:12});
const pointFeatureInTimeWindow = () => true;
const sourceChronologyFeatureMatches = () => true;
const featureMatchesAnimalFilters = () => true;
const featureMatchesScientificSelection = () => true;
const focal = {record_id:'synthetic:se:younger',country:'Sweden'};
const neighbor = {record_id:'synthetic:no:older',country:'Norway'};
const unrelated = {record_id:'synthetic:fi:other',country:'Finland'};
const visiblePointEntries = [focal,neighbor,unrelated]
  .filter(feature => pointFeatureVisible(layer, feature))
  .map(feature => ({feature,neighborContext:isRetainedNeighborContext(layer, feature)}));
const COUNTRIES = ['Sweden','Norway','Finland'];
const countryFilters = {innerHTML:''};
const countryStyle = () => ({fill:'#000',stroke:'#000'});
const escapeHtml = value => String(value);
const document = {querySelectorAll:() => []};
"""
        + edge_helpers
        + context_helper
        + visibility_helper
        + country_controls
        + """
renderCountryControls();
console.log(JSON.stringify({
  selectedEdges:selectedEdges.length,
  visible:visiblePointEntries.map(({feature,neighborContext}) => [feature.country,neighborContext]),
  swedenCount:countryFilters.innerHTML.match(/Sweden<\\/span><span class="chip-count">(\\d+)/)?.[1],
  norwayCount:countryFilters.innerHTML.match(/Norway<\\/span><span class="chip-count">(\\d+)/)?.[1],
  unrelatedCount:countryFilters.innerHTML.match(/Finland<\\/span><span class="chip-count">(\\d+)/)?.[1],
}));
"""
    )
    assert observed == {
        "selectedEdges": 1,
        "visible": [["Sweden", False], ["Norway", True]],
        "swedenCount": "1",
        "norwayCount": "0",
        "unrelatedCount": "0",
    }
    assert "Neighbor context · ${escapeHtml(feature.country)}" in template_block(
        "function renderPointLayers(", "function scientificSignalById("
    )

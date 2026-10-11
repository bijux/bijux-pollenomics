from __future__ import annotations

from .support import run_node_json, template_block


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

"""Independent retained signed view/capture checks do not call product validators."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.ci import atlas_browser


def _run(body: str) -> object:
    module = Path(atlas_browser.__file__).with_name("signed-native-lra.mjs").as_uri()
    source = (
        f"import {{signedViewAgreement,signedObservationAgreement,signedStaticAgreement}} from {json.dumps(module)};\n"
        """
const profile='calendar-bp1950-signed.v1',hash='e'.repeat(64);
const support=(kind,younger,older)=>({profile,axis:'BP1950',source_age_type:'calendar_bp',original_source_age_type:'calendar_bp',support_kind:kind,
younger_bp:younger,older_bp:older,younger_inclusive:true,older_inclusive:true,calibration_status:'not_recorded_in_saved_request',calibration_evidence:null,native_calendar_label:null,native_calendar_convention:null});
const view={schema_version:'lra-atlas-view.v2',temporal_profile:profile,temporal_axis:'BP1950',data_kind:'synthetic',operation:'lra',scientific_acceptance:'not_evaluated',
sites:[{role:'regional',site_id:'r'},{role:'local',site_id:'l'}],rows:['regional','local'].map(role=>({role,site_id:role==='regional'?'r':'l',sample_id:'sample-'+role,
bin_id:'b',declared_bin:{bin_id:'b',younger_bp:-.75,older_bp:.75},age_type:'calendar_bp',age_support_bp:[[-.5,.5]],
source_calendar_support:support('closed_age_support',-.5,.5),declared_calendar_support:support('declared_stationarity_envelope',-.75,.75)}))};
const snapshot={global_context:{active_layer_keys:[],temporal_profile:profile,temporal_axis:'BP1950',time_window_bp:[-.5,-.25]}};
const observation={snapshot,capture:{capture_api_version:'atlas-capture.v2',temporal_profile:profile,temporal_axis:'BP1950',native_view_sha256:hash,
native_lra:structuredClone(snapshot),time_window_bp:{younger_bp:-.5,older_bp:-.25}},exported:{payload:{schema_version:'lra-selected-estimates.v2',temporal_profile:profile,temporal_axis:'BP1950'}}};
""" + body
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "--eval", source],
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    return json.loads(completed.stdout)


def test_signed_positive_and_int_float_json_equivalence() -> None:
    assert _run(
        "console.log(JSON.stringify([signedViewAgreement(view),signedObservationAgreement(view,observation,hash)]));"
    ) == [True, True]


@pytest.mark.parametrize(
    "mutation",
    [
        "view.temporal_axis='radiocarbon'",
        "view.scientific_acceptance='approved'",
        "view.sites.push({role:'local',site_id:'third'})",
        "view.rows.pop()",
        "view.rows.push({...structuredClone(view.rows[0]),sample_id:'another'})",
        "view.rows[1].declared_bin.older_bp=1",
        "view.rows[1].declared_bin.bin_id='other'",
        "view.rows[0].age_support_bp=[[0,.5]]",
        "view.rows[0].source_calendar_support.younger_bp=null",
        "view.rows[0].source_calendar_support.younger_bp=true",
        "view.rows[0].source_calendar_support.younger_bp='-.5'",
        "view.rows[0].source_calendar_support.younger_bp=-Infinity",
        "view.rows[0].source_calendar_support.younger_bp=-(2**53)",
        "view.rows[0].source_calendar_support.calibration_evidence='invented'",
        "view.rows[0].source_calendar_support.younger_inclusive=false",
        "view.rows[0].source_calendar_support.native_calendar_label='2000CE'",
    ],
)
def test_rehashed_view_contradictions_refuse(mutation: str) -> None:
    assert (
        _run(mutation + ";console.log(JSON.stringify(signedViewAgreement(view)));")
        is False
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "observation.snapshot.global_context.temporal_profile='unknown'",
        "observation.snapshot.global_context.temporal_axis='unknown'",
        "observation.snapshot.global_context.time_window_bp=[true,0]",
        "observation.snapshot.global_context.time_window_bp=['-.5',0]",
        "observation.snapshot.global_context.time_window_bp=[-.25,-.5]",
        "observation.snapshot.global_context.time_window_bp=[-(2**53),0]",
        "observation.capture.capture_api_version='atlas-capture.v1'",
        "observation.capture.native_view_sha256='0'.repeat(64)",
        "observation.capture.temporal_axis='radiocarbon'",
        "observation.capture.time_window_bp.younger_bp=0",
        "observation.capture.native_lra.global_context.time_window_bp=[0,0]",
        "observation.exported.payload.schema_version='lra-selected-estimates.v1'",
        "observation.exported.payload.temporal_profile='unknown'",
    ],
)
def test_retained_capture_cannot_contradict_selected_contract(mutation: str) -> None:
    assert (
        _run(
            mutation
            + ";console.log(JSON.stringify(signedObservationAgreement(view,observation,hash)));"
        )
        is False
    )


def test_signed_static_requires_every_temporal_envelope() -> None:
    assert _run("""
const bootstrap={schema_version:'atlas-static-bootstrap.v3',temporal_profile:profile,temporal_axis:'BP1950',native_view_sha256:hash,
assets:{schema_version:'atlas-static-asset-table.v4',temporal_profile:profile,temporal_axis:'BP1950'},compatibility:{node_schema:'atlas-node-chunk.v2',index_schema:'atlas-static-indexes.v4'}};
const positive=signedStaticAgreement(bootstrap,hash);bootstrap.assets.temporal_axis='other';
console.log(JSON.stringify([positive,signedStaticAgreement(bootstrap,hash)]));
""") == [True, False]

/** Independent signed support, captured selection and real control evidence. */
const PROFILE = 'calendar-bp1950-signed.v1';
const finite = value => typeof value === 'number' && Number.isFinite(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER;
const canonical = value => Array.isArray(value) ? `[${value.map(canonical).join(',')}]`
  : value && typeof value === 'object' ? `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`
  : JSON.stringify(value);
const same = (left, right) => canonical(left) === canonical(right);

function support(value, kind) {
  const constants = {profile:PROFILE,axis:'BP1950',source_age_type:'calendar_bp',original_source_age_type:'calendar_bp',
    support_kind:kind,younger_inclusive:true,older_inclusive:true,calibration_status:'not_recorded_in_saved_request',
    calibration_evidence:null,native_calendar_label:null,native_calendar_convention:null};
  return value && typeof value === 'object' && !Array.isArray(value)
    && same(Object.keys(value).sort(),[...Object.keys(constants),'younger_bp','older_bp'].sort())
    && Object.entries(constants).every(([key,expected])=>value[key]===expected)
    && finite(value.younger_bp) && finite(value.older_bp) && value.younger_bp<=value.older_bp;
}

export function signedViewAgreement(view) {
  try {
    if (view.schema_version!=='lra-atlas-view.v2' || view.temporal_profile!==PROFILE || view.temporal_axis!=='BP1950'
      || view.data_kind!=='synthetic' || view.operation!=='lra' || view.scientific_acceptance!=='not_evaluated'
      || !Array.isArray(view.rows) || view.rows.length===0 || !Array.isArray(view.sites) || view.sites.length!==2
      || view.sites[0].site_id===view.sites[1].site_id
      || ['regional','local'].some(role=>view.sites.filter(site=>site.role===role).length!==1)) return false;
    const roles=new Map();
    for (const row of view.rows) {
      const age=row.source_calendar_support, window=row.declared_calendar_support;
      if (!support(age,'closed_age_support') || !support(window,'declared_stationarity_envelope')
          || row.age_type!=='calendar_bp' || !same(row.age_support_bp,[[age.younger_bp,age.older_bp]])
          || !same(Object.keys(row.declared_bin).sort(),['bin_id','older_bp','younger_bp'])
          || row.bin_id!==row.declared_bin.bin_id || row.declared_bin.younger_bp!==window.younger_bp
          || row.declared_bin.older_bp!==window.older_bp || age.younger_bp<window.younger_bp || age.older_bp>window.older_bp
          || !same(row.declared_bin,view.rows[0].declared_bin) || !same(window,view.rows[0].declared_calendar_support)
          || typeof row.sample_id!=='string' || !row.sample_id || !['regional','local'].includes(row.role)
          || row.site_id!==view.sites.find(site=>site.role===row.role).site_id) return false;
      const identity=[row.sample_id,age];
      if (roles.has(row.role) && !same(roles.get(row.role),identity)) return false;
      roles.set(row.role,identity);
    }
    return roles.size===2 && roles.get('regional')[0]!==roles.get('local')[0];
  } catch {return false;}
}

export function signedObservationAgreement(view, observation, expectedViewSha256) {
  try {
    if (!signedViewAgreement(view)) return false;
    const {snapshot,capture,exported}=observation;
    const context=snapshot.global_context, window=context.time_window_bp;
    return context.temporal_profile===PROFILE && context.temporal_axis==='BP1950'
      && same(Object.keys(context).sort(),['active_layer_keys','temporal_axis','temporal_profile','time_window_bp'])
      && Array.isArray(window) && window.length===2 && window.every(finite) && window[0]<=window[1]
      && window[1]-window[0]<=Number.MAX_SAFE_INTEGER
      && window[0]>=view.rows[0].declared_bin.younger_bp && window[1]<=view.rows[0].declared_bin.older_bp
      && exported.payload.schema_version==='lra-selected-estimates.v2' && exported.payload.temporal_profile===PROFILE
      && exported.payload.temporal_axis==='BP1950'
      && capture.capture_api_version==='atlas-capture.v2' && capture.temporal_profile===PROFILE && capture.temporal_axis==='BP1950'
      && capture.native_view_sha256===expectedViewSha256 && same(capture.native_lra,snapshot)
      && same(capture.time_window_bp,{younger_bp:window[0],older_bp:window[1]});
  } catch {return false;}
}

export function signedStaticAgreement(bootstrap, viewSha256) {
  return bootstrap?.schema_version==='atlas-static-bootstrap.v3' && bootstrap.temporal_profile===PROFILE
    && bootstrap.temporal_axis==='BP1950' && bootstrap.native_view_sha256===viewSha256
    && bootstrap.assets?.schema_version==='atlas-static-asset-table.v4' && bootstrap.assets.temporal_profile===PROFILE
    && bootstrap.assets.temporal_axis==='BP1950' && bootstrap.compatibility?.node_schema==='atlas-node-chunk.v2'
    && bootstrap.compatibility?.index_schema==='atlas-static-indexes.v4';
}

export async function exerciseSignedCalendar(cdp, evaluate, observe, initial) {
  const extent=initial.snapshot.global_context.time_window_bp;
  const width=extent[1]-extent[0];
  const window=width===0 ? [...extent] : [extent[0]+width/4,extent[1]-width/4];
  await evaluate(cdp, `(async()=>{const sidebar=document.getElementById('sidebar');
    if(sidebar.classList.contains('is-collapsed'))document.getElementById('panel-toggle').click();
    await Promise.all(sidebar.getAnimations().map(animation=>animation.finished));
    document.getElementById('time-controls').open=true;})()`);
  const apply=async values=>{
    for (const [index,name] of ['younger','older'].entries()) {
      await evaluate(cdp, `(()=>{const node=document.getElementById('calendar-${name}-input');node.scrollIntoView({block:'nearest'});node.focus({preventScroll:true});node.select();})()`);
      await cdp.send('Input.insertText',{text:String(values[index])});
    }
    await evaluate(cdp, `(async()=>{document.getElementById('calendar-older-input').dispatchEvent(new Event('change',{bubbles:true}));await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();})()`);
    return observe(cdp,evaluate);
  };
  const narrowed=await apply(window);
  const point=await apply([window[0],window[0]]);
  await apply(window);
  const url=await observe(cdp,evaluate);
  await apply([extent[1]+1,extent[1]+1]);
  const refusal=await evaluate(cdp, `({detail:document.getElementById('calendar-window-error').textContent,valid:['younger','older'].every(name=>document.getElementById('calendar-'+name+'-input').checkValidity()),visible_window:['younger','older'].map(name=>document.getElementById('calendar-'+name+'-input').valueAsNumber)})`);
  const afterRefusal=await observe(cdp,evaluate);
  await evaluate(cdp, `(async()=>{document.getElementById('calendar-full-extent').click();await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();})()`);
  const restored=await observe(cdp,evaluate);
  const media=await evaluate(cdp, `(async()=>{try{await globalThis.BijuxPollenomicsAtlasCapture.applyFrame({story_kind:'source_chronology',time_start_bp:0,time_end_bp:0});return {refused:false};}catch(error){return {refused:error.message==='signed_native_media_capture_unsupported',reason:error.message};}})()`);
  return {extent,window,point_only:width===0,narrowed,point,url,refusal,afterRefusal,restored,media};
}

export function signedControlAgreement(evidence, initial) {
  const expected=evidence.window;
  return same(evidence.narrowed.snapshot.global_context.time_window_bp,expected)
    && same(evidence.point.snapshot.global_context.time_window_bp,[expected[0],expected[0]])
    && evidence.refusal.valid===true && evidence.refusal.detail.startsWith('Edit not applied.')
    && same(evidence.refusal.visible_window,evidence.afterRefusal.snapshot.global_context.time_window_bp)
    && evidence.afterRefusal.exported.sha256===evidence.url.exported.sha256
    && evidence.restored.exported.sha256===initial.exported.sha256
    && (evidence.point_only ? same(expected,evidence.extent)
      : !same(expected,evidence.extent) && evidence.narrowed.exported.sha256!==initial.exported.sha256);
}

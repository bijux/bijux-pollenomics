import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';

export const NATIVE_LRA_REQUIRED_ASSERTIONS = Object.freeze([
  'capture_api_ready', 'candidate_identity', 'keyless_provider_policy',
  'native_view_identity', 'native_selection_agreement', 'native_empty_selection',
  'native_unknown_selection_refused', 'native_url_roundtrip',
  'native_native_units_and_missingness', 'native_model_cues',
  'native_download_integrity', 'native_keyboard_controls',
  'native_global_context', 'native_stale_url_refused',
  'responsive_1440', 'responsive_1024', 'responsive_768', 'responsive_390',
  'basemap_discoverability', 'help_dialog_accessible',
  'reduced_motion_manual_navigation', 'no_basemap_zero_tile_requests',
  'provider_failure_osm_terrain_none', 'provider_failure_evidence_unchanged',
  'runtime_console_clean', 'receipt_inventory_complete',
]);

function digest(text) {
  return createHash('sha256').update(text).digest('hex');
}

function same(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function ids(rows) {
  return rows.map((row) => row.row_id).sort();
}

export function selectionAgreement(view, observation, expectedViewSha256) {
  const { snapshot, exported, dom } = observation;
  if (!snapshot || !exported || !dom || typeof exported.bytes !== 'string') return false;
  let decoded;
  try { decoded = JSON.parse(exported.bytes); } catch { return false; }
  if (digest(exported.bytes) !== exported.sha256 || !same(decoded, exported.payload)
    || exported.bytes!==JSON.stringify(decoded)+'\n') return false;
  const stateFields=['view_sha256','product_manifest_sha256','geometry_sha256','selection','global_context',
    'selected_row_ids','mapped_anchor_ids','counts','rows','sites','refusal','temporal_refusal_policy'];
  const metadata={schema_version:'lra-selected-estimates.v1',serialization:'ECMAScript JSON.stringify + LF; UTF-8',
    request_sha256:view.request_sha256,scientific_content_sha256:view.scientific_content_sha256,
    data_kind:view.data_kind,operation:view.operation,method:view.method,
    scientific_acceptance:'not_evaluated',publication_authorized:false,
    uncertainty_omissions:view.uncertainty_omissions,exclusions:view.exclusions};
  if(!same(Object.keys(snapshot).sort(),[...stateFields].sort())
    || !same(Object.keys(decoded).sort(),[...stateFields,...Object.keys(metadata)].sort())
    || stateFields.some(key=>!same(snapshot[key],decoded[key]))
    || Object.entries(metadata).some(([key,value])=>value===undefined || !same(decoded[key],value))
    || typeof expectedViewSha256!=='string' || !/^[0-9a-f]{64}$/.test(expectedViewSha256)
    || snapshot.view_sha256!==expectedViewSha256
    || snapshot.product_manifest_sha256!==view.product_manifest_sha256
    || snapshot.geometry_sha256!==view.geometry_sha256 || snapshot.refusal!==null
    || snapshot.temporal_refusal_policy!=='geometry-refused rows retained; global map time/layers apply only to admitted anchors') return false;
  const selection = snapshot.selection;
  const fields={roles:'role',site_ids:'site_id',taxa:'taxon',bin_ids:'bin_id'};
  if (!selection || !same(Object.keys(selection).sort(),Object.keys(fields).sort())
    || Object.entries(fields).some(([key,field])=>!Array.isArray(selection[key])
      || new Set(selection[key]).size!==selection[key].length
      || selection[key].some(value=>typeof value!=='string' || !view.rows.some(row=>row[field]===value)))
    || !same(dom.selection,selection)) return false;
  const context = snapshot.global_context;
  if (!context || !same(Object.keys(context).sort(),['active_layer_keys','time_window_bp'])
    || !Array.isArray(context.time_window_bp) || context.time_window_bp.length!==2
    || context.time_window_bp.some(value=>typeof value!=='number' || !Number.isFinite(value) || value<0)
    || context.time_window_bp[0]>context.time_window_bp[1]
    || !Array.isArray(context.active_layer_keys)
    || context.active_layer_keys.some(value=>typeof value!=='string')
    || new Set(context.active_layer_keys).size!==context.active_layer_keys.length) return false;
  const expected = view.rows.filter((row) => selection.roles.includes(row.role)
    && selection.site_ids.includes(row.site_id) && selection.taxa.includes(row.taxon)
    && selection.bin_ids.includes(row.bin_id)).filter(row => {
      const site = view.sites.find(item=>item.model_row_ids.includes(row.row_id));
      return site && (site.map_status==='refused' || (context.active_layer_keys.includes(site.layer_key)
        && row.declared_bin.younger_bp<=context.time_window_bp[1] && row.declared_bin.older_bp>=context.time_window_bp[0]));
    });
  const rows = exported.payload.rows;
  if (!Array.isArray(rows) || !same(ids(rows), ids(expected))
      || !same([...snapshot.selected_row_ids].sort(), ids(expected))
      || !same(dom.rows.map((row) => row.row_id).sort(), ids(expected))) return false;
  const selectedIds=new Set(ids(expected));
  const selectedSites=view.sites.filter(site=>site.model_row_ids.some(id=>selectedIds.has(id)));
  const expectedAnchors=selectedSites.filter(site=>site.map_status==='synthetic_anchor').map(site=>site.anchor_id).sort();
  if(!Array.isArray(snapshot.mapped_anchor_ids) || !Array.isArray(snapshot.rows) || !Array.isArray(snapshot.sites)
      || !same(snapshot.rows,expected) || !same(snapshot.sites,selectedSites)
      || !Array.isArray(dom.model_cues) || !same(dom.model_cues.map(cue=>cue.anchor_id).sort(),expectedAnchors)
      || dom.model_cues.some(cue=>{
        const site=selectedSites.find(site=>site.anchor_id===cue.anchor_id);
        return !site || cue.role!==site.role || cue.text.trim()!==(site.role==='regional'?'R':'L');
      })
      || !same([...snapshot.mapped_anchor_ids].sort(),expectedAnchors)
      || snapshot.counts.selected_rows!==expected.length
      || snapshot.counts.mapped_anchors!==expectedAnchors.length
      || snapshot.counts.refused_sites!==selectedSites.filter(site=>site.map_status==='refused').length
      || snapshot.counts.missing_values!==expected.filter(row=>row.native_value===null).length) return false;
  return rows.every((row) => {
    const original = expected.find((item) => item.row_id === row.row_id);
    const rendered = dom.rows.find((item) => item.row_id === row.row_id);
    return same(row, original) && rendered.value === (row.native_value === null ? '' : row.native_value)
      && ['role','site_id','taxon','statistic'].every(key=>rendered[key]===row[key])
      && rendered.missing === String(row.native_value === null)
      && (row.native_value === null ? rendered.visible_value.startsWith('N/A') : rendered.visible_value===row.native_value)
      && rendered.unit === row.native_unit && rendered.visible_unit === row.native_unit;
  });
}

async function observe(cdp, evaluate) {
  return evaluate(cdp, `(async () => {
    const api = window.__BIJUX_LRA_VIEW__;
    if (!api) throw new Error('Native LRA controller unavailable');
    await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
    return {
      snapshot: api.snapshot(), exported: await api.exportSelection(),
      capture: globalThis.BijuxPollenomicsAtlasCapture.snapshot(),
      hash: location.hash,
      dom: {
        selection:Object.fromEntries(Object.entries({roles:'lra-role',site_ids:'lra-site',taxa:'lra-taxon',bin_ids:'lra-bin'})
          .map(([key,id])=>[key,[...document.getElementById(id).selectedOptions].map(option=>option.value)])),
        rows: [...document.querySelectorAll('#lra-estimates tbody tr[data-row-id]')].map(row => ({
          row_id: row.dataset.rowId,
          role:row.cells[0]?.textContent,site_id:row.cells[1]?.textContent,
          taxon:row.cells[2]?.textContent,statistic:row.cells[3]?.textContent,
          value: row.dataset.nativeValue, unit: row.dataset.nativeUnit, missing: row.dataset.missing,
          visible_value: row.cells[4]?.textContent, visible_unit: row.cells[5]?.textContent,
        })),
        status: document.getElementById('lra-selection-status')?.textContent,
        model_cues: [...document.querySelectorAll('.leaflet-marker-icon [data-lra-role]')].map(node => ({
          role: node.dataset.lraRole, text: node.textContent, anchor_id:node.dataset.lraAnchorId,
        })),
      },
    };
  })()`);
}

async function select(cdp, selection, evaluate) {
  await evaluate(cdp, `(async () => {
    await window.__BIJUX_LRA_VIEW__.setSelection(${JSON.stringify(selection)});
    await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
  })()`);
  return observe(cdp, evaluate);
}

async function nativeLayout(cdp, width, evaluate) {
  return evaluate(cdp, `(async () => {
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const controls = document.getElementById('lra-controls');
    const sidebar = document.getElementById('sidebar');
    if (sidebar?.classList.contains('is-collapsed')) document.getElementById('panel-toggle')?.click();
    await Promise.all(sidebar.getAnimations().map(animation => animation.finished));
    if (controls?.tagName === 'DETAILS') controls.open = true;
    controls?.scrollIntoView({block:'nearest'});
    const ids = ['lra-role','lra-site','lra-taxon','lra-bin','lra-download'];
    const values = ids.map(id => {
      const node = document.getElementById(id);
      if (!node) return {id, present:false};
      node.scrollIntoView({block:'nearest'});
      node.focus();
      const box = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      const hit=document.elementFromPoint(box.left+box.width/2,box.top+box.height/2);
      return {id, present:true, focused:document.activeElement === node,
        visible:style.display !== 'none' && style.visibility !== 'hidden' && box.width > 0 && box.height > 0,
        bounded:box.left >= 0 && box.right <= innerWidth + 1 && box.top>=0 && box.bottom<=innerHeight+1,
        uncovered:hit===node || node.contains(hit),
        labeled:!!(node.labels?.length || node.getAttribute('aria-label') || node.textContent.trim())};
    });
    const mapBox=document.getElementById('map').getBoundingClientRect();
    return {width:${width}, values, no_horizontal_overflow:document.body.scrollWidth <= innerWidth + 1,
      document_scroll_x:scrollX,document_scroll_y:scrollY,inside_scroller:sidebar.querySelector('.control-panel-body').contains(controls),
      viewport:{width:innerWidth,height:innerHeight},map_box:mapBox.toJSON(),
      map_bounded:mapBox.top>=0 && mapBox.left>=0 && mapBox.bottom<=innerHeight+1 && mapBox.right<=innerWidth+1};
  })()`);
}

export async function verifyNativeLraScope(scope, debuggerOrigin, service) {
  const { repositoryRoot, artifactRoot, candidate, openAtlas, closeAtlas, captureReady,
    evaluate, screenshot, writeScenario, pageFacts, basemapDiscoverabilityFacts,
    helpDialogFacts, helpDialogPasses, waitForProviderRefusal } = service;
  const receipts = [];
  const scenarios = [];
  const folder = join(repositoryRoot, dirname(scope.document));
  const viewBytes = await readFile(join(folder, 'native-view.json'), 'utf8');
  const view = JSON.parse(viewBytes);
  const presentation = JSON.parse(await readFile(join(folder, 'manifest.json'), 'utf8'));
  const agrees = observation => selectionAgreement(view,observation,presentation.native_view_sha256);
  const normal = await openAtlas(scope, debuggerOrigin, {name:'native-normal', hash:'#basemap=none'});
  const ready = await captureReady(normal.cdp);
  const page = await pageFacts(normal.cdp);
  const initial = await observe(normal.cdp, evaluate);
  const served = await evaluate(normal.cdp, `(async () => {
    const responses=await Promise.all(['manifest.json','native-view.json',${JSON.stringify(scope.manifest.split('/').at(-1))}].map(path=>fetch(path)));
    if(responses.some(response=>!response.ok)) throw Error('Presentation identity download unavailable');
    return Promise.all(responses.map(response=>response.text()));
  })()`);
  await evaluate(normal.cdp, `(async () => {
    const control=document.getElementById('lra-role');
    [...control.options].forEach((option,index)=>{option.selected=index===0;});
    control.dispatchEvent(new Event('change',{bubbles:true}));
    await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
  })()`);
  const userSelection=await observe(normal.cdp,evaluate);
  const selections = [];
  for (const [key, values] of Object.entries(initial.snapshot.selection)) {
    if (!['roles','site_ids','taxa','bin_ids'].includes(key)) continue;
    for (const value of values) {
      selections.push(await select(normal.cdp, {...initial.snapshot.selection, [key]:[value]}, evaluate));
    }
  }
  const empty = await select(normal.cdp, {...initial.snapshot.selection, taxa:[]}, evaluate);
  await select(normal.cdp, initial.snapshot.selection, evaluate);
  const invalid = await evaluate(normal.cdp, `(async () => {
    const api=window.__BIJUX_LRA_VIEW__, before=JSON.stringify(api.snapshot().selection);
    try { await api.setSelection({...api.snapshot().selection, taxa:['unknown-native-taxon']}); return {refused:false}; }
    catch(error) { let exportRefused=false;try{await api.exportSelection();}catch{exportRefused=true;}
      return {refused:true, unchanged_selection:JSON.stringify(api.snapshot().selection)===before,
        empty:api.snapshot().selected_row_ids.length===0, export_refused:exportRefused,
        disabled:document.getElementById('lra-download').disabled, detail:error.message}; }
  })()`);
  await select(normal.cdp,initial.snapshot.selection,evaluate);
  const layerKey=view.sites.find(site=>site.map_status==='synthetic_anchor').layer_key;
  await evaluate(normal.cdp, `(async () => {
    const node=[...document.querySelectorAll('.layer-checkbox')].find(node=>node.value===${JSON.stringify(layerKey)});
    if(!node || !node.checked) throw Error('Native layer checkbox unavailable');
    node.click(); await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
  })()`);
  const hiddenLayer=await observe(normal.cdp,evaluate);
  await evaluate(normal.cdp, `(async () => {
    [...document.querySelectorAll('.layer-checkbox')].find(node=>node.value===${JSON.stringify(layerKey)}).click();
    await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
  })()`);
  await evaluate(normal.cdp, `(async () => {
    const interval=document.getElementById('time-interval-slider');
    interval.value='1'; interval.dispatchEvent(new Event('input',{bubbles:true}));
    await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
    const start=document.getElementById('time-start-slider');
    start.value=start.max; start.dispatchEvent(new Event('input',{bubbles:true}));
    await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
  })()`);
  const narrowedTime=await observe(normal.cdp,evaluate);
  await evaluate(normal.cdp, `(async () => {
    document.querySelector('[data-time-interval="full"]').click();
    await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
  })()`);
  const restoredContext=await observe(normal.cdp,evaluate);
  const downloaded = await evaluate(normal.cdp, `(async () => {
    const original=URL.createObjectURL;
    let timeout;
    const observed=new Promise((resolve,reject)=>{
      timeout=setTimeout(()=>reject(Error('Native download button produced no blob')),5000);
      URL.createObjectURL=blob=>{clearTimeout(timeout);blob.text().then(resolve,reject);return original.call(URL,blob);};
    });
    try{document.getElementById('lra-download').click();return await observed;}
    finally{clearTimeout(timeout);URL.createObjectURL=original;}
  })()`);
  const layouts = {};
  for (const width of [1440,1024,768,390]) {
    await normal.cdp.send('Emulation.setDeviceMetricsOverride', {width, height:width===390?844:1000, deviceScaleFactor:1, mobile:width===390});
    layouts[width] = await nativeLayout(normal.cdp,width,evaluate);
    layouts[width].basemap = await basemapDiscoverabilityFacts(normal.cdp,width);
    layouts[width].help = await helpDialogFacts(normal.cdp,width);
    await nativeLayout(normal.cdp,width,evaluate);
    await evaluate(normal.cdp,"document.querySelector('.control-panel-body').scrollTop=0;document.querySelector('.control-panel-card').scrollTop=0;document.getElementById('lra-role').focus({preventScroll:true})");
    const path=`${scope.name}/native-responsive-${width}.png`;
    await screenshot(normal.cdp,path); receipts.push(path);
  }
  await normal.cdp.send('Emulation.setDeviceMetricsOverride', {width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await evaluate(normal.cdp,"document.getElementById('lra-role').focus()");
  const keyboard=[];
  for(const expected of ['lra-site','lra-taxon','lra-bin']) {
    await normal.cdp.send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    await normal.cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    keyboard.push({expected,actual:await evaluate(normal.cdp,'document.activeElement?.id')});
  }
  const selected = selections.find(item => item.snapshot.selected_row_ids.length > 0
    && item.snapshot.selected_row_ids.length < initial.snapshot.selected_row_ids.length);
  if (!selected) throw new Error('Native browser fixture needs a nonempty proper subset');
  const roundtripSource = await select(normal.cdp, selected.snapshot.selection, evaluate);
  const restored = await openAtlas(scope,debuggerOrigin,{name:'native-url',hash:roundtripSource.hash});
  await captureReady(restored.cdp);
  const roundtrip = await observe(restored.cdp,evaluate);
  await closeAtlas(restored,debuggerOrigin);
  const result = {
    scope:scope.name, name:'native-selection-and-responsive', initial,userSelection,selections,empty,invalid,layouts,roundtrip,hiddenLayer,narrowedTime,restoredContext,keyboard,
    runtime_failures:normal.runtimeFailures,
    assertions:{
      capture_api_ready:ready.ready===true && ready.capture_api_version==='atlas-capture.v1',
      candidate_identity:ready.build_id===candidate.build_id && ready.scope_slug===scope.name,
      keyless_provider_policy:page.api_key_sentinel_absent && page.carto_absent && page.osm_resource_present,
      native_view_identity:digest(viewBytes)===presentation.native_view_sha256
        && served[1]===viewBytes && digest(served[0])===digest(await readFile(join(folder,'manifest.json'),'utf8'))
        && initial.snapshot.view_sha256===presentation.native_view_sha256
        && initial.snapshot.product_manifest_sha256===presentation.product_manifest_sha256
        && initial.snapshot.geometry_sha256===presentation.display_geometry_sha256,
      native_selection_agreement:[initial,userSelection,...selections].every(item=>agrees(item))
        && userSelection.snapshot.selection.roles.length===1
        && userSelection.snapshot.selected_row_ids.length>0
        && userSelection.snapshot.selected_row_ids.length<initial.snapshot.selected_row_ids.length,
      native_empty_selection:agrees(empty) && empty.snapshot.selected_row_ids.length===0
        && empty.capture.visible_point_count===0 && empty.snapshot.mapped_anchor_ids.length===0,
      native_unknown_selection_refused:invalid.refused===true && invalid.unchanged_selection===true
        && invalid.empty===true && invalid.export_refused===true && invalid.disabled===true,
      native_url_roundtrip:same(roundtrip.snapshot.selection,roundtripSource.snapshot.selection)
        && roundtrip.exported.sha256===roundtripSource.exported.sha256 && agrees(roundtrip),
      native_native_units_and_missingness:agrees(initial)
        && view.rows.some(row=>row.native_unit==='fraction') && view.rows.some(row=>row.native_unit==='percent')
        && view.rows.some(row=>row.native_value===null) && initial.snapshot.counts.missing_values>0,
      native_model_cues:initial.dom.model_cues.length>0 && initial.dom.model_cues.every(row=>
        row.text.trim()===(row.role==='regional'?'R':row.role==='local'?'L':'INVALID'))
        && same(initial.dom.model_cues.map(row=>row.anchor_id).sort(),[...initial.snapshot.mapped_anchor_ids].sort()),
      native_download_integrity:downloaded===initial.exported.bytes
        && [initial,...selections,empty].every(item=>digest(item.exported.bytes)===item.exported.sha256),
      native_keyboard_controls:keyboard.every(row=>row.actual===row.expected)
        && Object.values(layouts).every(layout=>layout.values.every(row=>row.present&&row.focused&&row.labeled)),
      native_global_context:agrees(hiddenLayer)
        && !hiddenLayer.snapshot.global_context.active_layer_keys.includes(layerKey)
        && hiddenLayer.snapshot.selected_row_ids.length<initial.snapshot.selected_row_ids.length
        && hiddenLayer.capture.visible_point_count===hiddenLayer.snapshot.mapped_anchor_ids.length
        && agrees(narrowedTime)
        && !same(narrowedTime.snapshot.global_context.time_window_bp,initial.snapshot.global_context.time_window_bp)
        && narrowedTime.exported.sha256!==initial.exported.sha256
        && restoredContext.exported.sha256===initial.exported.sha256,
      responsive_1440:layoutPasses(layouts[1440]), responsive_1024:layoutPasses(layouts[1024]),
      responsive_768:layoutPasses(layouts[768]), responsive_390:layoutPasses(layouts[390]),
      basemap_discoverability:Object.values(layouts).every(layout=>layout.basemap.status_visible
        && layout.basemap.controls_opened && layout.basemap.active_provider_focused && layout.basemap.visible_provider_disclosure),
      help_dialog_accessible:[layouts[1440],layouts[390]].every(layout=>helpDialogPasses(layout.help)),
      no_basemap_zero_tile_requests:initial.capture.basemap==='none' && normal.providerRequests.length===0,
      runtime_console_clean:normal.runtimeFailures.length===0,
    },
  };
  await closeAtlas(normal,debuggerOrigin);
  await writeScenario(scope,result,receipts); scenarios.push(result);
  const staleHash=new URLSearchParams(roundtripSource.hash.slice(1));
  staleHash.set('lra_view','0'.repeat(64));
  const stale=await openAtlas(scope,debuggerOrigin,{name:'native-stale-url',hash:'#'+staleHash.toString()});
  await captureReady(stale.cdp);
  const staleState=await evaluate(stale.cdp, `(async () => {
    const api=window.__BIJUX_LRA_VIEW__;let refused=false;
    try{await api.exportSelection();}catch{refused=true;}
    return {snapshot:api.snapshot(),export_refused:refused,
      download_disabled:document.getElementById('lra-download').disabled,
      visible_refusal:document.getElementById('lra-selection-status').getAttribute('role')==='alert'};
  })()`);
  const staleResult={scope:scope.name,name:'native-stale-url',observation:staleState,assertions:{
    native_stale_url_refused:staleState.export_refused && staleState.download_disabled && staleState.visible_refusal
      && staleState.snapshot.selected_row_ids.length===0 && Boolean(staleState.snapshot.refusal),
    runtime_console_clean:stale.runtimeFailures.length===0,
  }};
  await closeAtlas(stale,debuggerOrigin);await writeScenario(scope,staleResult,receipts);scenarios.push(staleResult);
  const reduced=await openAtlas(scope,debuggerOrigin,{name:'native-reduced',hash:'#basemap=none',reducedMotion:true});
  await captureReady(reduced.cdp);
  const reducedBefore=await observe(reduced.cdp,evaluate);
  const reducedAfter=await select(reduced.cdp,selected.snapshot.selection,evaluate);
  const reducedPreference=await evaluate(reduced.cdp,"matchMedia('(prefers-reduced-motion: reduce)').matches");
  const reducedResult={scope:scope.name,name:'native-reduced',before:reducedBefore,after:reducedAfter,assertions:{
    reduced_motion_manual_navigation:reducedPreference===true && agrees(reducedAfter)
      && !same(reducedBefore.snapshot.selected_row_ids,reducedAfter.snapshot.selected_row_ids),
    runtime_console_clean:reduced.runtimeFailures.length===0,
  }};
  await closeAtlas(reduced,debuggerOrigin); await writeScenario(scope,reducedResult,receipts); scenarios.push(reducedResult);
  const failure=await openAtlas(scope,debuggerOrigin,{name:'native-provider-failure',hash:'#basemap=street',blockProviders:true});
  const failureObserved=await waitForProviderRefusal(failure.cdp);
  const afterFailure=await observe(failure.cdp,evaluate);
  const failureDom=await pageFacts(failure.cdp);
  await closeAtlas(failure,debuggerOrigin);
  const providerResult={scope:scope.name,name:'native-provider-failure',observation:failureObserved,after:afterFailure,
    requests:failure.providerRequests,runtime_failures:failure.runtimeFailures,dom:failureDom,assertions:{
      provider_failure_osm_terrain_none:!failureObserved.timed_out && afterFailure.capture.basemap==='none'
        && failure.providerRequests.some(row=>row.url.includes('tile.openstreetmap.org'))
        && failure.providerRequests.some(row=>row.url.includes('tile.opentopomap.org'))
        && failure.providerRequests.findIndex(row=>row.url.includes('tile.openstreetmap.org'))
          < failure.providerRequests.findIndex(row=>row.url.includes('tile.opentopomap.org'))
        && /unavailable|no basemap/i.test(failureDom.basemap_readout),
      provider_failure_evidence_unchanged:afterFailure.exported.sha256===initial.exported.sha256,
      runtime_console_clean:failure.runtimeFailures.length===0,
    }};
  await writeScenario(scope,providerResult,receipts); scenarios.push(providerResult);
  const complete=await Promise.all(receipts.map(async path=>{
    try{return (await readFile(join(artifactRoot,path))).length>0;}catch{return false;}
  }));
  scenarios.push({scope:scope.name,name:'native-receipt-inventory',assertions:{receipt_inventory_complete:complete.length>0&&complete.every(Boolean)}});
  return {scenarios,receipts};
}

export function layoutPasses(layout) {
  return layout.no_horizontal_overflow && layout.document_scroll_x===0 && layout.document_scroll_y===0 && layout.inside_scroller && layout.map_bounded
    && layout.values.every(row=>row.present&&row.visible&&row.bounded&&row.uncovered&&row.labeled);
}

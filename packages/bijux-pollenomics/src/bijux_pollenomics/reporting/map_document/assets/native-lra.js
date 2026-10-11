/* Native model selection in the shared atlas. No numerical engine or second map. */
function nativeCalendarNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER;
}
function nativeCalendarSame(left,right) {
  if (left === right) return true;
  if (!left || !right || typeof left !== 'object' || typeof right !== 'object' || Array.isArray(left) !== Array.isArray(right)) return false;
  const keys=Object.keys(left).sort();
  return keys.join() === Object.keys(right).sort().join() && keys.every(key=>nativeCalendarSame(left[key],right[key]));
}
function nativeCalendarSupport(value, kind) {
  const fields = ['profile','axis','source_age_type','original_source_age_type','support_kind','younger_bp','older_bp','younger_inclusive','older_inclusive','calibration_status','calibration_evidence','native_calendar_label','native_calendar_convention'];
  if (!value || typeof value !== 'object' || Array.isArray(value)
      || Object.keys(value).sort().join() !== fields.sort().join()
      || value.profile !== 'calendar-bp1950-signed.v1' || value.axis !== 'BP1950'
      || value.source_age_type !== 'calendar_bp' || value.original_source_age_type !== 'calendar_bp'
      || value.support_kind !== kind || value.younger_inclusive !== true || value.older_inclusive !== true
      || value.calibration_status !== 'not_recorded_in_saved_request' || value.calibration_evidence !== null
      || value.native_calendar_label !== null || value.native_calendar_convention !== null
      || !nativeCalendarNumber(value.younger_bp) || !nativeCalendarNumber(value.older_bp)
      || value.younger_bp > value.older_bp) throw Error('Invalid declared synthetic calendar support.');
  return [value.younger_bp, value.older_bp];
}
function nativeSignedCalendarView(view) {
  if (view.schema_version === 'lra-atlas-view.v1') {
    if ('temporal_profile' in view || 'temporal_axis' in view) throw Error('Legacy native view cannot declare signed chronology.');
    return false;
  }
  if (view.schema_version !== 'lra-atlas-view.v2' || view.temporal_profile !== 'calendar-bp1950-signed.v1'
      || view.temporal_axis !== 'BP1950' || view.data_kind !== 'synthetic' || view.operation !== 'lra'
      || !Array.isArray(view.rows)) throw Error('Unsupported native calendar view.');
  if (!Array.isArray(view.sites) || view.sites.length !== 2
      || ['regional','local'].some(role => view.sites.filter(site => site.role === role).length !== 1)
      || view.sites[0].site_id === view.sites[1].site_id || view.rows.length === 0) throw Error('Signed native view requires one site per paired role.');
  const roleSamples = new Map(), roleSupports = new Map();
  const firstBin = view.rows[0].declared_bin;
  const firstDeclared = view.rows[0].declared_calendar_support;
  view.rows.forEach(row => {
    const source = nativeCalendarSupport(row.source_calendar_support, 'closed_age_support');
    const declared = nativeCalendarSupport(row.declared_calendar_support, 'declared_stationarity_envelope');
    if (!['regional','local'].includes(row.role) || typeof row.sample_id !== 'string' || !row.sample_id
        || row.site_id !== view.sites.find(site => site.role === row.role).site_id
        || Object.keys(row.declared_bin).sort().join() !== 'bin_id,older_bp,younger_bp' || row.declared_bin.bin_id !== row.bin_id
        || !nativeCalendarSame(row.declared_bin,firstBin) || !nativeCalendarSame(row.declared_calendar_support,firstDeclared)
        || row.age_type !== 'calendar_bp' || JSON.stringify(row.age_support_bp) !== JSON.stringify([source])
        || row.declared_bin.younger_bp !== declared[0] || row.declared_bin.older_bp !== declared[1]
        || source[0] < declared[0] || source[1] > declared[1]) throw Error('Native calendar support differs from saved request.');
    if ((roleSamples.has(row.role) && roleSamples.get(row.role) !== row.sample_id)
        || (roleSupports.has(row.role) && !nativeCalendarSame(roleSupports.get(row.role),row.source_calendar_support))) throw Error('Signed role has more than one sample/support.');
    roleSamples.set(row.role,row.sample_id);roleSupports.set(row.role,row.source_calendar_support);
  });
  if (roleSamples.size !== 2 || new Set(roleSamples.values()).size !== 2) throw Error('Signed paired samples are incomplete or duplicated.');
  return true;
}
function createSignedNativeTimeState(extent, viewSha256) {
  const keys = ['calendar_younger','calendar_older','calendar_profile','calendar_view'];
  function validate(window) {
    if (!Array.isArray(window) || window.length !== 2 || window.some(value => !nativeCalendarNumber(value))
        || window[0] > window[1] || window[1] - window[0] > Number.MAX_SAFE_INTEGER
        || window[0] < extent[0] || window[1] > extent[1]) throw Error('Select ordered Calendar BP bounds inside the available extent.');
  }
  validate(extent);
  let selected = [...extent];
  function set(window) { validate(window); selected = [...window]; return [...selected]; }
  function restore(params) {
    if (params.has('time_start') || params.has('time_interval')) throw Error('Legacy time URL cannot select a signed calendar window.');
    if (![...keys,'lra_view','lra_selection'].some(key => params.has(key))) return;
    if (keys.some(key => params.getAll(key).length !== 1)
        || params.get('calendar_profile') !== 'calendar-bp1950-signed.v1'
        || params.get('calendar_view') !== viewSha256) throw Error('Calendar URL profile or view identity differs.');
    const window = keys.slice(0,2).map(key => {
      const raw = params.get(key), value = Number(raw);
      if (raw === null || !nativeCalendarNumber(value) || String(value) !== raw) throw Error('Calendar URL requires exact canonical endpoints.');
      return value;
    });
    set(window);
  }
  function write(params) {
    params.set(keys[0], String(selected[0])); params.set(keys[1], String(selected[1]));
    params.set(keys[2], 'calendar-bp1950-signed.v1'); params.set(keys[3], viewSha256);
  }
  return Object.freeze({window: () => [...selected], set, restore, write, extent: () => [...extent]});
}
function mountSignedNativeTimeControls(state, changed) {
  const root = document.getElementById('time-controls');
  root.querySelector('.dock-range-stack').hidden = true;
  root.querySelector('.dock-presets').hidden = true;
  root.querySelectorAll('.control-group-body > .search-meta:not(#time-record-count)').forEach(node => {node.hidden = true;});
  ['time-step-older','time-step-newer','time-playback-toggle'].forEach(id => {const node=document.getElementById(id);node.hidden=true;node.disabled=true;});
  const description=document.createElement('p');
  description.textContent='Calendar BP (1950 = 0). Choose younger and older bounds, including a single instant. Synthetic source-age support and the declared stationarity envelope remain separate in the model details.';
  description.id='calendar-window-description';
  const group=document.createElement('div');group.className='dock-range-stack';
  group.append(description);
  const inputs=['younger','older'].map((name,index)=>{
    const label=document.createElement('label');label.className='field-label';label.htmlFor=`calendar-${name}-input`;
    label.textContent=`${name === 'younger' ? 'Younger' : 'Older'} bound (Calendar BP)`;
    const input=document.createElement('input');input.type='number';input.step='any';input.id=label.htmlFor;
    input.min=String(state.extent()[0]);input.max=String(state.extent()[1]);
    input.setAttribute('aria-describedby',description.id);input.value=String(state.window()[index]);
    const field=document.createElement('div');field.append(label,input);group.append(field);return input;
  });
  const error=document.createElement('p');error.id='calendar-window-error';error.setAttribute('role','alert');
  const full=document.createElement('button');full.type='button';full.className='inline-button';full.id='calendar-full-extent';full.textContent='Restore full calendar extent';
  group.append(full,error);root.querySelector('.control-group-body').prepend(group);
  function refresh() {
    const window=state.window();inputs.forEach((input,index)=>{input.value=String(window[index]);});
    document.getElementById('dock-time-summary').textContent=`[${window[0]}, ${window[1]}] Calendar BP`;
    document.getElementById('time-stepper-status').textContent='Calendar bounds';
  }
  function apply(window) {
    try {state.set(window);inputs.forEach(input=>input.setCustomValidity(''));error.textContent='';refresh();changed();}
    catch(problem){inputs.forEach(input=>input.setCustomValidity(''));refresh();error.textContent=`Edit not applied. ${problem.message} The last applied calendar bounds are restored.`;}
  }
  inputs.forEach(input=>input.addEventListener('change',()=>apply(inputs.map(item=>item.valueAsNumber))));
  full.addEventListener('click',()=>apply(state.extent()));refresh();
  return Object.freeze({refresh});
}

function createNativeLraController(view, viewSha256, adapters) {
  'use strict';
  const clone = value => JSON.parse(JSON.stringify(value));
  const signed = nativeSignedCalendarView(view);
  const fields = {roles: 'role', site_ids: 'site_id', taxa: 'taxon', bin_ids: 'bin_id'};
  const sorted = values => [...values].sort((a, b) => {
    const left = Array.from(a, char => char.codePointAt(0));
    const right = Array.from(b, char => char.codePointAt(0));
    for (let i = 0; i < Math.min(left.length, right.length); i += 1) {
      if (left[i] !== right[i]) return left[i] - right[i];
    }
    return left.length - right.length;
  });
  const allowed = Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, sorted(new Set(view.rows.map(row => row[field])))]));
  let selection = clone(allowed);
  let refusal = null;
  let refusedHash = null;
  const siteByRow = new Map(view.sites.flatMap(site => site.model_row_ids.map(id => [id, site])));
  function validateSelection(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).sort().join() !== Object.keys(fields).sort().join()) throw Error('Native selection requires roles, site_ids, taxa and bin_ids.');
    return Object.fromEntries(Object.keys(fields).map(key => {
      const values = value[key];
      if (!Array.isArray(values) || values.some(item => typeof item !== 'string' || !allowed[key].includes(item)) || new Set(values).size !== values.length) throw Error(`Unknown or duplicate native selection: ${key}`);
      return [key, sorted(values)];
    }));
  }
  function current() {
    const context = clone(adapters.globalContext());
    const contextKeys = signed ? 'active_layer_keys,temporal_axis,temporal_profile,time_window_bp' : 'active_layer_keys,time_window_bp';
    if (Object.keys(context).sort().join() !== contextKeys) throw Error('Native global context is incomplete.');
    if (signed && (context.temporal_profile !== view.temporal_profile || context.temporal_axis !== view.temporal_axis)) throw Error('Native global calendar identity differs.');
    const interval = context.time_window_bp;
    if (!Array.isArray(interval) || interval.length !== 2 || interval.some(value => signed ? !nativeCalendarNumber(value) : typeof value !== 'number' || !Number.isFinite(value) || value < 0) || interval[0] > interval[1]) throw Error('Invalid native global time window.');
    if (signed && (interval[0] < view.rows[0].declared_bin.younger_bp || interval[1] > view.rows[0].declared_bin.older_bp || interval[1] - interval[0] > Number.MAX_SAFE_INTEGER)) throw Error('Native calendar selection exceeds the declared display envelope.');
    if (!Array.isArray(context.active_layer_keys) || context.active_layer_keys.some(value => typeof value !== 'string') || new Set(context.active_layer_keys).size !== context.active_layer_keys.length) throw Error('Invalid native global layers.');
    context.active_layer_keys = sorted(context.active_layer_keys);
    const rows = refusal ? [] : view.rows.filter(row => {
      if (Object.entries(fields).some(([key, field]) => !selection[key].includes(row[field]))) return false;
      const site = siteByRow.get(row.row_id);
      return site.map_status !== 'synthetic_anchor' || (context.active_layer_keys.includes(site.layer_key) && row.declared_bin.older_bp >= interval[0] && row.declared_bin.younger_bp <= interval[1]);
    });
    const ids = new Set(rows.map(row => row.row_id));
    const sites = view.sites.filter(site => site.model_row_ids.some(id => ids.has(id)));
    const anchors = sorted(sites.filter(site => site.map_status === 'synthetic_anchor').map(site => site.anchor_id));
    return {
      view_sha256: viewSha256,
      product_manifest_sha256: view.product_manifest_sha256,
      geometry_sha256: view.geometry_sha256,
      selection: clone(selection), global_context: context,
      selected_row_ids: rows.map(row => row.row_id), mapped_anchor_ids: anchors,
      counts: {selected_rows: rows.length, mapped_anchors: anchors.length, refused_sites: sites.filter(site => site.map_status === 'refused').length, missing_values: rows.filter(row => row.native_value === null).length},
      rows, sites, refusal,
      temporal_refusal_policy: 'geometry-refused rows retained; global map time/layers apply only to admitted anchors',
    };
  }
  function render() {
    if (typeof document === 'undefined') return;
    const state = current();
    const table = document.getElementById('lra-estimates');
    if (!table) return;
    const body = table.tBodies[0];
    body.replaceChildren();
    state.rows.forEach(row => {
      const tr = document.createElement('tr');
      tr.dataset.rowId = row.row_id;
      tr.dataset.nativeValue = row.native_value === null ? '' : row.native_value;
      tr.dataset.nativeUnit = row.native_unit;
      tr.dataset.missing = String(row.native_value === null);
      ['role', 'site_id', 'taxon', 'statistic', 'native_value', 'native_unit'].forEach(key => {
        const td = document.createElement('td');
        td.textContent = row[key] === null ? 'N/A (source statistic unavailable)' : String(row[key]);
        tr.append(td);
      });
      body.append(tr);
    });
    Object.entries({roles: 'lra-role', site_ids: 'lra-site', taxa: 'lra-taxon', bin_ids: 'lra-bin'}).forEach(([key, id]) => {
      [...document.getElementById(id).options].forEach(option => { option.selected = selection[key].includes(option.value); });
    });
    const status = document.getElementById('lra-selection-status');
    status.textContent = refusal || `${state.counts.selected_rows} model values · ${state.counts.mapped_anchors} display anchors · ${state.counts.refused_sites} geometry-refused sites · ${state.counts.missing_values} missing values. Global time/layers apply to admitted anchors; refused rows remain separately accounted.`;
    status.setAttribute('role', refusal ? 'alert' : 'status');
    document.getElementById('lra-download').disabled = Boolean(refusal);
  }
  function setSelection(value) {
    try { selection = validateSelection(value); refusal = null; refusedHash = null; }
    catch (error) { refusal = error.message; render(); adapters.changed(); throw error; }
    render(); adapters.changed(); return snapshot();
  }
  function snapshot() { return clone(current()); }
  async function exportSelection() {
    if (refusal) throw Error(refusal);
    const state = current();
    const payload = {
      schema_version: signed ? 'lra-selected-estimates.v2' : 'lra-selected-estimates.v1', serialization: 'ECMAScript JSON.stringify + LF; UTF-8',
      ...state, request_sha256: view.request_sha256,
      scientific_content_sha256: view.scientific_content_sha256,
      data_kind: view.data_kind, operation: view.operation, method: view.method,
      scientific_acceptance: 'not_evaluated', publication_authorized: false,
      uncertainty_omissions: view.uncertainty_omissions,
      exclusions: view.exclusions,
      ...(signed ? {temporal_profile:view.temporal_profile,temporal_axis:view.temporal_axis} : {}),
    };
    const bytes = JSON.stringify(payload) + '\n';
    return {payload: clone(payload), bytes, sha256: await adapters.sha256(bytes)};
  }
  function mount() {
    const host = document.getElementById('lra-controls');
    host.hidden = false;
    Object.entries({roles: 'lra-role', site_ids: 'lra-site', taxa: 'lra-taxon', bin_ids: 'lra-bin'}).forEach(([key, id]) => {
      const control = document.getElementById(id);
      allowed[key].forEach(value => {
        const option = document.createElement('option'); option.value = value; option.textContent = value; option.selected = true; control.append(option);
      });
      control.addEventListener('change', () => setSelection({...selection, [key]: [...control.selectedOptions].map(option => option.value)}));
    });
    document.getElementById('lra-download').addEventListener('click', async () => {
      try {
        const result = await exportSelection();
        const url = URL.createObjectURL(new Blob([result.bytes], {type: 'application/json;charset=utf-8'}));
        const link = document.createElement('a'); link.href = url; link.download = `lra-selection-${result.sha256}.json`; link.click(); URL.revokeObjectURL(url);
      } catch (error) { refusal = error.message; render(); }
    });
    render();
  }
  function restoreHash(params) {
    if (!signed && !params.has('lra_view') && !params.has('lra_selection')) return;
    try {
      if (signed) adapters.restoreTime(params);
      if (!params.has('lra_view') && !params.has('lra_selection')) return;
      if (params.getAll('lra_view').length !== 1 || params.getAll('lra_selection').length !== 1 || params.get('lra_view') !== viewSha256) throw Error('Native URL belongs to a different or ambiguous view.');
      const raw = params.get('lra_selection');
      selection = validateSelection(JSON.parse(raw));
      if (JSON.stringify(selection) !== raw) throw Error('Native URL selection must use its canonical JSON encoding.');
      refusal = null;
    } catch (error) { refusal = `Native URL refused: ${error.message}`; refusedHash = [...params.entries()].filter(([key]) => key === 'lra_view' || key === 'lra_selection' || (signed && (key.startsWith('calendar_') || key === 'time_start' || key === 'time_interval'))); }
  }
  function writeHash(params) {
    if (refusal) { if (refusedHash) refusedHash.forEach(([key, value]) => params.append(key, value)); return; }
    params.set('lra_view', viewSha256); params.set('lra_selection', JSON.stringify(selection));
    if (signed) adapters.writeTime(params);
  }
  return Object.freeze({snapshot, setSelection, exportSelection, mount, render, restoreHash, writeHash,
    anchorVisible: id => current().mapped_anchor_ids.includes(id),
    selectedRowsForAnchor: id => { const state = current(); const site = state.sites.find(item => item.anchor_id === id); return site ? state.rows.filter(row => site.model_row_ids.includes(row.row_id)) : []; },
  });
}

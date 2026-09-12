/* Native model selection in the shared atlas. No numerical engine or second map. */
function createNativeLraController(view, viewSha256, adapters) {
  'use strict';
  const clone = value => JSON.parse(JSON.stringify(value));
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
    if (Object.keys(context).sort().join() !== 'active_layer_keys,time_window_bp') throw Error('Native global context is incomplete.');
    const interval = context.time_window_bp;
    if (!Array.isArray(interval) || interval.length !== 2 || interval.some(value => typeof value !== 'number' || !Number.isFinite(value) || value < 0) || interval[0] > interval[1]) throw Error('Invalid native global time window.');
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
      schema_version: 'lra-selected-estimates.v1', serialization: 'ECMAScript JSON.stringify + LF; UTF-8',
      ...state, request_sha256: view.request_sha256,
      scientific_content_sha256: view.scientific_content_sha256,
      data_kind: view.data_kind, operation: view.operation, method: view.method,
      scientific_acceptance: 'not_evaluated', publication_authorized: false,
      uncertainty_omissions: view.uncertainty_omissions,
      exclusions: view.exclusions,
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
    if (!params.has('lra_view') && !params.has('lra_selection')) return;
    try {
      if (params.getAll('lra_view').length !== 1 || params.getAll('lra_selection').length !== 1 || params.get('lra_view') !== viewSha256) throw Error('Native URL belongs to a different or ambiguous view.');
      const raw = params.get('lra_selection');
      selection = validateSelection(JSON.parse(raw));
      if (JSON.stringify(selection) !== raw) throw Error('Native URL selection must use its canonical JSON encoding.');
      refusal = null;
    } catch (error) { refusal = `Native URL refused: ${error.message}`; refusedHash = [...params.entries()].filter(([key]) => key === 'lra_view' || key === 'lra_selection'); }
  }
  function writeHash(params) {
    if (refusal) { if (refusedHash) refusedHash.forEach(([key, value]) => params.append(key, value)); return; }
    params.set('lra_view', viewSha256); params.set('lra_selection', JSON.stringify(selection));
  }
  return Object.freeze({snapshot, setSelection, exportSelection, mount, render, restoreHash, writeHash,
    anchorVisible: id => current().mapped_anchor_ids.includes(id),
    selectedRowsForAnchor: id => { const state = current(); const site = state.sites.find(item => item.anchor_id === id); return site ? state.rows.filter(row => site.model_row_ids.includes(row.row_id)) : []; },
  });
}

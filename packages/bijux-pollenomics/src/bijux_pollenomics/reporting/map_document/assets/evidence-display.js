// Drawing choices do not select, classify or discard retained evidence.
function evidenceDisplayState(values) {
  const requested = Array.isArray(values) && values.every(value => typeof value === 'string') ? [...values] : null;
  const mode = requested === null || requested.length > 1 ? null : requested.length ? requested[0] : 'both';
  const available = ['nodes', 'edges', 'both'].includes(mode);
  const reason = available ? null : mode === 'density'
    ? 'Density is unavailable: no governed density product is supplied. Source-record concentration and modeled overlays are different products.'
    : 'Drawing mode unavailable: the shared selection must contain one known, nonempty mode.';
  return Object.freeze({values: requested === null ? null : Object.freeze(requested), mode,
    status: available ? 'available' : 'unavailable', reason});
}

function evidenceDisplayFromHash(params) {
  return evidenceDisplayState(params.getAll('display_mode'));
}

function resetEvidenceDisplay() {
  return evidenceDisplayState([]);
}

function evidenceDisplayDecision(state) {
  const current = evidenceDisplayState(state?.values);
  return {mode: current.mode, status: current.status, reason: current.reason,
    drawNodes: current.status === 'available' && current.mode !== 'edges',
    drawEdges: current.status === 'available' && current.mode !== 'nodes'};
}

function writeEvidenceDisplayHash(params, state) {
  const current = evidenceDisplayState(state?.values);
  params.delete('display_mode');
  if (current.values === null) params.append('display_mode', '');
  else current.values.forEach(value => params.append('display_mode', value));
  return params;
}

function evidenceDisplayMetadata(state) {
  const current = evidenceDisplayState(state?.values);
  return {...evidenceDisplayDecision(current), requestedValues: current.values === null ? null : [...current.values],
    scope: 'drawing_only_retained_evidence_unchanged'};
}

function renderEvidenceDisplayControls(state) {
  const current = evidenceDisplayState(state?.values), text = value => escapeHtml(String(value));
  const options = [['nodes', 'Nodes'], ['edges', 'Edges'], ['both', 'Nodes and edges'], ['density', 'Density (unavailable)']];
  const placeholder = current.mode === null || !options.some(([value]) => value === current.mode)
    ? '<option value="" selected disabled>Unavailable shared drawing mode</option>' : '';
  const detail = current.reason === null ? '' : ` ${text(current.reason)}`;
  return `<label for="evidence-display-mode">Evidence drawing mode</label><select id="evidence-display-mode" aria-describedby="evidence-display-status">${placeholder}${options.map(([value, label]) => `<option value="${value}"${current.mode === value ? ' selected' : ''}>${label}</option>`).join('')}</select><p id="evidence-display-status" role="status">Drawing only: retained records, endpoint matching, counts, detail views and data exports are unchanged. Other context layers remain separate.${detail}</p>`;
}

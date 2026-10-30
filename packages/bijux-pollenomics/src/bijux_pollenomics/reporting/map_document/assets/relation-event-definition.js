// Select supplied event definitions without estimating or reclassifying events.
function relationEventDefinitionTuple(value) {
  if (!Array.isArray(value) || value.length !== 4
    || !value.every(part => typeof part === 'string' && part.trim())
    || !['reported_positive_observation', 'derived_first_observed', 'derived_threshold_crossing'].includes(value[0])) return null;
  return value;
}
function relationEventDefinitionValue(value) {
  if (typeof value !== 'string') return null;
  try {
    const tuple = relationEventDefinitionTuple(JSON.parse(value));
    return tuple === null ? null : JSON.stringify(tuple);
  } catch { return null; }
}
function relationEventDefinitionFromHash(params) {
  const values = params.getAll('relation_event_definition');
  const value = values.length ? values[0] : null;
  return {value, invalid: values.length > 1 || (value !== null && relationEventDefinitionValue(value) === null), duplicate: values.length > 1};
}
function writeRelationEventDefinitionHash(params, state) {
  params.delete('relation_event_definition');
  if (state.value !== null) {
    params.append('relation_event_definition', state.value);
    if (state.duplicate) params.append('relation_event_definition', state.value);
  }
}
function relationEventDefinitionSelection(edges, state) {
  const result = {selected: [], catalog: [], retainedCount: Array.isArray(edges) ? edges.length : null,
    availableCount: 0, missingCount: 0, conflictingCount: 0, unavailable: false};
  if (!Array.isArray(edges)) return {...result, unavailable: true};
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const text = value => typeof value === 'string' && value.trim();
  const fields = ['event_type', 'threshold_profile_id', 'measurement_semantics_id', 'method_compatibility_key'];
  const identities = new Map(), conflicting = new Set(), ids = new Map();
  const rows = edges.map(edge => {
    const row = {edge, status: 'missing', value: null, events: []};
    if (!object(edge)) return row;
    if (text(edge.edge_id)) {
      if (ids.has(edge.edge_id)) { ids.get(edge.edge_id).status = 'conflicting'; row.status = 'conflicting'; }
      else ids.set(edge.edge_id, row);
    }
    if (!Object.hasOwn(edge, 'candidate_status')) return row;
    if (!text(edge.edge_id)) return {...row, status: 'conflicting'};
    const details = edge.relation_details;
    if (!object(details) || details.event_definition === undefined || details.event_definition === null) return row;
    if (details.basis !== 'derived_governed_evaluator_branch_explanation' || !text(edge.scenario_id)
      || details.scenario_id !== edge.scenario_id || !object(details.event_definition)) return {...row, status: 'conflicting'};
    const tuple = fields.map(key => details.event_definition[key]);
    if (tuple.some(value => value === undefined || value === null)) return row;
    if (relationEventDefinitionTuple(tuple) === null || edge.threshold_profile_id !== tuple[1]) return {...row, status: 'conflicting'};
    for (const side of ['source', 'target']) {
      const event = edge[`${side}_event`];
      if (event === undefined || event === null) return row;
      if (!object(event)) return {...row, status: 'conflicting'};
      const pairs = [['event_id', `${side}_event_id`], ['site_id', `${side}_site_id`],
        ['source_record_id', `${side}_record_id`], ['resolution', 'resolution'], ['feature_key', 'feature_key']];
      if (!pairs.every(([key, column]) => text(edge[column]) && event[key] === edge[column])) return {...row, status: 'conflicting'};
      if (!fields.every((key, index) => (index >= 2 && !Object.hasOwn(event, key)) || event[key] === tuple[index])) return {...row, status: 'conflicting'};
      const signature = JSON.stringify([...pairs.map(([key]) => event[key]), ...tuple]);
      if (identities.has(event.event_id) && identities.get(event.event_id) !== signature) conflicting.add(event.event_id);
      identities.set(event.event_id, signature);
      row.events.push(event.event_id);
    }
    if (row.status !== 'conflicting') { row.status = 'available'; row.value = JSON.stringify(tuple); }
    return row;
  });
  const catalog = new Map();
  for (const row of rows) {
    if (row.events.some(id => conflicting.has(id))) row.status = 'conflicting';
    result[`${row.status}Count`]++;
    if (row.status === 'available') catalog.set(row.value, (catalog.get(row.value) || 0) + 1);
  }
  result.catalog = [...catalog].sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0).map(([value, count]) => {
    const [type, threshold, measurement, method] = JSON.parse(value);
    return {value, count, label: `${type.replaceAll('_', ' ')}; threshold ${threshold}; measurement ${measurement}; method compatibility ${method}`};
  });
  const requested = state.value === null ? null : relationEventDefinitionValue(state.value);
  result.unavailable = state.invalid === true || state.duplicate === true || (state.value !== null && (requested === null || !catalog.has(requested)));
  result.selected = result.unavailable ? [] : rows.filter(row => requested === null || (row.status === 'available' && row.value === requested)).map(row => row.edge);
  return result;
}
function renderRelationEventDefinitionOptions(data, state) {
  const text = value => escapeHtml(String(value));
  const requested = relationEventDefinitionValue(state.value);
  return (data.unavailable ? '<option value="" selected disabled>Unavailable shared event definition</option>' : '')
    + `<option value="" ${!data.unavailable && state.value === null ? 'selected' : ''}>All retained</option>`
    + data.catalog.map(row => `<option value="${text(row.value)}" ${!data.unavailable && row.value === requested ? 'selected' : ''}>${text(row.label)} (${row.count})</option>`).join('');
}

const activeRelationEventDefinition = relationEventDefinitionFromHash(new URLSearchParams());
function resetRelationEventDefinition() {
  Object.assign(activeRelationEventDefinition, relationEventDefinitionFromHash(new URLSearchParams()));
}
function relationEventDefinitionMetadata(edges, state) {
  return {...state, unavailable: relationEventDefinitionSelection(edges, state).unavailable};
}

// Limit Leaflet primitives without changing scientific selection or exports.
function atlasEdgeIntersectsViewport(map, coordinates) {
  const [first, second] = coordinates.map((point) => map.latLngToContainerPoint(point));
  const size = map.getSize();
  if (![first.x, first.y, second.x, second.y, size.x, size.y].every(Number.isFinite) || size.x < 0 || size.y < 0) {
    throw new Error('Atlas edge rendering requires finite viewport coordinates.');
  }
  // Clip the displayed projected segment, including crossings with both ends outside.
  // Projection (including any world offset) belongs to the same map as L.polyline.
  let start = 0, end = 1;
  for (const [origin, delta, maximum] of [
    [first.x, second.x - first.x, size.x],
    [first.y, second.y - first.y, size.y],
  ]) {
    if (delta === 0) {
      if (origin < 0 || origin > maximum) return false;
    } else {
      const a = -origin / delta, b = (maximum - origin) / delta;
      start = Math.max(start, Math.min(a, b));
      end = Math.min(end, Math.max(a, b));
      if (start > end) return false;
    }
  }
  return true;
}
function atlasEdgeRenderSelection(edges, entriesByRecordId, zoom, coordinatePair, intersectsViewport) {
  if (!Number.isFinite(zoom)) throw new Error('Atlas edge rendering requires a finite zoom.');
  const limit = zoom < 5 ? 128 : zoom < 8 ? 256 : 512;
  const eligible = edges.flatMap((edge) => {
    const source = entriesByRecordId.get(String(edge.source_record_id));
    const target = entriesByRecordId.get(String(edge.target_record_id));
    if (!source || !target) return [];
    const a = coordinatePair(source.feature), b = coordinatePair(target.feature);
    if (!a || !b) return [];
    const coordinates = [a, b].map((point) => [point.latitude, point.longitude]);
    if (intersectsViewport && !intersectsViewport(coordinates)) return [];
    return [{ edge, source, target }];
  });
  // Uncapped order is retained; capped membership uses literal scientific IDs,
  // independent of publication order, locale, or analytical rank.
  const ordered = eligible.length <= limit ? eligible : [...eligible].sort((left, right) => {
    const a = String(left.edge.edge_id), b = String(right.edge.edge_id);
    return a < b ? -1 : a > b ? 1 : 0;
  });
  return { rows: ordered.slice(0, limit), viewport_count: eligible.length, limit };
}

function edgeEvidencePopupHtml(edge, signal, presentation) {
  const text = value => escapeHtml(typeof value === 'string' && value.trim() ? value : 'Unavailable');
  const number = value => typeof value === 'number' && Number.isFinite(value);
  const pair = relationEndpointPair(edge);
  function age(event) {
    if (!event || event.comparability_status !== 'comparable') return 'Unavailable (no comparable canonical event age)';
    const [younger, older] = [event.younger_bp, event.older_bp];
    if (![younger, older].every(value => number(value) && value >= 0) || younger > older) return 'Unavailable (invalid canonical event interval)';
    return `${younger === older ? younger : `${younger}–${older}`} BP`;
  }
  const directional = presentation.separator === ' → ';
  const countryPosture = Object.prototype.hasOwnProperty.call(edge, 'candidate_status') && typeof edge.cross_border === 'boolean'
    ? edge.cross_border ? 'Cross-border' : 'Domestic' : 'Country-pair posture unavailable';
  const endpoints = ['source', 'target'].map((prefix, index) => {
    const event = pair?.[index];
    const label = directional ? index === 0 ? 'Older endpoint' : 'Younger endpoint' : index === 0 ? 'Source endpoint' : 'Target endpoint';
    return `<div><strong>${label}</strong> ${text(event?.site_id)} · ${escapeHtml(age(event))}</div>`;
  }).join('');
  const distance = number(edge.distance_km_unrounded) && edge.distance_km_unrounded >= 0
    ? `${edge.distance_km_unrounded} km` : 'Unavailable';
  const [minimum, maximum] = [edge.minimum_lag_years, edge.maximum_lag_years];
  const lag = [minimum, maximum].every(number) && minimum <= maximum
    ? `${minimum} to ${maximum} years` : 'Unavailable';
  const details = edge.relation_details;
  const thresholds = details?.basis === 'derived_governed_evaluator_branch_explanation'
    && details.scenario_id === edge.scenario_id
    && [details.maximum_distance_km, details.maximum_lag_years].every(value => number(value) && value >= 0)
    ? ` · maximum distance ${details.maximum_distance_km} km; maximum lag ${details.maximum_lag_years} years` : '';
  return `<div class="popup-grid"><div><strong>${directional ? 'Candidate spatiotemporal succession' : escapeHtml(presentation.relationLabel)}</strong> ${escapeHtml(edge.edge_id)}</div><div><strong>Signal and resolution</strong> ${text(signal?.label || edge.signal_id)} · ${text(edge.resolution)}</div>${endpoints}<div><strong>Countries</strong> ${escapeHtml(countryPosture)} · ${text(edge.source_country)}${presentation.separator}${text(edge.target_country)}</div><div><strong>Distance</strong> ${escapeHtml(distance)}</div><div><strong>Directional lag bounds</strong> ${escapeHtml(lag)}</div><div><strong>Scenario</strong> ${text(edge.scenario_id)}${escapeHtml(thresholds)}</div><div><strong>Certainty / interval status</strong> ${escapeHtml(presentation.label)}</div><div><strong>Interpretation</strong> ${escapeHtml(presentation.interpretation)}</div><button type="button" class="inline-button" data-compare-edge="${escapeHtml(edge.edge_id)}">Compare evidence</button></div>`;
}

function renderRelationDetails(tab) {
  const object = (value) => value && typeof value === 'object' && !Array.isArray(value);
  const text = (value) => escapeHtml(value === undefined ? 'Unavailable (not supplied)' : value === null ? 'null (no numeric value)' : typeof value === 'object' ? JSON.stringify(value) : String(value));
  const pair = relationEndpointPair(tab), [source, target] = pair || [];
  const endpoints = pair !== null;
  const fields = [
    ['Event ID', 'event_id'], ['Source record ID', 'source_record_id'],
    ['Site ID', 'site_id'], ['Source family', 'source_family'],
    ['Source snapshot', 'source_snapshot_id'], ['Country', 'country_code'],
    ['Chronology claim ID', 'chronology_claim_id'], ['Younger BP', 'younger_bp'],
    ['Older BP', 'older_bp'], ['Comparability', 'comparability_status'],
    ['Event type', 'event_type'], ['Resolution', 'resolution'], ['Feature', 'feature_key'],
  ];
  const endpointHtml = endpoints
    ? `<div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>Canonical relation endpoints</caption><thead><tr><th scope="col">Field</th><th scope="col">Source endpoint</th><th scope="col">Target endpoint</th></tr></thead><tbody>${fields.map(([label, key]) => `<tr><th scope="row">${text(label)}</th><td>${text(source[key])}</td><td>${text(target[key])}</td></tr>`).join('')}</tbody></table></div>`
    : '<p>Canonical endpoint comparison unavailable: matching event, source record and site identities were not supplied. Map-node ages are not substituted.</p>';
  const details = tab?.relation_details;
  const ids = ['spatial_threshold', 'chronology_available', 'positive_lag_possible', 'positive_lag_certain', 'lag_within_limit_possible', 'lag_within_limit_certain'];
  const states = new Set(['pass', 'qualify', 'refuse', 'not_evaluated', 'unavailable']);
  const number = (value) => typeof value === 'number' && Number.isFinite(value);
  const supplied = endpoints && object(details)
    && details.basis === 'derived_governed_evaluator_branch_explanation'
    && typeof tab.scenario_id === 'string' && tab.scenario_id.trim() && details.scenario_id === tab.scenario_id
    && number(details.maximum_distance_km) && details.maximum_distance_km >= 0
    && number(details.maximum_lag_years) && details.maximum_lag_years >= 0
    && Array.isArray(details.predicates) && details.predicates.length === ids.length
    && details.predicates.every((row, index) => object(row) && row.predicate_id === ids[index]
      && typeof row.label === 'string' && row.label.trim() && states.has(row.status)
      && (row.observed === null || number(row.observed)) && (row.threshold === null || number(row.threshold)));
  const predicateHtml = supplied
    ? `<p>Scenario ${text(details.scenario_id)}: maximum distance ${text(details.maximum_distance_km)} km; maximum lag ${text(details.maximum_lag_years)} years. Derived governed evaluator branch explanation, not recorded execution telemetry. These supplied statuses do not confer scientific admission.</p><div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>Scenario predicates</caption><thead><tr><th scope="col">Predicate</th><th scope="col">Status</th><th scope="col">Observed value</th><th scope="col">Threshold</th></tr></thead><tbody>${details.predicates.map((row) => `<tr><th scope="row">${text(row.label)}</th><td>${text(row.status)}</td><td>${text(row.observed)}</td><td>${text(row.threshold)}</td></tr>`).join('')}</tbody></table></div><p>not_evaluated denotes a later check skipped by the evaluator branch; unavailable denotes missing evidence. Neither means pass. Endpoint lines are not reconstructed movement paths.</p>`
    : '<p>Scenario predicate explanation unavailable: this record has no complete, matching governed explanation. Legacy or missing checks are not inferred from a candidate label.</p>';
  return `<section aria-label="Relation endpoint and predicate comparison">${endpointHtml}${predicateHtml}</section>`;
}

function relationEndpointPair(tab) {
  const object = value => value && typeof value === 'object' && !Array.isArray(value);
  const source = tab?.source_event, target = tab?.target_event;
  const joined = (event, prefix) => object(event)
    && ['event_id', 'source_record_id', 'site_id'].every((key) => typeof event[key] === 'string' && event[key].trim()
      && event[key] === tab[`${prefix}_${key === 'source_record_id' ? 'record_id' : key}`]);
  return joined(source, 'source') && joined(target, 'target') ? [source, target] : null;
}


// A shared relation is restored only within its published build and exact scenario.
const edgeFocusLoadState = {request: 0, generation: 0, restoring: null};
function publishedEdgeFocusBuild() {
  const build = typeof STATIC_ATLAS_BOOTSTRAP === 'undefined' ? null : STATIC_ATLAS_BOOTSTRAP.build_id;
  return typeof build === 'string' && /^atlas-[a-f0-9]{64}$/.test(build) ? build : null;
}
function edgeFocusFromHash(params, allowedTabs) {
  const keys = ['focus_edge', 'focus_scenario', 'focus_build'];
  if (!keys.some(key => params.has(key))) return null;
  const invalid = {kind: 'edge', unavailable: true};
  if (keys.some(key => params.getAll(key).length !== 1 || !params.get(key).trim())
    || ['focus_layer', 'focus_feature', 'focus_record'].some(key => params.has(key))
    || params.getAll('focus_tab').length > 1) return invalid;
  const tab = params.get('focus_tab') || 'overview';
  if (!allowedTabs.includes(tab)) return invalid;
  return {kind: 'edge', edgeId: params.get('focus_edge'), scenarioId: params.get('focus_scenario'), atlasBuildId: params.get('focus_build'), tab};
}
function writeEdgeFocusHash(params, focus, tab, build) {
  if (focus?.kind !== 'edge' || focus.edgeShareable !== true || typeof build !== 'string'
    || !/^atlas-[a-f0-9]{64}$/.test(build) || focus.atlasBuildId !== build
    || ![focus.edgeId, focus.scenarioId].every(value => typeof value === 'string' && value.trim())) return false;
  params.set('focus_edge', focus.edgeId);
  params.set('focus_scenario', focus.scenarioId);
  params.set('focus_build', build);
  if (tab !== 'overview') params.set('focus_tab', tab);
  return true;
}
function availableEdgeFocus(edgeId, edges, entries) {
  const matches = edges.filter(edge => edge.edge_id === edgeId);
  if (matches.length !== 1) return null;
  const edge = matches[0];
  const endpoints = ['source_record_id', 'target_record_id'].map(key => entries.filter(entry => entry.feature.record_id === edge[key]));
  return endpoints.every(rows => rows.length === 1) ? {edge, source: endpoints[0][0]} : null;
}
function edgeFocusSelection(request, build, edges, entries) {
  if (!request || request.unavailable || !build || request.atlasBuildId !== build
    || ![request.edgeId, request.scenarioId].every(value => typeof value === 'string' && value.trim())) return null;
  const selected = availableEdgeFocus(request.edgeId, edges, entries);
  return selected && Object.prototype.hasOwnProperty.call(selected.edge, 'candidate_status')
    && selected.edge.scenario_id === request.scenarioId ? selected : null;
}


function relationFilterFields() {
  return [
    ['scenario', 'relation_scenario', 'scenario_id', 'scenario'],
    ['status', 'relation_status', 'candidate_status', 'candidate status'],
    ['sourceCountry', 'relation_source_country', 'source_country_code', 'stored source endpoint country'],
    ['targetCountry', 'relation_target_country', 'target_country_code', 'stored target endpoint country'],
  ];
}
function relationFiltersFromHash(params) {
  const filters = {invalid: []};
  relationFilterFields().forEach(([key, parameter]) => {
    filters[key] = params.has(parameter) ? params.get(parameter) : null;
    if (params.getAll(parameter).length > 1) filters.invalid.push(key);
  });
  return filters;
}
const activeRelationFilters = relationFiltersFromHash(new URLSearchParams());
function resetRelationFilters() {
  Object.assign(activeRelationFilters, relationFiltersFromHash(new URLSearchParams()));
}
function writeRelationFilterHash(params, filters) {
  relationFilterFields().forEach(([key, parameter]) => {
    if (filters.invalid.includes(key)) {
      params.append(parameter, filters[key]);
      params.append(parameter, filters[key]);
    } else if (filters[key] !== null) params.set(parameter, filters[key]);
  });
}
function relationFilterSelection(records, filters) {
  const fields = relationFilterFields();
  const native = records.filter(row => Object.prototype.hasOwnProperty.call(row, 'candidate_status'));
  const catalog = Object.fromEntries(fields.map(([key, , column]) => [key,
    [...new Set(native.map(row => row[column]).filter(value => typeof value === 'string' && value.trim()
      && (!['sourceCountry', 'targetCountry'].includes(key) || ['DK', 'FI', 'NO', 'SE'].includes(value))))].sort(),
  ]));
  const unavailable = fields.filter(([key]) => filters.invalid.includes(key)
    || (filters[key] !== null && !catalog[key].includes(filters[key]))).map(([key]) => key);
  const selected = unavailable.length ? [] : records.filter(row => fields.every(([key, , column]) => filters[key] === null
    || (Object.prototype.hasOwnProperty.call(row, 'candidate_status') && row[column] === filters[key])));
  return {catalog, unavailable, selected};
}
function relationFilterMetadata(records, filters) {
  return {...Object.fromEntries(relationFilterFields().map(([key]) => [key, filters[key]])),
    unavailable_fields: relationFilterSelection(records, filters).unavailable};
}
function relationFilterOptions(values, selected, unavailable, label) {
  return (unavailable ? `<option value="" selected disabled>Unavailable shared ${escapeHtml(label)}</option>` : '')
    + `<option value="" ${!unavailable && selected === null ? 'selected' : ''}>All retained</option>`
    + values.map(value => `<option value="${escapeHtml(value)}" ${!unavailable && selected === value ? 'selected' : ''}>${escapeHtml(value)}</option>`).join('');
}
function relationScenarioThresholds(records, selectedScenario) {
  const scenarios = relationFilterSelection(records, relationFiltersFromHash(new URLSearchParams())).catalog.scenario;
  const selected = selectedScenario === null ? scenarios : scenarios.filter(id => id === selectedScenario);
  if (!selected.length) return '<p>Scenario rule and thresholds unavailable.</p>';
  return selected.map(id => {
    const rows = records.filter(row => Object.prototype.hasOwnProperty.call(row, 'candidate_status') && row.scenario_id === id);
    const details = rows.map(row => row.relation_details);
    const valid = details.every(value => value && value.basis === 'derived_governed_evaluator_branch_explanation' && value.scenario_id === id
      && [value.maximum_distance_km, value.maximum_lag_years].every(number => typeof number === 'number' && Number.isFinite(number) && number >= 0));
    const consistent = valid && details.every(value => value.maximum_distance_km === details[0].maximum_distance_km && value.maximum_lag_years === details[0].maximum_lag_years);
    const rule = details[0]?.rule_type;
    const ruleLabel = typeof rule === 'string' && rule.trim() && details.every(value => value?.rule_type === rule) ? rule : 'unavailable';
    return `<p><strong>${escapeHtml(id)}</strong> · Rule: ${escapeHtml(valid ? ruleLabel : 'unavailable')} · ${consistent
      ? `maximum distance ${escapeHtml(String(details[0].maximum_distance_km))} km; maximum lag ${escapeHtml(String(details[0].maximum_lag_years))} years`
      : 'Thresholds unavailable: missing or conflicting supplied scenario metadata.'}</p>`;
  }).join('');
}

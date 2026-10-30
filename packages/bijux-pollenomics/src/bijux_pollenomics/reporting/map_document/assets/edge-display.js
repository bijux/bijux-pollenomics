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

function renderRelationDetails(tab) {
  const object = (value) => value && typeof value === 'object' && !Array.isArray(value);
  const text = (value) => escapeHtml(value === undefined ? 'Unavailable (not supplied)' : value === null ? 'null (no numeric value)' : typeof value === 'object' ? JSON.stringify(value) : String(value));
  const source = tab?.source_event, target = tab?.target_event;
  const joined = (event, prefix) => object(event)
    && ['event_id', 'source_record_id', 'site_id'].every((key) => typeof event[key] === 'string' && event[key].trim()
      && event[key] === tab[`${prefix}_${key === 'source_record_id' ? 'record_id' : key}`]);
  const endpoints = joined(source, 'source') && joined(target, 'target');
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

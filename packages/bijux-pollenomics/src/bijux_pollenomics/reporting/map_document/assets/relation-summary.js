// Counts describe supplied active relation rows, not independent events or spread.
function relationSummaryData(edges) {
  const countries = ['DK', 'FI', 'NO', 'SE'];
  const base = {sourceEdgeCount: Array.isArray(edges) ? edges.length : null, edgeCount: null, countries, partitions: []};
  const refused = reason => ({...base, status: 'refused', reason});
  if (!Array.isArray(edges)) return {...base, status: 'unavailable', reason: 'Retained relation rows were not supplied.'};
  const text = value => typeof value === 'string' && value.trim() === value && value.length > 0;
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const statuses = ['definite_candidate', 'possible_candidate', 'indeterminate_order', 'unresolved', 'excluded_spatial', 'excluded_temporal_nonpositive', 'excluded_temporal_too_large'];
  const ids = new Set(), events = new Map(), scenarios = new Map(), partitions = new Map();
  for (const edge of edges) {
    if (!object(edge) || !['edge_id', 'scenario_id', 'source_event_id', 'target_event_id', 'source_site_id', 'target_site_id', 'resolution', 'feature_key'].every(key => text(edge[key]))
      || !statuses.includes(edge.candidate_status)
      || !countries.includes(edge.source_country_code) || !countries.includes(edge.target_country_code)) return refused('Native relation identity, status or country codes are unavailable.');
    if (ids.has(edge.edge_id)) return refused('A repeated relation ID makes the retained population ambiguous.');
    ids.add(edge.edge_id);
    for (const side of ['source', 'target']) {
      const identity = [edge[`${side}_site_id`], edge[`${side}_country_code`], edge.resolution, edge.feature_key];
      const id = edge[`${side}_event_id`], previous = events.get(id);
      if (previous && JSON.stringify(previous) !== JSON.stringify(identity)) return refused('One event ID has conflicting site, country or feature identities.');
      events.set(id, identity);
      const event = edge[`${side}_event`];
      if (event !== undefined && (!object(event) || event.event_id !== id || event.site_id !== identity[0] || event.country_code !== identity[1] || event.resolution !== identity[2] || event.feature_key !== identity[3])) return refused('A relation conflicts with its supplied canonical endpoint.');
    }
    const details = edge.relation_details;
    if (details !== undefined) {
      if (!object(details) || details.scenario_id !== edge.scenario_id
        || details.basis !== 'derived_governed_evaluator_branch_explanation'
        || ![details.maximum_distance_km, details.maximum_lag_years].every(value => typeof value === 'number' && Number.isFinite(value) && value >= 0)) return refused('Supplied scenario metadata conflicts with the relation.');
      if (details.rule_type !== undefined && !text(details.rule_type)) return refused('Supplied scenario rule type is not a literal identity.');
      const definition = {distance: details.maximum_distance_km, lag: details.maximum_lag_years, rule: details.rule_type};
      const previous = scenarios.get(edge.scenario_id);
      if (previous && (previous.distance !== definition.distance || previous.lag !== definition.lag || (previous.rule !== undefined && definition.rule !== undefined && previous.rule !== definition.rule))) return refused('One scenario ID has conflicting distance, lag or rule definitions.');
      scenarios.set(edge.scenario_id, {...definition, rule: definition.rule ?? previous?.rule});
    }
    const orientation = ['definite_candidate', 'possible_candidate'].includes(edge.candidate_status) && edge.directional_arrow_allowed === true ? 'directed' : 'stored_endpoint_order';
    const key = JSON.stringify([edge.scenario_id, edge.candidate_status, orientation]);
    if (!partitions.has(key)) partitions.set(key, {scenarioId: edge.scenario_id, status: edge.candidate_status, orientation, cells: new Map()});
    const partition = partitions.get(key), cellKey = JSON.stringify([edge.source_country_code, edge.target_country_code]);
    if (!partition.cells.has(cellKey)) partition.cells.set(cellKey, {sourceCountry: edge.source_country_code, targetCountry: edge.target_country_code, edgeIds: []});
    partition.cells.get(cellKey).edgeIds.push(edge.edge_id);
  }
  const literalOrder = (left, right) => left < right ? -1 : left > right ? 1 : 0;
  const ordered = [...partitions.entries()].sort(([left], [right]) => literalOrder(left, right)).map(([, partition]) => ({
    scenarioId: partition.scenarioId, status: partition.status, orientation: partition.orientation,
    cells: [...partition.cells.entries()].sort(([left], [right]) => literalOrder(left, right)).map(([, cell]) => ({...cell, edgeIds: cell.edgeIds.sort(literalOrder)})),
  }));
  return {...base, status: 'available', reason: null, edgeCount: edges.length, partitions: ordered};
}

function renderRelationSummary(data, edgeHref = () => null, displayLimit = 25) {
  if (!Number.isSafeInteger(displayLimit) || displayLimit < 1 || displayLimit > 25) throw Error('Relation ID display limit must be an integer from 1 to 25.');
  const text = value => escapeHtml(String(value));
  if (data.status !== 'available') return `<section aria-label="Retained relation country counts"><p>Relation country summary ${text(data.status)}: ${text(data.reason)} No country matrix is inferred.</p></section>`;
  const introduction = `<p>${data.edgeCount} supplied active relations. Counts follow relation, country and signal filters before endpoint time, layer and viewport eligibility; displayed lines may be fewer. Counts are partitioned by exact scenario and candidate status; they are not independent events, migration rates or evidence of country origins. A zero cell means no supplied relation in this selection, not source absence.</p>`;
  if (!data.partitions.length) return `<section aria-label="Retained relation country counts">${introduction}<p>No retained active relation rows were supplied.</p></section>`;
  let remainingIds = displayLimit;
  const tables = data.partitions.slice(0, 25).map(partition => {
    const directed = partition.orientation === 'directed';
    const description = directed ? 'Directed source → target country counts' : 'NON-DIRECTIONAL stored first / second endpoint country counts';
    const heading = directed ? 'Source / target' : 'Stored first / second endpoint';
    const cells = new Map(partition.cells.map(cell => [JSON.stringify([cell.sourceCountry, cell.targetCountry]), cell.edgeIds]));
    const rows = data.countries.map(country => `<tr><th scope="row">${text(country)}</th>${data.countries.map(target => {
      const ids = cells.get(JSON.stringify([country, target])) || [];
      const shownIds = ids.slice(0, remainingIds);
      remainingIds -= shownIds.length;
      const links = shownIds.map(id => {
        const href = edgeHref(id, partition.scenarioId);
        const label = text(id);
        return typeof href === 'string' && href.startsWith('#') ? `<a href="${text(href)}">${label}</a>` : label;
      });
      return `<td>${ids.length}${links.length ? `<details><summary>Exact relation IDs: first ${links.length} of ${ids.length}</summary><ul>${links.map(link => `<li>${link}</li>`).join('')}</ul></details>` : ids.length ? ' · IDs omitted here; narrow filters to inspect.' : ''}</td>`;
    }).join('')}</tr>`).join('');
    return `<div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>${text(description)} · ${text(partition.scenarioId)} · ${text(partition.status)}</caption><thead><tr><th scope="col">${text(heading)}</th>${data.countries.map(country => `<th scope="col">${text(country)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }).join('');
  return `<section aria-label="Retained relation country counts">${introduction}<p>Non-directional rows retain stored endpoint order only; neither endpoint is asserted to be older or an origin. No time bins or midpoint ages are inferred. Showing the first ${Math.min(25, data.partitions.length)} of ${data.partitions.length} scenario/status/orientation tables and at most ${displayLimit} IDs in total; narrow the scenario, status, country or signal filters to inspect a smaller retained set. Full counts and IDs remain in the retained selection. Unlinked IDs lack currently loaded eligible endpoints. Zooming changes map detail, not these full active counts.</p>${tables}</section>`;
}

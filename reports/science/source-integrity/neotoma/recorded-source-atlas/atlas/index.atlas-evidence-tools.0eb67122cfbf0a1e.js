globalThis.BijuxPollenomicsEvidenceTools=function(escapeHtml,scientificCueGlyph){

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
    if (!partitions.has(key)) partitions.set(key, {scenarioId: edge.scenario_id, status: edge.candidate_status, orientation, cells: new Map(), featureScopes: new Map()});
    const partition = partitions.get(key), cellKey = JSON.stringify([edge.source_country_code, edge.target_country_code]);
    partition.featureScopes.set(JSON.stringify([edge.resolution, edge.feature_key]), {resolution: edge.resolution, featureKey: edge.feature_key});
    if (!partition.cells.has(cellKey)) partition.cells.set(cellKey, {sourceCountry: edge.source_country_code, targetCountry: edge.target_country_code, edgeIds: []});
    partition.cells.get(cellKey).edgeIds.push(edge.edge_id);
  }
  const literalOrder = (left, right) => left < right ? -1 : left > right ? 1 : 0;
  const ordered = [...partitions.entries()].sort(([left], [right]) => literalOrder(left, right)).map(([, partition]) => ({
    scenarioId: partition.scenarioId, status: partition.status, orientation: partition.orientation,
    featureScopes: [...partition.featureScopes.entries()].sort(([left], [right]) => literalOrder(left, right)).map(([, scope]) => scope),
    cells: [...partition.cells.entries()].sort(([left], [right]) => literalOrder(left, right)).map(([, cell]) => ({...cell, edgeIds: cell.edgeIds.sort(literalOrder)})),
  }));
  return {...base, status: 'available', reason: null, edgeCount: edges.length, partitions: ordered};
}

function renderRelationSummary(data, edgeHref = () => null, displayLimit = 25) {
  if (!Number.isSafeInteger(displayLimit) || displayLimit < 1 || displayLimit > 25) throw Error('Relation ID display limit must be an integer from 1 to 25.');
  const text = value => escapeHtml(String(value));
  if (data.status !== 'available') return `<section aria-label="Retained relation country counts"><p>Relation country summary ${text(data.status)}: ${text(data.reason)} No country matrix is inferred.</p></section>`;
  const introduction = `<p>${data.edgeCount} supplied active relations. Counts follow relation, country and signal filters before endpoint time, layer and viewport eligibility; displayed lines may be fewer. Counts are partitioned by exact scenario and candidate status; they are not independent events, migration rates or evidence of country origins. A zero cell means no supplied relation in this selection, not source absence. Supplied feature and resolution identities do not select an analysis chronology. Admitted, indeterminate and refused scientific-event denominators are not established here.</p>`;
  if (!data.partitions.length) return `<section aria-label="Retained relation country counts">${introduction}<p>No retained active relation rows were supplied.</p></section>`;
  let remainingIds = displayLimit;
  const tables = data.partitions.slice(0, 25).map(partition => {
    const directed = partition.orientation === 'directed';
    const description = directed ? 'Directed source → target country counts' : 'NON-DIRECTIONAL stored first / second endpoint country counts';
    const heading = directed ? 'Source / target' : 'Stored first / second endpoint';
    const scopes = partition.featureScopes.slice(0, 25).map(scope => `Resolution: <code>${text(scope.resolution)}</code>; feature: <code>${text(scope.featureKey)}</code>`);
    const omittedScopes = partition.featureScopes.length - scopes.length;
    const scopeCaption = scopes.length === 1 ? `<span style="display:block;overflow-wrap:anywhere">${scopes[0]}</span>`
      : `<details style="overflow-wrap:anywhere"><summary>Aggregated across ${partition.featureScopes.length} supplied feature-resolution pairs</summary>${omittedScopes ? `<p>Showing the first ${scopes.length} of ${partition.featureScopes.length} exact pairs. ${omittedScopes} pairs omitted here; narrow signal filters to inspect other supplied identities. The full pair set remains in the retained selection.</p>` : ''}<ul>${scopes.map(scope => `<li>${scope}</li>`).join('')}</ul></details>`;
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
    return `<div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>${text(description)} · ${text(partition.scenarioId)} · ${text(partition.status)}${scopeCaption}</caption><thead><tr><th scope="col">${text(heading)}</th>${data.countries.map(country => `<th scope="col">${text(country)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }).join('');
  return `<section aria-label="Retained relation country counts">${introduction}<p>Non-directional rows retain stored endpoint order only; neither endpoint is asserted to be older or an origin. No time bins or midpoint ages are inferred. Showing the first ${Math.min(25, data.partitions.length)} of ${data.partitions.length} scenario/status/orientation tables and at most ${displayLimit} IDs in total; narrow the scenario, status, country or signal filters to inspect a smaller retained set. Full counts and IDs remain in the retained selection. Unlinked IDs lack currently loaded eligible endpoints. Zooming changes map detail, not these full active counts.</p>${tables}</section>`;
}

      // Literal endpoint envelopes describe supplied relations, not temporal coverage.
function relationTimeSummaryData(edges) {
  const base = {sourceEdgeCount: Array.isArray(edges) ? edges.length : null, groups: []};
  const refused = reason => ({...base, status: 'refused', reason});
  if (!Array.isArray(edges)) return {...base, status: 'unavailable', reason: 'Retained relation rows were not supplied.'};
  const text = value => typeof value === 'string' && value.length > 0 && value.trim() === value;
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const fields = ['scenario_id', 'signal_id', 'resolution', 'feature_key', 'candidate_status', 'temporal_contract_version'];
  const statuses = ['definite_candidate', 'possible_candidate', 'indeterminate_order', 'unresolved', 'excluded_spatial', 'excluded_temporal_nonpositive', 'excluded_temporal_too_large'];
  const ids = new Set(), identities = new Map(), facts = new Map(), groups = new Map();
  const endpoint = () => ({events: new Set(), comparable: new Set(), unresolved: new Set(), missingEndpointCount: 0, youngerBp: null, olderBp: null});
  for (const edge of edges) {
    if (!object(edge) || !text(edge.edge_id) || !fields.every(key => text(edge[key]))
      || !statuses.includes(edge.candidate_status)) return refused('Native relation or grouping identities are unavailable.');
    if (ids.has(edge.edge_id)) return refused('A repeated relation ID makes the retained population ambiguous.');
    ids.add(edge.edge_id);
    if (edge.temporal_contract_version !== '1.0.0') return refused('Unknown or mixed temporal contracts cannot form a numeric BP envelope.');
    const key = JSON.stringify(fields.map(name => edge[name]));
    if (!groups.has(key)) groups.set(key, {...Object.fromEntries(fields.map(name => [name, edge[name]])), edgeCount: 0, events: new Set(), source: endpoint(), target: endpoint()});
    const group = groups.get(key);
    group.edgeCount++;
    for (const side of ['source', 'target']) {
      const id = edge[`${side}_event_id`];
      const identity = [edge[`${side}_site_id`], edge[`${side}_record_id`], edge.resolution, edge.feature_key];
      if (!text(id) || !identity.every(text)) return refused('Exact endpoint event, site, record and feature identities are required.');
      const encoded = JSON.stringify(identity);
      if (identities.has(id) && identities.get(id) !== encoded) return refused('One event ID has conflicting endpoint identities.');
      identities.set(id, encoded);
      const summary = group[side], event = edge[`${side}_event`];
      group.events.add(id);
      summary.events.add(id);
      if (event === undefined || event === null) { summary.missingEndpointCount++; continue; }
      if (!object(event) || event.event_id !== id || event.site_id !== identity[0] || event.source_record_id !== identity[1]
        || event.resolution !== identity[2] || event.feature_key !== identity[3]
        || (event.temporal_contract_version !== undefined && event.temporal_contract_version !== edge.temporal_contract_version)) return refused('A supplied canonical endpoint conflicts with its relation.');
      const {younger_bp: younger, older_bp: older, comparability_status: posture} = event;
      const fingerprint = JSON.stringify([encoded, event.country_code, event.source_family, event.source_snapshot_id, event.chronology_claim_id, posture, younger, older]);
      if (facts.has(id) && facts.get(id) !== fingerprint) return refused('One event ID has conflicting age or comparability facts.');
      facts.set(id, fingerprint);
      if (posture === 'unresolved' && younger === null && older === null) { summary.unresolved.add(id); continue; }
      if (posture !== 'comparable' || ![younger, older].every(value => typeof value === 'number' && Number.isFinite(value) && value >= 0)
        || younger > older) return refused('Invalid or refused endpoint ages cannot form a numeric BP envelope.');
      summary.comparable.add(id);
      summary.youngerBp = summary.youngerBp === null ? younger : Math.min(summary.youngerBp, younger);
      summary.olderBp = summary.olderBp === null ? older : Math.max(summary.olderBp, older);
    }
  }
  const ordered = [...groups.entries()].sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0).map(([, group]) => {
    const result = {...group, distinctEventCount: group.events.size};
    delete result.events;
    for (const side of ['source', 'target']) {
      const summary = group[side];
      result[side] = {distinctEventCount: summary.events.size, comparableEventCount: summary.comparable.size,
        unresolvedEventCount: summary.unresolved.size, missingEndpointCount: summary.missingEndpointCount,
        youngerBp: summary.youngerBp, olderBp: summary.olderBp};
    }
    return result;
  });
  return {...base, status: 'available', reason: null, groups: ordered};
}

function renderRelationTimeSummary(data) {
  const text = value => escapeHtml(String(value));
  const scope = '<p>Counts follow relation, country and signal filters before endpoint time, layer and viewport eligibility; displayed lines may be fewer. These are properties of supplied candidate relations under their exact active rules, not independent events, rates or origins. An envelope may combine supplied endpoint chronology claims and countries within the current relation filters. The temporal contract version identifies a temporal rule contract, not a selected analysis chronology. Read the retained endpoint details for their exact supplied support.</p>';
  if (data.status !== 'available') return `<section aria-label="Relation endpoint temporal summary">${scope}<p>Temporal summary ${text(data.status)}: ${text(data.reason)} No numeric envelope is inferred.</p></section>`;
  if (!data.groups.length) return `<section aria-label="Relation endpoint temporal summary">${scope}<p>No retained active relation rows were supplied.</p></section>`;
  const rows = data.groups.slice(0, 25).map(group => ['source', 'target'].map(side => {
    const e = group[side];
    const envelope = e.youngerBp === null ? 'Unavailable (no comparable supplied endpoint ages)' : `${text(e.youngerBp)} to ${text(e.olderBp)} BP`;
    return `<tr><th scope="row">${text(group.scenario_id)} / ${text(group.signal_id)} / ${text(group.resolution)} / ${text(group.feature_key)} / ${text(group.candidate_status)} / ${text(group.temporal_contract_version)}</th><td>Stored ${side} endpoint</td><td>${group.edgeCount}</td><td>${group.distinctEventCount}</td><td>${e.distinctEventCount}</td><td>${e.comparableEventCount}</td><td>${e.unresolvedEventCount}</td><td>${e.missingEndpointCount}</td><td>${envelope}</td></tr>`;
  }).join('')).join('');
  return `<section aria-label="Relation endpoint temporal summary">${scope}<p>Each range is only the youngest minimum to oldest maximum of supplied comparable intervals: a descriptive envelope, not continuous coverage through gaps or a confidence interval. Stored source/target labels do not establish age order for indeterminate relations. No midpoint, time bin, calibration or interpolation is inferred. Distinct event counts are within each exact group and endpoint side; reused events across groups are not independent. Missing endpoint counts count relation endpoint occurrences.</p><p>Showing the first ${Math.min(25, data.groups.length)} of ${data.groups.length} exact groups. All groups remain in the retained selection; narrow the scenario, status, country or signal filters to inspect a smaller set.</p><div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>Literal supplied endpoint BP envelopes and completeness</caption><thead><tr>${['Scenario / signal / resolution / feature / status / temporal contract', 'Stored endpoint', 'Relations', 'Distinct events in group', 'Distinct events on side', 'Comparable events', 'Unresolved events', 'Missing endpoints', 'Descriptive envelope'].map(label => `<th scope="col">${label}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div></section>`;
}

      // Display actions preserve supplied hierarchy and membership.
function scientificPickerCatalog(signals) {
  const refused = error => ({status: 'refused', error, rows: [], hierarchy: []});
  if (!Array.isArray(signals)) return refused('Accepted scientific signals were not supplied.');
  const text = value => typeof value === 'string' && value.length > 0 && value.trim() === value;
  const ids = new Map(), children = new Map(), roots = [];
  for (const row of signals) {
    if (!row || typeof row !== 'object' || !['signal_id', 'label', 'feature_key'].every(key => text(row[key]))
      || row.status !== 'accepted' || !['whole', 'group', 'subgroup', 'role', 'taxon'].includes(row.resolution)
      || !/^#[0-9a-fA-F]{6}$/.test(row.color) || !['circle', 'square', 'triangle', 'diamond', 'cross', 'ring'].includes(row.non_color_cue)
      || (row.synonyms !== undefined && (!Array.isArray(row.synonyms) || !row.synonyms.every(text)))) return refused('Supplied signal identity, labels or display semantics are invalid.');
    if (ids.has(row.signal_id)) return refused('Duplicate signal IDs make hierarchy ambiguous.');
    ids.set(row.signal_id, row); children.set(row.signal_id, []);
  }
  for (const row of signals) {
    const parent = row.parent_signal_id;
    if (parent === undefined || parent === null) roots.push(row.signal_id);
    else if (!text(parent) || !ids.has(parent)) return refused('Supplied parent unavailable; hierarchy is not inferred.');
    else children.get(parent).push(row.signal_id);
  }
  const order = (a, b) => a < b ? -1 : a > b ? 1 : 0;
  const stack = roots.sort(order).reverse().map(id => ({id, depth: 0})), hierarchy = [];
  while (stack.length) {
    const entry = stack.pop(); hierarchy.push({...entry, signal: ids.get(entry.id)});
    for (const id of children.get(entry.id).sort(order).reverse()) stack.push({id, depth: entry.depth + 1});
  }
  if (hierarchy.length !== signals.length) return refused('Cyclic parent links make hierarchy unavailable.');
  return {status: 'available', error: null, rows: [...signals], hierarchy};
}
function scientificPickerSearch(catalog, query = '') {
  if (catalog.status !== 'available' || typeof query !== 'string') return [];
  const needle = query.trim().toLowerCase();
  return catalog.hierarchy.filter(({signal}) => [signal.signal_id, signal.label, signal.feature_key, ...(signal.synonyms || [])].some(value => value.toLowerCase().includes(needle)));
}
function scientificPickerStateError(catalog, state) {
  if (catalog.status !== 'available') return catalog.error;
  const ids = new Set(catalog.rows.map(row => row.signal_id));
  if (!state || !['pinnedIds', 'visibleIds'].every(key => Array.isArray(state[key]) && new Set(state[key]).size === state[key].length && state[key].every(id => ids.has(id))) || state.pinnedIds.length > 6) return 'Unknown, repeated or excessive picker identities.';
  return null;
}
function scientificPickerInitialState(catalog, selectedIds, pinRequest = []) {
  if (!Array.isArray(pinRequest) || !pinRequest.every(value => typeof value === 'string') || pinRequest.length > 1) {
    return {state: null, error: 'Shared pinned comparison was supplied more than once or is unavailable.'};
  }
  let pinnedIds = Array.isArray(selectedIds) ? selectedIds.slice(0, 6) : null;
  if (pinRequest.length) {
    try { pinnedIds = JSON.parse(pinRequest[0]); }
    catch { return {state: null, error: 'Shared pinned comparison is unavailable.'}; }
  }
  const state = {pinnedIds, visibleIds: Array.isArray(selectedIds) ? [...selectedIds] : null};
  const error = scientificPickerStateError(catalog, state);
  return {state: error ? null : state, error};
}
function scientificPickerAction(catalog, state, action) {
  const error = scientificPickerStateError(catalog, state);
  if (error) return {state, error};
  const next = {pinnedIds: [...state.pinnedIds], visibleIds: [...state.visibleIds]};
  const id = action?.id, pinned = next.pinnedIds.indexOf(id);
  if (!catalog.rows.some(row => row.signal_id === id)) return {state, error: 'The exact signal ID is unavailable.'};
  if (action.type === 'pin') {
    if (pinned >= 0) return {state, error: 'This exact signal is already pinned.'};
    if (next.pinnedIds.length === 6) return {state, error: 'At most six exact signal IDs can be pinned.'};
    next.pinnedIds.push(id);
    if (!next.visibleIds.includes(id)) next.visibleIds.push(id);
  } else {
    if (pinned < 0) return {state, error: 'Action requires an exact pinned signal.'};
    if (action.type === 'remove') { next.pinnedIds.splice(pinned, 1); next.visibleIds = next.visibleIds.filter(value => value !== id); }
    else if (action.type === 'hide') next.visibleIds = next.visibleIds.filter(value => value !== id);
    else if (action.type === 'show') { if (!next.visibleIds.includes(id)) next.visibleIds.push(id); }
    else if (action.type === 'solo') next.visibleIds = [id];
    else if (['earlier', 'later'].includes(action.type)) {
      const target = pinned + (action.type === 'earlier' ? -1 : 1);
      if (target < 0 || target >= next.pinnedIds.length) return {state, error: 'Signal is already at this tray end.'};
      [next.pinnedIds[pinned], next.pinnedIds[target]] = [next.pinnedIds[target], next.pinnedIds[pinned]];
    } else return {state, error: 'Unknown scientific display action.'};
  }
  return {state: next, error: null};
}
function renderScientificPicker(catalog, state, query = '') {
  const text = value => escapeHtml(String(value)), error = scientificPickerStateError(catalog, state) || (typeof query !== 'string' ? 'Search text is unavailable.' : null);
  if (error) return `<section aria-label="Scientific signal picker"><p>Scientific picker unavailable: ${text(error)}</p></section>`;
  const ids = new Map(catalog.rows.map(row => [row.signal_id, row]));
  const matches = scientificPickerSearch(catalog, query), shown = matches.slice(0, 25), searching = Boolean(query.trim());
  const button = (type, row, label, disabled = false) => `<button type="button" class="inline-button" data-scientific-action="${type}" data-scientific-id="${text(row.signal_id)}" aria-label="${text(label)} ${text(row.label)} (${text(row.signal_id)})" ${disabled ? 'disabled' : ''}>${text(label)}</button>`;
  const label = row => `<span class="scientific-cue" data-cue="${text(row.non_color_cue)}" style="color:${text(row.color)}">${text(scientificCueGlyph(row.non_color_cue))}</span> ${text(row.label)} · ${text(row.resolution)} · ${text(row.signal_id)} · ${text(row.feature_key)}`;
  let list = '', depth = 0;
  shown.forEach((entry, index) => {
    const level = searching ? 0 : entry.depth;
    if (level > depth) list += '<ul>'; else if (index) list += '</li>' + '</ul></li>'.repeat(depth - level);
    const row = entry.signal, pinned = state.pinnedIds.includes(row.signal_id);
    list += `<li>${label(row)}${searching && row.parent_signal_id ? ` · Supplied parent: ${text(row.parent_signal_id)}` : ''} ${button('pin', row, pinned ? 'Pinned' : 'Pin', pinned || state.pinnedIds.length === 6)}`;
    depth = level;
  });
  if (shown.length) list += '</li>' + '</ul></li>'.repeat(depth);
  const tray = state.pinnedIds.map((id, index) => {
    const row = ids.get(id), visible = state.visibleIds.includes(id);
    return `<li>${label(row)} · ${visible ? 'Visible' : 'Hidden'} ${button(visible ? 'hide' : 'show', row, visible ? 'Hide' : 'Show')}${button('solo', row, 'Solo')}${button('earlier', row, 'Move earlier', index === 0)}${button('later', row, 'Move later', index === state.pinnedIds.length - 1)}${button('remove', row, 'Remove')}</li>`;
  }).join('');
  const unpinned = state.visibleIds.filter(id => !state.pinnedIds.includes(id)).length;
  return `<section aria-label="Scientific signal picker"><p>${state.pinnedIds.length} pinned of at most 6; ${state.visibleIds.length} selected for display; Visible but unpinned: ${unpinned}. Other map filters still apply.</p><p>Only supplied parent links define hierarchy. Display actions never select descendants, merge resolutions or create scientific membership.</p><label>Find a supplied signal <input type="search" class="search-input" data-scientific-query value="${text(query)}" aria-label="Find supplied scientific signals"></label><p>Showing first ${shown.length} of ${matches.length} matches from ${catalog.rows.length} supplied signals. Search supplied IDs, labels, features and explicit synonyms.</p><ul aria-label="Supplied signal hierarchy or search results">${list}</ul><ol aria-label="Pinned comparison signals">${tray}</ol>${catalog.rows.length ? '' : '<p>No accepted scientific signals were supplied.</p>'}</section>`;
}

      // Mount supplied display choices; the host owns selection, URL state and map rendering.
function mountScientificPicker(container, catalog, owners) {
  let query = '', actionError = '';
  function render(caret = null) {
    const current = owners.read();
    container.innerHTML = renderScientificPicker(catalog, current.state, query)
      + (current.error ? `<p role="status">${escapeHtml(current.error)}</p><button type="button" class="inline-button" data-scientific-reset-pins>Reset comparison pins</button>` : '')
      + (actionError ? `<p role="status">${escapeHtml(actionError)}</p>` : '');
    if (caret !== null) {
      const input = container.querySelector('[data-scientific-query]');
      if (input) {
        input.focus();
        input.setSelectionRange(caret.start, caret.end);
      }
    }
  }
  container.addEventListener('input', event => {
    if (!event.target.matches('[data-scientific-query]')) return;
    query = event.target.value;
    render({start: event.target.selectionStart, end: event.target.selectionEnd});
  });
  container.addEventListener('click', event => {
    const reset = event.target.closest('[data-scientific-reset-pins]');
    if (reset && container.contains(reset)) {
      actionError = '';
      owners.reset();
      return;
    }
    const button = event.target.closest('[data-scientific-action]');
    if (!button || !container.contains(button) || button.disabled) return;
    const current = owners.read();
    if (current.error) return;
    const result = scientificPickerAction(catalog, current.state, {
      type: button.dataset.scientificAction, id: button.dataset.scientificId,
    });
    actionError = result.error || '';
    if (result.error) render();
    else owners.change(result.state);
  });
  return Object.freeze({render, clearSearch() { query = ''; actionError = ''; }});
}

      // Metadata geometry is a separate, opt-in layer; extents never become site points.
function createSourceResourceGeography({browser,map,leaflet,countries,onSelect,status,current = () => true}) {
  const group=leaflet.layerGroup(), renderer=leaflet.svg(), codes={Denmark:'DK',Finland:'FI',Norway:'NO',Sweden:'SE'};
  let generation=0, zoomGeneration=0;
  const position=value=>Array.isArray(value)&&value.length===2&&value.every(Number.isFinite)
    &&Math.abs(value[0])<=180&&Math.abs(value[1])<=90;
  function qualifiedExtent(value) {
    if(!value || !['Polygon','MultiPolygon'].includes(value.type))return false;
    const polygons=value.type==='Polygon'?[value.coordinates]:value.coordinates;
    if(!Array.isArray(polygons)||!polygons.length||polygons.length>20000)return false;
    let count=0;
    return polygons.every(polygon=>Array.isArray(polygon)&&polygon.length&&polygon.length<=20000
      &&polygon.every(ring=>Array.isArray(ring)&&ring.length>=4&&ring.length<=20000
        &&(count+=ring.length)<=20000&&ring.every(position)&&JSON.stringify(ring[0])===JSON.stringify(ring.at(-1))));
  }
  function point(row) {
    const value=row.marker_geometry;
    return row.geometry_status==='native_point_consensus'&&value?.type==='Point'&&position(value.coordinates)?value:null;
  }
  async function geometries(row) {
    const result=[],p=point(row);
    if(p)result.push({geometry:p,kind:'point'});
    const ids=row.native_extent_variant_ids ?? [];
    if(!Array.isArray(ids)||ids.length>128)throw Error('Metadata extent membership exceeds its bound.');
    if(ids.length) {
      const site=await browser.site(row.record_id);
      if(!site||site.site_id!==row.record_id||!Array.isArray(site.native_site_variants)||site.native_site_variants.length>128)throw Error('Metadata extent site identity differs.');
      const seen=new Set();let total=0;
      for(const identity of ids) {
        if(typeof identity!=='string'||seen.has(identity))throw Error('Metadata extent variant identity repeats.');seen.add(identity);
        const matched=site.native_site_variants.filter(variant=>variant.variant_id===identity);
        if(matched.length!==1||matched[0].extent_status!=='explicit_native_extent'||!qualifiedExtent(matched[0].extent_geometry))throw Error('Metadata extent is unavailable or not qualified.');
        const geometry=matched[0].extent_geometry;
        const polygons=geometry.type==='Polygon'?[geometry.coordinates]:geometry.coordinates;
        total+=polygons.reduce((sum,polygon)=>sum+polygon.reduce((n,ring)=>n+ring.length,0),0);
        if(total>20000)throw Error('Metadata site coordinate population exceeds its bound.');
        result.push({geometry,kind:'extent'});
      }
    }
    return result;
  }
  function layer(value,identity) {
    const result=leaflet.geoJSON(value.geometry,{bubblingMouseEvents:false,renderer,
      pointToLayer:(_feature,latlng)=>leaflet.circleMarker(latlng,{renderer,radius:7,color:'#74508b',weight:2,fillOpacity:0.12,bubblingMouseEvents:false,className:'neotoma-metadata-geometry'}),
      style:()=>({color:'#74508b',weight:2,fillOpacity:0.08,dashArray:'5 4',className:'neotoma-metadata-geometry'})});
    result.bindTooltip(`Neotoma metadata ${value.kind}; native site ${identity}. No scientific admission.`);
    result.on('click',event=>{leaflet.DomEvent.stopPropagation(event);onSelect(identity);});return result;
  }
  // Superseded requests may settle, but cannot draw or describe a newer selection.
  async function update({enabled,includeUnassigned,rows,sites}) {
    const token=++generation;zoomGeneration++;group.clearLayers();if(map.hasLayer(group))map.removeLayer(group);
    if(!enabled){status.textContent='Metadata geometry is off. Unlocated resources remain searchable.';return;}
    const selected=new Set(rows.map(row=>row.site_id)),active=new Set(countries().map(country=>codes[country]||country));
    const matches=sites.filter(row=>selected.has(row.record_id)
      &&(row.country_code===null||row.country_code==='UNASSIGNED'?includeUnassigned:active.has(row.country_code)));
    let results;
    try {results=await Promise.all(matches.map(async row=>({row,values:await geometries(row)})));}
    catch(error){if(token===generation && current())status.textContent=`Metadata geometry unavailable: ${error.message}. Searchable metadata and scientific layers remain available.`;return;}
    if(token!==generation || !current())return;
    let points=0,extents=0,unlocated=0;
    for(const {row,values} of results){if(!values.length)unlocated++;for(const value of values){group.addLayer(layer(value,row.record_id));value.kind==='point'?points++:extents++;}}
    group.addTo(map);
    status.textContent=`Metadata geometry: ${points} consensus points; ${extents} native extent variants; ${unlocated} matching sites without drawable geometry. Separate metadata layer; scientific counts, fit and time filters are unchanged.`;
  }
  async function zoom(identity) {
    const token=++zoomGeneration;
    try {
    const row=await browser.site(identity);
    if(token!==zoomGeneration || !current())return;
    if(!row)throw Error('The native metadata site is unavailable.');
    const values=await geometries({...row,record_id:row.site_id});
    if(token!==zoomGeneration || !current())return;
    if(!values.length)throw Error('This metadata site has no qualified geometry; no location is invented.');
    const bounds=leaflet.featureGroup(values.map(value=>layer(value,identity))).getBounds();
    if(bounds.isValid())map.fitBounds(bounds,{padding:[30,30],maxZoom:11});
    } catch(error) {if(token===zoomGeneration && current())status.textContent=`Metadata zoom unavailable: ${error.message}. No location is invented.`;}
  }
  return Object.freeze({update,zoom,cancel:()=>{generation++;zoomGeneration++;},cancelZoom:()=>{zoomGeneration++;}});
}

      // Listing posture summarizes source qualification, never HTTP availability or admission.
function sourceResourceQualification(row, version) {
  if (!['development_resource_discovery','exposed_development'].includes(row.exposure_role)) return {metadataOnly:true};
  const statuses=row.version_statuses?.[version] || {};
  let field='qualification_status';
  if (version==='doi_frozen') {
    if (Object.hasOwn(statuses,'strict_current_binding_status') && statuses.strict_current_binding_status!=='matches_current_metadata') {
      field='strict_current_binding_status';
    } else if ((!Object.hasOwn(statuses,'qualification_status') || statuses.qualification_status==='parsed_frozen_native')
      && Object.hasOwn(statuses,'snapshot_qualification_status')) field='snapshot_qualification_status';
  } else {
    const identityRefusal=['qualification_status','source_terminal_status','acquisition_status']
      .find(name=>statuses[name]==='refused_native_protocol');
    if (identityRefusal) field=identityRefusal;
    else if (statuses.qualification_status==='not_qualified' && statuses.acquisition_status==='unsupported_dataset_type'
      && statuses.source_terminal_status==='unsupported_dataset_type' && Object.hasOwn(statuses,'current_source_qualification_status')) {
      field='current_source_qualification_status';
    }
  }
  return {field,value:statuses[field],metadataOnly:false};
}
// A shared metadata reader owns its DOM; scientific selections remain independent.
function createSourceResourceReader({browser, domain, map, leaflet, publishQuery, canPublish,
  countries = () => [], standaloneMetadata = false, location = globalThis.location}) {
  const element = (tag, text, attributes = {}) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    Object.entries(attributes).forEach(([key,value]) => node.setAttribute(key,String(value)));
    return node;
  };
  const ownedLabel = value => typeof value === 'string' ? value.replaceAll('_',' ') : text(value);
  const text = value => value === undefined ? 'not supplied' : value === null ? 'explicit null' : typeof value === 'string' ? value : JSON.stringify(value);
  const dialog = element('dialog', undefined, {id:'source-resources-dialog',class:'help-dialog-card','aria-label':'Neotoma source resource metadata'});
  dialog.hidden = true;
  const card = element('div',undefined,{class:'focus-detail'});
  const heading = element('div', undefined, {class:'help-dialog-head'});
  const title = element('h2','Neotoma sources');
  const close = element('button','Close',{type:'button',class:'toolbar-button focus-close','aria-label':'Close Neotoma source resource metadata'});
  heading.append(title,close);
  const status = element('p','Loading source metadata…',{role:'status','aria-live':'polite','data-resource-status':''});
  const qualification = element('p','Metadata only; no scientific admission or independent validation.');
  const scope = element('details',undefined,{'data-resource-scope':''});
  scope.append(element('summary','Source scope and epochs'),element('p','Current and DOI-frozen versions keep their own epochs, rights and qualification. A frozen version does not establish original-paper identity. These resources do not expand the published scientific population or establish independent evidence.'));
  const controls = element('div',undefined,{class:'focus-detail'}), list = element('div',undefined,{'data-resource-list':''});
  const detail = element('section',undefined,{'aria-label':'Selected source resource','data-resource-detail':''});
  const navigation = element('div',undefined,{class:'map-actions'});
  const previous = element('button','Previous metadata page',{type:'button',class:'toolbar-button'});
  const next = element('button','Next metadata page',{type:'button',class:'toolbar-button'});
  const pageLabel = element('span');
  navigation.append(previous,pageLabel,next);
  card.append(heading,qualification,controls,list,navigation,detail);dialog.append(card);document.body.append(dialog);
  let initializing = false;
  let generation = 0, detailGeneration = 0, page = 0, selectedSite = null, returnFocus = null;
  let downloadIntent = null, inventory = null, context = null, rows = [], overlay = null;
  const filters = {};
  function input(label, kind, values = []) {
    const wrapper = element('label',label+' '), node = element(kind === 'search' ? 'input' : 'select');
    node.setAttribute('aria-label',label);node.className='search-input';
    if (kind === 'search') { node.type='search'; node.maxLength=4096; }
    else for (const [value,name] of values) node.append(element('option',name,{value}));
    wrapper.append(node);controls.append(wrapper);return node;
  }
  const populationLabels={resources:'Native datasets',ancillary_context:'Capture scope and epochs',facet_slots:'Captured facet slots',ancillary_observations:'Captured source observations',linked_occurrences:'Linked source occurrences',supporting_archives:'Supporting metadata archives',supporting_entries:'Supporting metadata entries'};
  const population=domain.schema_version==='atlas-source-resources.v2'
    ? input('Metadata population','select',Object.entries(populationLabels)) : {value:'resources'};
  const search = input('Search source metadata','search');
  controls.append(scope,status);
  const country = input('Metadata country','select',[['','All countries'],['DK','Denmark'],['FI','Finland'],['NO','Norway'],['SE','Sweden'],['UNASSIGNED','Unassigned / review']]);
  const type = input('Native dataset type','select',[['','All native types']]);
  const role = input('Exposure role','select',[['','All exposure roles']]);
  const version = input('Source version','select',[['current','Current'],['doi_frozen','DOI-frozen']]);
  const statusFilter = input('Version status','select',[['','All version statuses']]);
  const showMetadata = element('input',undefined,{type:'checkbox','aria-label':'Show metadata geometry'});
  const showUnassigned = element('input',undefined,{type:'checkbox','aria-label':'Include unassigned metadata geometry'});
  for (const [node,label] of [[showMetadata,'Show separate metadata geometry (off by default)'],[showUnassigned,'Include unassigned / review metadata geometry']]) {
    const wrapper=element('label');wrapper.append(node,document.createTextNode(label));controls.append(wrapper);
  }
  controls.append(element('p',standaloneMetadata
    ? 'This source-only map uses the metadata country filter for its separate geometry. Scientific countries, layers and counts remain unchanged.'
    : 'Geometry follows the Atlas country switches. Unassigned geometry uses its separate switch; metadata searches include unlocated and country-review sites.'));
  const geometryStatus = element('p','Metadata geometry is off. Unlocated resources remain searchable.',{'data-resource-geometry-status':''});controls.append(geometryStatus);
  function authority() { return typeof canPublish !== 'function' || canPublish(); }
  function publish(site = selectedSite, dataset = null) {
    if (!authority()) return false;
    return typeof publishQuery !== 'function' || publishQuery({neotoma_catalogue:domain.catalogue_manifest_sha256,
      neotoma_site:site,neotoma_dataset:dataset,neotoma_version:dataset ? version.value : null});
  }
  function message(error) {
    status.textContent = `Source metadata unavailable: ${error.message || error}. Retry by reopening the source resources reader.`;
    status.dataset.state='unavailable';
  }
  function rawSection(parent,label,value) {
    const section=element('details'),summary=element('summary',label),pre=element('pre',JSON.stringify(value,null,2));
    pre.className='source-diagram-plot';section.append(summary,pre);parent.append(section);
  }
  function displayFields(parent, values) {
    const table=element('dl');
    for(const [key,value] of Object.entries(values || {}))table.append(element('dt',key),element('dd',text(value)));
    parent.append(table);
  }
  function versionAndRights(record) {
    const versions=element('section',undefined,{'data-source-versions':''});versions.append(element('h4','Version-specific source posture'));
    for(const [name,fields] of Object.entries(record.versions || {})) {
      versions.append(element('h5',name));
      displayFields(versions,Object.fromEntries(Object.entries(fields).filter(([key])=>key.endsWith('_status')||key.includes('profile')||key==='epoch_kind')));
    }
    detail.append(versions);
    const rights=element('section',undefined,{'data-source-rights':''});rights.append(element('h4','Source rights and attribution'));
    displayFields(rights,record.rights);
    for(const [label,values] of [['Data-use policy',record.rights?.policy_sources],['Native dataset DOI',record.rights?.dataset_doi_values]]) {
      if(!Array.isArray(values))continue;
      for(const value of values) {
        if(typeof value!=='string')continue;
        let url;try{url=new URL(/^10\.[0-9]{4,9}\/\S+$/.test(value)?`https://doi.org/${value}`:value);}catch{continue;}
        if(!['https:','http:'].includes(url.protocol)||url.username||url.password)continue;
        const row=element('p');row.append(element('a',`${label}: ${value}`,{href:url.href,target:'_blank',rel:'noopener noreferrer'}));rights.append(row);
      }
    }
    detail.append(rights);
  }
  function addAction(parent,label,handler,attributes={}) {
    const button=element('button',label,{type:'button',class:'toolbar-button',...attributes});
    button.addEventListener('click',()=>{Promise.resolve(handler()).catch(message);});parent.append(button);return button;
  }
  async function save(record, kind) {
    downloadIntent?.abort();downloadIntent=new AbortController();
    const intent=downloadIntent, identity=detailGeneration;
    const info=detail.querySelector('[data-download-status]');
    if(info)info.textContent='Verifying the selected original bytes…';
    try {
      const selected=version.value;
      const data=await (kind==='receipt' ? browser.downloadReceipt : browser.downloadResource)(record.dataset_id,selected,{signal:intent.signal});
      if(intent.signal.aborted || identity!==detailGeneration || !authority() || !dialog.open)return;
      const href=URL.createObjectURL(new Blob([data.bytes],{type:'application/octet-stream'}));
      const anchor=element('a',undefined,{href,download:data.filename});document.body.append(anchor);anchor.click();anchor.remove();
      setTimeout(()=>URL.revokeObjectURL(href),1000);
      if(info)info.textContent=`Verified ${data.bytes.length} original bytes; SHA-256 ${data.sha256}. Source entity only; scientific admission is not asserted.`;
    } catch(error) {if(error.name!=='AbortError' && identity===detailGeneration && info)info.textContent=`Download unavailable: ${error.message}`;}
  }
  async function selectDataset(identity, {write=true}={}) {
    const token=++detailGeneration;downloadIntent?.abort();overlay?.cancelZoom();
    detail.replaceChildren(element('p','Loading the selected resource metadata…'));
    try {
      const record=await browser.resource(identity);
      if(token!==detailGeneration || !dialog.open || !authority())return;
      if(!record || selectedSite && record.site_id!==selectedSite)throw Error('The dataset does not match the selected native site.');
      if(write && !publish(record.site_id,identity))return;
      detail.replaceChildren(element('h3',`Native dataset ${identity}`));
      detail.append(element('p',`Site ${record.site_id}; collection unit ${record.collection_unit_id}; type ${text(record.dataset_type)}; role ${text(record.exposure_role)}. Metadata only; no scientific admission is asserted.`));
      const selected=record.versions?.[version.value];
      if(!selected)throw Error('The exact selected source version is unavailable.');
      versionAndRights(record);
      rawSection(detail,`${version.value}: acquisition, qualification, source epoch and locators`,selected);
      rawSection(detail,'Native metadata, country decision and rights',record);
      const site=await browser.site(record.site_id);
      if(token!==detailGeneration || !dialog.open || !authority())return;
      rawSection(detail,'All retained native site variants and geometry qualifications',site);
      const actions=element('div',undefined,{class:'map-actions'});
      if(['development_resource_discovery','exposed_development'].includes(record.exposure_role)) {
        addAction(actions,'Verify and download original source entity',()=>save(record,'body'),{'data-resource-download':'body'});
        addAction(actions,'Verify and download HTTP receipt',()=>save(record,'receipt'),{'data-resource-download':'receipt'});
      } else detail.append(element('p','Metadata-only exposure role: source body and receipt downloads are blocked before access.'));
      addAction(actions,'Zoom to this metadata geometry',async()=>{await ensureOverlay();await overlay.zoom(record.site_id);});
      detail.append(actions,element('p',['http:','https:'].includes(location?.protocol)
        ? 'Downloads verify the pinned manifest, index and selected file before saving. A raw response may contain NoRecord or a method refusal; it is not a count of scientific observations.'
        : 'Verified source downloads are unavailable in file mode. Use HTTPS or a local HTTP server.',{'data-download-status':'',role:'status','aria-live':'polite'}));
    } catch(error) {if(token===detailGeneration)message(error);}
  }
  async function selectAncillary(kind,identity) {
    const token=++detailGeneration;downloadIntent?.abort();overlay?.cancelZoom();
    detail.replaceChildren(element('p','Loading the selected captured metadata…'));
    try {
      const record=await browser.ancillary(kind,identity);
      if(token!==detailGeneration || !dialog.open || !authority())return;
      if(!record)throw Error('The captured metadata record is unavailable.');
      detail.replaceChildren(element('h3',populationLabels[kind]));
      detail.append(element('p','Recorded metadata only. Native entity bodies, biological meaning and scientific admission are not verified by this view. No source body download is offered.'));
      rawSection(detail,'Exact recorded metadata and source identities',record);
    } catch(error) {if(token===detailGeneration)message(error);}
  }
  async function ensureOverlay() {
    overlay ||= createSourceResourceGeography({browser,map,leaflet,countries:standaloneMetadata?()=>['DK','FI','NO','SE']:countries,onSelect:identity=>open({site:identity}),status:geometryStatus,current:authority});
    return overlay;
  }
  async function updateOverlay() {
    if(!inventory)return;
    await ensureOverlay();
    await overlay.update({enabled:showMetadata.checked && population.value==='resources',includeUnassigned:showUnassigned.checked,rows:population.value==='resources'?rows:[],sites:inventory.sites});
  }
  async function refresh({write=true}={}) {
    // Initial input values are applied by the opener once its complete index arrives.
    if(initializing)return;
    const token=++generation;
    try {
      const native=population.value==='resources';
      for(const node of [country,type,role,version,statusFilter,showMetadata,showUnassigned])node.disabled=!native;
      const selected=native && statusFilter.value ? JSON.parse(statusFilter.value) : null;
      const found=await browser.search(search.value,native?{country:country.value,type:type.value,role:role.value,
        ...(selected ? {version:version.value,statusField:selected[0],status:selected[1]} : {})}:{population:population.value});
      if(token!==generation || !dialog.open || !authority())return;
      rows=found.filter(row=>!native || !selectedSite || row.site_id===selectedSite);
      page=Math.min(page,Math.max(0,Math.ceil(rows.length/25)-1));
      list.replaceChildren();
      for(const row of rows.slice(page*25,page*25+25)) {
        if(!native) {
          const item=element('section',undefined,{class:'help-card','data-ancillary-record':row.record_id});
          addAction(item,`${populationLabels[population.value]} · ${row.record_id}`,()=>selectAncillary(population.value,row.record_id));
          item.append(element('p','Metadata only; this row is not added to native dataset, site or scientific counts.'));
          list.append(item);continue;
        }
        const item=element('section',undefined,{class:'help-card','data-resource-dataset':row.record_id});
        addAction(item,`Dataset ${row.record_id} · site ${row.site_id} · ${text(row.dataset_type)}`,()=>selectDataset(row.record_id));
        item.append(element('p',(inventory.sites.find(site=>site.record_id===row.site_id)?.native_site_names || []).join(' / ')));
        const posture=sourceResourceQualification(row,version.value);
        const label=posture.field==='current_source_qualification_status' ? 'Derived current source qualification'
          : posture.field==='snapshot_qualification_status' ? 'Snapshot source qualification'
            : posture.field==='strict_current_binding_status' ? 'Current metadata binding'
              : ['source_terminal_status','acquisition_status'].includes(posture.field) ? 'Source capture posture' : 'Source qualification';
        const qualification=posture.metadataOnly ? 'Metadata only; numerical requests blocked.' : `${label}: ${ownedLabel(posture.value)}.`;
        item.append(element('p',`${row.country_code ?? 'UNASSIGNED'} · ${ownedLabel(row.exposure_role)} · ${version.value === 'doi_frozen' ? 'DOI-frozen' : 'Current'}. ${qualification}`));
        list.append(item);
      }
      previous.disabled=page===0;next.disabled=(page+1)*25>=rows.length;
      pageLabel.textContent=`Page ${page+1} of ${Math.max(1,Math.ceil(rows.length/25))}`;
      const siteCount=new Set(rows.map(row=>row.site_id)).size;
      const catalogueScope=rows.length===domain.record_count && siteCount===domain.site_count ? '' : ` Catalogue: ${domain.record_count} resources at ${domain.site_count} metadata sites.`;
      status.textContent=native ? `${rows.length} matching metadata resources at ${siteCount} native sites.${catalogueScope}`
        : `${rows.length} recorded ${populationLabels[population.value].toLowerCase()}. Native catalogue remains ${domain.record_count} resources at ${domain.site_count} sites. This population uses the catalogue-wide metadata scope.`;
      status.dataset.state='available';
      if(write && native)publish();
      await updateOverlay();
    }catch(error){if(token===generation)message(error);}
  }
  if(typeof population.addEventListener==='function')population.addEventListener('change',()=>{page=0;detailGeneration++;downloadIntent?.abort();overlay?.cancel();detail.replaceChildren();void refresh();});
  for(const node of [search,country,type,role,statusFilter])node.addEventListener(node===search?'input':'change',()=>{page=0;detailGeneration++;downloadIntent?.abort();overlay?.cancel();detail.replaceChildren();void refresh();});
  version.addEventListener('change',()=>{detailGeneration++;downloadIntent?.abort();overlay?.cancel();detail.replaceChildren();page=0;void refresh();});
  previous.addEventListener('click',()=>{overlay?.cancelZoom();page--;void refresh();});next.addEventListener('click',()=>{overlay?.cancelZoom();page++;void refresh();});
  for(const node of [showMetadata,showUnassigned])node.addEventListener('change',()=>{void updateOverlay().catch(message);});
  function hide({write=true}={}) {
    generation++;detailGeneration++;downloadIntent?.abort();overlay?.cancelZoom();dialog.close();dialog.hidden=true;
    if(write && authority() && typeof publishQuery==='function')publishQuery({neotoma_catalogue:null,neotoma_site:null,neotoma_dataset:null,neotoma_version:null});
    returnFocus?.focus();
  }
  addAction(controls,'All metadata sites',()=>{population.value='resources';overlay?.cancel();selectedSite=null;search.value='';country.value='';type.value='';role.value='';statusFilter.value='';page=0;detailGeneration++;downloadIntent?.abort();detail.replaceChildren();return open();});
  close.addEventListener('click',()=>hide());
  dialog.addEventListener('keydown',event=>event.stopPropagation());
  dialog.addEventListener('cancel',event=>{event.preventDefault();hide();});
  async function open(selection = {}) {
    const token=++generation;overlay?.cancel();initializing=true;
    if(!dialog.open)returnFocus=document.activeElement;dialog.hidden=false;if(!dialog.open)dialog.showModal();status.textContent='Loading source metadata…';
    try {
      if(selection.url) {
        const query=new URL(selection.url).searchParams, keys=['neotoma_catalogue','neotoma_site','neotoma_dataset','neotoma_version'];
        if(keys.some(key=>query.getAll(key).length>1 || query.has(key) && !query.get(key))
          || !query.has('neotoma_catalogue') || [...query.keys()].some(key=>key.startsWith('neotoma_')&&!keys.includes(key)))throw Error('The shared metadata URL is incomplete or ambiguous.');
        selection={...selection,catalogue:query.get('neotoma_catalogue'),site:query.get('neotoma_site'),dataset:query.get('neotoma_dataset'),version:query.get('neotoma_version')};
      }
      if(selection.catalogue && selection.catalogue!==domain.catalogue_manifest_sha256)throw Error('The shared URL names a different catalogue epoch.');
      if(selection.version && !['current','doi_frozen'].includes(selection.version))throw Error('The shared URL source version is unsupported.');
      if(selection.site && !/^[1-9][0-9]*$/.test(selection.site) || selection.dataset && !/^[1-9][0-9]*$/.test(selection.dataset))throw Error('The shared URL native identity is invalid.');
      if(selection.site || selection.dataset || selection.record)population.value='resources';
      version.value=selection.version || 'current';
      [inventory,context]=await Promise.all([browser.inventory(),browser.context()]);
      if(token!==generation || !dialog.open || !authority())return;
      if(selection.record) {
        const joined=context.legacy_site_references?.filter(row=>row.record_id===selection.record && row.site_id===selection.site && row.status==='matched') || [];
        if(joined.length!==1)throw Error('The selected scientific record has no exact native metadata-site join.');
      }
      if(selection.site && !inventory.sites.some(row=>row.record_id===selection.site))throw Error('The shared URL native site is absent from this catalogue.');
      selectedSite=selection.site || null;page=0;detailGeneration++;downloadIntent?.abort();detail.replaceChildren();
      for(const [node,field] of [[type,'dataset_type'],[role,'exposure_role']]) {
        node.replaceChildren(element('option',field==='dataset_type'?'All native types':'All exposure roles',{value:''}));
        [...new Set(inventory.resources.map(row=>row[field]).filter(value=>typeof value==='string'))].sort().forEach(value=>node.append(element('option',value,{value})));
      }
      statusFilter.replaceChildren(element('option','All version statuses',{value:''}));
      const states=new Map();inventory.resources.forEach(row=>Object.values(row.version_statuses || {}).forEach(value=>Object.entries(value).forEach(([key,state])=>states.set(JSON.stringify([key,state]),`${key}: ${text(state)}`))));
      [...states].sort((a,b)=>a[1].localeCompare(b[1])).forEach(([value,label])=>statusFilter.append(element('option',label,{value})));
      initializing=false;
      await refresh({write:selection.write!==false});
      if(selection.dataset && token+1===generation)await selectDataset(selection.dataset,{write:selection.write!==false});
      dialog.scrollTop=0;search.focus({preventScroll:true});
    }catch(error){if(token===generation){initializing=false;message(error);}}
  }
  return Object.freeze({open,hide,countriesChanged:()=>updateOverlay().catch(message)});
}

      // Verify shared source metadata and only the explicitly selected entity buffer.
function createSourceResourceDownloads({domain, context, resource, fetcher = globalThis.fetch,
  cryptoProvider = globalThis.crypto, location = globalThis.location}) {
  const metadataCap = 16 * 1024 * 1024, bodyCap = 32 * 1024 * 1024;
  const development = new Set(['development_resource_discovery', 'exposed_development']);
  let archiveRequest = null;
  function refuse(code, message) {
    const error = Error(message);
    error.code = code;
    throw error;
  }
  const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  const nativeId = value => typeof value === 'string' && /^[1-9][0-9]*$/.test(value);
  const ordinary = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const stable = value => JSON.stringify(value && typeof value === 'object'
    ? Array.isArray(value) ? value.map(item => JSON.parse(stable(item)))
      : Object.fromEntries(Object.keys(value).sort().map(key => [key, JSON.parse(stable(value[key]))])) : value);
  function memberPath(value) {
    if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._/-]*$/.test(value)
      || value.split('/').some(part => !part || part === '.' || part === '..')
      || value.split('/').length > 32) refuse('member_path', 'Source download member path is unavailable.');
    return value;
  }
  function baseURL(reference) {
    if (!['http:', 'https:'].includes(location?.protocol)) {
      refuse('file_protocol', 'Verified source downloads require HTTPS or a local HTTP server. File-mode downloads are unavailable.');
    }
    if (typeof cryptoProvider?.subtle?.digest !== 'function' || typeof fetcher !== 'function') {
      refuse('verification_unavailable', 'Source download verification is unavailable. Use HTTPS or localhost HTTP.');
    }
    const path = reference?.published_base_url;
    if (typeof path !== 'string' || !/^\/(?:[A-Za-z0-9][A-Za-z0-9._-]*\/)*$/.test(path)
      || path.split('/').some(part => part.toLowerCase() === 'artifacts')) refuse('public_route', 'The shared source publication route is invalid.');
    const base = new URL(path, location.href);
    if (base.origin !== location.origin) refuse('public_route', 'Source downloads require the declared same-origin publication.');
    return base;
  }
  async function buffer(base, path, expectedDigest, expectedSize, cap, signal) {
    memberPath(path);
    if (!digest(expectedDigest) || expectedSize !== undefined
      && (!Number.isSafeInteger(expectedSize) || expectedSize < 0 || expectedSize > cap)) {
      refuse('declared_size', 'The selected source file exceeds its declared download bound.');
    }
    const url = new URL(path, base);
    if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) refuse('member_path', 'Source download escaped its declared publication.');
    const response = await fetcher(url.href, {redirect: 'error', credentials: 'same-origin', signal});
    async function cancel(code, message) {
      await response.body?.cancel().catch(() => {});
      refuse(code, message);
    }
    if (!response.ok || response.url && response.url !== url.href) {
      return cancel('http_response', 'The selected source file could not be loaded from its declared location.');
    }
    // Fetch decodes content encodings; wire length is not the original file length.
    const encoded = Boolean(response.headers.get('Content-Encoding')
      && response.headers.get('Content-Encoding').trim().toLowerCase() !== 'identity');
    const declared = response.headers.get('Content-Length');
    if (declared !== null && (!/^[0-9]+$/.test(declared) || !Number.isSafeInteger(Number(declared))
      || Number(declared) > cap || !encoded && expectedSize !== undefined && Number(declared) !== expectedSize)) {
      return cancel('response_size', 'The source response size differs from the declared file.');
    }
    if (!response.body || typeof response.body.getReader !== 'function') {
      return cancel('stream_unavailable', 'Bounded source download streaming is unavailable in this browser.');
    }
    const reader = response.body.getReader(), chunks = [];
    let total = 0;
    try {
      while (true) {
        const next = await reader.read();
        if (next.done) break;
        if (!(next.value instanceof Uint8Array) || next.value.byteLength > cap - total
          || expectedSize !== undefined && next.value.byteLength > expectedSize - total) {
          await reader.cancel();
          refuse('response_size', 'The source response exceeded its declared file size.');
        }
        total += next.value.byteLength;
        chunks.push(next.value);
      }
    } finally { reader.releaseLock(); }
    if (expectedSize !== undefined && total !== expectedSize) refuse('response_size', 'The source response ended before its declared file size.');
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    const actual = [...new Uint8Array(await cryptoProvider.subtle.digest('SHA-256', bytes))]
      .map(value => value.toString(16).padStart(2, '0')).join('');
    if (actual !== expectedDigest) refuse('file_digest', 'Source file verification failed. The original bytes were not downloaded.');
    return bytes;
  }
  function object(bytes) {
    try {
      const value = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
      if (!ordinary(value)) throw Error('Not an object');
      return value;
    } catch { refuse('metadata_json', 'The shared source metadata is not a valid JSON object.'); }
  }
  function fileMember(manifest, path, cap) {
    memberPath(path);
    const member = manifest.files[path];
    if (!ordinary(member) || Object.keys(member).sort().join('|') !== 'bytes|sha256'
      || !Number.isSafeInteger(member.bytes) || member.bytes < 0 || member.bytes > cap || !digest(member.sha256)) {
      refuse('declared_size', 'The selected source file has no valid bounded manifest member.');
    }
    return member;
  }
  async function loadArchive(signal) {
    const metadata = await context(), reference = metadata?.provenance?.source_archive;
    if (reference?.schema_version !== 'atlas-source-resource-archive-reference.v1'
      || reference.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || !digest(reference.manifest_sha256) || reference.index?.path !== 'downloads/index.json'
      || reference.validation_scope !== 'manifest_and_download_index_only'
      || reference.scientific_admission !== 'not_asserted') refuse('archive_reference', 'This catalogue has no independently pinned source download publication.');
    const base = baseURL(reference);
    const manifest = object(await buffer(base, 'manifest.json', reference.manifest_sha256, undefined, metadataCap, signal));
    if (manifest.schema_version !== 'neotoma-source-resource-archive.v1'
      || manifest.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || manifest.scientific_admission !== 'not_asserted' || manifest.historical_snapshot_replaced !== false
      || !ordinary(manifest.files) || Object.keys(manifest.files).length > 20000) refuse('archive_manifest', 'The source publication manifest does not match this catalogue.');
    let total = 0;
    for (const path of Object.keys(manifest.files)) total += fileMember(manifest, path, 512 * 1024 * 1024).bytes;
    if (!Number.isSafeInteger(total) || total > 512 * 1024 * 1024 || manifest.source_bytes !== total) refuse('archive_manifest', 'The source publication byte population differs.');
    const declaration = fileMember(manifest, 'downloads/index.json', metadataCap);
    if (declaration.bytes !== reference.index.bytes || declaration.sha256 !== reference.index.sha256) refuse('index_identity', 'The source download index differs from its catalogue reference.');
    const index = object(await buffer(base, 'downloads/index.json', declaration.sha256, declaration.bytes, metadataCap, signal));
    if (index.schema_version !== 'neotoma-source-download-index.v1'
      || index.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || index.scientific_admission !== 'not_asserted' || !Array.isArray(index.resources)
      || index.resources.length !== 2 * domain.record_count) refuse('index_identity', 'The source download index population differs.');
    const seen = new Set(), partitions = {};
    for (const row of index.resources) {
      const key = `${row.dataset_id}:${row.version}`;
      if (![row.dataset_id,row.site_id,row.collection_unit_id].every(nativeId)
        || !['current','doi_frozen'].includes(row.version) || seen.has(key)
        || row.scientific_admission !== 'not_asserted' || row.use_scope !== 'source_entity_download_only'
        || !['available_source_entity','unavailable_source_entity','blocked_exposure_role'].includes(row.state)) refuse('index_identity', 'The source download index contains an ambiguous resource.');
      seen.add(key);
      partitions[row.state] = (partitions[row.state] || 0) + 1;
      if (!development.has(row.exposure_role) && (row.state !== 'blocked_exposure_role'
        || 'download_path' in row || 'source' in row)) refuse('blocked_role', 'A protected resource has an unowned source download link.');
    }
    if (stable(partitions) !== stable(index.partitions)) refuse('index_identity', 'The source download state counts differ.');
    return {base, manifest, index};
  }
  // Shared metadata survives cancellation of an individual selected download.
  function archive() {
    return archiveRequest ||= loadArchive().catch(error => { archiveRequest = null; throw error; });
  }
  function active(signal) {
    if (signal?.aborted) throw new DOMException('The selected source download was cancelled.', 'AbortError');
  }
  async function download(dataset, version, kind = 'body', {signal} = {}) {
    active(signal);
    if (!nativeId(dataset) || !['current','doi_frozen'].includes(version)) refuse('resource_identity', 'Select one exact native dataset and version.');
    const record = await resource(dataset);
    if (!record || record.dataset_id !== dataset || !ordinary(record.versions?.[version])) refuse('resource_identity', 'The selected native resource is unavailable.');
    if (!development.has(record.exposure_role)) refuse('blocked_role', 'This resource is metadata-only under its declared exposure role.');
    active(signal);
    const publication = await archive(), selected = record.versions[version];
    active(signal);
    const row = publication.index.resources.find(value => value.dataset_id === dataset && value.version === version);
    const statuses = Object.fromEntries(Object.entries(selected).filter(([key]) => key.endsWith('_status')));
    if (!row || ['dataset_id','site_id','collection_unit_id','exposure_role'].some(key => row[key] !== record[key])
      || stable(row.statuses) !== stable(statuses) || stable(row.source ?? null) !== stable(selected.source ?? null)) {
      refuse('resource_identity', 'The selected source version does not match its catalogue identity, role or status.');
    }
    let path, cap;
    if (kind === 'receipt') {
      if (row.source?.source_kind !== 'source_http_attempt' || !digest(row.source.capture_manifest_sha256)
        || !digest(row.source.receipt_sha256)) refuse('source_unavailable', 'No captured HTTP receipt is available for this source version.');
      path = `captures/${row.source.capture_manifest_sha256}/${memberPath(row.source.receipt_file)}`;
      cap = metadataCap;
    } else {
      if (row.state !== 'available_source_entity') refuse('source_unavailable', 'No complete public source entity is available for this version.');
      const source = row.source;
      if (source?.source_kind === 'retained_public_response') {
        path = `captures/retained/dataset-${dataset}-${version}/native.body`;
      } else if (source?.source_kind === 'source_http_attempt' && source.http_status === 200
        && source.body_complete === true && digest(source.capture_manifest_sha256)) {
        path = `captures/${source.capture_manifest_sha256}/${memberPath(source.body_file)}`;
      } else refuse('source_unavailable', 'No complete public source entity is available for this version.');
      if (path !== row.download_path) refuse('resource_identity', 'The source entity path differs from its captured identity.');
      cap = bodyCap;
    }
    const member = fileMember(publication.manifest, path, cap);
    const expectedDigest = kind === 'receipt' ? row.source.receipt_sha256 : row.source.body_sha256;
    if (member.sha256 !== expectedDigest || kind !== 'receipt' && 'body_bytes' in row.source
      && row.source.body_bytes !== member.bytes) refuse('resource_identity', 'The selected source file identity differs from its receipt.');
    active(signal);
    const bytes = await buffer(publication.base, path, member.sha256, member.bytes, cap, signal);
    active(signal);
    return {bytes, filename: path.split('/').at(-1), sha256: member.sha256, dataset_id: dataset, version,
      scientific_admission: 'not_asserted', source: row.source};
  }
  return Object.freeze({body: (dataset, version, options) => download(dataset, version, 'body', options),
    receipt: (dataset, version, options) => download(dataset, version, 'receipt', options)});
}

      // Ancillary metadata has its own identities and counts, never dataset or sample mass.
function createSourceResourceAncillaryContract(domain, fail) {
  const counts = domain.schema_version === 'atlas-source-resources.v2' ? {
    ancillary_context: null, facet_slots: 'ancillary_slot_count', ancillary_observations: 'ancillary_observation_count',
    linked_occurrences: 'ancillary_linked_occurrence_count', supporting_archives: 'supporting_archive_count', supporting_entries: 'supporting_entry_count'
  } : {};
  const kinds = Object.keys(counts), support = {unit_metadata:'units', reference_tables:'tables', context_resources:'resources', taxon_ancestry:'targets'};
  const isSupport = kind => kind.startsWith('supporting_');
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const native = value => Number.isSafeInteger(value) && value > 0;
  const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  const literal = value => typeof value === 'string' && value.length > 0 && value.length <= 4096;
  function metadata(value) {
    if (Array.isArray(value)) { value.forEach(metadata); return; }
    if (!object(value)) { if (value !== null && !['string','number','boolean'].includes(typeof value)) fail('non-JSON ancillary metadata'); if (typeof value === 'number' && !Number.isFinite(value)) fail('nonfinite ancillary metadata'); return; }
    for (const [key, item] of Object.entries(value)) {
      if (['native_body','native_payload','body_buffer','href','download_url'].includes(key)) fail('native body or route is outside ancillary metadata');
      if (['entity_body_hashes_verified','source_entity_bodies_verified','body_hashes_verified','native_profiles_verified','native_field_value_verified','source_assessments_replayed','related_resource_graph_complete','current_roles_revalidated','native_source_fields_revalidated','GET_authorized'].includes(key) && item !== false
        || key === 'scientific_admission' && item !== 'not_asserted') fail('ancillary metadata cannot elevate source verification or scientific admission');
      if (key === 'native_entity_bodies_opened' && item !== 0) fail('native bodies are outside metadata');
      metadata(item);
    }
  }
  function valid(kind, identity) {
    if (!kinds.includes(kind) || !literal(identity)) return false;
    if (kind === 'ancillary_context') return identity === 'ancillary';
    if (isSupport(kind)) {
      const [archive,pin,population,ordinal,...extra] = identity.split(':');
      if (!Object.hasOwn(support,archive) || !hash(pin)) return false;
      return kind === 'supporting_archives' ? population === undefined
        : support[archive] === population && /^(0|[1-9][0-9]*)$/.test(ordinal || '') && Number.isSafeInteger(Number(ordinal)) && !extra.length;
    }
    return true;
  }
  // Canonical IDs bound safe ordinals; explicit types prevent string/boolean coercion.
  function identity(kind, row) {
    metadata(row);
    let value;
    if (isSupport(kind)) {
      value = `${row.archive_kind}:${row.archive_manifest_sha256}`;
      if (kind === 'supporting_entries') value += `:${row.population}:${row.row_index}`;
      if (kind === 'supporting_entries' && (typeof row.row_index !== 'number' || !object(row.entry))) fail('supporting metadata row differs');
    } else value = row[{ancillary_context:'record_id',facet_slots:'slot_key',ancillary_observations:'observation_id',linked_occurrences:'occurrence_id'}[kind]];
    if (!valid(kind,value)) fail('ancillary record identity differs');
    if (isSupport(kind) && row.archive_kind === 'taxon_ancestry') {
      const entry = kind === 'supporting_entries', target = entry ? row.entry : row;
      if (target.integrity_scope !== (entry ? 'anchored_selected_metadata_parts_only' : 'SELECTED_RECORDED_TARGETS_ONLY')
        || target.current_roles_revalidated !== false || target.native_source_fields_revalidated !== false
        || target.GET_authorized !== false || target.native_entity_bodies_opened !== 0 || target.scientific_admission !== 'not_asserted') fail('selected ancestry posture differs');
      if (entry && (!['taxon','publication'].includes(target.kind) || !native(target.native_id)
        || target.target_key !== `${target.kind}-${target.native_id}` || !object(target.recorded_node)
        || target.recorded_node.target_kind !== target.kind || ['target_key','native_id'].some(key=>target.recorded_node[key] !== target[key]))) fail('selected ancestry native owner differs');
    }
    if (kind === 'ancillary_context' && (!object(row.source_manifest) || !object(row.summary) || !object(row.provenance))) fail('ancillary context differs');
    if (kind === 'facet_slots' && (!object(row.root_identity) || !['dataset_id','site_id','collection_unit_id'].every(key=>native(row.root_identity[key]))
      || value !== `dataset-${row.root_identity.dataset_id}-facet-${row.facet}-current`)) fail('facet native owner differs');
    if (kind === 'ancillary_observations' && (!['facet','linked'].includes(row.kind) || !object(row.capture_epoch)
      || row.selected_by_default !== false || !hash(row.source_capture_manifest_sha256) || !hash(row.capsule_manifest_sha256)
      || value !== `${row.source_capture_manifest_sha256}:${row.source_entry_pointer}`)) fail('captured observation identity differs');
    return value;
  }
  function index(row) {
    metadata(row);
    if (!valid(row.entity_type,row.record_id)) fail('ancillary index identity differs');
    if (row.entity_type === 'facet_slots' && (!native(row.root_dataset_id) || !native(row.site_id) || !native(row.collection_unit_id)
      || row.record_id !== `dataset-${row.root_dataset_id}-facet-${row.facet}-current`)) fail('facet index owner differs');
    if (row.entity_type === 'ancillary_observations' && (!['facet','linked'].includes(row.kind) || !hash(row.source_capture_manifest_sha256)
      || !object(row.capture_epoch))) fail('observation index kind or epoch differs');
    if (isSupport(row.entity_type)) {
      const expected = `${row.archive_kind}:${row.archive_manifest_sha256}` + (row.entity_type === 'supporting_entries' ? `:${row.population}:${row.row_index}` : '');
      if (row.record_id !== expected || row.entity_type === 'supporting_entries' && typeof row.row_index !== 'number') fail('supporting index identity differs');
    }
  }
  // Match the producer's ancillary_index_entry projection without loading other parts.
  function projection(kind,row,partId) {
    const result={entity_type:kind,record_id:identity(kind,row),part_id:partId};
    const take=(owner,fields)=>{
      if(!object(owner) || fields.some(key=>!Object.hasOwn(owner,key)))fail('indexed source fields are absent');
      return Object.fromEntries(fields.map(key=>[key,owner[key]]));
    };
    const owner=()=>{
      const nativeOwner=take(row.root_identity,['dataset_id','site_id','collection_unit_id','dataset_type']);
      return {root_dataset_id:nativeOwner.dataset_id,site_id:nativeOwner.site_id,
        collection_unit_id:nativeOwner.collection_unit_id,dataset_type:nativeOwner.dataset_type};
    };
    if(kind==='facet_slots')Object.assign(result,owner(),take(row,['facet','current_use_role','coverage_status','current_declared_role']));
    else if(kind==='ancillary_observations') {
      Object.assign(result,take(row,['kind','terminal_status','current_owner_join','current_use_role','source_capture_manifest_sha256','capture_epoch']));
      if(row.kind==='facet')Object.assign(result,owner(),take(row,['facet','facet_key']),{original_role:row.parent_scope_role ?? null});
      else Object.assign(result,{linked_kind:row.identity?.kind,native_id:row.identity?.native_id});
    } else if(kind==='linked_occurrences')Object.assign(result,take(row,['observation_id','current_owner_join','current_use_role']),
      {root_dataset_id:Object.hasOwn(row,'root_dataset_id')?row.root_dataset_id:row.source_proof?.root_dataset_id ?? null});
    else if(isSupport(kind)) {
      Object.assign(result,take(row,['archive_kind','archive_manifest_sha256']));
      if(kind==='supporting_entries')Object.assign(result,take(row,['row_index','population']),{
        source_selectors:Object.fromEntries(Object.entries(row.entry).filter(([key])=>['unit_key','resource_key','table_key','table','site_id','terminal_status'].includes(key) || row.archive_kind==='taxon_ancestry' && ['target_key','kind','native_id'].includes(key))),scope:row.entry.scope ?? null});
    }
    metadata(result);
    return result;
  }
  function same(left,right) {
    if(left===right)return true;
    if(left===null || right===null || typeof left!=='object' || typeof right!=='object' || Array.isArray(left)!==Array.isArray(right))return false;
    const keys=Object.keys(left);
    return keys.length===Object.keys(right).length && keys.every(key=>Object.hasOwn(right,key) && same(left[key],right[key]));
  }
  return Object.freeze({kinds, counts, metadata, valid, identity, index, projection, same});
}

// Read only independently pinned catalogue metadata through the common asset loader.
function createSourceResourceBrowser({manifest, loadAsset, payloadForAsset, downloadTransport = {}, readerContext = {}}) {
  const domain = manifest?.domains?.resources;
  const fail = message => { throw Error(`Source resource metadata: ${message}`); };
  if (!domain || !['atlas-source-resources.v1','atlas-source-resources.v2'].includes(domain.schema_version)
    || !/^[a-f0-9]{64}$/.test(domain.catalogue_manifest_sha256 || '')
    || domain.source_family !== 'neotoma' || domain.scientific_admission !== 'not_asserted'
    || domain.numerical_atlas_denominator_changed !== false || domain.initial_load !== false
    || domain.payload_encoding !== 'gzip_base64' || domain.metadata_only !== true
    || !Array.isArray(manifest.assets)
    || typeof loadAsset !== 'function' || typeof payloadForAsset !== 'function') fail('catalogue or loader unavailable');
  const ancillary = createSourceResourceAncillaryContract(domain, fail);
  const populations = {resources:'record_count',sites:'site_count',descriptors:'source_descriptor_count',...ancillary.counts};
  const mapping = domain.part_asset_keys;
  if (!mapping || Array.isArray(mapping) || typeof mapping !== 'object'
    || !Array.isArray(domain.index_part_ids)
    || !Number.isSafeInteger(domain.part_count) || Object.keys(mapping).length !== domain.part_count
    || new Set(Object.values(mapping)).size !== domain.part_count
    || new Set(domain.index_part_ids).size !== domain.index_part_ids.length) fail('part inventory differs');
  const allowedKinds=['context','index',...Object.keys(populations)], ordinals=new Map();
  for (const [partId,key] of Object.entries(mapping)) {
    const [kind,number,...extra]=partId.split(':');
    if (!allowedKinds.includes(kind) || !/^(0|[1-9][0-9]*)$/.test(number || '') || extra.length
      || typeof key !== 'string' || !key || !manifest.assets.some(row=>row.asset_key===key && row.domain==='resources')) fail('part kind or binding differs');
    if(!ordinals.has(kind))ordinals.set(kind,[]);ordinals.get(kind).push(Number(number));
  }
  for(const values of ordinals.values())if(values.sort((a,b)=>a-b).some((value,number)=>value!==number))fail('part sequence differs');
  if (domain.index_part_ids.some((id,number)=>id!==`index:${number}` || !Object.hasOwn(mapping,id))
    || (ordinals.get('index')?.length || 0)!==domain.index_part_ids.length
    || ordinals.get('context')?.length!==1 || !Object.hasOwn(mapping,'context:0')
    || ancillary.kinds.length && domain.ancillary_context_part_id !== 'ancillary_context:0') fail('index or ancillary context part differs');
  const payloads = new Map(), index = new Map(), partCounts = new Map();
  let indexRequest = null;
  const clone = value => JSON.parse(JSON.stringify(value));
  const nativeId = value => typeof value === 'string' && /^[1-9][0-9]*$/.test(value);
  const rowId = (kind, row) => ancillary.kinds.includes(kind) ? ancillary.identity(kind,row)
    : kind === 'resources' ? row.dataset_id : kind === 'sites' ? row.site_id : row.record_id;
  const count = name => {
    if (!Number.isSafeInteger(domain[name]) || domain[name] < 0) fail(`invalid ${name}`);
    return domain[name];
  };
  function consume(row, payload) {
    if (row?.domain !== 'resources' || payload?.schema_version !== 'atlas-source-resource-chunk.v1'
      || payload.source_family !== 'neotoma' || payload.catalogue_manifest_sha256 !== domain.catalogue_manifest_sha256
      || payload.scientific_admission !== 'not_asserted'
      || !['context','sites','resources','descriptors','index',...ancillary.kinds].includes(payload.kind)
      || mapping[payload.part_id] !== row.asset_key || payload.asset_key !== row.asset_key
      || !Array.isArray(payload.records) || !payload.records.length || row.record_count !== payload.records.length) fail('part identity differs');
    const seen = new Set();
    for (const record of payload.records) {
      if (!record || typeof record !== 'object' || Array.isArray(record)) fail('record is malformed');
      if (payload.kind === 'index') continue;
      const identity = rowId(payload.kind, record);
      if ((['resources','sites'].includes(payload.kind) && !nativeId(identity))
        || (payload.kind === 'descriptors' && !/^[a-f0-9]{64}$/.test(identity || ''))
        || (payload.kind === 'context' && identity !== 'catalogue') || seen.has(identity)) fail('record identity repeats or differs');
      seen.add(identity);
      if (payload.kind === 'resources' && ('native_body' in record || 'native_payload' in record)) fail('native body is outside metadata transport');
    }
    const old = payloads.get(payload.part_id);
    if (old && JSON.stringify(old) !== JSON.stringify(payload)) fail('part was replaced');
    payloads.set(payload.part_id, payload);
  }
  async function part(identity) {
    const key = mapping[identity];
    const row = manifest.assets.find(candidate => candidate.asset_key === key && candidate.domain === 'resources');
    if (!row) fail('part is absent from the asset inventory');
    if (!payloads.has(identity)) {
      await loadAsset(row);
      const payload = payloadForAsset(key);
      if (!payload) fail('loaded metadata part unavailable');
      consume(row, payload);
    }
    return payloads.get(identity);
  }
  function loadIndex() {
    if(indexRequest)return indexRequest;
    indexRequest = (async () => {
      const next = new Map();
      const parts = await Promise.all(domain.index_part_ids.map(part));
      for (const payload of parts) {
        if (payload.kind !== 'index') fail('index part has another kind');
        for (const record of payload.records) {
          const kind = record.entity_type, identity = record.record_id, key = `${kind}:${identity}`;
          if (!Object.hasOwn(populations,kind)
            || (ancillary.kinds.includes(kind) ? !ancillary.valid(kind,identity) : kind === 'descriptors' ? !/^[a-f0-9]{64}$/.test(identity || '') : !nativeId(identity))
            || typeof record.part_id !== 'string' || !record.part_id.startsWith(`${kind}:`)
            || !mapping[record.part_id] || next.has(key)) fail('index identity repeats or dangles');
          if (ancillary.kinds.includes(kind)) ancillary.index(record);
          next.set(key, record);
        }
      }
      const referenced=new Set([...next.values()].map(row=>row.part_id));
      if(Object.keys(mapping).some(id=>!id.startsWith('index:') && id!=='context:0' && !referenced.has(id)))fail('metadata part has no index membership');
      for (const [kind, field] of Object.entries(populations)) {
        if ([...next.values()].filter(row => row.entity_type === kind).length !== (field === null ? 1 : count(field))) fail('index population differs');
      }
      if (ancillary.kinds.length && (count('ancillary_facet_observation_count') + count('ancillary_linked_observation_count') !== count('ancillary_observation_count')
        || [...next.values()].filter(row=>row.entity_type==='ancillary_observations' && row.kind==='facet').length !== count('ancillary_facet_observation_count')
        || [...next.values()].filter(row=>row.entity_type==='ancillary_observations' && row.kind==='linked').length !== count('ancillary_linked_observation_count'))) fail('ancillary observation population differs');
      if (count('version_status_count') !== 2 * count('record_count')) fail('version population differs');
      next.forEach((value,key)=>{index.set(key,value);partCounts.set(value.part_id,(partCounts.get(value.part_id)||0)+1);});
    })();
    indexRequest = indexRequest.catch(error=>{indexRequest=null;throw error;});
    return indexRequest;
  }
  async function record(kind, identity) {
    if (!Object.hasOwn(populations,kind) || (ancillary.kinds.includes(kind) ? !ancillary.valid(kind,identity) : !nativeId(identity) && kind !== 'descriptors')) fail('native identity is invalid');
    await loadIndex();
    const reference = index.get(`${kind}:${identity}`);
    if (!reference) return null;
    const payload = await part(reference.part_id);
    if (payload.kind !== kind) fail('record reference has another kind');
    if (ancillary.kinds.includes(kind)) {
      if(partCounts.get(payload.part_id)!==payload.records.length)fail('selected ancillary part membership differs');
      const seen=new Set();
      for(const member of payload.records) {
        const projected=ancillary.projection(kind,member,payload.part_id);
        if(seen.has(projected.record_id) || !ancillary.same(projected,index.get(`${kind}:${projected.record_id}`)))fail('selected ancillary index owner or source posture differs');
        seen.add(projected.record_id);
      }
    }
    const found = payload.records.find(row => rowId(kind, row) === identity);
    if (!found) fail('referenced record is absent');
    return clone(found);
  }
  async function search(query = '', filters = {}) {
    const population=filters.population || 'resources';
    if (!Object.hasOwn(populations,population) || ['sites','descriptors'].includes(population)) fail('unsupported search population');
    if (population !== 'resources' && Object.keys(filters).some(key=>key!=='population')) fail('native filters do not apply to the catalogue-wide ancillary population');
    await loadIndex();
    const text = String(query).trim().toLocaleLowerCase();
    return [...index.values()].filter(row => {
      if (row.entity_type !== population) return false;
      if (population !== 'resources') return !text || JSON.stringify(row).toLocaleLowerCase().includes(text);
      const site = index.get(`sites:${row.site_id}`), names = site?.native_site_names || [];
      return (!filters.country || (row.country_code ?? 'UNASSIGNED') === filters.country)
        && (!filters.type || row.dataset_type === filters.type)
        && (!filters.role || row.exposure_role === filters.role)
        && (!filters.statusField || Object.hasOwn(row.version_statuses?.[filters.version] || {}, filters.statusField)
          && row.version_statuses[filters.version][filters.statusField] === filters.status)
        && (!text || [row.record_id, row.site_id, row.collection_unit_id, row.dataset_type, row.country_code, ...names].join(' ').toLocaleLowerCase().includes(text));
    }).map(clone);
  }
  async function inventory() {
    await loadIndex();
    return Object.fromEntries(Object.keys(populations).map(kind => [kind,
      [...index.values()].filter(row => row.entity_type === kind).map(clone)]));
  }
  async function context() {
    if (domain.context_part_id !== undefined && domain.context_part_id !== 'context:0') fail('context part identity differs');
    const payload = await part(domain.context_part_id ?? 'context:0');
    if (payload.kind !== 'context' || payload.records.length !== 1 || payload.records[0].record_id !== 'catalogue') fail('catalogue context differs');
    return clone(payload.records[0]);
  }
  let reader = null;
  const api = {consume, loadIndex, search, inventory, context, site: identity => record('sites', identity), resource: identity => record('resources', identity), ancillary:(kind,identity)=>{if(!ancillary.kinds.includes(kind))fail('unknown ancillary kind');return record(kind,identity);}};
  let downloads = null;
  function downloadManager() {
    return downloads ||= createSourceResourceDownloads({domain, context, resource: identity => record('resources', identity),
      fetcher: downloadTransport.fetcher, cryptoProvider: downloadTransport.cryptoProvider, location: downloadTransport.location});
  }
  return Object.freeze(Object.assign(api, {open: selection => (reader ||= createSourceResourceReader({...readerContext,browser:api,domain})).open(selection),
    countriesChanged: () => reader?.countriesChanged(),
    downloadResource: (identity, version, options) => downloadManager().body(identity, version, options),
    downloadReceipt: (identity, version, options) => downloadManager().receipt(identity, version, options)}));
}

      // Bind the existing source renderers to their owning table and escaping functions.
function createSourceRecordDetails(bindings) {
  const {detailTableShape, decodeDetailTableRow, detailTableText, renderDetailTable, renderDetailObjectEntries, escapeHtml} = bindings;
  if (![detailTableShape, decodeDetailTableRow, detailTableText, renderDetailTable, escapeHtml].every(value => typeof value === 'function')) {
    throw Error('Source detail renderer bindings are unavailable.');
  }
  // Source relationships and assertions are display context, not analysis admission.
function sourceRecordRows(table, required) {
  if (!detailTableShape(table) || table.record_count !== table.records.length
    || new Set(table.fields).size !== table.fields.length
    || required.some(field => !table.fields.includes(field))) throw Error('source table unavailable');
  return table.records.map(row => decodeDetailTableRow(table,row));
}
function sourceRecordFields(rows) {
  return rows.map(([label,value]) => `<div class="focus-detail-row"><span class="focus-detail-key">${escapeHtml(label)}</span><span>${escapeHtml(detailTableText(value))}</span></div>`).join('');
}
function sourceRecordSignalMatchesSite(tabs, feature) {
  const identifier = value => typeof value === 'string' && value.trim() && value === value.trim();
  return [feature?.record_id,feature?.source_record_id,feature?.source_snapshot_id,feature?.build_id,
    tabs?.overview?.site_id,tabs?.provenance?.source_snapshot_id,tabs?.provenance?.build_id].every(identifier)
    && feature.record_id === tabs.overview.site_id
    && feature.source_snapshot_id === tabs.provenance.source_snapshot_id
    && feature.build_id === tabs.provenance.build_id;
}
function nativeCharcoalSourceSignal(tabs, feature) {
  const unavailable = reason => ({status:'unavailable',reason});
  if (tabs?.overview?.source_family !== 'neotoma' || feature?.source_family !== 'neotoma'
    || feature.semantic_role !== 'native_charcoal_source_context' || feature.node_level !== 'native_charcoal_observation'
    || feature.source_join_status !== 'retained' || feature.propagation_eligible !== false
    || feature.candidate_generation_status !== 'refused' || feature.record_count !== 1 || feature.observation_denominator !== 1) return unavailable('Selected feature has no supported literal CHAR source posture.');
  if (!sourceRecordSignalMatchesSite(tabs,feature)
    || feature.site_id !== tabs.overview.site_id
    || ({DK:'Denmark',FI:'Finland',NO:'Norway',SE:'Sweden'})[tabs.overview.country_code] !== feature.country
    || !Number.isFinite(feature.latitude) || !Number.isFinite(feature.longitude)
    || Math.abs(feature.latitude) > 90 || Math.abs(feature.longitude) > 180) return unavailable('Selected CHAR feature and detail site or source epoch do not agree.');
  try {
    const fields = ['sample_id','variable_id','source_taxon_id','source_value','source_unit','source_denominator',
      'denominator_status','detection_status','source_context','source_ecological_group','source_element','source_element_type','unit_family','source_part_number'];
    const observations = sourceRecordRows(tabs.pollen_composition,['observation_id',...fields]);
    const matched = observations.filter(row => row.observation_id === feature.observation_id);
    if (typeof feature.observation_id !== 'string' || !feature.observation_id || feature.observation_id.trim() !== feature.observation_id
      || matched.length !== 1 || feature.node_id !== `neotoma:native-charcoal:${feature.observation_id}`) return unavailable('Selected native CHAR observation identity is missing or ambiguous.');
    const observation = matched[0];
    if (observation.source_ecological_group !== 'CHAR' || feature.source_ecological_group !== 'CHAR'
      || fields.some(field => JSON.stringify(observation[field]) !== JSON.stringify(feature[field]))) return unavailable('Selected CHAR assertion differs from its retained native observation.');
    const part = observation.source_part_number;
    if (!Number.isSafeInteger(part) || part < 1
      || feature.source_observation_locator !== `surfaces/observations/part-${String(part).padStart(5,'0')}.json#observation_id=${feature.observation_id}`) return unavailable('Selected CHAR source locator is unavailable or inconsistent.');
    const samples = sourceRecordRows(tabs.samples?.samples,['sample_id','dataset_id','collection_unit_id','source_depth']);
    const sampleMatches = samples.filter(row => row.sample_id === observation.sample_id);
    if (sampleMatches.length !== 1 || feature.source_record_id !== observation.sample_id) return unavailable('Selected CHAR sample identity is unavailable or ambiguous.');
    const sample = sampleMatches[0];
    const datasets = sourceRecordRows(tabs.samples?.datasets,['dataset_id','collection_unit_id']);
    const units = sourceRecordRows(tabs.samples?.collection_units,['collection_unit_id']);
    const variables = sourceRecordRows(tabs.pollen_composition.variables,['variable_id','source_taxon_id']);
    const datasetMatches = datasets.filter(row => row.dataset_id === sample.dataset_id);
    const variableMatches = variables.filter(row => row.variable_id === observation.variable_id);
    if (sample.dataset_id !== feature.dataset_id || sample.collection_unit_id !== feature.collection_unit_id
      || JSON.stringify(sample.source_depth) !== JSON.stringify(feature.source_depth)
      || datasetMatches.length !== 1 || datasetMatches[0].collection_unit_id !== sample.collection_unit_id
      || units.filter(row => row.collection_unit_id === sample.collection_unit_id).length !== 1
      || variableMatches.length !== 1 || variableMatches[0].source_taxon_id !== observation.source_taxon_id) return unavailable('Selected CHAR variable, sample, dataset or collection relations do not reconcile uniquely.');
    return {status:'matched',reason:'',observation,sample};
  } catch { return unavailable('Native CHAR source tables are unavailable or cannot be decoded consistently.'); }
}
function renderNativeCharcoalObservation(tabs, feature, data) {
  const heading = '<h3>Literal CHAR source observation</h3>';
  if (data.status !== 'matched') return `<section data-native-charcoal-details="unavailable">${heading}<p>${escapeHtml(data.reason)} Original source observations remain in the source table.</p></section>`;
  const row = data.observation;
  const fields = [['Source observation ID',row.observation_id],['Native sample ID',row.sample_id],
    ['Taxon-derived variable key',row.variable_id],['Native source taxon ID',row.source_taxon_id],
    ['Source-reported variable provenance',Object.hasOwn(row,'source_variable_provenance') ? row.source_variable_provenance : 'not available in this compact document'],
    ['Literal source ecological code',row.source_ecological_group],['Native reported value',row.source_value],
    ['Source measurement unit',row.source_unit],['Denominator',row.source_denominator],
    ['Denominator status',row.denominator_status],['Detection status',row.detection_status],
    ['Source element',row.source_element],['Source element type',row.source_element_type],
    ['Source context',row.source_context],['Native source depth',data.sample.source_depth],
    ['Observation identity denominator',feature.observation_denominator],['Source observation locator',feature.source_observation_locator]];
  return `<section data-native-charcoal-details="matched">${heading}<p>One literal native observation; no fire, vegetation, cultivation or pollen corroboration is inferred. Material fractions, values, units, denominator and detection states remain separate. Missing is not zero; no fraction sum or ecological event is calculated. Source chronology remains a separate assertion.</p>${sourceRecordFields(fields)}</section>`;
}
function renderSourceChronologyIssues(tabs) {
  const unavailable = () => '<section aria-label="Source chronology review" data-source-chronology-review="unavailable"><h3>Source chronology review</h3><p>Source issue review is not available in these retained tables. This does not establish that no source issues exist. Original model, control and age tables remain below.</p></section>';
  const issues = tabs?.chronology?.source_issues;
  if (!issues || issues.status === 'unavailable') return unavailable();
  try {
    const conflicts = sourceRecordRows(issues.conflicts,['conflict_id']);
    const orphans = sourceRecordRows(issues.orphans,['orphan_id']);
    const variants = sourceRecordRows(issues.chronology_control_variants,['conflict_id','variant_index']);
    let references = 'Reference verification was not supplied with these model rows.';
    if (detailTableShape(tabs.chronology.models)) {
      const models = sourceRecordRows(tabs.chronology.models,['chronology_id']);
      if (models.every(row => typeof row.reference_verification_status === 'string')) {
        const count = models.filter(row => row.reference_verification_status === 'refused_missing_source_identifier').length;
        references = `${count} model${count === 1 ? ' lacks' : 's lack'} an identified native reference and ${count === 1 ? 'is' : 'are'} not treated as referenced selections. Original projection flags remain visible beside their effective reference status.`;
      }
    }
    const sections = [['conflicts','Retained source conflicts'],['orphans','Retained source orphans'],['chronology_control_variants','Constituent dated-specimen variants']];
    const metadata = sourceRecordFields(Object.entries(issues).filter(([key]) => !sections.some(([name]) => key === name)));
    const tables = sections.map(([key,label]) => `<h4>${escapeHtml(label)}</h4>${renderDetailTable(issues[key], `chronology.source_issues.${key}`)}`).join('');
    return `<section aria-label="Source chronology review" data-source-chronology-review="available"><h3>Source chronology review</h3><p>${conflicts.length} retained conflict records, ${orphans.length} orphan records and ${variants.length} constituent dated-specimen variants. A source control may combine several dated specimens. Canonical storage does not select a specimen or an analysis chronology.</p><p>${escapeHtml(references)}</p><p>All retained issue records, variants and native locators remain in the tables below and the source record download. These records are not additional pollen observations or independent validation data.</p>${metadata}${tables}</section>`;
  } catch { return unavailable(); }
}
function renderSourceChronologyQuality(tabs) {
  const unavailable = () => '<section aria-label="Source chronology support" data-source-chronology-quality="unavailable"><h3>Source chronology support</h3><p>Matching chronology-quality metadata is unavailable or could not be decoded. This does not establish that no chronology-quality issues exist. Original chronology tables and source downloads remain available.</p></section>';
  const quality = tabs?.chronology?.source_quality;
  if (!quality || !sourceChronologyQualityMatches(tabs)) return unavailable();
  try {
    const profiles = sourceRecordRows(quality.profiles,['profile_id','flags']);
    const samples = sourceRecordRows(quality.sample_flags,['sample_id','flags']);
    const claims = sourceRecordRows(quality.claim_diagnostics,['chronology_claim_id','sample_id','profile_id','point_status','flags']);
    const counts = quality.site_denominators;
    if (counts?.profiles !== profiles.length || counts?.samples !== samples.length || counts?.age_claims !== claims.length
      || quality.source_profile?.eligibility_changed !== false || quality.source_profile?.chronology_selected !== false) return unavailable();
    const sections = [['profiles','Source chronology profiles'],['sample_flags','Sample flags across profiles'],['claim_diagnostics','Individual age-claim diagnostics']];
    const metadata = sourceRecordFields(Object.entries(quality).filter(([key]) => !sections.some(([name]) => key === name)));
    const tables = sections.map(([key,label]) => `<h4>${escapeHtml(label)}</h4>${renderDetailTable(quality[key], `chronology.source_quality.${key}`)}`).join('');
    return `<section aria-label="Source chronology support" data-source-chronology-quality="available"><h3>Source chronology support</h3><p>${profiles.length} source profile${profiles.length === 1 ? '' : 's'}, ${samples.length} sample flag record${samples.length === 1 ? '' : 's'} and ${claims.length} age-claim diagnostic${claims.length === 1 ? '' : 's'}. This review does not select a chronology or change sample eligibility.</p><p>Profiles keep source models and age bases separate. Sample flags combine their associated profile context; inspect the matching profile and claim before interpreting a flag. Declared reliable-age bounds and control midpoint depth envelopes are distinct checks. These diagnostics do not establish chronological precision, a hiatus, model extrapolation, the physical core base or ecological accuracy.</p>${metadata}${tables}</section>`;
  } catch { return unavailable(); }
}
function renderSourceChronologyContext(tabs) {
  return renderSourceChronologyIssues(tabs) + renderSourceChronologyQuality(tabs);
}
function renderSelectedSourceOverview(tabs, feature) {
  const unavailable = reason => `<section aria-label="Selected source record" data-source-record-details="unavailable"><h3>Selected source record</h3><p>${escapeHtml(reason)} Original source tables remain available.</p></section>`;
  const identifier = value => typeof value === 'string' && value.trim() && value === value.trim();
  if (tabs?.overview?.source_family !== 'neotoma' || feature?.source_family !== 'neotoma') return unavailable('Selected sample metadata is supported for Neotoma source features only.');
  if (!sourceRecordSignalMatchesSite(tabs,feature)) return unavailable('Selected feature and detail site or source epoch do not agree.');
  if (!Number.isFinite(feature.latitude) || !Number.isFinite(feature.longitude)
    || Math.abs(feature.latitude) > 90 || Math.abs(feature.longitude) > 180) return unavailable('Selected feature representative coordinates are unavailable or outside geographic bounds.');
  const charcoal = feature.semantic_role === 'native_charcoal_source_context' ? nativeCharcoalSourceSignal(tabs,feature) : null;
  const charcoalHtml = charcoal ? renderNativeCharcoalObservation(tabs,feature,charcoal) : '';
  if (charcoal?.status === 'unavailable') return charcoalHtml;
  try {
    const samples = sourceRecordRows(tabs.samples?.samples,['sample_id','dataset_id','collection_unit_id']);
    const datasets = sourceRecordRows(tabs.samples?.datasets,['dataset_id','collection_unit_id']);
    const units = sourceRecordRows(tabs.samples?.collection_units,['collection_unit_id']);
    const matching = samples.filter(row => row.sample_id === feature.source_record_id);
    if (matching.length !== 1) return unavailable('Selected native sample identity is missing or ambiguous.');
    const sample = matching[0];
    if (![sample.dataset_id,sample.collection_unit_id].every(identifier)) return unavailable('Selected sample dataset or collection identity is unavailable.');
    const dataset = datasets.filter(row => row.dataset_id === sample.dataset_id);
    if (dataset.length !== 1 || dataset[0].collection_unit_id !== sample.collection_unit_id
      || units.filter(row => row.collection_unit_id === sample.collection_unit_id).length !== 1) return unavailable('Selected sample dataset and collection relationships do not reconcile uniquely.');
    let claim = null, reason = 'The selected map age claim has no exact unique sample, dataset, collection and chronology join.';
    try {
      const claims = sourceRecordRows(tabs.chronology,['chronology_claim_id','subject_type','subject_id','source_record_id','dataset_id','collection_unit_id','chronology_id']);
      const matchingClaims = identifier(feature.chronology_claim_id) ? claims.filter(row => row.chronology_claim_id === feature.chronology_claim_id) : [];
      if (matchingClaims.length === 1) {
        const candidate = matchingClaims[0];
        if (candidate.subject_type === 'sample' && candidate.subject_id === sample.sample_id
          && candidate.source_record_id === sample.sample_id && candidate.dataset_id === sample.dataset_id
          && candidate.collection_unit_id === sample.collection_unit_id
          && candidate.chronology_id === feature.chronology_id) claim = candidate;
      }
    } catch (error) {
      reason = 'Source age claims are unavailable or cannot be decoded consistently.';
    }
    const refused = claim && (claim.comparability_status === 'refused' || Boolean(claim.refusal_reason));
    const status = !claim ? 'unmatched' : refused ? 'refused' : 'matched';
    const fields = [
      ['Source site ID',feature.record_id],['Native sample ID',sample.sample_id],
      ['Native dataset ID',sample.dataset_id],['Native collection-unit ID',sample.collection_unit_id],
      ['Source snapshot',feature.source_snapshot_id],['Source build',feature.build_id],
      ['Latitude',feature.latitude],['Longitude',feature.longitude],['Coordinate quality',feature.coordinate_quality],
      ['Source measurement unit',feature.source_unit],['Map age claim ID',feature.chronology_claim_id],
      ['Map chronology ID',feature.chronology_id],['Map chronology name',feature.chronology_name],
      ['Map source-default assertion',feature.is_default_chronology],
      ['Source chronology selection posture',feature.chronology_selection_posture],
      ['Candidate-generation status',feature.candidate_generation_status],
      ['Candidate refusal reason',feature.candidate_refusal_reason],['Propagation eligible',feature.propagation_eligible],
    ];
    if (claim) fields.push(
      ['Age-claim default flag',claim.is_default_chronology],['Source age type',claim.source_age_type],
      ['Source age unit',claim.source_age_unit],['Source age value',claim.source_age_value],
      ['Source younger endpoint',claim.source_age_younger],['Source older endpoint',claim.source_age_older],
      ['Age comparability status',claim.comparability_status],['Age refusal reason',claim.refusal_reason],
    );
    return charcoalHtml + `<section aria-label="Selected source record" data-source-record-details="${status}"><h3>Selected source record</h3><p>${!claim ? escapeHtml(reason) : refused ? 'The uniquely joined source age claim is refused; its values remain source context.' : 'One exact source sample and age claim are joined.'}</p>${sourceRecordFields(fields)}<p>Coordinates are source representative positions with the stated quality; that quality is not a numerical uncertainty estimate. Age values retain their reported units. Source-default flags and source selection posture do not select an analysis chronology. No age conversion, fitted age model, physical-core equivalence, ecological mapping or propagation admission is introduced. All source claims remain in the Chronology tab.</p></section>`;
  } catch (error) {
    return unavailable('Selected sample source tables are unavailable or cannot be decoded consistently.');
  }
}
function renderSourceSampleObservations(tabs) {
  const unavailable = reason => `<section aria-label="Sample source observations"><h3>Sample source observations</h3><p>${escapeHtml(reason)}</p></section>`;
  if (tabs?.overview?.source_family !== 'neotoma') return unavailable(`Sample observation values are not available through this view for source family ${detailTableText(tabs?.overview?.source_family)}.`);
  const table = tabs.pollen_composition;
  if (!detailTableShape(table) || ['observation_id','sample_id','source_value','source_unit','source_denominator','denominator_status','detection_status'].some(field => !table.fields.includes(field))) return unavailable('Neotoma sample observation values or measurement metadata are unavailable.');
  return `<section aria-label="Sample source observations"><h3>Sample source observations</h3><p>Original site-wide source observations, linked by native sample and observation IDs. Values, units, denominators and missingness are retained as reported; source null is not zero. No cross-unit sum, inferred percentage or vegetation reconstruction is made. This is the same observation table available in Pollen/composition.</p>${renderDetailTable(table,'samples.observations')}</section>`;
}
function renderReviewedClassificationContext(value, valuePath) {
  const unavailable = '<div class="scientific-status">Unavailable: reviewed_classification_context_invalid</div>';
  const roleIds = ['direct_crop_confirmed', 'crop_type_qualified', 'anthropogenic_indicator', 'pastoral_indicator', 'ruderal_disturbance_indicator'];
  const totals = value.crop_indicator_totals;
  const count = (number) => Number.isSafeInteger(number) && number >= 0;
  if (value.schema_version !== 'classification-reviewed-context.v1' || value.scope !== 'reviewed_source_context_only'
    || !Array.isArray(totals) || totals.length !== roleIds.length
    || !totals.every((row) => row && roleIds.includes(row.role_id)
      && typeof row.label === 'string' && row.label.trim()
      && count(row.unique_observation_count) && row.pollen_alone_proves === false
      && typeof row.unproven_claim === 'string' && row.unproven_claim.trim())
    || new Set(totals.map((row) => row.role_id)).size !== roleIds.length
    || !count(value.crop_indicator_union_observation_count)
    || !count(value.whole_pollen_category_observation_count)) return unavailable;
  const union = value.crop_indicator_union_observation_count;
  const memberships = totals.reduce((total, row) => total + row.unique_observation_count, 0);
  if (union < Math.max(...totals.map((row) => row.unique_observation_count)) || union > memberships || union > value.whole_pollen_category_observation_count) return unavailable;
  const byRole = new Map(totals.map((row) => [row.role_id, row]));
  const rows = roleIds.map((role) => {
    const row = byRole.get(role);
    return `<tr><th scope="row">${escapeHtml(row.label)}</th><td>${row.unique_observation_count}</td><td>Pollen alone does not prove ${escapeHtml(row.unproven_claim)}.</td></tr>`;
  }).join('');
  const summaryKeys = new Set(['crop_indicator_totals', 'crop_indicator_union_observation_count', 'whole_pollen_category_observation_count']);
  return `<div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>Reviewed crop and indicator context</caption><thead><tr><th scope="col">Evidence category</th><th scope="col">Unique observations</th><th scope="col">Interpretation limit</th></tr></thead><tbody>${rows}</tbody></table></div><p>Unique observations across these categories: ${union}. Categories overlap; do not add their counts.</p><p>Whole-pollen category observations: ${value.whole_pollen_category_observation_count}. These are category memberships, not pollen abundances or cultivation, grazing or other causal proof. Context review alone does not admit a pollen event or LRA input.</p>${renderDetailObjectEntries(value, valuePath, summaryKeys)}`;
}
function renderClassificationContext(value, valuePath) {
  if (typeof value?.schema_version === 'string' && value.schema_version.startsWith('classification-reviewed-context.')
    || value?.scope === 'reviewed_source_context_only') {
    if (typeof renderDetailObjectEntries !== 'function') return '<div class="scientific-status">Unavailable: reviewed_classification_context_renderer_unavailable</div>';
    return renderReviewedClassificationContext(value, valuePath);
  }
  return renderNativeClassificationContext(value);
}
function renderNativeClassificationContext(tabs) {
  const family = tabs?.overview?.source_family;
  const table = family === 'neotoma' ? tabs.pollen_composition?.variables
    : family === 'sead' ? tabs.pollen_composition?.taxa : null;
  const required = family === 'neotoma' ? ['variable_id','source_taxon_id','source_reported_name','source_semantics']
    : ['taxon_relation_id','taxon_id','source_ecocodes','derived_classification_status'];
  const heading = '<h3>Native classification context</h3>';
  try {
    if (!['neotoma','sead'].includes(family)) throw Error('unsupported source');
    sourceRecordRows(table,required);
    return `<section aria-label="Native classification context">${heading}<p>Literal source names, taxon identities, group codes and element semantics only. Multiple reported codes or semantics are retained together; they do not establish accepted normalized names, memberships, crosswalk versions, review evidence or a ranking of alternatives. Per-observation codes and missingness remain in Samples and Pollen/composition. Accepted classification status is shown separately.</p>${renderDetailTable(table,'classification.native_context')}</section>`;
  } catch (error) {
    return `<section aria-label="Native classification context">${heading}<p>Native classification context is unavailable for source family ${escapeHtml(detailTableText(family))}: the supported native taxon table is not available. This does not establish an accepted classification.</p></section>`;
  }
}
function renderSourceResourceEntry(tabs) {
  const overview=tabs?.overview, identity=overview?.source_site_id;
  if (bindings.resourceCatalogueAvailable !== true || overview?.source_family !== 'neotoma'
    || typeof identity !== 'string' || !/^[1-9][0-9]*$/.test(identity)
    || overview.site_id !== `neotoma:site:${identity}`) return '';
  return `<p><button type="button" class="toolbar-button" data-source-resources="${escapeHtml(overview.site_id)}">Browse source resources for native site ${escapeHtml(identity)}</button></p>`;
}
function renderSourceProvenanceContext(tabs) {
  const family = tabs?.overview?.source_family, heading = '<h3>Source dataset metadata</h3>';
  const transformations = renderSourceTransformationContext(tabs);
  const table = family === 'neotoma' ? tabs.samples?.datasets
    : family === 'sead' ? tabs.pollen_composition?.dataset_semantics : null;
  try {
    if (!['neotoma','sead'].includes(family)) throw Error('unsupported source');
    const datasets = sourceRecordRows(table,family === 'neotoma' ? ['dataset_id','source_payload'] : ['dataset_id']);
    const providerLink = row => {
      const id = row.source_dataset_id;
      if (!Number.isSafeInteger(id) || id <= 0 || row.source_payload?.datasetid !== id
        || row.dataset_id !== `neotoma:dataset:${id}`
        || datasets.filter(candidate => candidate.source_dataset_id === id).length !== 1
        || datasets.filter(candidate => candidate.dataset_id === row.dataset_id).length !== 1) return '<p>Current provider dataset JSON link is unavailable: native dataset identities are missing, unsafe, inconsistent or ambiguous.</p>';
      const url = `https://api.neotomadb.org/v2.0/data/downloads/${id}`;
      return `<p><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Current provider dataset JSON</a> for ${escapeHtml(row.dataset_id)}.</p>`;
    };
    const citations = family === 'neotoma' ? datasets.map(row => {
      const payload = row.source_payload;
      const native = key => payload && typeof payload === 'object' && !Array.isArray(payload) && Object.hasOwn(payload,key) ? payload[key] : undefined;
      return `<article><h4>Native dataset ${escapeHtml(detailTableText(row.dataset_id))}</h4>${sourceRecordFields([
        ['Dataset DOI values as reported',native('doi')],['Dataset investigators as reported',native('datasetpi')],
        ['Constituent database',native('database')],['Dataset notes',native('datasetnotes')],
      ])}${providerLink(row)}</article>`;
    }).join('') : '<p>SEAD dataset semantics are available below; primary publication citations are not exposed by this dataset table.</p>';
    const navigation = family === 'neotoma' ? '<p>Current provider data may differ from the retained source snapshot. These links do not retrieve the retained serialized archive; that archive is not the original HTTP response bytes.</p>' : '';
    return `<section aria-label="Source dataset metadata">${heading}${citations}${navigation}<p>Native metadata and the original dataset table are retained without selecting, merging or normalizing citation alternatives. A dataset DOI alone is not a full primary publication citation or a rights decision. Missing, source-null and empty citation values remain distinct; captured publication records require a separate qualified join and capture identity.</p>${renderDetailTable(table,'provenance.datasets')}${family === 'neotoma' ? renderCapturedSourcePublications(tabs) : ''}${transformations}<p>Source identities, digests, schema tags and record locators are retained in this tab where supplied. Record and part locators identify the preserved evidence named there; they do not establish a complete original-acquisition or transformation chain. No transformation history is invented here. Supplied transformation fields remain unchanged in Chronology.</p></section>`;
  } catch (error) {
    return `<section aria-label="Source dataset metadata">${heading}<p>Dataset citation context is unavailable for source family ${escapeHtml(detailTableText(family))}. Existing provenance remains available; missing citation metadata is not a claim that the original source is externally unavailable.</p>${transformations}</section>`;
  }
}
function renderSourceTransformationContext(tabs) {
  const family = tabs?.overview?.source_family, heading = '<h3>Supplied source transformations</h3>';
  const unavailable = reason => `<section aria-label="Supplied source transformations">${heading}<p>${escapeHtml(reason)}</p></section>`;
  if (family !== 'sead') return unavailable(`A per-record transformation table is not supplied for source family ${detailTableText(family)}. Source identities and locators do not imply an unavailable processing history.`);
  try {
    const table = tabs.chronology, rows = sourceRecordRows(table,['chronology_claim_id','source_age_value','source_age_unit','younger_bp','older_bp','original_interval_orientation','selection_rule_version','source_relation_path','reason_codes']);
    if (rows.some(row => row.source_family !== 'sead' || !Object.hasOwn(row,'provenance_record_id'))) throw Error('source claim context unavailable');
    if (rows.some(row => row.transformation_id != null && typeof row.transformation_id !== 'string')) throw Error('invalid transformation identity');
    const supplied = rows.filter(row => typeof row.transformation_id === 'string' && row.transformation_id.trim());
    const absent = rows.filter(row => row.transformation_id === undefined).length;
    const nullable = rows.filter(row => row.transformation_id === null).length;
    const empty = rows.length - supplied.length - absent - nullable;
    const ids = [...new Set(supplied.map(row => row.transformation_id))];
    return `<section aria-label="Supplied source transformations">${heading}<p>${rows.length} chronology claims; ${supplied.length} with an explicit transformation ID, ${absent} with no supplied field, ${nullable} with source-null ID and ${empty} with an empty ID. Missing IDs do not establish that no processing occurred.</p><p>Provided IDs: ${escapeHtml(ids.length ? ids.join('; ') : 'None supplied')}. IDs and selection-rule versions are shown as supplied, without inferring an operation from an unknown identifier. Source age values retain their reported units and endpoint orientation; younger BP and older BP columns retain the supplied normalized bounds. No conversion is performed in this view. Relation paths, provenance locators, qualification and refusal reasons remain attached to every claim; this is not a complete transformation ledger or an analysis-chronology selection.</p>${renderDetailTable(table,'provenance.transformations')}</section>`;
  } catch (error) {
    return unavailable('SEAD transformation context is unavailable or cannot be decoded consistently. Original chronology and provenance remain available.');
  }
}
function renderCapturedSourcePublications(tabs) {
  const heading = '<h4>Separately captured provider publications</h4>', capture = tabs.provenance?.publication_capture;
  if (!capture) return `${heading}<p>Provider publication records are unavailable: no separate publication capture is configured.</p>`;
  try {
    if (capture.epoch_posture !== 'separate_provider_capture_not_original_pollen_snapshot') throw Error('capture epoch unavailable');
    sourceRecordRows(capture.datasets,['dataset_id','status','publication_count','source_primary_count','request_url','retrieved_at_utc','response_sha256','response_byte_count']);
    const publications = sourceRecordRows(capture.publications,['dataset_id','publication_id','source_primary_flag','source_payload']);
    const citations = publications.map(row => `<article><h5>${escapeHtml(detailTableText(row.dataset_id))}, publication ${escapeHtml(detailTableText(row.publication_id))}</h5>${sourceRecordFields([['Citation as reported',row.source_payload?.citation],['Title as reported',row.source_payload?.articletitle],['Authors as reported',row.source_payload?.author],['Year as reported',row.source_payload?.year],['Provider primary flag',row.source_primary_flag]])}</article>`).join('');
    return `${heading}<p>These native bibliography records were captured separately from the original pollen snapshot. Per-dataset retrieval dates, request URLs and response identities are retained below. A provider primary flag is a source designation only; null, false, multiple primaries and no linked publication remain distinct. Uncaptured datasets are not failed publication searches. No reviewed citation choice, full-paper access, rights decision or scientific admission follows.</p>${sourceRecordFields([['Publication capture source',capture.source_id],['Publication capture manifest SHA-256',capture.manifest_sha256]])}${citations}${renderDetailTable(capture.datasets,'provenance.publication_datasets')}${renderDetailTable(capture.publications,'provenance.publications')}`;
  } catch (error) {
    return `${heading}<p>Separate provider publication metadata is unavailable or cannot be decoded consistently. Original source dataset metadata remains available.</p>`;
  }
}

  function sourceDepthText(value) {
    return value === null || value === undefined || value === '' ? 'not supplied' : String(value);
  }
function sourceChronologyQualityMatches(tabs) {
  const quality = tabs?.chronology?.source_quality, overview = tabs?.overview, provenance = tabs?.provenance;
  const scope = quality?.source_scope;
  return overview?.source_family === 'neotoma' && quality?.schema_version === 'neotoma-source-chronology-quality.v1'
    && quality.status !== 'unavailable' && Boolean(scope) && scope.source_family === 'neotoma'
    && ['site_id','country_code'].every(field => typeof overview[field] === 'string' && overview[field] && scope[field] === overview[field])
    && ['source_snapshot_id','build_id','materialization_sha256'].every(field => typeof provenance?.[field] === 'string' && provenance[field] && scope[field] === provenance[field]);
}
// Only the bound metadata owner can qualify units for an exact native partition.
function sourceDepthProfile(tabs, collection, dataset, chronology = null, sampleIds = []) {
  const result = (unit,status,sources,refused=false) => {
    const profile = {unit,status,sources,refused};
    return {...profile,label:sourceDepthLabel(profile),html:sourceDepthProfileHtml(profile)};
  };
  const unavailable = status => result(null,status,[]);
  const quality = tabs?.chronology?.source_quality;
  if (tabs?.overview?.source_family !== 'neotoma'
    || quality?.schema_version !== 'neotoma-source-chronology-quality.v1') return unavailable('matching source depth profile unavailable');
  if (!sourceChronologyQualityMatches(tabs)) return unavailable('source depth profile scope mismatch');
  const overview = tabs.overview;
  try {
    const sampleFlags = sourceRecordRows(quality.sample_flags,['sample_id','flags']);
    const flagIds = new Set();
    for (const row of sampleFlags) {
      if (typeof row.sample_id !== 'string' || !row.sample_id || flagIds.has(row.sample_id)
        || !Array.isArray(row.flags) || row.flags.some(flag => typeof flag !== 'string')) return unavailable('source depth sample flags invalid');
      flagIds.add(row.sample_id);
    }
    // Sample flags combine every model; age-depth plots use their exact profile.
    if (chronology === null && sampleFlags.some(row => sampleIds.includes(row.sample_id) && row.flags.includes('explicit_depth_unit_contradiction'))) return {...unavailable('explicit depth unit contradiction; coordinate comparison refused'),refused:true};
    const identity = ['collection_unit_id','dataset_id','site_id','country_code','chronology_id','source_age_type','source_age_unit'];
    const profiles = sourceRecordRows(quality.profiles,
      ['profile_id',...identity,'depth_unit','depth_coordinate_status','depth_contract_sources']);
    const ids = new Set(), groups = new Set();
    for (const profile of profiles) {
      const key = JSON.stringify(identity.map(field => profile[field]));
      if (typeof profile.profile_id !== 'string' || !profile.profile_id || ids.has(profile.profile_id) || groups.has(key)) return unavailable('ambiguous source depth profiles');
      ids.add(profile.profile_id); groups.add(key);
    }
    const matches = profiles.filter(profile => profile.collection_unit_id === collection && profile.dataset_id === dataset
      && profile.site_id === overview.site_id && profile.country_code === overview.country_code
      && (chronology === null || ['chronology_id','source_age_type','source_age_unit'].every((field,index) => profile[field] === chronology[index])));
    if (!matches.length) return unavailable('matching source depth profile unavailable');
    if (matches.some(profile => profile.depth_coordinate_status === 'refused_explicit_depth_unit_contradiction')) return {...unavailable('explicit depth unit contradiction; coordinate comparison refused'),refused:true};
    const diagnostics = sourceRecordRows(quality.claim_diagnostics,['chronology_claim_id','sample_id','profile_id']);
    const claimIds = new Set();
    for (const row of diagnostics) {
      if (typeof row.chronology_claim_id !== 'string' || !row.chronology_claim_id || claimIds.has(row.chronology_claim_id)) return unavailable('ambiguous source depth sample linkage');
      claimIds.add(row.chronology_claim_id);
    }
    const matchedIds = new Set(matches.map(profile => profile.profile_id));
    if (!sampleIds.length || sampleIds.some(sample => !diagnostics.some(row => row.sample_id === sample && matchedIds.has(row.profile_id)))) return unavailable('matching source depth profile sample linkage unavailable');
    if (matches.some(profile => profile.depth_unit !== 'cm' || profile.depth_coordinate_status !== 'documented_source_cm_midpoints'
      || !Array.isArray(profile.depth_contract_sources) || !profile.depth_contract_sources.length
      || profile.depth_contract_sources.some(source => typeof source !== 'string' || !source.trim()))) return unavailable('source depth profile unit unqualified');
    return result('cm','documented source cm midpoints',[...new Set(matches.flatMap(profile => profile.depth_contract_sources))].sort());
  } catch (error) {
    return unavailable('source depth profile table invalid');
  }
}
function sourceDepthLabel(profile) {
  return profile?.unit === 'cm' ? 'Source depth (cm)' : 'Source depth (unit not supplied)';
}
function sourceDepthProfileHtml(profile) {
  const text = value => escapeHtml(sourceDepthText(value));
  return `<p>Depth coordinate qualification: ${text(profile?.status || 'matching source depth profile unavailable')}.${profile?.sources?.length ? ` Source contract: ${profile.sources.map(text).join('; ')}.` : ''} Captured midpoint extents do not identify the physical core base, a hiatus or physical-core equivalence. No depth conversion is performed.</p>`;
}
function ageDepthScale(values, start, extent) {
  let minimum = values[0], maximum = values[0];
  for (const value of values) { minimum = Math.min(minimum, value); maximum = Math.max(maximum, value); }
  const scale = Math.max(Math.abs(minimum), Math.abs(maximum)) || 1;
  const low = minimum / scale, range = maximum / scale - low;
  return {minimum, maximum, position(value) {
    const fraction = range === 0 ? 0.5 : (value / scale - low) / range;
    return Math.round((start + fraction * extent) * 1000) / 1000;
  }};
}
function ageDepthGroupHtml(group, index) {
  const [unit,dataset,chronology,type,ageUnit,calibration,comparability] = group.identity;
  const qualification = sourceDepthProfileHtml(group.depthProfile);
  if (group.depthProfile?.refused) return `<section><p>${escapeHtml(`Collection unit ${unit}; dataset ${dataset}; chronology ${chronology}`)}</p>${qualification}<p>${group.rows.length} source claims remain in the original table; no depth coordinates are compared.</p></section>`;
  const ages = group.rows.flatMap(row => [...(row.point === null ? [] : [row.point]), ...(row.endpoints || [])]);
  const x = ageDepthScale(ages, 85, 500), y = ageDepthScale(group.rows.map(row => row.depth), 40, 190);
  const text = value => escapeHtml(sourceDepthText(value));
  const label = `Collection unit ${unit}; dataset ${dataset}; chronology ${chronology}`;
  const titleId = `age-depth-title-${index}`, descriptionId = `age-depth-description-${index}`;
  // Limit only displayed marks; complete counts, extrema and original tables remain.
  const shown = group.rows.slice(0, 500);
  const marks = shown.map(row => {
    const claim = row.claim, cy = y.position(row.depth);
    const refused = Boolean(claim.refusal_reason) || claim.comparability_status === 'refused';
    const dash = refused ? '2 3' : claim.comparability_status === 'comparable' ? '' : '7 4';
    const defaultLabel = claim.is_default_chronology === true ? 'retained default flag: true' : claim.is_default_chronology === false ? 'retained default flag: false' : 'retained default flag not supplied';
    const detail = `${claim.chronology_claim_id}; sample ${row.sample}; depth ${row.depth} (${group.depthProfile?.unit || 'unit not supplied'}); reported age point ${sourceDepthText(row.point)}; reported endpoints ${row.endpoints ? row.endpoints.join(', ') : 'not supplied'}; ${defaultLabel}; source posture ${sourceDepthText(claim.comparability_status)}; source refusal ${sourceDepthText(claim.refusal_reason)}`;
    let span = '';
    if (row.endpoints) {
      const [a,b] = row.endpoints.map(value => x.position(value));
      span = `<path d="M${a},${cy-4}v8M${a},${cy}H${b}M${b},${cy-4}v8" fill="none" stroke="#334155" stroke-width="2" stroke-dasharray="${dash}"/>`;
    }
    let point = '';
    if (row.point !== null) {
      const cx = x.position(row.point);
      point = claim.is_default_chronology === true
        ? `<path d="M${cx},${cy-5}l5,5l-5,5l-5,-5z" fill="white" stroke="#0f172a" stroke-width="2" stroke-dasharray="${dash}"/>`
        : claim.is_default_chronology === false
          ? `<circle cx="${cx}" cy="${cy}" r="4" fill="white" stroke="#0f172a" stroke-width="2" stroke-dasharray="${dash}"/>`
          : `<rect x="${cx-4}" y="${cy-4}" width="8" height="8" fill="white" stroke="#0f172a" stroke-width="2" stroke-dasharray="${dash}"/>`;
    }
    return `<g role="img" tabindex="0" aria-label="${text(detail)}"><title>${text(detail)}</title>${span}${point}</g>`;
  }).join('');
  const xTicks = x.minimum === x.maximum ? [[x.minimum,335]] : [[x.minimum,85],[x.maximum,585]];
  const yTicks = y.minimum === y.maximum ? [[y.minimum,135]] : [[y.minimum,40],[y.maximum,230]];
  return `<figure class="age-depth-diagram" style="margin:1rem 0"><figcaption><strong>${text(label)}</strong><br>${text(group.names.join(' / '))}<br>Source age type: ${text(type)} · unit: ${text(ageUnit)}<br>Calibration: ${text(calibration)} · source comparability: ${text(comparability)}<br>${shown.length} of ${group.rows.length} source claims drawn; all remain in the table.${qualification}</figcaption><div class="source-diagram-plot" tabindex="0" role="region" aria-label="Scrollable source age-depth plot"><svg viewBox="0 0 640 300" width="640" style="max-width:100%;height:auto;background:white" role="img" aria-labelledby="${titleId} ${descriptionId}"><title id="${titleId}">${text(label)}: source age–depth assignments</title><desc id="${descriptionId}">Raw source assignments and reported endpoint spans, not an interpolated curve or fitted age-depth model. Depth increases downward. Age values increase rightward in this source's own basis.</desc><path d="M85,30V240H595" fill="none" stroke="#64748b"/>${xTicks.map(([value,cx]) => `<text x="${cx}" y="256" text-anchor="middle" font-size="12">${text(value)}</text>`).join('')}${yTicks.map(([value,cy]) => `<text x="78" y="${cy+4}" text-anchor="end" font-size="12">${text(value)}</text>`).join('')}<text x="335" y="281" text-anchor="middle" font-size="12">Source age (${text(ageUnit)})</text><text transform="translate(18 135) rotate(-90)" text-anchor="middle" font-size="12">${text(sourceDepthLabel(group.depthProfile))}</text>${marks}</svg></div></figure>`;
}

  return Object.freeze({overview: renderSelectedSourceOverview, samples: renderSourceSampleObservations,
    chronology: renderSourceChronologyContext, classification: renderClassificationContext, provenance: tabs => renderSourceResourceEntry(tabs) + renderSourceProvenanceContext(tabs),
    depthProfile: sourceDepthProfile, ageDepthGroup: ageDepthGroupHtml, charcoalSignal: nativeCharcoalSourceSignal});
}

      // Bind source export to the same table admission and decoder as its visible drawer.
function createSourceRecordExport(bindings) {
  const {tableAvailable:sourcePollenTableAvailable,exportAvailable:sourcePollenExportAvailable,decodeRow} = bindings;
  if (![sourcePollenTableAvailable,sourcePollenExportAvailable,decodeRow].every(value => typeof value === 'function')) throw Error('Source record export bindings are unavailable.');
  function sourcePollenDecodedTable(table, decodeRow) {
    if (!sourcePollenTableAvailable(table)) throw Error('source_pollen_table_unavailable');
    if (table.fields.some(field => typeof field !== 'string') || new Set(table.fields).size !== table.fields.length) throw Error('source_pollen_table_fields_invalid');
    return {
      record_count: table.record_count,
      records: table.records.map(row => decodeRow(table, row)),
    };
  }

  function sourcePollenChronologyMetadata(table, surface, decodeRow) {
    if (table === undefined) return {status:'unavailable', reason_code:`source_${surface}_surface_not_available`};
    if (table?.status === 'unavailable') return {...table};
    return {
      ...sourcePollenDecodedTable(table, decodeRow),
      ...(Object.hasOwn(table, 'source_locator_contract') ? {source_locator_contract:table.source_locator_contract} : {}),
    };
  }

  function sourcePollenChronologyIssues(issues) {
    if (issues == null) return {status:'unavailable', reason_code:'source_chronology_issues_not_available'};
    if (typeof issues !== 'object' || Array.isArray(issues)) throw Error('source_chronology_issues_invalid');
    if (issues.status === 'unavailable') return {...issues};
    const {conflicts, orphans, chronology_control_variants, ...metadata} = issues;
    return {
      ...metadata,
      conflicts: sourcePollenChronologyMetadata(conflicts, 'conflicts', decodeRow),
      orphans: sourcePollenChronologyMetadata(orphans, 'orphans', decodeRow),
      chronology_control_variants: sourcePollenChronologyMetadata(chronology_control_variants, 'chronology_control_variants', decodeRow),
    };
  }

  function sourcePollenChronologyQuality(quality) {
    if (quality == null) return {status:'unavailable', reason_code:'source_chronology_quality_not_available'};
    if (typeof quality !== 'object' || Array.isArray(quality)) throw Error('source_chronology_quality_invalid');
    if (quality.status === 'unavailable') return {...quality};
    const {profiles, sample_flags, claim_diagnostics, ...metadata} = quality;
    return {
      ...metadata,
      profiles: sourcePollenChronologyMetadata(profiles, 'chronology_quality_profiles', decodeRow),
      sample_flags: sourcePollenChronologyMetadata(sample_flags, 'chronology_quality_sample_flags', decodeRow),
      claim_diagnostics: sourcePollenChronologyMetadata(claim_diagnostics, 'chronology_quality_claim_diagnostics', decodeRow),
    };
  }

  function buildSourcePollenRecordExport(focus, selection) {
    if (!sourcePollenExportAvailable(focus)) throw Error('source_pollen_record_export_unavailable');
    const tabs = focus.detailTabs;
    return {
      schema_version: 'source-pollen-record-export.v1',
      record_id: focus.recordId,
      feature_identity: { layer_key: focus.layerKey, feature_key: focus.featureKey },
      title: focus.title,
      selection,
      source_provenance: { ...tabs.provenance },
      record_scope: 'complete_source_record_not_filtered_to_map_time_window',
      temporal_support: {
        chronology_scope: 'all_source_claims_including_contextual_and_refused',
        interval_semantics: tabs.chronology.interval_semantics || null,
        interpolation_allowed: false,
        site_range_is_continuous_support: false,
        model_metadata_posture: tabs.chronology.model_metadata_posture || null,
        ...(Object.hasOwn(tabs.chronology, 'reference_verification_posture') ? {reference_verification_posture:tabs.chronology.reference_verification_posture} : {}),
      },
      source_semantics: {
        unit_policy: 'literal_source_unit_per_observation',
        denominator_policy: 'literal_source_denominator_and_status; null_remains_null',
        aggregation_policy: tabs.pollen_composition.aggregation_posture || 'source_observations_without_reaggregation',
        classification_status: tabs.pollen_composition.classification_status || 'not_asserted',
      },
      samples: sourcePollenDecodedTable(tabs.samples.samples, decodeRow),
      chronology_claims: sourcePollenDecodedTable(tabs.chronology, decodeRow),
      source_chronology_models: sourcePollenChronologyMetadata(tabs.chronology.models, 'chronologies', decodeRow),
      source_chronology_controls: sourcePollenChronologyMetadata(tabs.chronology.controls, 'chronology_controls', decodeRow),
      source_chronology_issues: sourcePollenChronologyIssues(tabs.chronology.source_issues),
      source_chronology_quality: sourcePollenChronologyQuality(tabs.chronology.source_quality),
      pollen_observations: sourcePollenDecodedTable(tabs.pollen_composition, decodeRow),
      source_variables: sourcePollenTableAvailable(tabs.pollen_composition.variables)
        ? sourcePollenDecodedTable(tabs.pollen_composition.variables, decodeRow) : null,
      collection_units: sourcePollenTableAvailable(tabs.samples.collection_units)
        ? sourcePollenDecodedTable(tabs.samples.collection_units, decodeRow) : null,
      datasets: sourcePollenTableAvailable(tabs.samples.datasets)
        ? sourcePollenDecodedTable(tabs.samples.datasets, decodeRow) : null,
    };
  }

  return buildSourcePollenRecordExport;
}

      // Export published selection rows; transport authentication and selection stay with their owners.
function atlasSelectionExportJson(value) {
  return JSON.stringify(value, (_key, item) => {
    if (typeof item === 'number' && !Number.isFinite(item)
      || ['undefined', 'function', 'symbol', 'bigint'].includes(typeof item)) {
      throw Error('Current selection export contains a value that JSON cannot preserve.');
    }
    return item;
  });
}

async function prepareAtlasSelectionExport(owner) {
  // snapshot includes current capture, shared selection, display and generation.
  // readAsset exposes only authenticated node chunks; layerForAsset returns the
  // original provenance layer, without hydrated feature arrays. Existing host
  // predicates own asset/feature selection and uncapped endpoint eligibility.
  const refuse = reason => { throw Error(`Current selection export unavailable: ${reason}`); };
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const integer = (value, label) => {
    if (!Number.isSafeInteger(value) || value < 0) refuse(`${label} is invalid.`);
    return value;
  };
  const callbacks = ['snapshot', 'assetNeeded', 'isLoaded', 'loadAsset', 'readAsset',
    'layerForAsset', 'featureSelected', 'relations', 'endpointEligible'];
  if (!object(owner) || callbacks.some(key => typeof owner[key] !== 'function')) refuse('selection owners are missing.');
  const bootstrap = owner.bootstrap;
  if (!object(bootstrap) || !['atlas-static-bootstrap.v2', 'atlas-static-bootstrap.v3'].includes(bootstrap.schema_version)
    || !['build_id', 'scope_slug', 'version'].every(key => typeof bootstrap[key] === 'string' && bootstrap[key])
    || !Array.isArray(bootstrap.assets) || bootstrap.assets.some(row => !object(row))
    || !object(bootstrap.budgets)) refuse('published static identity is missing.');
  const snapshotText = atlasSelectionExportJson(owner.snapshot());
  const snapshot = JSON.parse(snapshotText);
  const current = () => {
    if (!object(snapshot) || snapshot.ready !== true
      || !['build_id', 'scope_slug', 'version'].every(key => snapshot[key] === bootstrap[key])
      || atlasSelectionExportJson(owner.snapshot()) !== snapshotText) refuse('the build, filters or display changed; request the selection again.');
  };
  current();
  const requestLimit = integer(bootstrap.budgets.interaction_max_requests, 'interaction request budget');
  const byteLimit = integer(bootstrap.budgets.interaction_max_bytes, 'interaction byte budget');
  const chunkLimit = integer(bootstrap.budgets.chunk_max_bytes, 'decoded chunk budget');
  const overhead = owner.transportOverhead === undefined ? {request_count: 0, byte_count: 0} : owner.transportOverhead;
  if (!object(overhead) || Object.keys(overhead).sort().join('|') !== 'byte_count|request_count') refuse('transport overhead is invalid.');
  const overheadRequests = integer(overhead.request_count, 'transport overhead request count');
  const overheadBytes = integer(overhead.byte_count, 'transport overhead byte count');
  const assets = bootstrap.assets.filter(row => row.domain === 'nodes' && owner.assetNeeded(row));
  if (new Set(assets.map(row => row.asset_key)).size !== assets.length) refuse('selected asset identities are repeated.');
  let decodedBytes = 0;
  for (const row of assets) {
    if (!object(row) || typeof row.asset_key !== 'string' || !row.asset_key
      || !['point', 'polygon'].includes(row.layer_kind)) refuse('selected node metadata is invalid.');
    const size = row.decoded_byte_count === undefined ? chunkLimit : integer(row.decoded_byte_count, 'decoded asset size');
    if (size > chunkLimit) refuse('a selected asset exceeds its decoded chunk budget.');
    decodedBytes += size;
    if (!Number.isSafeInteger(decodedBytes) || decodedBytes > byteLimit) refuse('complete selected assets exceed the interaction byte budget. Narrow the filters.');
  }
  const missing = assets.filter(row => !owner.isLoaded(row));
  const requestBytes = overheadBytes + missing.reduce((total, row) => total + integer(row.byte_count, 'asset byte count'), 0);
  const requests = overheadRequests + missing.length;
  if (!Number.isSafeInteger(requests) || requests > requestLimit || !Number.isSafeInteger(requestBytes) || requestBytes > byteLimit) {
    refuse('complete selected assets exceed the interaction request or byte budget. Narrow the filters.');
  }
  const outcomes = await Promise.allSettled(missing.map(row => Promise.resolve().then(() => owner.loadAsset(row))));
  current();
  if (outcomes.some(result => result.status === 'rejected')) refuse('a selected asset failed loading or authentication; no partial download was produced.');
  const layers = [], entries = [], literalIds = new Set();
  let inspected = 0, selected = 0, pointCount = 0, polygonCount = 0, identifiedRows = 0;
  const groups = new Map();
  for (const row of assets) {
    if (owner.isLoaded(row) !== true) refuse('a selected asset was not authenticated.');
    const payload = owner.readAsset(row), metadata = owner.layerForAsset(row);
    if (!object(payload) || !object(metadata) || metadata.key !== row.layer_key
      || Object.hasOwn(metadata, 'features') || Object.hasOwn(metadata.geojson || {}, 'features')
      || payload.asset_key !== row.asset_key || payload.build_id !== bootstrap.build_id
      || payload.scope_slug !== bootstrap.scope_slug || payload.version !== bootstrap.version
      || payload.layer_key !== row.layer_key || payload.layer_index !== row.layer_index || payload.layer_kind !== row.layer_kind
      || !Array.isArray(payload.features) || !Array.isArray(payload.feature_indexes)
      || payload.features.length !== integer(row.record_count, 'asset row count')
      || payload.feature_indexes.length !== payload.features.length) refuse('a selected decoded asset or layer is missing or inconsistent.');
    const key = `${row.layer_kind}:${row.layer_index}`;
    let group = groups.get(key);
    if (!group) {
      group = {layer_index: row.layer_index, layer_key: row.layer_key, layer_kind: row.layer_kind, metadata, records: []};
      groups.set(key, group); layers.push(group);
    } else if (group.layer_key !== row.layer_key || atlasSelectionExportJson(group.metadata) !== atlasSelectionExportJson(metadata)) {
      refuse('selected layer identities disagree.');
    }
    payload.features.forEach((feature, index) => {
      if (!object(feature)) refuse('a decoded public row is invalid.');
      const featureIndex = integer(payload.feature_indexes[index], 'published feature index');
      inspected++;
      if (!owner.featureSelected(metadata, feature, row.layer_kind)) return;
      group.records.push({asset_key: row.asset_key, feature_index: featureIndex, feature});
      selected++;
      if (row.layer_kind === 'point') pointCount++;
      else polygonCount++;
      const id = row.layer_kind === 'point' ? feature.record_id : feature.properties?.record_id;
      if (typeof id === 'string' && id) { identifiedRows++; literalIds.add(id); }
    });
  }
  layers.sort((left, right) => left.layer_index - right.layer_index);
  for (const layer of layers) {
    layer.records.sort((left, right) => left.feature_index - right.feature_index);
    if (layer.layer_kind === 'point') layer.records.forEach(row => entries.push({layer: layer.metadata, feature: row.feature}));
  }
  const relations = owner.relations();
  if (!object(relations) || !Array.isArray(relations.records)
    || integer(relations.retained_count, 'retained relation count') < relations.records.length
    || relations.records.some(row => !object(row))) refuse('retained relation selection is unavailable.');
  const eligibility = relations.records.map((edge, index) => {
    const eligible = owner.endpointEligible(edge, entries);
    if (typeof eligible !== 'boolean') refuse('relation endpoint eligibility is unavailable.');
    return {relation_index: index, endpoint_eligible: eligible};
  });
  const counts = {
    selected_node_assets: assets.length, authenticated_cached_node_assets: assets.length - missing.length,
    newly_loaded_node_assets: missing.length, inspected_public_rows: inspected, selected_public_rows: selected,
    point_rows: pointCount, polygon_rows: polygonCount, rows_with_literal_record_id: identifiedRows,
    unique_literal_record_ids: literalIds.size, retained_relation_rows: relations.retained_count,
    selected_relation_rows: relations.records.length,
    unique_literal_edge_ids: new Set(relations.records.map(row => row.edge_id).filter(id => typeof id === 'string' && id)).size,
    endpoint_eligible_relation_rows: eligibility.filter(row => row.endpoint_eligible).length,
  };
  current();
  const payload = {
    schema_version: 'atlas-selection-export.v1', snapshot, counts,
    scope: {
      nodes: 'complete_public_rows_matching_existing_selection_without_viewport_pruning',
      relations: 'complete_retained_rows_matching_relation_country_signal_filters_before_endpoint_time_layer_viewport_display_eligibility',
      endpoint_eligibility: 'existing_endpoint_selector_on_complete_selected_point_rows_without_viewport_or_primitive_cap',
      drawing_mode_filters_rows: false, source_series_included: false,
      unit_policy: 'literal_public_fields_without_conversion_or_cross_unit_aggregation',
      scientific_admission: 'not_asserted', rights_approval: 'not_asserted',
    },
    layers, relations: {records: relations.records, endpoint_eligibility: eligibility},
  };
  const text = atlasSelectionExportJson(payload) + '\n';
  const byteCount = new TextEncoder().encode(text).byteLength;
  if (byteCount > byteLimit) refuse('the complete JSON exceeds the interaction byte budget. Narrow the filters.');
  current();
  return Object.freeze({text, byte_count: byteCount, counts: Object.freeze(counts)});
}


return Object.freeze({countryData:relationSummaryData,countryHtml:renderRelationSummary,timeData:relationTimeSummaryData,timeHtml:renderRelationTimeSummary,pickerCatalog:scientificPickerCatalog,pickerSearch:scientificPickerSearch,pickerInitial:scientificPickerInitialState,pickerAction:scientificPickerAction,pickerHtml:renderScientificPicker,pickerMount:mountScientificPicker,sourceDetails:createSourceRecordDetails,sourceExport:createSourceRecordExport,sourceResources:createSourceResourceBrowser,selectionExport:prepareAtlasSelectionExport});
};

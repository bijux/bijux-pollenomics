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
  const scope = '<p>Counts follow relation, country and signal filters before endpoint time, layer and viewport eligibility; displayed lines may be fewer. These are properties of supplied candidate relations under their exact active rules, not independent events, rates or origins.</p>';
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

      // Bind the existing source renderers to their owning table and escaping functions.
function createSourceRecordDetails(bindings) {
  const {detailTableShape, decodeDetailTableRow, detailTableText, renderDetailTable, escapeHtml} = bindings;
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
function renderSelectedSourceOverview(tabs, feature) {
  const unavailable = reason => `<section aria-label="Selected source record" data-source-record-details="unavailable"><h3>Selected source record</h3><p>${escapeHtml(reason)} Original source tables remain available.</p></section>`;
  const identifier = value => typeof value === 'string' && value.trim() && value === value.trim();
  if (tabs?.overview?.source_family !== 'neotoma' || feature?.source_family !== 'neotoma') return unavailable('Selected sample metadata is supported for Neotoma source features only.');
  if (![feature.record_id,feature.source_record_id,feature.source_snapshot_id,feature.build_id,
    tabs.overview.site_id,tabs.provenance?.source_snapshot_id,tabs.provenance?.build_id].every(identifier)
    || feature.record_id !== tabs.overview.site_id
    || feature.source_snapshot_id !== tabs.provenance.source_snapshot_id
    || feature.build_id !== tabs.provenance.build_id) return unavailable('Selected feature and detail site or source epoch do not agree.');
  if (!Number.isFinite(feature.latitude) || !Number.isFinite(feature.longitude)
    || Math.abs(feature.latitude) > 90 || Math.abs(feature.longitude) > 180) return unavailable('Selected feature representative coordinates are unavailable or outside geographic bounds.');
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
    return `<section aria-label="Selected source record" data-source-record-details="${status}"><h3>Selected source record</h3><p>${!claim ? escapeHtml(reason) : refused ? 'The uniquely joined source age claim is refused; its values remain source context.' : 'One exact source sample and age claim are joined.'}</p>${sourceRecordFields(fields)}<p>Coordinates are source representative positions with the stated quality; that quality is not a numerical uncertainty estimate. Age values retain their reported units. Source-default flags and source selection posture do not select an analysis chronology. No age conversion, fitted age model, physical-core equivalence, ecological mapping or propagation admission is introduced. All source claims remain in the Chronology tab.</p></section>`;
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

  return Object.freeze({overview: renderSelectedSourceOverview, samples: renderSourceSampleObservations,
    classification: renderNativeClassificationContext, provenance: renderSourceProvenanceContext});
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


return Object.freeze({countryData:relationSummaryData,countryHtml:renderRelationSummary,timeData:relationTimeSummaryData,timeHtml:renderRelationTimeSummary,pickerCatalog:scientificPickerCatalog,pickerSearch:scientificPickerSearch,pickerInitial:scientificPickerInitialState,pickerAction:scientificPickerAction,pickerHtml:renderScientificPicker,pickerMount:mountScientificPicker,sourceDetails:createSourceRecordDetails,selectionExport:prepareAtlasSelectionExport});
};

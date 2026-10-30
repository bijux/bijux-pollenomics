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

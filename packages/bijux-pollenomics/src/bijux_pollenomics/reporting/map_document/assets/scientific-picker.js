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
function scientificPickerInitialState(catalog, selectedIds) {
  const state = {pinnedIds: Array.isArray(selectedIds) ? selectedIds.slice(0, 6) : null, visibleIds: Array.isArray(selectedIds) ? [...selectedIds] : null};
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

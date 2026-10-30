// Describe current selection/display facts, without diagnosing missing science.
function selectionEmptyState(input) {
  const count = value => Number.isSafeInteger(value) && value >= 0;
  const fields = ['countryCount', 'pointCount', 'polygonLayerCount', 'retainedRelationCount', 'relationViewportCount', 'drawnRelationCount'];
  let populations = null;
  const result = (reason, title, message, hidden = false, facts = []) => ({reason, title, message, hidden, populations, facts});
  // loadStatus describes the whole current selection operation, not one layer.
  // Counts can still belong to the preceding generation until loading finishes.
  if (input?.loadStatus === 'loading') return result('loading', 'Loading selected evidence', 'Selection loading is incomplete; earlier display counts do not establish the current result.');
  if (input?.loadStatus === 'unavailable') return result('loading_unavailable', 'Selected evidence could not be loaded', 'The current selection operation failed. This does not establish that a source was not collected or that observations are absent.');
  const valid = input && typeof input === 'object' && !Array.isArray(input) && fields.every(key => count(input[key]))
    && Array.isArray(input.selectedLayers) && input.selectedLayers.every(layer => layer && typeof layer === 'object' && !Array.isArray(layer))
    && count(input.scientificSignalCount) && count(input.selectedScientificSignalCount)
    && input.selectedScientificSignalCount <= input.scientificSignalCount
    && input.drawnRelationCount <= input.relationViewportCount
    && input.relationViewportCount <= input.retainedRelationCount
    && typeof input.drawNodes === 'boolean' && typeof input.drawEdges === 'boolean'
    && (input.drawEdges || input.drawnRelationCount === 0)
    && input.loadStatus === 'ready';
  populations = valid ? Object.fromEntries(fields.map(key => [key, input[key]])) : null;
  if (!valid) return result('unknown', 'Selection state unavailable', 'Current selection counts or loading state are unavailable. No scientific reason for an empty display is inferred.');
  if ((input.drawNodes && input.pointCount > 0) || input.drawnRelationCount > 0) return result('not_empty', '', '', true);
  const facts = [`${input.pointCount} eligible point entries (drawing ${input.drawNodes ? 'enabled' : 'disabled'}; not a primitive count); ${input.polygonLayerCount} displayed polygon layers; ${input.retainedRelationCount} retained relations before endpoint time/layer/viewport eligibility; ${input.relationViewportCount} display-eligible viewport candidates; ${input.drawnRelationCount} drawn relations.`];
  const untimed = input.untimedExclusion;
  if (input.timeFilterActive === true && untimed?.status === 'available' && count(untimed.count)) {
    const split = [untimed.absent_count, untimed.refused_count, untimed.contextual_count];
    const complete = untimed.split_status === 'available' && split.every(count)
      && split.reduce((sum, value) => sum + value, 0) === untimed.count;
    facts.push(`${untimed.count} records without admitted numeric BP chronology are separately excluded from the active generic time-filter scope${complete ? ` (${split[0]} absent, ${split[1]} refused, ${split[2]} contextual)` : '; the absent/refused/contextual split is unavailable'}. This separate count does not explain the entire empty selection.`);
  }
  if (input.polygonLayerCount > 0) return result('polygons_only', 'Only polygon layers are displayed', 'Polygon layers remain displayed separately from point and relation drawing. Their count alone does not establish their scientific role or the presence or absence of qualifying observations.', false, facts);
  if (!input.drawNodes && !input.drawEdges) return result('drawing_disabled', 'Evidence drawing is not enabled', 'The drawing decision enables neither points nor relations. Logical entries and retained relations are unchanged; this is not evidence of absent observations.', false, facts);
  if (input.countryCount === 0) return result('empty_countries', 'No countries selected', 'Select a country to inspect country-filtered evidence. This selection is not a finding of absent observations.', false, facts);
  if (input.selectedLayers.length === 0) return result('empty_layers', 'No map layers enabled', 'Enable a layer to inspect its records. Retained relation counts remain separate from endpoint display eligibility.', false, facts);
  if (input.scientificSignalCount > 0 && input.selectedScientificSignalCount === 0
      && input.selectedLayers.every(layer => layer.scientific_selection_enabled === true)) {
    return result('empty_scientific_selection', 'No scientific signals selected', 'All enabled layers require a selected supplied scientific signal. Select a signal; no scientific absence is inferred.', false, facts);
  }
  if (input.pointCount > 0 && !input.drawNodes) return result('points_not_drawn', 'Eligible points are not drawn', 'Point drawing is disabled while eligible point entries remain retained. No relations are drawn in the current view; this is not evidence that observations are absent.', false, facts);
  if (input.relationViewportCount > 0) return result('relations_not_drawn', 'Eligible relations are not drawn', 'Display-eligible viewport candidates remain retained. Drawing mode and rendering limits are separate from evidence availability.', false, facts);
  if (input.retainedRelationCount > 0) return result('retained_relations_not_display_eligible', 'Retained relations are not display-eligible', 'Relations match the retained filters, but none is currently display-eligible in the viewport. No chronology, comparability or admission cause is inferred.', false, facts);
  return result('unknown', 'No qualifying map records', 'The current filters yield no eligible point entries, displayed polygon layers or drawn relations. Available metadata does not distinguish source unavailable, not collected, unresolved chronology, not comparable or all refused. This is not evidence that observations were absent.', false, facts);
}

function renderSelectionEmptyState(summary) {
  if (summary.hidden) return '';
  return `<strong>${escapeHtml(summary.title)}</strong><span>${escapeHtml(summary.message)}</span>${summary.facts.map(fact => `<span>${escapeHtml(fact)}</span>`).join('')}`;
}

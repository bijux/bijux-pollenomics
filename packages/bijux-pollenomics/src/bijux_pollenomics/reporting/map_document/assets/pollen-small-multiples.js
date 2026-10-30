// Compare compatible native variables without aggregating or admitting a chronology.
function pollenSmallMultiplesData(tabs, anchorNativeGroupKey, selectedAgeGroupKey = null) {
  const native = pollenObservationDiagramData(tabs);
  const unavailable = reason => ({status:'unavailable', reason, panels:[]});
  if (native.status !== 'available') return unavailable('native_source_tables_unavailable');
  const anchor = native.groups.find(group => group.key === anchorNativeGroupKey);
  if (!anchor) return unavailable('native_source_group_unavailable');
  const ages = sourceAgeAssignmentData(tabs);
  const compatible = group => group.identity.every((value,index) => index === 2 || index === 3
    || JSON.stringify(value) === JSON.stringify(anchor.identity[index]));
  const groups = native.groups.filter(compatible);
  groups.sort((a,b) => a === anchor ? -1 : b === anchor ? 1 : a.key < b.key ? -1 : a.key > b.key ? 1 : 0);
  const panels = groups.map(group => ({group, anchor:group === anchor,
    alignment:pollenAgeAxisForGroup(group, ages, selectedAgeGroupKey)}));
  if (panels.some(panel => panel.alignment.status === 'unavailable')) return unavailable('selected_source_age_group_unavailable');
  return {status:selectedAgeGroupKey === null ? 'depth' : 'age', reason:'', panels,
    incompatibleGroupCount:native.groups.length - groups.length,
    nativeTotal:native.total, nativeOmitted:{...native.omitted}};
}
function pollenSmallMultiplesReason(reason) {
  return ({sample_age_assignment_unavailable:'sample has no assignment in the selected source age group',
    ambiguous_sample_age_assignment:'sample has multiple assignments in the selected source age group'})[reason]
    || pollenDepthReasonText(reason);
}
function renderPollenSmallMultiples(tabs, anchorNativeGroupKey, selectedAgeGroupKey = null, selectedObservationIds = []) {
  const data = pollenSmallMultiplesData(tabs, anchorNativeGroupKey, selectedAgeGroupKey);
  const text = value => escapeHtml(pollenDepthText(value));
  if (data.status === 'unavailable') return `<section aria-label="Compatible native variable panels"><p>Compatible native panels unavailable: ${text(pollenSmallMultiplesReason(data.reason))}. Original source tables remain below.</p></section>`;
  const values = [], coordinates = [];
  let eligible = 0, selectedTotal = 0;
  for (const panel of data.panels) {
    selectedTotal += panel.alignment.total;
    for (const row of panel.alignment.rows) {
      values.push(row.value);
      coordinates.push(...(data.status === 'depth' ? [row.depth]
        : [...(row.age.point === null ? [] : [row.age.point]), ...(row.age.endpoints || [])]));
      eligible += 1;
    }
  }
  const shownPanels = data.panels.slice(0, 8);
  const shown = shownPanels.reduce((total,panel) => total + Math.min(500,panel.alignment.rows.length), 0);
  const nativeOmissions = Object.entries(data.nativeOmitted).sort().map(([reason,count]) => `${text(pollenDepthReasonText(reason))}: ${count}`).join('; ') || 'none';
  const selected = data.panels[0].alignment.selected;
  const ageBasis = selected ? `Explicit source age group: ${text(JSON.stringify(selected.identity))}. Source names: ${text(selected.names.join(' / '))}.` : 'Native source depth; depth units are not supplied.';
  const summary = `<h3>Compatible native variable panels</h3><p>${ageBasis} ${shownPanels.length} of ${data.panels.length} compatible panels displayed; ${shown} of ${eligible} aligned observations drawn, from ${selectedTotal} compatible source observations. ${data.incompatibleGroupCount} incompatible source groups are kept separate. Across all ${data.nativeTotal} native source observations, not chartable: ${nativeOmissions}.</p><p>Shared scales include every compatible aligned observation, even undisplayed panels and marks. Only native variable/taxon identities may differ; units, contexts, elements and denominator/status remain exact. No values are summed, converted to percentages or filled with zero. No ecological mapping, preferred chronology, interpolation, physical-core equivalence or vegetation inference is introduced. All original source tables remain below.</p>${data.status === 'age' ? pollenAgeSemanticsHtml() : ''}`;
  if (!eligible) return `<section aria-label="Compatible native variable panels">${summary}<p>No observations have an unambiguous assignment in this selected source group.</p>${shownPanels.map(panel => `<p>${text(pollenDepthGroupLabel(panel.group))}: ${Object.entries(panel.alignment.omitted).map(([reason,count]) => `${text(pollenSmallMultiplesReason(reason))}: ${count}`).join('; ') || 'no drawable observations'}.</p>`).join('')}</section>`;
  const scales = {x:pollenDepthScale(values, 85, 500), y:pollenDepthScale(coordinates, 40, 190)};
  const figures = shownPanels.map((panel,index) => {
    const heading = `${panel.anchor ? 'Selected anchor: ' : ''}${pollenDepthText(panel.group.variable.source_reported_name)}`;
    const omitted = Object.entries(panel.alignment.omitted).sort().map(([reason,count]) => `${text(pollenSmallMultiplesReason(reason))}: ${count}`).join('; ') || 'none';
    const figure = !panel.alignment.rows.length ? `<p>${text(pollenDepthGroupLabel(panel.group))}</p><p>No observations align with this selected source age group.</p>`
      : data.status === 'age' ? pollenAgeFigureHtml(panel.alignment, panel.group, index, scales, selectedObservationIds)
        : pollenDepthGroupHtml(panel.group, index, scales, selectedObservationIds);
    return `<article data-native-panel="${text(panel.group.key)}" style="margin:1rem 0;padding:0.5rem;border:${panel.anchor ? '3px double' : '1px solid'} #475569"><h4>${text(heading)}</h4><p>${Math.min(500,panel.alignment.rows.length)} of ${panel.alignment.rows.length} aligned observations drawn; ${panel.alignment.total} source observations; not aligned: ${omitted}.</p>${figure}</article>`;
  }).join('');
  return `<section aria-label="Compatible native variable panels">${summary}${figures}</section>`;
}

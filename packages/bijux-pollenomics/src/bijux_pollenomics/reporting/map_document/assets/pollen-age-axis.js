// A display-only alignment of already-qualified source rows, not a chronology model.
// Exact age/value joins do not require depth; the depth mode still does.
// No age/depth conversion, default selection or missing-age interpolation occurs.
function pollenAgeAxisData(tabs, nativeGroupKey, selectedAgeGroupKey = null) {
  const native = pollenObservationDiagramData(tabs);
  const empty = reason => ({status:'unavailable', reason, options:[], selected:null,
    rows:[], total:0, omitted:{}, sourceAgeOmitted:null, sourceAgeTotal:null});
  if (native.status !== 'available') return empty('native_source_tables_unavailable');
  const source = native.groups.find(group => group.key === nativeGroupKey);
  if (!source) return empty('native_source_group_unavailable');
  return pollenAgeAxisForGroup(source, sourceAgeAssignmentData(tabs), selectedAgeGroupKey);
}
// Reuse one qualified chronology table across compatible native variable panels.
function pollenAgeAxisForGroup(source, ages, selectedAgeGroupKey = null) {
  const compatible = ages.status === 'available' ? ages.groups.filter(group =>
    group.identity[0] === source.identity[0] && group.identity[1] === source.identity[1]) : [];
  const options = compatible.map(group => ({key:JSON.stringify(group.identity),
    identity:[...group.identity], names:[...group.names], claimCount:group.rows.length}));
  const result = {status:'depth', reason:ages.status === 'available' ? '' : ages.reason,
    options, selected:null, rows:source.rows.filter(row => pollenDepthFinite(row.depth)), total:source.rows.length,
    omitted:source.rows.some(row => !pollenDepthFinite(row.depth))
      ? {source_depth_not_numeric:source.rows.filter(row => !pollenDepthFinite(row.depth)).length} : {},
    sourceAgeOmitted:ages.status === 'available' ? {...ages.omitted} : null,
    sourceAgeTotal:ages.status === 'available' ? ages.total : null};
  // Null is the explicit depth mode, regardless of default flags or option ordering.
  if (selectedAgeGroupKey === null) return result;
  const selected = options.find(option => option.key === selectedAgeGroupKey);
  if (!selected) return {...result, status:'unavailable', reason:'selected_source_age_group_unavailable', rows:[]};
  const group = compatible.find(candidate => JSON.stringify(candidate.identity) === selected.key);
  const bySample = new Map();
  for (const row of group.rows) {
    if (!bySample.has(row.sample)) bySample.set(row.sample, []);
    bySample.get(row.sample).push(row);
  }
  const rows = [], omitted = {};
  for (const row of source.rows) {
    const matches = bySample.get(row.sample) || [];
    if (matches.length !== 1) {
      const reason = matches.length ? 'ambiguous_sample_age_assignment' : 'sample_age_assignment_unavailable';
      omitted[reason] = (omitted[reason] || 0) + 1;
      continue;
    }
    // Exactly one preserved claim, including its raw point/endpoints and source
    // posture. Interval-only claims stay interval-only; no midpoint is created.
    rows.push({...row, age:matches[0]});
  }
  return {...result, status:'age', reason:'', selected, rows, omitted};
}
function pollenAgeOptionLabel(option) {
  const labels = ['collection','dataset','chronology','source age type','age unit','calibration','comparability'];
  return option.identity.map((value,index) => `${labels[index]} ${JSON.stringify(value)}`).join('; ')
    + `; names ${JSON.stringify(option.names)}`;
}
function pollenAgeOmissionText(omitted, labels) {
  if (omitted === null) return 'not available';
  return Object.entries(omitted).sort().map(([reason,count]) =>
    `${labels[reason] || 'source assignment unavailable'}: ${count}`).join('; ') || 'none';
}
function pollenAgeFigureHtml(data, source, index = 0, scales = null, selectedObservationIds = []) {
  const text = value => escapeHtml(pollenDepthText(value));
  const figureIndex = Number.isSafeInteger(index) && index >= 0 ? index : 0;
  const titleId = `native-value-source-age-title-${figureIndex}`, descriptionId = `native-value-source-age-description-${figureIndex}`;
  const x = scales?.x ?? pollenDepthScale(data.rows.map(row => row.value), 85, 500);
  const ages = data.rows.flatMap(row => [...(row.age.point === null ? [] : [row.age.point]), ...(row.age.endpoints || [])]);
  const y = scales?.y ?? pollenDepthScale(ages, 40, 190), shown = data.rows.slice(0, 500);
  const selection = pollenObservationSelection(selectedObservationIds);
  const marks = shown.map(row => {
    const age = row.age, claim = age.claim, cx = x.position(row.value);
    const refused = Boolean(claim.refusal_reason) || claim.comparability_status === 'refused';
    const dash = refused ? '2 3' : claim.comparability_status === 'comparable' ? '' : '7 4';
    const defaultLabel = claim.is_default_chronology === true ? 'source-default' : claim.is_default_chronology === false ? 'source alternative' : 'default flag not supplied';
    const selected = selection.has(row.observation.observation_id);
    const detail = `${selected ? 'Selected map-signal observation; ' : ''}${row.observation.observation_id}; sample ${row.sample}; reported value ${row.value} ${source.identity[4]}; age claim ${claim.chronology_claim_id}; reported age point ${pollenDepthText(age.point)}; reported endpoints ${age.endpoints ? age.endpoints.join(', ') : 'not supplied'}; ${defaultLabel}; source posture ${pollenDepthText(claim.comparability_status)}; source refusal ${pollenDepthText(claim.refusal_reason)}`;
    let span = '', point = '';
    if (age.endpoints) {
      const [a,b] = age.endpoints.map(value => y.position(value));
      span = `<path d="M${cx-4},${a}h8M${cx},${a}V${b}M${cx-4},${b}h8" fill="none" stroke="#334155" stroke-width="2" stroke-dasharray="${dash}"/>`;
    }
    if (age.point !== null) {
      const cy = y.position(age.point);
      point = claim.is_default_chronology === true
        ? `<path d="M${cx},${cy-5}l5,5l-5,5l-5,-5z" fill="white" stroke="#0f172a" stroke-width="2" stroke-dasharray="${dash}"/>`
        : claim.is_default_chronology === false
          ? `<circle cx="${cx}" cy="${cy}" r="4" fill="white" stroke="#0f172a" stroke-width="2" stroke-dasharray="${dash}"/>`
          : `<rect x="${cx-4}" y="${cy-4}" width="8" height="8" fill="white" stroke="#0f172a" stroke-width="2" stroke-dasharray="${dash}"/>`;
    }
    const coordinates = [...(age.point === null ? [] : [age.point]), ...(age.endpoints || [])].map(value => y.position(value));
    return `<g role="img" tabindex="0"${selected ? ' data-selected-observation="true"' : ''} aria-label="${text(detail)}"><title>${text(detail)}</title>${selected ? pollenObservationSelectionBox(cx,coordinates) : ''}${span}${point}</g>`;
  }).join('');
  return `<figure style="margin:1rem 0"><figcaption><strong>Native reported values on the chosen source age axis</strong><br/>${text(pollenDepthGroupLabel(source))}<br/>Native variable semantics: ${text(source.variable.source_semantics)}<br/>Denominator: ${text(source.identity[8])}; status: ${text(source.identity[9])}.<br/>Chosen source assignment group: ${text(pollenAgeOptionLabel(data.selected))}<br/>${shown.length} of ${data.rows.length} aligned observations drawn; extrema use all aligned observations. All original observations and age claims remain in their tables.${pollenObservationSelectionCaption(data.rows,shown,selection)}</figcaption>${pollenObservationPlotHtml(x,y,marks,{titleId,descriptionId,title:'Native observations versus explicitly chosen source ages',description:'Raw age values increase downward in their exact source basis. Points and reported endpoint spans are individual assignments, not an age model or interpolated curve. Repeated observations stay separate even where marks overlap.',unit:source.identity[4],verticalLabel:`Source age (${pollenDepthText(data.selected.identity[4])})`,scrollLabel:"Scrollable source age plot"})}</figure>`;
}
function pollenAgeSemanticsHtml() {
  return '<p>Age values increase downward in the exact source basis shown. Diamond: source-default point; circle: source alternative; square: default flag not supplied. Solid: source-comparable; dashed: contextual or unspecified; dotted: source-refused. Vertical spans show raw reported endpoints with unspecified coverage, not confidence intervals. Interval-only assignments have no inferred point or midpoint. Contextual and refused source ages remain context, not admitted calendar dates or propagation evidence.</p>';
}
function renderPollenAgeDiagram(tabs, nativeGroupKey, selectedAgeGroupKey = null, includeFigure = true, selectedObservationIds = []) {
  const data = pollenAgeAxisData(tabs, nativeGroupKey, selectedAgeGroupKey);
  const text = value => escapeHtml(pollenDepthText(value));
  const unavailable = reason => `<section aria-label="Source age axis"><p>Source age axis unavailable: ${text(reason)}. Original source tables remain available.</p></section>`;
  if (data.status === 'unavailable') return unavailable(data.reason === 'selected_source_age_group_unavailable'
    ? 'the chosen assignment group does not belong to this native source group'
    : 'a qualified native observation group is not available');
  const options = data.options.map(option => `<option value="${text(option.key)}"${data.selected?.key === option.key ? ' selected="selected"' : ''}>${text(pollenAgeOptionLabel(option))}</option>`).join('');
  const chooser = `<label for="native-value-age-group">Display axis and explicit source age assignment group</label><select id="native-value-age-group" data-pollen-age-group="true" style="display:block;max-width:100%"><option value=""${data.status === 'depth' ? ' selected="selected"' : ''}>Native depth (unit not supplied)</option>${options}</select>`;
  const scope = '<p>This is a local display choice, not selection of an analysis chronology. Depth mode requires numeric native depth; an explicit source-age axis requires an exact observation/sample/age-claim join and can display samples without depth. No age/depth conversion, calibration, interpolation, physical-core equivalence, vegetation reconstruction or event admission is made. Original tables retain all rows.</p>';
  if (data.status === 'depth') return `<section aria-label="Source age axis">${chooser}${scope}<p>${data.rows.length} of ${data.total} observations have numeric source depth; ${data.omitted.source_depth_not_numeric || 0} do not.</p>${data.options.length ? '' : '<p>No qualified source age group is available for this collection unit and dataset. Native depth remains the display axis.</p>'}</section>`;
  const omissionLabels = {sample_age_assignment_unavailable:'no unique age claim for this sample in the chosen group', ambiguous_sample_age_assignment:'multiple age claims for this sample in the chosen group'};
  const summary = `<p>${data.rows.length} of ${data.total} observations in this native group align to exactly one claim in the chosen source group. Not aligned: ${text(pollenAgeOmissionText(data.omitted,omissionLabels))}. Complete source age table: ${data.sourceAgeTotal} claims; not chartable across that whole table: ${text(pollenAgeOmissionText(data.sourceAgeOmitted,SOURCE_AGE_OMISSION_LABELS))}.</p>`;
  const semantics = pollenAgeSemanticsHtml();
  const source = includeFigure && data.rows.length ? pollenObservationDiagramData(tabs).groups.find(group => group.key === nativeGroupKey) : null;
  return `<section aria-label="Source age axis">${chooser}${scope}${summary}${semantics}${data.rows.length ? (includeFigure ? pollenAgeFigureHtml(data,source,0,null,selectedObservationIds) : '') : '<p>No observations have one usable source age assignment in this chosen group. No zero age or alternative chronology is substituted.</p>'}</section>`;
}

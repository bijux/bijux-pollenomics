// Display exact native observations; never infer pollen percentages or vegetation.
function pollenDepthTableRows(table, fields) {
  if (!detailTableShape(table) || table.record_count !== table.records.length
    || new Set(table.fields).size !== table.fields.length
    || fields.some(field => !table.fields.includes(field))) throw new Error('native_value_table_unavailable');
  return table.records.map(row => decodeDetailTableRow(table, row));
}
function pollenDepthFinite(value) {
  return typeof value === 'number' && Number.isFinite(value);
}
function pollenDepthText(value) {
  return value === null || value === undefined || value === '' ? 'not supplied'
    : typeof value === 'object' ? JSON.stringify(value) : String(value);
}
function pollenDepthReasonText(reason) {
  return ({
    native_observation_depth_tables_not_available:'this source has no supported observation and depth tables',
    encoded_native_observation_table_invalid:'the source tables could not be decoded consistently',
    ambiguous_observation_identity:'observation identities are missing or repeated',
    sample_identity_unavailable:'samples are missing or have ambiguous identities',
    sample_source_relation_unavailable:'sample dataset or collection identities are unavailable',
    variable_identity_unavailable:'native variables are missing or have ambiguous identities',
    source_taxon_identity_mismatch:'observation and native variable taxon identities disagree',
    source_depth_not_numeric:'source depth is missing or not a finite number',
    source_value_not_reported:'the source value is missing, null or not reported',
    source_value_not_numeric:'the reported value is missing or not a finite number',
    source_unit_unavailable:'source measurement units are unavailable',
    source_count_not_nonnegative_exact_integer:'reported counts are negative, fractional or beyond exact integer precision',
    selected_native_source_group_not_available:'the selected native source group is unavailable',
  })[reason] || 'source values cannot be displayed consistently';
}
function pollenDepthDiagramData(tabs) {
  const unavailable = reason => ({status:'unavailable', reason, groups:[], total:0, omitted:{}});
  if (tabs?.overview?.source_family !== 'neotoma') return unavailable('native_observation_depth_tables_not_available');
  try {
    const samples = pollenDepthTableRows(tabs.samples?.samples,
      ['sample_id','collection_unit_id','dataset_id','source_depth']);
    const observations = pollenDepthTableRows(tabs.pollen_composition, [
      'observation_id','sample_id','variable_id','source_taxon_id','source_value',
      'source_unit','source_denominator','denominator_status','detection_status',
      'source_context','source_element','source_element_type','unit_family',
    ]);
    const variables = pollenDepthTableRows(tabs.pollen_composition.variables,
      ['variable_id','source_taxon_id','source_reported_name','source_semantics']);
    const index = (rows, field) => {
      const result = new Map();
      for (const row of rows) {
        if (!result.has(row[field])) result.set(row[field], []);
        result.get(row[field]).push(row);
      }
      return result;
    };
    const bySample = index(samples, 'sample_id'), byVariable = index(variables, 'variable_id');
    const byObservation = index(observations, 'observation_id');
    const groups = new Map(), omitted = {};
    const omit = reason => { omitted[reason] = (omitted[reason] || 0) + 1; };
    for (const observation of observations) {
      if (typeof observation.observation_id !== 'string' || !observation.observation_id
        || byObservation.get(observation.observation_id).length !== 1) { omit('ambiguous_observation_identity'); continue; }
      const matchingSamples = bySample.get(observation.sample_id) || [];
      if (typeof observation.sample_id !== 'string' || !observation.sample_id
        || matchingSamples.length !== 1) { omit('sample_identity_unavailable'); continue; }
      const sample = matchingSamples[0];
      if (typeof sample.collection_unit_id !== 'string' || !sample.collection_unit_id
        || typeof sample.dataset_id !== 'string' || !sample.dataset_id) { omit('sample_source_relation_unavailable'); continue; }
      const matchingVariables = byVariable.get(observation.variable_id) || [];
      if (typeof observation.variable_id !== 'string' || !observation.variable_id
        || matchingVariables.length !== 1) { omit('variable_identity_unavailable'); continue; }
      const variable = matchingVariables[0];
      if (variable.source_taxon_id !== observation.source_taxon_id) { omit('source_taxon_identity_mismatch'); continue; }
      if (!pollenDepthFinite(sample.source_depth)) { omit('source_depth_not_numeric'); continue; }
      if (observation.detection_status !== 'reported_value') { omit('source_value_not_reported'); continue; }
      if (!pollenDepthFinite(observation.source_value)) { omit('source_value_not_numeric'); continue; }
      if (typeof observation.source_unit !== 'string' || !observation.source_unit.trim()) { omit('source_unit_unavailable'); continue; }
      if (observation.unit_family === 'count'
        && (!Number.isSafeInteger(observation.source_value) || observation.source_value < 0)) { omit('source_count_not_nonnegative_exact_integer'); continue; }
      const identity = [sample.collection_unit_id,sample.dataset_id,observation.variable_id,
        observation.source_taxon_id,observation.source_unit,observation.source_context,
        observation.source_element,observation.source_element_type,
        observation.source_denominator,observation.denominator_status,observation.unit_family];
      const key = JSON.stringify(identity);
      if (!groups.has(key)) groups.set(key, {key, identity, variable, rows:[]});
      groups.get(key).rows.push({observation, sample:sample.sample_id, depth:sample.source_depth, value:observation.source_value});
    }
    const ordered = [...groups.values()].sort((a,b) => a.key < b.key ? -1 : a.key > b.key ? 1 : 0);
    for (const group of ordered) group.rows.sort((a,b) => a.observation.observation_id < b.observation.observation_id ? -1 : a.observation.observation_id > b.observation.observation_id ? 1 : 0);
    return {status:'available', reason:'', groups:ordered, total:observations.length, omitted};
  } catch (error) {
    return unavailable('encoded_native_observation_table_invalid');
  }
}
function pollenDepthScale(values, start, extent) {
  const minimum = values.reduce((a,b) => Math.min(a,b)), maximum = values.reduce((a,b) => Math.max(a,b));
  const scale = Math.max(Math.abs(minimum), Math.abs(maximum)) || 1;
  const low = minimum / scale, range = maximum / scale - low;
  return {minimum, maximum, position(value) {
    return Math.round((start + (range === 0 ? 0.5 : (value / scale - low) / range) * extent) * 1000) / 1000;
  }};
}
function pollenDepthGroupLabel(group) {
  const [unit,dataset,variable,taxon,sourceUnit,context,element,elementType,denominator,denominatorStatus,unitFamily] = group.identity;
  const literal = value => value === null ? 'not supplied (null)' : JSON.stringify(value);
  return `${pollenDepthText(group.variable.source_reported_name)} [${variable}]; source taxon ${literal(taxon)}; unit ${literal(sourceUnit)}; unit family ${literal(unitFamily)}; collection ${unit}; dataset ${dataset}; context ${literal(context)}; element ${literal(element)}; element type ${literal(elementType)}; denominator ${literal(denominator)}; denominator status ${literal(denominatorStatus)}`;
}
function pollenObservationPlotHtml(x, y, marks, labels) {
  const text = value => escapeHtml(pollenDepthText(value));
  const ticks = (scale, low, high, middle) => scale.minimum === scale.maximum ? [[scale.minimum,middle]] : [[scale.minimum,low],[scale.maximum,high]];
  return `<div class="source-diagram-plot" tabindex="0" role="region" aria-label="${text(labels.scrollLabel)}"><svg viewBox="0 0 640 300" width="640" style="max-width:100%;height:auto;background:white" role="img" aria-labelledby="${text(labels.titleId)} ${text(labels.descriptionId)}"><title id="${text(labels.titleId)}">${text(labels.title)}</title><desc id="${text(labels.descriptionId)}">${text(labels.description)}</desc><path d="M85,30V240H595" fill="none" stroke="#64748b"/>${ticks(x,85,585,335).map(([value,cx]) => `<text x="${cx}" y="256" text-anchor="middle" font-size="12">${text(value)}</text>`).join('')}${ticks(y,40,230,135).map(([value,cy]) => `<text x="78" y="${cy+4}" text-anchor="end" font-size="12">${text(value)}</text>`).join('')}<text x="335" y="281" text-anchor="middle" font-size="12">Reported value (${text(labels.unit)})</text><text transform="translate(18 135) rotate(-90)" text-anchor="middle" font-size="12">${text(labels.verticalLabel)}</text>${marks}</svg></div>`;
}
function pollenObservationSelection(ids) {
  return new Set(Array.isArray(ids) ? ids.filter(id => typeof id === 'string' && id.length) : []);
}
function pollenObservationSelectionBox(cx, coordinates) {
  const low = Math.min(...coordinates), high = Math.max(...coordinates);
  return `<rect x="${cx-8}" y="${low-8}" width="16" height="${high-low+16}" fill="none" stroke="#0f172a" stroke-width="2" stroke-dasharray="3 2"/>`;
}
function pollenObservationSelectionCaption(rows, shown, selection) {
  const count = values => values.filter(row => selection.has(row.observation.observation_id)).length;
  return selection.size ? `<br/>${count(shown)} of ${count(rows)} aligned selected map-signal observations drawn. Dashed selection boxes mark exact observation IDs, not uncertainty or ecological admission.` : '';
}
function pollenDepthGroupHtml(group, index = null, scales = null, selectedObservationIds = []) {
  const text = value => escapeHtml(pollenDepthText(value));
  const suffix = Number.isSafeInteger(index) && index >= 0 ? `-${index}` : '';
  const titleId = `native-value-depth-title${suffix}`, descriptionId = `native-value-depth-description${suffix}`;
  const x = scales?.x ?? pollenDepthScale(group.rows.map(row => row.value), 85, 500);
  const y = scales?.y ?? pollenDepthScale(group.rows.map(row => row.depth), 40, 190);
  const shown = group.rows.slice(0, 500), selection = pollenObservationSelection(selectedObservationIds);
  const marks = shown.map(row => {
    const selected = selection.has(row.observation.observation_id);
    const label = `${selected ? 'Selected map-signal observation; ' : ''}${row.observation.observation_id}; sample ${row.sample}; reported value ${row.value} ${group.identity[4]}; source depth ${row.depth} (unit not supplied)`;
    return `<g role="img" tabindex="0"${selected ? ' data-selected-observation="true"' : ''} aria-label="${text(label)}"><title>${text(label)}</title>${selected ? pollenObservationSelectionBox(x.position(row.value),[y.position(row.depth)]) : ''}<circle cx="${x.position(row.value)}" cy="${y.position(row.depth)}" r="4" fill="#0f172a" stroke="white" stroke-width="1"/></g>`;
  }).join('');
  return `<figure style="margin:1rem 0"><figcaption><strong>${text(group.variable.source_reported_name)}</strong><br/>${text(pollenDepthGroupLabel(group))}<br/>Native variable semantics: ${text(group.variable.source_semantics)}<br/>Denominator: ${text(group.identity[8])}; status: ${text(group.identity[9])}. ${shown.length} of ${group.rows.length} individual source observations drawn; all remain in the table.${pollenObservationSelectionCaption(group.rows,shown,selection)}</figcaption>${pollenObservationPlotHtml(x,y,marks,{titleId,descriptionId,title:'Native reported observation values versus source depth',description:'Individual exact-source observations, not ecological groups, reconstructed vegetation or percentages calculated from counts. Depth increases downward; values increase rightward. Separate observations at the same sample remain separate, even where marks overlap.',unit:group.identity[4],verticalLabel:"Source depth (unit not supplied)",scrollLabel:"Scrollable native value-depth plot"})}</figure>`;
}
function renderPollenDepthDiagram(tabs, selectedGroupKey = null, renderGroup = (group, ids) => pollenDepthGroupHtml(group,null,null,ids), options = {}) {
  const data = pollenDepthDiagramData(tabs);
  const unavailable = reason => `<section aria-label="Native observation diagrams"><p>Native value-depth diagram unavailable: ${escapeHtml(pollenDepthReasonText(reason))}. Original source tables remain below.</p></section>`;
  if (data.status !== 'available') return unavailable(data.reason);
  const omitted = Object.entries(data.omitted).sort().map(([reason,count]) => `${escapeHtml(pollenDepthReasonText(reason))}: ${count}`).join('; ') || 'none';
  const plotted = data.groups.reduce((total,group) => total + group.rows.length, 0);
  const summary = `<h3>Native reported observations</h3><p>${plotted} of ${data.total} source observations have joinable numeric values and depth, in ${data.groups.length} exact source groups. Not charted: ${omitted}. All source tables are unchanged.</p><p>Display only: the anchor fixes native variable, unit, context, dataset and collection. Source element and semantics preserve reported material; no ecological classification is accepted here. No counts are summed or converted to percentages; denominators are not invented. Missing is not zero; separate observation IDs remain separate. Depth units are not supplied. Choose any source-age axis explicitly. No age conversion, interpolation, physical-core equivalence or vegetation inference is made.</p>`;
  if (!data.groups.length) return `<section aria-label="Native observation diagrams">${summary}<p>No source group has drawable values.</p></section>`;
  const chosen = selectedGroupKey === null ? (options.requireExplicitAnchor ? null : data.groups[0]) : data.groups.find(group => group.key === selectedGroupKey);
  if (selectedGroupKey !== null && !chosen) return unavailable('selected_native_source_group_not_available');
  const groupOptions = data.groups.map(group => `<option value="${escapeHtml(group.key)}"${group === chosen ? ' selected="selected"' : ''}>${escapeHtml(pollenDepthGroupLabel(group))}</option>`).join('');
  return `<section aria-label="Native observation diagrams">${summary}<label for="native-value-depth-group">Exact native source group</label><select id="native-value-depth-group" data-pollen-depth-group="true" style="display:block;max-width:100%">${options.requireExplicitAnchor ? `<option value=""${chosen ? '' : ' selected="selected"'}>Choose an exact native source group</option>` : ''}${groupOptions}</select>${chosen ? renderGroup(chosen,options.selectedObservationIds || []) : '<p>Choose a native source group explicitly before drawing panels. No display anchor is inferred from the selected map signal.</p>'}</section>`;
}

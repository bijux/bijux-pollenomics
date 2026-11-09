// Bind a clicked source facet to native observations, never accepted taxonomy.
function pollenFocusedSignalData(tabs, signal) {
  const empty = (status, reason) => ({status,reason,groupKeys:[],matches:[],observationIds:[],unmatchedVariableIds:[],ambiguousObservationIds:[],matchBasisCounts:{},defaultAnchorKey:null,anchorStatus:'unavailable'});
  const text = value => typeof value === 'string' && value.trim() ? value.trim() : null;
  if (!signal) return empty('unavailable','No source map signal is selected.');
  if (signal.source_family !== 'neotoma' || signal.semantic_role !== 'source_chronology_context'
    || tabs?.overview?.source_family !== 'neotoma') return empty('unavailable','This map feature has no supported native source facet.');
  if (![signal.record_id,signal.source_record_id,tabs.overview.site_id,signal.source_snapshot_id,tabs.provenance?.source_snapshot_id,signal.build_id,tabs.provenance?.build_id].every(value => text(value) === value && value !== null && value !== undefined)
    || signal.record_id !== tabs.overview.site_id
    || signal.source_snapshot_id !== tabs.provenance?.source_snapshot_id
    || signal.build_id !== tabs.provenance?.build_id) return empty('unavailable','Selected feature and detail source identities do not agree.');
  const ids = signal.source_variable_ids, taxon = signal.source_taxon_id, code = signal.source_ecological_code;
  const taxonMode = signal.node_level === 'source_taxon', codeMode = signal.node_level === 'source_ecological_code';
  if (signal.node_level === 'source_sample_presence') return empty('unavailable','Sample presence does not select one native taxon or ecological code.');
  if (!Array.isArray(ids) || ids.some(id => !text(id) || id !== text(id)) || new Set(ids).size !== ids.length
    || !text(signal.source_unit) || signal.source_unit !== text(signal.source_unit)
    || !(taxonMode && ids.length && code === null && ((Number.isSafeInteger(taxon) && taxon >= 0) || text(taxon))
      || codeMode && !ids.length && taxon === null && text(code) && code === text(code))) return empty('unavailable','Selected source facet fields are incomplete or contradictory.');
  const requestedIds = new Set(ids);
  try {
    const native = pollenObservationDiagramData(tabs);
    if (native.status !== 'available') return empty('unavailable','Native observation tables are unavailable.');
    const variables = pollenDepthTableRows(tabs.pollen_composition.variables,['variable_id','source_semantics']);
    const raw = pollenDepthTableRows(tabs.pollen_composition,['observation_id','sample_id','variable_id','source_taxon_id','source_unit','source_ecological_group','source_element_type','source_value','detection_status']);
    const samples = pollenDepthTableRows(tabs.samples?.samples,['sample_id']);
    const index = (rows,field) => { const result=new Map(); for(const row of rows){if(!result.has(row[field]))result.set(row[field],[]);result.get(row[field]).push(row);}return result; };
    const byVariable=index(variables,'variable_id'),byObservation=index(raw,'observation_id'),bySample=index(samples,'sample_id');
    const basis = new Map(), ambiguous = new Set();
    for (const row of raw) {
      if (row.sample_id !== signal.source_record_id || row.source_unit !== signal.source_unit || (taxonMode && !requestedIds.has(row.variable_id))) continue;
      if (text(row.source_element_type) !== 'pollen' || text(row.detection_status) !== 'reported_value'
        || !pollenDepthFinite(row.source_value) || row.source_value <= 0) continue;
      const matches = byVariable.get(row.variable_id) || [];
      let matchBasis = '';
      if (taxonMode) {
        if (row.source_taxon_id !== taxon) continue;
        matchBasis = 'exact_variable_taxon_unit';
      } else {
        const rawCode = text(row.source_ecological_group);
        if (rawCode !== null) {
          if (rawCode !== code) continue;
          matchBasis = 'raw_source_code';
        } else {
          const codes = new Set(matches.flatMap(variable => Array.isArray(variable.source_semantics)
            ? variable.source_semantics.map(item => text(item?.source_ecological_group)).filter(value => value !== null) : []));
          if (!codes.has(code)) continue;
          if (codes.size !== 1) { ambiguous.add(row.observation_id); continue; }
          matchBasis = 'unique_variable_source_code';
        }
      }
      if (matches.length !== 1 || byObservation.get(row.observation_id).length !== 1
        || (bySample.get(row.sample_id) || []).length !== 1) { ambiguous.add(row.observation_id); continue; }
      basis.set(row.observation_id,matchBasis);
    }
    const matches = native.groups.map(group => ({groupKey:group.key,observationIds:group.rows.filter(row => basis.has(row.observation.observation_id)).map(row => row.observation.observation_id)})).filter(match => match.observationIds.length);
    const groupKeys = matches.map(match => match.groupKey), groupKeySet = new Set(groupKeys), observationIds = matches.flatMap(match => match.observationIds);
    const matchedGroups = native.groups.filter(group => groupKeySet.has(group.key));
    const matchedVariables = new Set(matchedGroups.map(group => group.identity[2]));
    const unmatchedVariableIds = ids.filter(id => !matchedVariables.has(id));
    const matchBasisCounts = {};
    for (const id of observationIds) { const value=basis.get(id); matchBasisCounts[value]=(matchBasisCounts[value] || 0)+1; }
    const status = !matches.length ? ambiguous.size ? 'ambiguous' : 'unmatched'
      : ambiguous.size || unmatchedVariableIds.length ? 'partial' : 'matched';
    const contexts = new Set(matchedGroups.map(group => JSON.stringify(group.identity.filter((_,index) => index !== 2 && index !== 3))));
    return {status,reason:'',groupKeys,matches,observationIds,unmatchedVariableIds,ambiguousObservationIds:[...ambiguous],matchBasisCounts,
      defaultAnchorKey:status === 'matched' && contexts.size === 1 ? groupKeys[0] : null,
      anchorStatus:contexts.size > 1 ? 'ambiguous_measurement_context' : contexts.size === 1 ? 'compatible' : 'unavailable'};
  } catch (error) {
    return empty('unavailable','Source signal tables could not be decoded consistently.');
  }
}
function renderPollenFocusedSignal(tabs, signal, data = pollenFocusedSignalData(tabs,signal), activeCountrySelection = null) {
  const text = value => escapeHtml(pollenDepthText(value));
  const countries = Array.isArray(activeCountrySelection)
    && activeCountrySelection.every(value => typeof value === 'string' && value.trim() === value && value.length)
    && new Set(activeCountrySelection).size === activeCountrySelection.length
    ? activeCountrySelection.length ? activeCountrySelection.join(', ') : 'none selected'
    : 'not supplied';
  const sourceContext = signal?.source_family === 'neotoma' && signal?.semantic_role === 'source_chronology_context';
  const scope = `<details><summary>Source signal identity and display scope</summary><dl style="overflow-wrap:anywhere"><dt>Identity</dt><dd>Node: <code>${text(signal?.node_id)}</code>; feature key: <code>${text(signal?.feature_key)}</code>; resolution: ${text(signal?.node_level)}.</dd><dt>Geography</dt><dd>Source country: ${text(signal?.country)}. Active map countries: ${text(countries)}. Source country and display selection are separate.</dd><dt>Selected map chronology</dt><dd>Chronology: <code>${text(signal?.chronology_id)}</code>; claim: <code>${text(signal?.chronology_claim_id)}</code>; selection posture: ${text(signal?.chronology_selection_posture)}. This is separate from the source-age display axis chosen below.</dd><dt>Candidate and propagation posture</dt><dd>Candidate generation: ${text(signal?.candidate_generation_status)}; refusal reason: ${text(signal?.candidate_refusal_reason)}; propagation eligible: ${text(signal?.propagation_eligible)}.</dd><dt>Scenario applicability</dt><dd>${sourceContext ? 'Not applicable: this display-only source context is not a candidate relation scenario. Relation filters do not select an analysis scenario for these observations.' : 'Not established: no supported source-context scenario applicability is supplied.'}</dd><dt>Scientific admission denominators</dt><dd>Admitted, indeterminate and refused scientific-event denominators are not established here. The matched, unmatched and ambiguous observations above are native join counts, not scientific admission counts.</dd></dl></details>`;
  const label = signal?.node_level === 'source_taxon' ? `native taxon ${pollenDepthText(signal.source_taxon_id)}; variables ${pollenDepthText(signal.source_variable_ids)}`
    : signal?.node_level === 'source_ecological_code' ? `literal source code ${pollenDepthText(signal.source_ecological_code)}`
    : signal?.node_level === 'source_sample_presence' ? 'sample presence without one selected taxon or ecological code' : 'native source facet unavailable';
  return `<section data-pollen-focused-signal="${data.status}"><p><strong>Selected map signal:</strong> ${signal ? text(label) : 'none'}; source sample ${text(signal?.source_record_id)}. ${text(data.reason)} ${data.observationIds.length} drawable source observations in ${data.groupKeys.length} native measurement groups match. ${data.unmatchedVariableIds.length} requested variables have no drawable match; ${data.ambiguousObservationIds.length} observation identities or code assignments are ambiguous. Basis: ${data.matchBasisCounts.exact_variable_taxon_unit || 0} exact variable/taxon/unit, ${data.matchBasisCounts.raw_source_code || 0} raw source code, ${data.matchBasisCounts.unique_variable_source_code || 0} uniquely supplied variable code. ${data.anchorStatus === 'ambiguous_measurement_context' ? 'Matching measurement contexts differ; choose a display anchor explicitly.' : ''} Matching groups can contain other source observations. A manual display anchor is separate from the selected map signal; neither literal source codes nor this highlight approve ecological taxonomy or a chronology.</p>${scope}</section>`;
}

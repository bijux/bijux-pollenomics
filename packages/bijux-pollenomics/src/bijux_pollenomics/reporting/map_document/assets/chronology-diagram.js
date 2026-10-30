// Display literal source age assignments without selecting or fitting a chronology.
function ageDepthTableRows(table, fields) {
  if (!detailTableShape(table) || table.record_count !== table.records.length
    || new Set(table.fields).size !== table.fields.length
    || fields.some(field => !table.fields.includes(field))) throw new Error('age_depth_table_unavailable');
  return table.records.map(row => decodeDetailTableRow(table, row));
}
function ageDepthFinite(value) {
  return typeof value === 'number' && Number.isFinite(value);
}
function ageDepthText(value) {
  return value === null || value === undefined || value === '' ? 'not supplied' : String(value);
}
function ageDepthDiagramData(tabs) {
  return sourceAgeAssignmentData(tabs, true);
}
// Exact sample age assignments need no depth until an age-depth plot is requested.
function sourceAgeAssignmentData(tabs, requireDepth = false) {
  const unavailable = reason => ({status:'unavailable', reason, groups:[], total:0, omitted:{}});
  if (tabs?.overview?.source_family !== 'neotoma') return unavailable('source_age_depth_tables_not_available');
  try {
    const samples = ageDepthTableRows(tabs.samples?.samples,
      ['sample_id','collection_unit_id','dataset_id','source_depth']);
    const claims = ageDepthTableRows(tabs.chronology, [
      'chronology_claim_id','subject_type','subject_id','source_record_id',
      'collection_unit_id','dataset_id','chronology_id','chronology_name',
      'source_age_type','source_age_unit','source_age_value',
      'source_age_younger','source_age_older','calibration_status',
      'comparability_status','refusal_reason','is_default_chronology',
    ]);
    const bySample = new Map(), claimIds = new Map(), groups = new Map(), omitted = {};
    for (const sample of samples) {
      if (!bySample.has(sample.sample_id)) bySample.set(sample.sample_id, []);
      bySample.get(sample.sample_id).push(sample);
    }
    for (const claim of claims) claimIds.set(claim.chronology_claim_id, (claimIds.get(claim.chronology_claim_id) || 0) + 1);
    const omit = reason => { omitted[reason] = (omitted[reason] || 0) + 1; };
    for (const claim of claims) {
      if (typeof claim.chronology_claim_id !== 'string' || !claim.chronology_claim_id
        || claimIds.get(claim.chronology_claim_id) !== 1) { omit('ambiguous_claim_identity'); continue; }
      if (claim.subject_type !== 'sample') { omit('non_sample_age_claim'); continue; }
      if (typeof claim.subject_id !== 'string' || !claim.subject_id) { omit('sample_depth_identity_unavailable'); continue; }
      const matches = bySample.get(claim.subject_id) || [];
      if (matches.length !== 1) { omit('sample_depth_identity_unavailable'); continue; }
      const sample = matches[0];
      if (claim.source_record_id !== sample.sample_id
        || typeof sample.collection_unit_id !== 'string' || !sample.collection_unit_id
        || typeof sample.dataset_id !== 'string' || !sample.dataset_id
        || claim.collection_unit_id !== sample.collection_unit_id
        || claim.dataset_id !== sample.dataset_id) { omit('sample_source_relation_mismatch'); continue; }
      if (typeof claim.chronology_id !== 'string' || !claim.chronology_id) { omit('chronology_identity_unavailable'); continue; }
      if (requireDepth && !ageDepthFinite(sample.source_depth)) { omit('source_depth_not_numeric'); continue; }
      const pointPresent = claim.source_age_value !== null && claim.source_age_value !== undefined;
      const youngerPresent = claim.source_age_younger !== null && claim.source_age_younger !== undefined;
      const olderPresent = claim.source_age_older !== null && claim.source_age_older !== undefined;
      if ((pointPresent && !ageDepthFinite(claim.source_age_value))
        || (youngerPresent && !ageDepthFinite(claim.source_age_younger))
        || (olderPresent && !ageDepthFinite(claim.source_age_older))) { omit('source_age_not_numeric'); continue; }
      if (youngerPresent !== olderPresent) { omit('source_age_endpoint_missing'); continue; }
      if (!pointPresent && !youngerPresent) { omit('source_age_not_provided'); continue; }
      if (youngerPresent && claim.source_age_younger > claim.source_age_older) { omit('source_age_endpoints_reversed'); continue; }
      if (pointPresent && youngerPresent && (claim.source_age_value < claim.source_age_younger
        || claim.source_age_value > claim.source_age_older)) { omit('source_age_point_outside_endpoints'); continue; }
      if (![true, false, null, undefined].includes(claim.is_default_chronology)) { omit('source_default_flag_invalid'); continue; }
      const identity = [sample.collection_unit_id,sample.dataset_id,claim.chronology_id,
        claim.source_age_type,claim.source_age_unit,claim.calibration_status,claim.comparability_status];
      const key = JSON.stringify(identity);
      if (!groups.has(key)) groups.set(key, {identity, names:new Set(), rows:[]});
      const group = groups.get(key);
      group.names.add(ageDepthText(claim.chronology_name));
      group.rows.push({claim, depth:sample.source_depth, sample:sample.sample_id,
        point:pointPresent ? claim.source_age_value : null,
        endpoints:youngerPresent ? [claim.source_age_younger,claim.source_age_older] : null});
    }
    const ordered = [...groups.entries()].sort(([left],[right]) => left < right ? -1 : left > right ? 1 : 0)
      .map(([,group]) => ({...group, names:[...group.names].sort(), rows:group.rows.sort((a,b) => a.claim.chronology_claim_id.localeCompare(b.claim.chronology_claim_id))}));
    return {status:'available', groups:ordered, total:claims.length, omitted};
  } catch (error) {
    return unavailable('encoded_age_depth_table_invalid');
  }
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
  const ages = group.rows.flatMap(row => [...(row.point === null ? [] : [row.point]), ...(row.endpoints || [])]);
  const x = ageDepthScale(ages, 85, 500), y = ageDepthScale(group.rows.map(row => row.depth), 40, 190);
  const text = value => escapeHtml(ageDepthText(value));
  const label = `Collection unit ${unit}; dataset ${dataset}; chronology ${chronology}`;
  const titleId = `age-depth-title-${index}`, descriptionId = `age-depth-description-${index}`;
  // Limit only displayed marks; complete counts, extrema and original tables remain.
  const shown = group.rows.slice(0, 500);
  const marks = shown.map(row => {
    const claim = row.claim, cy = y.position(row.depth);
    const refused = Boolean(claim.refusal_reason) || claim.comparability_status === 'refused';
    const dash = refused ? '2 3' : claim.comparability_status === 'comparable' ? '' : '7 4';
    const defaultLabel = claim.is_default_chronology === true ? 'source-default' : claim.is_default_chronology === false ? 'source alternative' : 'default flag not supplied';
    const detail = `${claim.chronology_claim_id}; sample ${row.sample}; depth ${row.depth} (unit not supplied); reported age point ${ageDepthText(row.point)}; reported endpoints ${row.endpoints ? row.endpoints.join(', ') : 'not supplied'}; ${defaultLabel}; source posture ${ageDepthText(claim.comparability_status)}; source refusal ${ageDepthText(claim.refusal_reason)}`;
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
  return `<figure class="age-depth-diagram" style="margin:1rem 0"><figcaption><strong>${text(label)}</strong><br>${text(group.names.join(' / '))}<br>Source age type: ${text(type)} · unit: ${text(ageUnit)}<br>Calibration: ${text(calibration)} · source comparability: ${text(comparability)}<br>${shown.length} of ${group.rows.length} source claims drawn; all remain in the table.</figcaption><div class="source-diagram-plot" tabindex="0" role="region" aria-label="Scrollable source age-depth plot"><svg viewBox="0 0 640 300" width="640" style="max-width:100%;height:auto;background:white" role="img" aria-labelledby="${titleId} ${descriptionId}"><title id="${titleId}">${text(label)}: source age–depth assignments</title><desc id="${descriptionId}">Raw source assignments and reported endpoint spans, not an interpolated curve or fitted age-depth model. Depth increases downward. Age values increase rightward in this source's own basis.</desc><path d="M85,30V240H595" fill="none" stroke="#64748b"/>${xTicks.map(([value,cx]) => `<text x="${cx}" y="256" text-anchor="middle" font-size="12">${text(value)}</text>`).join('')}${yTicks.map(([value,cy]) => `<text x="78" y="${cy+4}" text-anchor="end" font-size="12">${text(value)}</text>`).join('')}<text x="335" y="281" text-anchor="middle" font-size="12">Source age (${text(ageUnit)})</text><text transform="translate(18 135) rotate(-90)" text-anchor="middle" font-size="12">Source depth (unit not supplied)</text>${marks}</svg></div></figure>`;
}
const SOURCE_AGE_OMISSION_LABELS = {
    ambiguous_claim_identity:'duplicate or missing claim identity', non_sample_age_claim:'age claim is not sample-level',
    sample_depth_identity_unavailable:'sample identity is missing, ambiguous or unjoined', sample_source_relation_mismatch:'sample source relations do not match',
    chronology_identity_unavailable:'chronology identity not supplied', source_depth_not_numeric:'missing numeric depth',
    source_age_not_numeric:'age value is not numeric', source_age_endpoint_missing:'incomplete age bounds',
    source_age_not_provided:'age point and bounds not supplied', source_age_endpoints_reversed:'age bounds are reversed',
    source_age_point_outside_endpoints:'age point lies outside its reported bounds', source_default_flag_invalid:'source default flag is invalid',
  };
function renderAgeDepthDiagram(tabs) {
  const data = ageDepthDiagramData(tabs);
  if (data.status !== 'available') return `<section aria-label="Source age-depth diagram"><p>Age-depth diagram unavailable: ${data.reason === 'encoded_age_depth_table_invalid' ? 'the source tables could not be decoded safely' : 'this source has no supported sample/depth tables'}. Original source tables remain below.</p></section>`;
  const plotted = data.groups.reduce((total,group) => total + group.rows.length, 0);
  const omitted = Object.entries(data.omitted).sort().map(([reason,count]) => `${escapeHtml(SOURCE_AGE_OMISSION_LABELS[reason] || 'source assignment cannot be charted')}: ${count}`).join('; ') || 'none';
  return `<section aria-label="Source age-depth diagram"><h3>Source age–depth assignments</h3><p>${plotted} of ${data.total} claims have joinable numeric source age/depth values, in ${data.groups.length} separate source groups. Not charted: ${omitted}. All claims remain in the source table.</p><p>No preferred chronology is selected. Diamond: source-default point; circle: source alternative; square: default flag not supplied. Solid: source-comparable; dashed: context or unspecified; dotted: source-refused. Horizontal spans are reported endpoints with unspecified coverage, not confidence intervals. Refused and contextual assignments are source context, not admitted calendar dates or propagation evidence. Native depth units are not supplied; no centimetre conversion or physical-core equivalence is asserted.</p>${data.groups.map(ageDepthGroupHtml).join('')}</section>`;
}

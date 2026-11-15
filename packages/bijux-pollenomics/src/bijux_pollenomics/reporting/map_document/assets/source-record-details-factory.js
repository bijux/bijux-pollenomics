// Bind the existing source renderers to their owning table and escaping functions.
function createSourceRecordDetails(bindings) {
  const {detailTableShape, decodeDetailTableRow, detailTableText, renderDetailTable, escapeHtml} = bindings;
  if (![detailTableShape, decodeDetailTableRow, detailTableText, renderDetailTable, escapeHtml].every(value => typeof value === 'function')) {
    throw Error('Source detail renderer bindings are unavailable.');
  }
  __SOURCE_RECORD_DETAILS_CONTROLLER__
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
    chronology: renderSourceChronologyContext, classification: renderNativeClassificationContext, provenance: renderSourceProvenanceContext,
    depthProfile: sourceDepthProfile, ageDepthGroup: ageDepthGroupHtml});
}

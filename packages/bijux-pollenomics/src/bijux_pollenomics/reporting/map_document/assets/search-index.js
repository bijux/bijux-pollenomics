// Published UTF-16 postings retain literal substring semantics and visible order.
const ATLAS_SEARCH_ABI = 'atlas-substring-postings.v1';
const atlasSearchIndexes = new WeakMap();
let atlasVisibleSearch = null;
function atlasSearchGrams(text, sizes = [1, 2, 3]) {
  const units = Array.from({length:text.length}, (_, i) => text.charCodeAt(i).toString(16).padStart(4, '0'));
  const result = new Set();
  for (const size of sizes) for (let i = 0; i + size <= units.length; i++) result.add(units.slice(i, i + size).join(''));
  return result;
}
function atlasPublishedSearch(index, layers) {
  if (!index || typeof index !== 'object') staticAtlasFailure('published search index is missing');
  if (atlasSearchIndexes.has(index)) return atlasSearchIndexes.get(index);
  if (index.search_index_abi !== ATLAS_SEARCH_ABI || !index.text_search_index || typeof index.text_search_index !== 'object' || Array.isArray(index.text_search_index)) staticAtlasFailure('search index ABI or object is invalid');
  if (!Array.isArray(layers)) staticAtlasFailure('search layer metadata is missing');
  const metadata = new Map();
  for (const row of layers) {
    if (!row || typeof row !== 'object') staticAtlasFailure('search layer shape is invalid');
    if (row.layer_kind !== 'point') continue;
    if (!Number.isSafeInteger(row.layer_index) || row.layer_index < 0 || metadata.has(row.layer_index) || !Number.isSafeInteger(row.feature_count) || row.feature_count < 0 || !row.layer || typeof row.layer.key !== 'string' || !row.layer.key) staticAtlasFailure('search layer membership is invalid');
    metadata.set(row.layer_index, row);
  }
  if ([...metadata.keys()].sort((a,b)=>a-b).some((value,i)=>value!==i)) staticAtlasFailure('search layer membership is incomplete');
  const docs = new Map(), postings = new Map(), expected = new Map();
  for (const [key, row] of Object.entries(index.text_search_index)) {
    if (key.startsWith('p:')) continue;
    if (!row || typeof row !== 'object' || Array.isArray(row) || Object.keys(row).sort().join(',') !== 'feature_index,layer_index,layer_key,record_id,text' || !Number.isSafeInteger(row.layer_index) || !Number.isSafeInteger(row.feature_index) || row.feature_index < 0 || typeof row.text !== 'string') staticAtlasFailure('search document shape is invalid');
    const layer = metadata.get(row.layer_index);
    if (!layer || row.layer_key !== layer.layer.key || row.feature_index >= layer.feature_count || key !== `d:${row.layer_index}:${row.feature_index}`) staticAtlasFailure('search document representation is foreign');
    docs.set(key, row);
    for (const gram of atlasSearchGrams(row.text)) {
      const posting = expected.get('p:' + gram) || [];
      posting.push(key); expected.set('p:' + gram, posting);
    }
  }
  for (const layer of metadata.values()) for (let i = 0; i < layer.feature_count; i++) if (!docs.has(`d:${layer.layer_index}:${i}`)) staticAtlasFailure('search document membership is incomplete');
  for (const [key, value] of Object.entries(index.text_search_index)) {
    if (!key.startsWith('p:')) continue;
    const wanted = expected.get(key);
    if (!Array.isArray(value) || !wanted || JSON.stringify(value) !== JSON.stringify(wanted.sort())) staticAtlasFailure('search posting membership differs');
    postings.set(key, new Set(value));
  }
  if (postings.size !== expected.size) staticAtlasFailure('search posting membership is incomplete');
  const result = {docs, postings}; atlasSearchIndexes.set(index, result); return result;
}
function atlasSearchText(layer, feature, timeLabel) {
  return `${feature.title || ''} ${feature.subtitle || ''} ${feature.country || ''} ${layer.label || ''} ${timeLabel(feature)}`.toLowerCase();
}
function atlasPrepareVisibleSearch(published, entries, keyFor, timeLabel) {
  const visible = new Map(), fallback = [];
  let normalizationFallbackCount = 0, runtimeRepresentationCount = 0, focalCount = 0;
  entries.forEach((entry, order) => {
    if (!entry.neighborContext) focalCount++;
    const key = keyFor(entry.feature), text = atlasSearchText(entry.layer, entry.feature, timeLabel);
    const row = {entry, order, text};
    if (key === undefined) {
      fallback.push(row); runtimeRepresentationCount++; return;
    }
    const doc = published.docs.get(key);
    if (!doc || doc.layer_key !== entry.layer.key || JSON.stringify(doc.record_id) !== JSON.stringify(entry.feature.record_id ?? null)) staticAtlasFailure('visible search representation differs');
    if (visible.has(key)) staticAtlasFailure('visible search representation is duplicated');
    visible.set(key, row);
    if (text !== doc.text) { fallback.push(row); normalizationFallbackCount++; }
  });
  return {published, visible, fallback, normalizationFallbackCount, runtimeRepresentationCount, focalCount, neighborCount:entries.length - focalCount};
}
function atlasLookupSearch(state, query) {
  const grams = [...atlasSearchGrams(query, [Math.min(3, query.length)])];
  const postings = grams.map(gram => state.published.postings.get('p:' + gram) || new Set()).sort((a, b) => a.size - b.size);
  const results = new Map();
  for (const key of postings[0] || []) {
    if (!postings.every(posting => posting.has(key))) continue;
    const row = state.visible.get(key);
    if (row && row.text.includes(query)) results.set(row.order, row);
  }
  // Only explicitly detected JS/Python text differences and runtime-only views scan.
  for (const row of state.fallback) if (row.text.includes(query)) results.set(row.order, row);
  return [...results.values()].sort((a, b) => a.order - b.order).slice(0, 12).map(row => row.entry);
}
function atlasSearchDeclared() {
  const compatibility = STATIC_ATLAS_BOOTSTRAP.compatibility || {};
  if (!Object.hasOwn(compatibility, 'search_index_abi')) return false;
  if (compatibility.search_index_abi !== ATLAS_SEARCH_ABI) staticAtlasFailure('unsupported search ABI');
  return true;
}
function preparePublishedSearch() {
  if (STATIC_ATLAS_INLINE || !atlasSearchDeclared()) {
    atlasVisibleSearch = null; return;
  }
  const published = atlasPublishedSearch(STATIC_ATLAS_CHUNKS.indexes, STATIC_ATLAS_CHUNKS.provenance.layers);
  atlasVisibleSearch = atlasPrepareVisibleSearch(published, visiblePointEntries, feature => staticAtlasSearchFeatureKeys.get(feature), featureTimeLabel);
  searchCount.dataset.normalizationFallbackCount = String(atlasVisibleSearch.normalizationFallbackCount);
  searchCount.dataset.runtimeRepresentationCount = String(atlasVisibleSearch.runtimeRepresentationCount);
}
function publishedSearchResults(query) {
  if (STATIC_ATLAS_INLINE || !atlasSearchDeclared()) return visiblePointEntries.filter(({layer, feature}) => atlasSearchText(layer, feature, featureTimeLabel).includes(query)).slice(0, 12);
  if (!atlasVisibleSearch && !visiblePointEntries.length) return [];
  if (!atlasVisibleSearch) staticAtlasFailure('published search selection is not prepared');
  return atlasLookupSearch(atlasVisibleSearch, query);
}

function publishedSearchCounts() {
  if (STATIC_ATLAS_INLINE || !atlasSearchDeclared()) {
    const focalCount = visiblePointEntries.filter(({neighborContext}) => !neighborContext).length;
    return {focalCount, neighborCount:visiblePointEntries.length - focalCount};
  }
  if (!atlasVisibleSearch && !visiblePointEntries.length) return {focalCount:0,neighborCount:0};
  if (!atlasVisibleSearch) staticAtlasFailure('published search selection is not prepared');
  return atlasVisibleSearch;
}

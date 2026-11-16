globalThis.BijuxPollenomicsIndexTransport = Object.freeze({
  create(dependencies) {
    const STATIC_ATLAS_BOOTSTRAP = dependencies.bootstrap;
    const staticAtlasFailure = dependencies.failure;
    const staticAtlasTemporalIdentity = dependencies.temporalIdentity;
    const staticAtlasNonnegativeInteger = dependencies.nonnegativeInteger;
    const nativeCalendarNumber = dependencies.nativeCalendarNumber;
    const staticAtlasBoundedGunzip = dependencies.boundedGunzip;
    const staticAtlasSha256 = dependencies.sha256;
    const yieldTask = dependencies.yieldTask;
    if (yieldTask !== undefined && typeof yieldTask !== 'function') staticAtlasFailure('index scheduler must be callable');
    // Keep bounded gram storage private and allocate it only for search restoration.
    let ATLAS_SEARCH_CODE_UNITS, gramUnits, twoUnitGrams, threeUnitGrams;
    const gramCacheLimit = 16384;
    function searchGrams(text, sizes = [1, 2, 3]) {
      if (!ATLAS_SEARCH_CODE_UNITS) {
        ATLAS_SEARCH_CODE_UNITS = Object.freeze(Array.from({length:65536}, (_, unit) => unit.toString(16).padStart(4, '0')));
        gramUnits = new Uint16Array(4096);
        twoUnitGrams = new Map();
        threeUnitGrams = new Map();
      }
      if (typeof text === 'string' && text.length <= gramUnits.length && (arguments.length < 2 || arguments[1] === undefined)) {
        const result = new Set(), count = text.length;
        for (let i = 0; i < count; i++) {
          const unit = text.charCodeAt(i);
          gramUnits[i] = unit;
          result.add(ATLAS_SEARCH_CODE_UNITS[unit]);
        }
        for (let i = 0; i + 1 < count; i++) {
          const a = gramUnits[i], b = gramUnits[i + 1], key = a * 65536 + b;
          let gram = twoUnitGrams.get(key);
          if (gram === undefined) {
            gram = ATLAS_SEARCH_CODE_UNITS[a] + ATLAS_SEARCH_CODE_UNITS[b];
            if (twoUnitGrams.size < gramCacheLimit) twoUnitGrams.set(key, gram);
          }
          result.add(gram);
        }
        for (let i = 0; i + 2 < count; i++) {
          const a = gramUnits[i], b = gramUnits[i + 1], c = gramUnits[i + 2];
          const key = a * 4294967296 + b * 65536 + c;
          let gram = threeUnitGrams.get(key);
          if (gram === undefined) {
            gram = ATLAS_SEARCH_CODE_UNITS[a] + ATLAS_SEARCH_CODE_UNITS[b] + ATLAS_SEARCH_CODE_UNITS[c];
            if (threeUnitGrams.size < gramCacheLimit) threeUnitGrams.set(key, gram);
          }
          result.add(gram);
        }
        return result;
      }
      let encoded = '';
      for (let i = 0; i < text.length; i++) encoded += ATLAS_SEARCH_CODE_UNITS[text.charCodeAt(i)];
      const result = new Set();
      for (const size of sizes) for (let i = 0; i + size * 4 <= encoded.length; i += 4) result.add(encoded.slice(i, i + size * 4));
      return result;
    }
    const SEARCH_DOCUMENTS_SCHEMA = 'atlas-search-documents.v1';
    const SEARCH_COUNT_FIELDS = ['document_count', 'posting_key_count', 'posting_reference_count', 'utf16_unit_count'];
    function searchTransportCounts(payload) {
      const declared = STATIC_ATLAS_BOOTSTRAP.compatibility || {};
      if (Object.hasOwn(declared, 'search_transport_counts')) staticAtlasFailure('search transport counts belong to the bundle header');
      if (!Object.hasOwn(payload, 'search_transport_schema')) {
        if (Object.hasOwn(payload, 'search_transport_counts') || Object.hasOwn(declared, 'search_transport_schema')) staticAtlasFailure('search transport declaration is missing');
        return null;
      }
      if (payload.search_transport_schema !== SEARCH_DOCUMENTS_SCHEMA || declared.search_transport_schema !== SEARCH_DOCUMENTS_SCHEMA || payload.search_index_abi !== 'atlas-substring-postings.v1') staticAtlasFailure('search documents transport declaration differs');
      if (!LOGICAL_SCHEMAS.includes(payload.schema_version === PART_SCHEMA ? payload.bundle_schema : payload.schema_version)) staticAtlasFailure('search documents require a logical shard bundle');
      const counts = payload.search_transport_counts;
      if (!counts || typeof counts !== 'object' || Array.isArray(counts) || Object.keys(counts).sort().join('|') !== SEARCH_COUNT_FIELDS.join('|')) staticAtlasFailure('search transport counts are invalid');
      SEARCH_COUNT_FIELDS.forEach(field => integer(counts[field], `search ${field}`));
      return counts;
    }
    function validateSearchDocument(key, row) {
      if (!row || typeof row !== 'object' || Array.isArray(row) || Object.keys(row).sort().join('|') !== 'feature_index|layer_index|layer_key|record_id|text' || !Number.isSafeInteger(row.layer_index) || row.layer_index < 0 || !Number.isSafeInteger(row.feature_index) || row.feature_index < 0 || typeof row.layer_key !== 'string' || !row.layer_key || typeof row.text !== 'string' || key !== `d:${row.layer_index}:${row.feature_index}`) staticAtlasFailure('search transport document identity is invalid');
    }
    async function restoreSearchDocuments(index, counts) {
      const documents = index.text_search_index;
      if (typeof dependencies.searchGrams !== 'function') staticAtlasFailure('search documents require the published UTF-16 gram helper');
      const postings = Object.create(null);
      const actual = {document_count: 0, utf16_unit_count: 0, posting_key_count: 0, posting_reference_count: 0};
      function add(field, increment) {
        actual[field] = integer(actual[field] + increment, `derived search ${field}`);
        if (actual[field] > counts[field]) staticAtlasFailure(`derived search ${field} exceeds its declared count`);
      }
      const documentKeys = Object.keys(documents).sort();
      for (const key of documentKeys) {
        const row = documents[key];
        validateSearchDocument(key, row);
        add('document_count', 1);
        add('utf16_unit_count', row.text.length);
        const grams = dependencies.searchGrams(row.text);
        if (!(grams instanceof Set)) staticAtlasFailure('search UTF-16 gram helper did not return unique grams');
        let documentReferences = 0;
        const maximumDocumentReferences = Number.MAX_SAFE_INTEGER - actual.posting_reference_count;
        for (const gram of grams) {
          if (typeof gram !== 'string') staticAtlasFailure('search UTF-16 gram identity is invalid');
          const posting = `p:${gram}`;
          if (!Object.hasOwn(postings, posting)) {
            if (!/^(?:[a-f0-9]{4}){1,3}$/.test(gram)) staticAtlasFailure('search UTF-16 gram identity is invalid');
            add('posting_key_count', 1);
            postings[posting] = [];
          }
          documentReferences += 1;
          if (documentReferences > maximumDocumentReferences) integer(actual.posting_reference_count + documentReferences, 'derived search posting_reference_count');
          if (actual.posting_reference_count + documentReferences > counts.posting_reference_count) staticAtlasFailure('derived search posting_reference_count exceeds its declared count');
          // Globally sorted document keys append each unique membership in lexical order.
          postings[posting].push(key);
        }
        // The cap is observed per yield; iterator completion may change it, so do not read it again here.
        actual.posting_reference_count = integer(actual.posting_reference_count + documentReferences, 'derived search posting_reference_count');
        // Yield only between complete documents; no partial search state is published.
        if (yieldTask && actual.document_count % 1024 === 0 && actual.document_count < documentKeys.length) await yieldTask();
      }
      if (SEARCH_COUNT_FIELDS.some(field => actual[field] !== counts[field])) staticAtlasFailure('derived search counts differ from their declaration');
      for (const key of Object.keys(postings).sort()) documents[key] = postings[key];
      if (typeof dependencies.rememberRestoredSearch === 'function') dependencies.rememberRestoredSearch(index, postings);
      return documents;
    }
    const STATIC_ATLAS_INDEX_KINDS = Object.freeze([
      'country_feature_indexes',
      'spatial_degree_feature_indexes',
      'time_interval_feature_indexes',
      'signal_layer_indexes',
      'detail_record_asset_keys',
    ]);
    function staticAtlasSearchKinds(payload) {
      if (!Object.hasOwn(payload, 'search_index_abi')) {
        if (Object.hasOwn(payload, 'text_search_index')) staticAtlasFailure('undeclared search index');
        return STATIC_ATLAS_INDEX_KINDS;
      }
      if (payload.search_index_abi !== 'atlas-substring-postings.v1') staticAtlasFailure('unsupported search ABI');
      return [...STATIC_ATLAS_INDEX_KINDS, 'text_search_index'];
    }
    function staticAtlasIndexShardEnvelopes(row, payload) {
      const signed = STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3';
      searchTransportCounts(payload);
      staticAtlasTemporalIdentity(payload, signed);
      const components = payload.schema_version === 'atlas-static-indexes.v5';
      if (components ? signed || payload.component_time_support !== true : Object.hasOwn(payload, 'component_time_support')) staticAtlasFailure(`${row.asset_key} component time declaration is invalid`);
      if (payload.shard_schema !== (signed ? 'atlas-static-index-shard.v2' : components ? 'atlas-static-index-shard.v3' : 'atlas-static-index-shard.v1') || !Array.isArray(payload.shards)) staticAtlasFailure(`${row.asset_key} index shard declaration is invalid`);
      if (!Number.isSafeInteger(payload.shard_count) || payload.shard_count <= 0) staticAtlasFailure(`${row.asset_key} shard count is invalid`);
      if (!Number.isSafeInteger(payload.reference_count) || payload.reference_count < 0) staticAtlasFailure(`${row.asset_key} reference count is invalid`);
      const shardCount = payload.shard_count;
      const referenceCount = payload.reference_count;
      if (!shardCount || payload.shards.length !== shardCount) staticAtlasFailure(`${row.asset_key} shard count mismatch`);
      if (referenceCount !== staticAtlasNonnegativeInteger(row.record_count, `${row.asset_key} record count`)) staticAtlasFailure(`${row.asset_key} reference count mismatch`);
      const kinds = staticAtlasSearchKinds(payload);
      let previousKindIndex = -1;
      const seenKinds = new Set();
      payload.shards.forEach((shard, index) => {
        const label = `${row.asset_key} shard ${index + 1}`;
        if (!shard || typeof shard !== 'object' || shard.shard_number !== index + 1) staticAtlasFailure(`${label} sequence is invalid`);
        const kindIndex = kinds.indexOf(shard.index_kind);
        if (kindIndex < 0 || kindIndex < previousKindIndex) staticAtlasFailure(`${label} kind ordering is invalid`);
        previousKindIndex = kindIndex;
        seenKinds.add(shard.index_kind);
        if (shard.payload_encoding !== 'gzip_base64') staticAtlasFailure(`${label} payload encoding is invalid`);
        if (!Number.isSafeInteger(shard.record_count) || shard.record_count < 0) staticAtlasFailure(`${label} record count is invalid`);
        if (!Number.isSafeInteger(shard.decoded_byte_count) || shard.decoded_byte_count <= 0 || shard.decoded_byte_count > Number(STATIC_ATLAS_BOOTSTRAP.budgets.chunk_max_bytes)) staticAtlasFailure(`${label} decoded byte count exceeds its byte budget`);
        if (!/^[a-f0-9]{64}$/.test(String(shard.payload_sha256 || ''))) staticAtlasFailure(`${label} payload digest is invalid`);
        if (typeof shard.payload_gzip_base64 !== 'string' || !shard.payload_gzip_base64) staticAtlasFailure(`${label} compressed payload is missing`);
      });
      if (kinds.some((kind) => !seenKinds.has(kind))) staticAtlasFailure(`${row.asset_key} index shard kind is missing`);
      return payload.shards;
    }
    async function staticAtlasDecodeIndexShard(row, shard, components = false, compactSearch = false) {
      const label = `${row.asset_key} shard ${shard.shard_number}`;
      const payloadJson = await staticAtlasBoundedGunzip(shard.payload_gzip_base64, shard.decoded_byte_count, label);
      if (await staticAtlasSha256(payloadJson) !== shard.payload_sha256) staticAtlasFailure(`${label} payload integrity mismatch`);
      let decoded;
      try {
        decoded = JSON.parse(payloadJson);
      } catch (error) {
        staticAtlasFailure(`${label} payload JSON is invalid`);
      }
      const signed = STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3';
      if (!decoded || decoded.schema_version !== (signed ? 'atlas-static-index-shard.v2' : components ? 'atlas-static-index-shard.v3' : 'atlas-static-index-shard.v1') || decoded.index_kind !== shard.index_kind || !Array.isArray(decoded.entries)) staticAtlasFailure(`${label} decoded contract is invalid`);
      if (components ? decoded.component_time_support !== true : Object.hasOwn(decoded, 'component_time_support')) staticAtlasFailure(`${label} component time declaration is invalid`);
      staticAtlasTemporalIdentity(decoded, signed);
      const search = shard.index_kind === 'text_search_index';
      if (Object.hasOwn(decoded, 'search_transport_counts') || (compactSearch && search ? decoded.search_transport_schema !== SEARCH_DOCUMENTS_SCHEMA : Object.hasOwn(decoded, 'search_transport_schema'))) staticAtlasFailure(`${label} search transport declaration differs`);
      if (decoded.entries.length !== shard.record_count) staticAtlasFailure(`${label} record count mismatch`);
      return decoded;
    }
    function staticAtlasIndexTupleCompare(left, right) {
      for (let index = 0; index < Math.max(left.length, right.length); index += 1) {
        if (left[index] === right[index]) continue;
        return left[index] < right[index] ? -1 : 1;
      }
      return 0;
    }
    function staticAtlasValidateFeatureIndexes(value, label) {
      if (!Array.isArray(value) || !value.length) staticAtlasFailure(`${label} feature indexes are invalid`);
      let previous = -1;
      value.forEach((featureIndex) => {
        if (!Number.isSafeInteger(featureIndex) || featureIndex < 0 || featureIndex <= previous) staticAtlasFailure(`${label} feature indexes are invalid`);
        previous = featureIndex;
      });
      return [...value];
    }
    async function staticAtlasMergeIndexShards(row, payload) {
      const envelopes = staticAtlasIndexShardEnvelopes(row, payload);
      const components = payload.schema_version === 'atlas-static-indexes.v5';
      const counts = searchTransportCounts(payload);
      const merged = {
        schema_version: STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3' ? 'atlas-static-signed-indexes.v1' : 'atlas-static-indexes.v2',
        ...(STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3' ? {temporal_profile:payload.temporal_profile,temporal_axis:payload.temporal_axis} : {}),
        ...(components ? {component_time_support:true} : {}),
        scope_slug: payload.scope_slug,
        version: payload.version,
        build_id: payload.build_id,
        asset_key: payload.asset_key,
        reference_count: payload.reference_count,
        country_feature_indexes: Object.create(null),
        spatial_degree_feature_indexes: Object.create(null),
        time_interval_feature_indexes: [],
        signal_layer_indexes: Object.create(null),
        detail_record_asset_keys: Object.create(null),
        ...(payload.search_index_abi ? {search_index_abi:payload.search_index_abi,text_search_index:Object.create(null)} : {}),
      };
      const previousKeys = new Map();
      const componentEnds = new Map();
      const featureReferences = new Map([
        ['country_feature_indexes', new Set()],
        ['spatial_degree_feature_indexes', new Set()],
        ['time_interval_feature_indexes', new Set()],
      ]);
      const assertOrderedUnique = (kind, key, label) => {
        const previous = previousKeys.get(kind);
        if (previous && staticAtlasIndexTupleCompare(previous, key) >= 0) staticAtlasFailure(`${label} entries are duplicated or out of order`);
        previousKeys.set(kind, key);
      };
      const documentWork = {document_count: 0, utf16_unit_count: 0};
      for (const [shardIndex, envelope] of envelopes.entries()) {
        const shard = await staticAtlasDecodeIndexShard(row, envelope, components, counts !== null);
        const kind = shard.index_kind;
        shard.entries.forEach((entry, entryIndex) => {
          const label = `${row.asset_key} shard ${shardIndex + 1} entry ${entryIndex + 1}`;
          if (!Array.isArray(entry)) staticAtlasFailure(`${label} is malformed`);
          if (kind === 'country_feature_indexes' || kind === 'spatial_degree_feature_indexes') {
            if (entry.length !== 3 || typeof entry[0] !== 'string' || !entry[0] || typeof entry[1] !== 'string' || !entry[1]) staticAtlasFailure(`${label} is malformed`);
            assertOrderedUnique(kind, [entry[0], entry[1]], label);
            const outer = merged[kind][entry[0]] || Object.create(null);
            const indexes = staticAtlasValidateFeatureIndexes(entry[2], label);
            indexes.forEach((featureIndex) => {
              const reference = `${entry[1]}\u0000${featureIndex}`;
              if (featureReferences.get(kind).has(reference)) staticAtlasFailure(`${label} feature reference overlaps another shard`);
              featureReferences.get(kind).add(reference);
            });
            outer[entry[1]] = indexes;
            merged[kind][entry[0]] = outer;
          } else if (kind === 'time_interval_feature_indexes') {
            const signed = STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3';
            if (entry.length !== 4 || (signed ? !nativeCalendarNumber(entry[0]) || !nativeCalendarNumber(entry[1]) : !Number.isFinite(entry[0]) || entry[0] < 0 || !Number.isFinite(entry[1])) || entry[1] < entry[0] || typeof entry[2] !== 'string' || !entry[2] || !Number.isSafeInteger(entry[3]) || entry[3] < 0) staticAtlasFailure(`${label} is malformed`);
            assertOrderedUnique(kind, entry, label);
            const reference = `${entry[2]}\u0000${entry[3]}`;
            if (featureReferences.get(kind).has(reference) && (!components || entry[0] <= componentEnds.get(reference))) staticAtlasFailure(`${label} feature reference overlaps another shard`);
            componentEnds.set(reference, entry[1]);
            featureReferences.get(kind).add(reference);
            merged.time_interval_feature_indexes.push([...entry]);
          } else if (kind === 'signal_layer_indexes') {
            if (entry.length !== 2 || typeof entry[0] !== 'string' || !entry[0] || !Array.isArray(entry[1]) || !entry[1].length) staticAtlasFailure(`${label} is malformed`);
            assertOrderedUnique(kind, [entry[0]], label);
            const layers = entry[1];
            if (layers.some((layerKey, index) => typeof layerKey !== 'string' || !layerKey || (index > 0 && layers[index - 1] >= layerKey))) staticAtlasFailure(`${label} layer keys are invalid`);
            merged.signal_layer_indexes[entry[0]] = [...layers];
          } else if (kind === 'detail_record_asset_keys') {
            if (entry.length !== 2 || typeof entry[0] !== 'string' || !entry[0] || typeof entry[1] !== 'string' || !entry[1]) staticAtlasFailure(`${label} is malformed`);
            assertOrderedUnique(kind, [entry[0]], label);
            merged.detail_record_asset_keys[entry[0]] = entry[1];
          } else if (kind === 'text_search_index') {
            if (entry.length !== 2 || typeof entry[0] !== 'string' || !entry[0]) staticAtlasFailure(`${label} search entry is invalid`);
            assertOrderedUnique(kind, [entry[0]], label);
            if (counts !== null) {
              validateSearchDocument(entry[0], entry[1]);
              documentWork.document_count = integer(documentWork.document_count + 1, 'merged search document count');
              documentWork.utf16_unit_count = integer(documentWork.utf16_unit_count + entry[1].text.length, 'merged search UTF-16 unit count');
              if (documentWork.document_count > counts.document_count || documentWork.utf16_unit_count > counts.utf16_unit_count) staticAtlasFailure('merged search documents exceed their declared counts');
            }
            merged.text_search_index[entry[0]] = entry[1];
          } else staticAtlasFailure(`${label} kind is unsupported`);
        });
      }
      const referenceCount = Object.values(merged.country_feature_indexes).reduce(
        (total, layers) => total + Object.values(layers).reduce((subtotal, indexes) => subtotal + indexes.length, 0),
        0
      ) + Object.keys(merged.detail_record_asset_keys).length;
      if (referenceCount !== payload.reference_count) staticAtlasFailure(`${row.asset_key} merged reference count mismatch`);
      if (counts !== null) merged.text_search_index = await restoreSearchDocuments(merged, counts);
      return merged;
    }
    const PART_SCHEMA = 'atlas-static-index-part.v1';
    const LOGICAL_SCHEMAS = ['atlas-static-indexes.v3', 'atlas-static-indexes.v4', 'atlas-static-indexes.v5'];
    const PART_FIELDS = ['asset_key', 'bundle_schema', 'bundle_sha256', 'part_number', 'part_count', 'first_shard_number', 'last_shard_number'];
    const HEADER_FIELDS = ['schema_version', 'scope_slug', 'version', 'build_id', 'search_index_abi', 'search_transport_schema', 'search_transport_counts', 'shard_schema', 'component_time_support', 'temporal_profile', 'temporal_axis', 'shard_count', 'reference_count'];
    const staged = new Map();
    const stagedAssets = new Map();
    let assembly = null;

    function canonicalJSON(value) {
      if (Array.isArray(value)) return `[${value.map(canonicalJSON).join(',')}]`;
      if (value && typeof value === 'object') {
        return `{${Object.keys(value).sort().map(key => `${canonicalJSON(key)}:${canonicalJSON(value[key])}`).join(',')}}`;
      }
      if (typeof value === 'string') return JSON.stringify(value).replace(/[\u007f-\uffff]/g, character => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`);
      if (value === null || typeof value === 'boolean' || Number.isSafeInteger(value)) return JSON.stringify(value);
      staticAtlasFailure('index bundle canonical value is invalid');
    }
    function integer(value, label, minimum = 0) {
      if (!Number.isSafeInteger(value) || value < minimum) staticAtlasFailure(`index ${label} is invalid`);
      return value;
    }
    function commonHeader(payload) {
      return Object.fromEntries(Object.entries(payload).filter(([key]) => !PART_FIELDS.includes(key) && key !== 'shards'));
    }
    function validateIdentity(row, payload) {
      if (!payload || typeof payload !== 'object' || Array.isArray(payload) || row.domain !== 'indexes' || payload.asset_key !== row.asset_key) staticAtlasFailure('index transport identity differs');
      for (const field of ['scope_slug', 'version', 'build_id', 'temporal_profile', 'temporal_axis']) {
        if (payload[field] !== STATIC_ATLAS_BOOTSTRAP[field]) staticAtlasFailure(`index transport ${field} differs`);
      }
      if (payload.search_index_abi !== STATIC_ATLAS_BOOTSTRAP.compatibility?.search_index_abi) staticAtlasFailure('index transport search ABI differs');
      staticAtlasTemporalIdentity(payload, STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3');
    }
    function validatePayload(row, payload) {
      validateIdentity(row, payload);
      searchTransportCounts(payload);
      const transport = STATIC_ATLAS_BOOTSTRAP.compatibility?.index_transport_schema;
      if (payload.schema_version === PART_SCHEMA) {
        if (transport !== PART_SCHEMA || payload.bundle_schema !== STATIC_ATLAS_BOOTSTRAP.compatibility.index_schema || !LOGICAL_SCHEMAS.includes(payload.bundle_schema)) staticAtlasFailure('index part transport declaration differs');
        const header = commonHeader(payload);
        if (Object.keys(header).some(key => !HEADER_FIELDS.includes(key))) staticAtlasFailure('index part header contains unknown fields');
        if (!/^[a-f0-9]{64}$/.test(String(payload.bundle_sha256 || ''))) staticAtlasFailure('index bundle digest is invalid');
        integer(payload.part_number, 'part number', 1);
        integer(payload.part_count, 'part count', 2);
        const first = integer(payload.first_shard_number, 'first shard', 1);
        const last = integer(payload.last_shard_number, 'last shard', first);
        const total = integer(payload.shard_count, 'global shard count', 1);
        integer(payload.reference_count, 'global reference count');
        if (last > total || payload.part_number > payload.part_count || !Array.isArray(payload.shards) || payload.shards.length !== last - first + 1 || row.record_count !== payload.shards.length) staticAtlasFailure('index part shard range differs');
        const expectedFields = [...Object.keys(header), ...PART_FIELDS, 'shards'].sort();
        if (JSON.stringify(Object.keys(payload).sort()) !== JSON.stringify(expectedFields)) staticAtlasFailure('index part fields differ');
        payload.shards.forEach((shard, index) => {
          if (!shard || shard.shard_number !== first + index) staticAtlasFailure('index part global shard numbering differs');
        });
      } else {
        if (transport !== undefined || payload.schema_version !== STATIC_ATLAS_BOOTSTRAP.compatibility?.index_schema) staticAtlasFailure('singleton and part index transports are mixed');
        if (LOGICAL_SCHEMAS.includes(payload.schema_version)) staticAtlasIndexShardEnvelopes(row, payload);
      }
    }
    function references(payload) {
      return Object.values(payload.country_feature_indexes || {}).reduce((total, layers) => total + Object.values(layers).reduce((subtotal, indexes) => subtotal + indexes.length, 0), 0)
        + Object.keys(payload.detail_record_asset_keys || {}).length;
    }
    function validateReferences(payload, rows, split) {
      const count = references(payload);
      if (integer(STATIC_ATLAS_BOOTSTRAP.domains?.indexes?.record_count, 'domain reference count') !== count) staticAtlasFailure('global index reference count differs');
      if (!split && integer(rows[0].record_count, 'singleton reference count') !== count) staticAtlasFailure('singleton index reference count differs');
      return payload;
    }
    async function acceptPart(row, payload, rows) {
      validatePayload(row, payload);
      if (payload.schema_version !== PART_SCHEMA || !Array.isArray(rows) || rows.length !== payload.part_count || rows.length < 2) staticAtlasFailure('index part inventory is incomplete');
      const identities = rows.map(candidate => candidate.asset_key);
      if (new Set(identities).size !== rows.length) staticAtlasFailure('index part asset identity is duplicated');
      rows.forEach((candidate, index) => {
        integer(candidate.sequence, 'asset sequence');
        if (candidate.domain !== 'indexes' || candidate.asset_key !== `indexes:${candidate.sequence}` || (index > 0 && candidate.sequence !== rows[index - 1].sequence + 1)) staticAtlasFailure('index part manifest order differs');
      });
      if (identities[payload.part_number - 1] !== row.asset_key) staticAtlasFailure('index part numbering differs from manifest');
      const encoded = canonicalJSON(payload);
      if (staged.has(payload.part_number)) {
        const previous = staged.get(payload.part_number);
        if (previous.asset_key !== row.asset_key || stagedAssets.get(row.asset_key) !== encoded) staticAtlasFailure('index part number is claimed by another or changed asset');
      } else {
        if (stagedAssets.has(row.asset_key)) staticAtlasFailure('index asset claims different part numbers');
        if (staged.size) {
          const previous = staged.values().next().value;
          if (canonicalJSON(commonHeader(previous)) !== canonicalJSON(commonHeader(payload)) || previous.bundle_schema !== payload.bundle_schema || previous.bundle_sha256 !== payload.bundle_sha256 || previous.part_count !== payload.part_count) staticAtlasFailure('index parts refer to different bundle headers');
        }
        staged.set(payload.part_number, payload);
        stagedAssets.set(row.asset_key, encoded);
      }
      if (staged.size !== rows.length) return null;
      if (!assembly) assembly = (async () => {
        const joined = [], digests = new Set();
        for (let number = 1; number <= rows.length; number += 1) {
          const part = staged.get(number);
          if (!part || part.first_shard_number !== joined.length + 1 || part.last_shard_number !== joined.length + part.shards.length) staticAtlasFailure('index part ranges are not complete and contiguous');
          for (const shard of part.shards) {
            if (shard.shard_number !== joined.length + 1 || typeof shard.payload_sha256 !== 'string' || digests.has(shard.payload_sha256)) staticAtlasFailure('global index shard identity is missing, duplicate or out of order');
            digests.add(shard.payload_sha256);
            joined.push(shard);
          }
        }
        if (joined.length !== payload.shard_count) staticAtlasFailure('global index shard inventory is incomplete');
        const bundle = {...commonHeader(payload), schema_version: payload.bundle_schema, shards: joined};
        if (await staticAtlasSha256(canonicalJSON(bundle)) !== payload.bundle_sha256) staticAtlasFailure('assembled index bundle digest differs');
        const decoded = await staticAtlasMergeIndexShards({asset_key: 'complete-index-bundle', record_count: payload.reference_count}, bundle);
        return validateReferences(decoded, rows, true);
      })();
      return assembly;
    }
    async function consume(row, payload, rows) {
      validatePayload(row, payload);
      if (payload.schema_version === PART_SCHEMA) return acceptPart(row, payload, rows);
      if (!Array.isArray(rows) || rows.length !== 1 || rows[0].asset_key !== row.asset_key) staticAtlasFailure('singleton index inventory differs');
      const decoded = LOGICAL_SCHEMAS.includes(payload.schema_version) ? await staticAtlasMergeIndexShards(row, payload) : payload;
      return validateReferences(decoded, rows, false);
    }
    function sourceFacetAssets(layer, selection) {
      if (layer.semantic_role !== 'source_chronology_context' || !['source_taxon', 'source_ecological_code'].includes(layer.node_level)) return null;
      const schema = STATIC_ATLAS_BOOTSTRAP.compatibility?.source_facet_routing_schema, routing = layer.static_source_facets;
      if (schema === undefined && routing === undefined) return null;
      if (schema !== 'atlas-source-facet-routing.v1' || !routing || Object.keys(routing).sort().join('|') !== 'facets|node_level|schema_version'
        || routing.schema_version !== schema || routing.node_level !== layer.node_level || !routing.facets || typeof routing.facets !== 'object' || Array.isArray(routing.facets)) staticAtlasFailure('source facet routing declaration differs');
      const taxonKey = value => {
        if (!(typeof value === 'number' || typeof value === 'string' && /^\d+$/.test(value)) || !Number.isSafeInteger(Number(value)) || Number(value) < 0) staticAtlasFailure('source facet taxon identity is invalid');
        return String(Number(value));
      };
      const taxon = layer.node_level === 'source_taxon', declarations = layer.facet_metadata?.[taxon ? 'source_taxa' : 'source_ecological_codes'];
      if (!Array.isArray(declarations)) staticAtlasFailure('source facet native declaration is absent');
      const facets = new Map(), nodes = new Map(STATIC_ATLAS_BOOTSTRAP.assets.filter(row => row.domain === 'nodes').map(row => [row.asset_key, row]));
      for (const facet of declarations) {
        const key = taxon ? taxonKey(facet.source_taxon_id) : facet.value, route = routing.facets[key];
        if (typeof key !== 'string' || !key.trim() || facets.has(key) || !Object.hasOwn(routing.facets, key) || !route
          || Object.keys(route).sort().join('|') !== 'asset_keys|record_count' || !Array.isArray(route.asset_keys)
          || staticAtlasNonnegativeInteger(route.record_count, 'source facet route count') !== facet.node_count
          || Boolean(route.record_count) !== Boolean(route.asset_keys.length)) staticAtlasFailure('source facet routing membership is incomplete');
        for (const [index, asset] of route.asset_keys.entries()) {
          const row = nodes.get(asset);
          if (typeof asset !== 'string' || !row || row.layer_key !== layer.key || row.layer_kind !== 'point' || index && route.asset_keys[index - 1] >= asset) staticAtlasFailure('source facet routing asset is foreign or repeated');
        }
        facets.set(key, {facet, assets: route.asset_keys});
      }
      if (Object.keys(routing.facets).length !== facets.size) staticAtlasFailure('source facet routing population differs');
      let selected = null;
      if (!taxon && selection.code !== 'all') selected = [selection.code];
      if (taxon && selection.taxon !== 'all') {
        const match = declarations.find(facet => facet.value === selection.taxon);
        if (!match) staticAtlasFailure('selected source facet is undeclared');
        selected = [taxonKey(match.source_taxon_id)];
      } else if (taxon && selection.preset) selected = selection.preset.member_taxon_ids.map(taxonKey);
      if (selected === null) return null;
      const result = new Set();
      for (const key of selected) {
        if (!facets.has(key)) staticAtlasFailure('selected source facet routing is missing');
        facets.get(key).assets.forEach(asset => result.add(asset));
      }
      return result;
    }
    function requiredStaticAtlasEdgeNodeKeys({STATIC_ATLAS_INLINE, STATIC_ATLAS_CHUNKS,
      validateStaticAtlasEdgeAssets, visibleGovernedEdges, staticAtlasNodeSelectionNeeded,
      map, featureCoordinatePair, atlasEdgeIntersectsViewport}) {
      if (STATIC_ATLAS_INLINE || STATIC_ATLAS_CHUNKS.edges.schema_version === 'atlas-edges-chunk.v1') return new Set();
      const edges = STATIC_ATLAS_CHUNKS.edges, nodeRows = validateStaticAtlasEdgeAssets(edges);
      const result = new Set();
      for (const edge of visibleGovernedEdges()) {
        const source = edges.endpoint_node_geometry[edge.source_record_id].filter(hint => staticAtlasNodeSelectionNeeded(nodeRows.get(hint.asset_key)));
        const target = edges.endpoint_node_geometry[edge.target_record_id].filter(hint => staticAtlasNodeSelectionNeeded(nodeRows.get(hint.asset_key)));
        const intersects = !map._loaded || source.some(left => {
          const a = featureCoordinatePair(left);
          return a && target.some(right => {
            const b = featureCoordinatePair(right);
            return b && atlasEdgeIntersectsViewport(map, [[a.latitude, a.longitude], [b.latitude, b.longitude]]);
          });
        });
        if (intersects) [...source, ...target].forEach(hint => result.add(hint.asset_key));
      }
      return result;
    }
    function planNodeAssets({endpointKeys, edgeSelection, nodeNeeded, viewportNeeded, layerForRow, isLoaded, indexes, overhead, sourceSelection}) {
      if (edgeSelection !== undefined) endpointKeys = requiredStaticAtlasEdgeNodeKeys(edgeSelection);
      const routes = new Map();
      const required = STATIC_ATLAS_BOOTSTRAP.assets.filter(row => {
        if (row.domain !== 'nodes' || isLoaded(row.asset_key) || !nodeNeeded(row)) return false;
        const layer = layerForRow(row);
        if (!routes.has(layer.key)) routes.set(layer.key, sourceFacetAssets(layer, layer.semantic_role === 'source_chronology_context' ? sourceSelection(layer) : null));
        const selected = routes.get(layer.key);
        return endpointKeys.has(row.asset_key) || ((selected === null || selected.has(row.asset_key)) && viewportNeeded(row));
      });
      if (Object.hasOwn(STATIC_ATLAS_BOOTSTRAP.compatibility || {}, 'search_index_abi')) {
        if (STATIC_ATLAS_BOOTSTRAP.compatibility.search_index_abi !== 'atlas-substring-postings.v1') staticAtlasFailure('unsupported search ABI');
        const rows = indexes();
        if (!rows.length) staticAtlasFailure('published search index is missing');
        required.push(...rows.filter(row => !isLoaded(row.asset_key)));
      }
      const requests = required.length + overhead.request_count;
      if (requests > staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests, 'interaction request budget')) staticAtlasFailure(`selection requires ${requests} requests, above the interaction budget`);
      const bytes = overhead.byte_count + required.reduce((total, row) => total + staticAtlasNonnegativeInteger(row.byte_count, `${row.asset_key} byte count`), 0);
      if (bytes > staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes, 'interaction byte budget')) staticAtlasFailure(`selection requires ${bytes} bytes, above the interaction budget`);
      return required;
    }
    return Object.freeze({searchGrams, validatePayload, mergeShards: staticAtlasMergeIndexShards, acceptPart, consume, planNodeAssets});
  }
});

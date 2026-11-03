
      (async () => {
      const STATIC_ATLAS_ASSET_TABLE_FIELDS = Object.freeze([
        'asset_key', 'domain', 'sequence', 'path', 'sha256', 'integrity',
        'payload_sha256', 'payload_encoding', 'decoded_byte_count', 'byte_count',
        'record_count', 'initial_load', 'layer_index', 'layer_key', 'layer_kind',
        'country_keys', 'bounds', 'time_min_bp', 'time_max_bp',
        'untimed_record_count', 'chronology_absent_record_count',
        'refused_chronology_record_count', 'contextual_chronology_record_count',
        'scientific_signal_ids',
      ]);
      const STATIC_ATLAS_ASSET_TABLE_STORED_FIELDS = Object.freeze([
        'domain', 'sha256', 'payload_sha256', 'decoded_byte_count', 'byte_count',
        'record_count', 'layer_index', 'layer_key', 'layer_kind', 'country_keys',
        'bounds', 'time_min_bp', 'time_max_bp', 'untimed_record_count',
        'chronology_absent_record_count', 'refused_chronology_record_count',
        'contextual_chronology_record_count',
        'scientific_signal_ids',
      ]);
      const STATIC_ATLAS_ASSET_TABLE_V2_STORED_FIELDS = Object.freeze(
        STATIC_ATLAS_ASSET_TABLE_STORED_FIELDS.filter((field) => ![
          'chronology_absent_record_count',
          'refused_chronology_record_count',
          'contextual_chronology_record_count',
        ].includes(field))
      );
      const STATIC_ATLAS_ASSET_TABLE_V1_FIELDS = Object.freeze(
        STATIC_ATLAS_ASSET_TABLE_FIELDS.filter((field) => ![
          'chronology_absent_record_count',
          'refused_chronology_record_count',
          'contextual_chronology_record_count',
        ].includes(field))
      );
      const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT = 12;
      const STATIC_ATLAS_BOOTSTRAP = normalizeStaticAtlasBootstrap(JSON.parse(document.getElementById('atlas-static-bootstrap').textContent || '{}'));
      const STATIC_ATLAS_INLINE = STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-inline-bootstrap.v1';
      globalThis.__BIJUX_ATLAS_RAW_CHUNKS__ = globalThis.__BIJUX_ATLAS_RAW_CHUNKS__ || [];
      const STATIC_ATLAS_RAW_CHUNKS = globalThis.__BIJUX_ATLAS_RAW_CHUNKS__;
      const STATIC_ATLAS_CHUNKS = { nodes: [], details: [] };
      const staticAtlasLoadedAssets = new Set();
      const staticAtlasInFlightAssets = new Map();
      let staticAtlasIndexTransport = null;
      let staticAtlasIndexTransportRequest = null;
      const staticAtlasSearchFeatureKeys = new WeakMap();
      const STATIC_ATLAS_SCHEMAS = {
        provenance: ['atlas-provenance-chunk.v2', 'atlas-provenance-chunk.v3'],
        nodes: STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3' ? ['atlas-node-chunk.v2'] : ['atlas-node-chunk.v1'],
        details: ['atlas-details-chunk.v1'],
        edges: ['atlas-edges-chunk.v1', 'atlas-edges-chunk.v2'],
        sequences: ['atlas-sequences-chunk.v1'],
        indexes: STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3' ? ['atlas-static-indexes.v4'] : ['atlas-static-indexes.v1', 'atlas-static-indexes.v2', 'atlas-static-indexes.v3', 'atlas-static-indexes.v5'],
      };
      function staticAtlasFailure(message) {
        throw new Error(`Static atlas data cannot be loaded: ${message}. Reload the page; if the problem persists, redeploy the HTML and hashed assets from the same build.`);
      }
      function staticAtlasNonnegativeInteger(value, label) {
        if (value === null || value === undefined) staticAtlasFailure(`${label} is missing`);
        if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0) staticAtlasFailure(`${label} is invalid`);
        return value;
      }
      function staticAtlasNullableFiniteNumber(value, label, minimum, maximum) {
        if (value === null) return null;
        if (value === undefined || typeof value === 'boolean' || (typeof value === 'string' && !value.trim())) staticAtlasFailure(`${label} is missing`);
        if (typeof value !== 'number' && typeof value !== 'string') staticAtlasFailure(`${label} is invalid`);
        const numeric = Number(value);
        if (!Number.isFinite(numeric) || numeric < minimum || numeric > maximum) staticAtlasFailure(`${label} is invalid`);
        return numeric;
      }
      function staticAtlasIntegrityFromHex(digest) {
        if (!/^[a-f0-9]{64}$/.test(String(digest || '')) || typeof btoa !== 'function') staticAtlasFailure('asset table digest is invalid');
        const bytes = String(digest).match(/.{2}/g).map((pair) => String.fromCharCode(Number.parseInt(pair, 16))).join('');
        return `sha256-${btoa(bytes)}`;
      }
      function staticAtlasTemporalIdentity(payload, signed) {
        if (!payload || typeof payload !== 'object' || (signed
            ? payload.temporal_profile !== 'calendar-bp1950-signed.v1' || payload.temporal_axis !== 'BP1950'
            : 'temporal_profile' in payload || 'temporal_axis' in payload)) staticAtlasFailure('static temporal profile identity differs');
      }
      function normalizeStaticAtlasBootstrap(bootstrap) {
        if (!bootstrap || typeof bootstrap !== 'object' || !['atlas-static-bootstrap.v2','atlas-static-bootstrap.v3'].includes(bootstrap.schema_version)) return bootstrap;
        const signed = bootstrap.schema_version === 'atlas-static-bootstrap.v3';
        staticAtlasTemporalIdentity(bootstrap, signed);
        if (signed && !/^[a-f0-9]{64}$/.test(bootstrap.native_view_sha256 || '')) staticAtlasFailure('signed native view identity is missing');
        const table = bootstrap.assets;
        const compact = ['atlas-static-asset-table.v2', 'atlas-static-asset-table.v3', 'atlas-static-asset-table.v4'].includes(table?.schema_version);
        const expectedTableKeys = compact
          ? ['fields', 'record_count', 'records', 'schema_version', 'scope_slug']
          : ['fields', 'record_count', 'records', 'schema_version'];
        if (signed) expectedTableKeys.push('temporal_axis', 'temporal_profile');
        if (!table || typeof table !== 'object' || Object.keys(table).sort().join('|') !== expectedTableKeys.join('|')) staticAtlasFailure('asset table shape is invalid');
        if (!(signed ? ['atlas-static-asset-table.v4'] : ['atlas-static-asset-table.v1', 'atlas-static-asset-table.v2', 'atlas-static-asset-table.v3']).includes(table.schema_version)) staticAtlasFailure('asset table schema is invalid');
        staticAtlasTemporalIdentity(table, signed);
        const splitFields = ['chronology_absent_record_count', 'refused_chronology_record_count', 'contextual_chronology_record_count'];
        const storedFields = ['atlas-static-asset-table.v3','atlas-static-asset-table.v4'].includes(table.schema_version)
          ? STATIC_ATLAS_ASSET_TABLE_STORED_FIELDS
          : table.schema_version === 'atlas-static-asset-table.v2'
            ? STATIC_ATLAS_ASSET_TABLE_STORED_FIELDS.filter((field) => !splitFields.includes(field))
            : STATIC_ATLAS_ASSET_TABLE_FIELDS.filter((field) => !splitFields.includes(field));
        if (!Array.isArray(table.fields) || table.fields.length !== storedFields.length || table.fields.some((field, index) => field !== storedFields[index]) || new Set(table.fields).size !== table.fields.length) staticAtlasFailure('asset table fields are invalid');
        if (compact && (typeof table.scope_slug !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(table.scope_slug))) staticAtlasFailure('asset table scope is invalid');
        if (!Number.isSafeInteger(table.record_count) || table.record_count < 0 || !Array.isArray(table.records) || table.records.length !== table.record_count) staticAtlasFailure('asset table record count is invalid');
        const assetKeys = new Set();
        const paths = new Set();
        const sequences = new Set();
        const assets = table.records.map((record, recordIndex) => {
          if (!Array.isArray(record) || record.length !== storedFields.length) staticAtlasFailure(`asset table row ${recordIndex} width is invalid`);
          const stored = Object.fromEntries(storedFields.map((field, index) => [field, record[index]]));
          const domain = stored.domain;
          let row = compact
            ? {
                asset_key: `${domain}:${recordIndex}`,
                domain,
                sequence: recordIndex,
                path: `${table.scope_slug}.atlas-${domain}.${String(recordIndex).padStart(4, '0')}.${String(stored.sha256 || '').slice(0, 16)}.js`,
                sha256: stored.sha256,
                integrity: staticAtlasIntegrityFromHex(stored.sha256),
                payload_sha256: stored.payload_sha256,
                payload_encoding: ['provenance', 'nodes', 'details'].includes(domain) ? 'gzip_base64' : 'json',
                decoded_byte_count: stored.decoded_byte_count,
                byte_count: stored.byte_count,
                record_count: stored.record_count,
                initial_load: !['nodes', 'details', 'indexes'].includes(domain),
                ...Object.fromEntries(STATIC_ATLAS_ASSET_TABLE_FIELDS.slice(STATIC_ATLAS_ASSET_CORE_FIELD_COUNT).map((field) => [field, stored[field]])),
              }
            : stored;
          if (row.domain === 'nodes' && !['atlas-static-asset-table.v3','atlas-static-asset-table.v4'].includes(table.schema_version)) {
            row = {
              ...row,
              chronology_absent_record_count: null,
              refused_chronology_record_count: null,
              contextual_chronology_record_count: null,
            };
          }
          if (STATIC_ATLAS_ASSET_TABLE_FIELDS.slice(0, STATIC_ATLAS_ASSET_CORE_FIELD_COUNT).some((field) => row[field] === null || row[field] === undefined)) staticAtlasFailure(`asset table row ${recordIndex} core field is missing`);
          if (typeof row.asset_key !== 'string' || !row.asset_key || typeof row.domain !== 'string' || !row.domain || typeof row.path !== 'string' || !row.path) staticAtlasFailure(`asset table row ${recordIndex} identity is invalid`);
          if (!['provenance', 'nodes', 'details', 'edges', 'sequences', 'indexes'].includes(row.domain)) staticAtlasFailure(`asset table row ${recordIndex} domain is invalid`);
          if (['sha256', 'integrity', 'payload_sha256', 'payload_encoding'].some((field) => typeof row[field] !== 'string' || !row[field])) staticAtlasFailure(`asset table row ${recordIndex} transport field is invalid`);
          if (['decoded_byte_count', 'byte_count', 'record_count'].some((field) => !Number.isSafeInteger(row[field]) || row[field] < 0) || typeof row.initial_load !== 'boolean') staticAtlasFailure(`asset table row ${recordIndex} accounting field is invalid`);
          if (!Number.isSafeInteger(row.sequence) || row.sequence !== recordIndex || sequences.has(row.sequence)) staticAtlasFailure(`asset table row ${recordIndex} sequence is invalid`);
          if (assetKeys.has(row.asset_key) || paths.has(row.path)) staticAtlasFailure(`asset table row ${recordIndex} identity is duplicated`);
          assetKeys.add(row.asset_key);
          paths.add(row.path);
          sequences.add(row.sequence);
          const optionalFields = STATIC_ATLAS_ASSET_TABLE_FIELDS.slice(STATIC_ATLAS_ASSET_CORE_FIELD_COUNT);
          if (row.domain === 'nodes') {
            if (!Number.isSafeInteger(row.layer_index) || row.layer_index < 0 || typeof row.layer_key !== 'string' || !row.layer_key || !['point', 'polygon'].includes(row.layer_kind)) staticAtlasFailure(`asset table row ${recordIndex} node identity is invalid`);
            if (!Array.isArray(row.country_keys) || row.country_keys.some((country) => typeof country !== 'string' || !country) || !Array.isArray(row.scientific_signal_ids) || row.scientific_signal_ids.some((signalId) => typeof signalId !== 'string' || !signalId)) staticAtlasFailure(`asset table row ${recordIndex} node selection field is invalid`);
            const chronologySplit = [row.chronology_absent_record_count, row.refused_chronology_record_count, row.contextual_chronology_record_count];
            const splitAvailable = chronologySplit.map((value) => value !== null && value !== undefined);
            if (splitAvailable.some(Boolean) && !splitAvailable.every(Boolean)) staticAtlasFailure(`asset table row ${recordIndex} chronology split is incomplete`);
            if (['atlas-static-asset-table.v3','atlas-static-asset-table.v4'].includes(table.schema_version) && !splitAvailable.every(Boolean)) staticAtlasFailure(`asset table row ${recordIndex} chronology split is required`);
            if (splitAvailable.every(Boolean) && (chronologySplit.some((value) => !Number.isSafeInteger(value) || value < 0) || chronologySplit.reduce((total, value) => total + value, 0) !== row.untimed_record_count)) staticAtlasFailure(`asset table row ${recordIndex} chronology split is inconsistent`);
          } else {
            if (optionalFields.some((field) => row[field] !== null && row[field] !== undefined)) staticAtlasFailure(`asset table row ${recordIndex} non-node selection field is not null`);
            optionalFields.forEach((field) => delete row[field]);
          }
          return row;
        });
        return { ...bootstrap, assets };
      }
      function validateStaticAtlasBootstrap() {
        if (!['atlas-static-bootstrap.v1', 'atlas-static-bootstrap.v2', 'atlas-static-bootstrap.v3'].includes(STATIC_ATLAS_BOOTSTRAP.schema_version)) staticAtlasFailure('bootstrap schema mismatch');
        staticAtlasTemporalIdentity(STATIC_ATLAS_BOOTSTRAP, STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3');
        if (STATIC_ATLAS_BOOTSTRAP.version !== "v66") staticAtlasFailure('bootstrap version mismatch');
        if (!/^atlas-[a-f0-9]{64}$/.test(String(STATIC_ATLAS_BOOTSTRAP.build_id || ''))) staticAtlasFailure('bootstrap build identity is invalid');
        if (!Array.isArray(STATIC_ATLAS_BOOTSTRAP.assets)) staticAtlasFailure('bootstrap asset inventory is missing');
        if (STATIC_ATLAS_BOOTSTRAP.transport_integrity?.http_https !== 'subresource_integrity_plus_payload_sha256' || STATIC_ATLAS_BOOTSTRAP.transport_integrity?.file !== 'payload_sha256_after_script_registration' || STATIC_ATLAS_BOOTSTRAP.transport_integrity?.file_pre_execution_sri !== false) staticAtlasFailure('transport-integrity posture mismatch');
        const compatibilityKeys = { provenance: 'provenance_schema', nodes: 'node_schema', details: 'detail_schema', edges: 'edge_schema', sequences: 'sequence_schema', indexes: 'index_schema' };
        Object.entries(STATIC_ATLAS_SCHEMAS).forEach(([domain, schemas]) => {
          const declared = STATIC_ATLAS_BOOTSTRAP.compatibility?.[compatibilityKeys[domain]];
          const legacyWithoutDetails = domain === 'details' && STATIC_ATLAS_BOOTSTRAP.compatibility?.provenance_schema === 'atlas-provenance-chunk.v2' && declared === undefined;
          if (!legacyWithoutDetails && !schemas.includes(declared)) staticAtlasFailure(`${domain} compatibility declaration mismatch`);
        });
        STATIC_ATLAS_BOOTSTRAP.assets.forEach((row) => {
          if (!/^[a-z0-9][a-z0-9.-]*[.]js$/.test(String(row.path || ''))) staticAtlasFailure(`${row.asset_key || 'unknown asset'} path is invalid`);
          if (!/^[a-f0-9]{64}$/.test(String(row.sha256 || '')) || !/^[a-f0-9]{64}$/.test(String(row.payload_sha256 || ''))) staticAtlasFailure(`${row.asset_key || 'unknown asset'} digest is invalid`);
          if (!/^sha256-[A-Za-z0-9+/]{43}=$/.test(String(row.integrity || ''))) staticAtlasFailure(`${row.asset_key || 'unknown asset'} integrity declaration is invalid`);
          const payloadEncoding = row.payload_encoding || 'json';
          if (!['json', 'gzip_base64'].includes(payloadEncoding)) staticAtlasFailure(`${row.asset_key || 'unknown asset'} payload encoding is invalid`);
          if (payloadEncoding === 'gzip_base64' && !['provenance', 'nodes', 'details'].includes(row.domain)) staticAtlasFailure(`${row.asset_key || 'unknown asset'} compressed payload domain is invalid`);
          const requiresDecodedByteCount = ['atlas-static-indexes.v3','atlas-static-indexes.v4','atlas-static-indexes.v5'].includes(STATIC_ATLAS_BOOTSTRAP.compatibility?.index_schema) || (['provenance', 'nodes', 'details'].includes(row.domain) && payloadEncoding === 'gzip_base64');
          if (requiresDecodedByteCount && (!Number.isSafeInteger(row.decoded_byte_count) || row.decoded_byte_count <= 0)) staticAtlasFailure(`${row.asset_key || 'unknown asset'} decoded byte count is invalid`);
          if (row.decoded_byte_count !== undefined && (!Number.isSafeInteger(row.decoded_byte_count) || row.decoded_byte_count <= 0 || row.decoded_byte_count > Number(STATIC_ATLAS_BOOTSTRAP.budgets?.chunk_max_bytes))) staticAtlasFailure(`${row.asset_key || 'unknown asset'} decoded byte count exceeds its byte budget`);
          const recordCount = staticAtlasNonnegativeInteger(row.record_count, `${row.asset_key || 'unknown asset'} record count`);
          staticAtlasNonnegativeInteger(row.byte_count, `${row.asset_key || 'unknown asset'} byte count`);
          if (row.domain === 'nodes') {
            const untimedCount = staticAtlasNonnegativeInteger(row.untimed_record_count, `${row.asset_key || 'unknown asset'} untimed record count`);
            if (untimedCount > recordCount) staticAtlasFailure(`${row.asset_key || 'unknown asset'} untimed record count exceeds its record count`);
            const chronologySplit = [
              row.chronology_absent_record_count,
              row.refused_chronology_record_count,
              row.contextual_chronology_record_count,
            ];
            const splitAvailable = chronologySplit.map((value) => value !== null && value !== undefined);
            if (splitAvailable.some(Boolean) && !splitAvailable.every(Boolean)) staticAtlasFailure(`${row.asset_key || 'unknown asset'} chronology split is incomplete`);
            if (splitAvailable.every(Boolean)) {
              const splitTotal = chronologySplit.reduce((total, value, index) => total + staticAtlasNonnegativeInteger(value, `${row.asset_key || 'unknown asset'} chronology split ${index}`), 0);
              if (splitTotal !== untimedCount) staticAtlasFailure(`${row.asset_key || 'unknown asset'} chronology split is inconsistent`);
            }
            const minimumAllowed = STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3' ? -Number.MAX_SAFE_INTEGER : 0;
            if (STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3' && [row.time_min_bp,row.time_max_bp].some(value => value !== null && !nativeCalendarNumber(value))) staticAtlasFailure('signed node time extent is invalid');
            const timeMinimum = staticAtlasNullableFiniteNumber(row.time_min_bp, `${row.asset_key || 'unknown asset'} minimum BP`, minimumAllowed, Number.MAX_SAFE_INTEGER);
            const timeMaximum = staticAtlasNullableFiniteNumber(row.time_max_bp, `${row.asset_key || 'unknown asset'} maximum BP`, minimumAllowed, Number.MAX_SAFE_INTEGER);
            if ((timeMinimum === null) !== (timeMaximum === null) || (timeMinimum !== null && timeMinimum > timeMaximum)) staticAtlasFailure(`${row.asset_key || 'unknown asset'} BP interval is invalid`);
            if ((timeMinimum === null) !== (untimedCount === recordCount)) staticAtlasFailure(`${row.asset_key || 'unknown asset'} BP interval contradicts its untimed record count`);
            if (row.bounds !== null) {
              if (!Array.isArray(row.bounds) || row.bounds.length !== 4) staticAtlasFailure(`${row.asset_key || 'unknown asset'} bounds are invalid`);
              const [south, west, north, east] = row.bounds;
              const validSouth = staticAtlasNullableFiniteNumber(south, `${row.asset_key || 'unknown asset'} south bound`, -90, 90);
              const validWest = staticAtlasNullableFiniteNumber(west, `${row.asset_key || 'unknown asset'} west bound`, -180, 180);
              const validNorth = staticAtlasNullableFiniteNumber(north, `${row.asset_key || 'unknown asset'} north bound`, -90, 90);
              const validEast = staticAtlasNullableFiniteNumber(east, `${row.asset_key || 'unknown asset'} east bound`, -180, 180);
              if ([validSouth, validWest, validNorth, validEast].some((value) => value === null) || validSouth > validNorth || validWest > validEast) staticAtlasFailure(`${row.asset_key || 'unknown asset'} bounds ordering is invalid`);
            }
          }
        });
        const keys = STATIC_ATLAS_BOOTSTRAP.assets.map((row) => row.asset_key);
        if (new Set(keys).size !== keys.length) staticAtlasFailure('bootstrap asset identities are duplicated');
        const paths = STATIC_ATLAS_BOOTSTRAP.assets.map((row) => row.path);
        if (new Set(paths).size !== paths.length) staticAtlasFailure('bootstrap asset paths are duplicated');
        const sequences = STATIC_ATLAS_BOOTSTRAP.assets.map((row) => row.sequence);
        if (sequences.some((sequence, index) => !Number.isSafeInteger(sequence) || sequence !== index) || new Set(sequences).size !== sequences.length) staticAtlasFailure('bootstrap asset sequences are invalid');
        const initial = STATIC_ATLAS_BOOTSTRAP.assets.filter((row) => row.initial_load === true);
        const runtime = STATIC_ATLAS_BOOTSTRAP.runtime;
        let runtimeBytes = 0, runtimeRequests = 0;
        if (runtime !== undefined) {
          if (!runtime || typeof runtime !== 'object'
            || typeof runtime.path !== 'string' || typeof runtime.integrity !== 'string'
            || !/^[A-Za-z0-9][A-Za-z0-9._-]*[.]atlas-runtime[.][a-f0-9]{16}[.]js$/.test(runtime.path)
            || !/^sha256-[A-Za-z0-9+/]{43}=$/.test(runtime.integrity)) staticAtlasFailure('runtime transport identity is invalid');
          runtimeBytes = staticAtlasNonnegativeInteger(runtime.byte_count, 'runtime byte count');
          if (runtimeBytes <= 0 || runtimeBytes > 524288) staticAtlasFailure('runtime byte budget exceeded');
          runtimeRequests = 1;
        }
        const inlineBytes = ['atlas-native-lra-binding', 'atlas-modeled-context-binding'].reduce((total, id) => {
          const bindings = document.querySelectorAll(`[id="${id}"]`);
          if (bindings.length !== 1 || bindings[0].tagName !== 'SCRIPT' || bindings[0].type !== 'application/json' || typeof bindings[0].textContent !== 'string') staticAtlasFailure(`${id} binding payload is unavailable`);
          try { JSON.parse(bindings[0].textContent); } catch (error) { staticAtlasFailure(`${id} binding JSON is invalid`); }
          return total + new TextEncoder().encode(bindings[0].textContent).byteLength;
        }, 0);
        const optionalControllers = runtime?.optional_controllers;
        const controllerKeys = optionalControllers && Object.keys(optionalControllers).sort().join('|');
        if (optionalControllers !== undefined && (!optionalControllers || !['evidence_tools','evidence_tools|index_transport'].includes(controllerKeys))) staticAtlasFailure('optional runtime controllers are invalid');
        const optionalTools = optionalControllers === undefined ? [] : [evidenceToolsDescriptor(), ...(Object.hasOwn(optionalControllers, 'index_transport') ? [indexTransportDescriptor()] : [])];
        const controllerPaths = optionalTools.map(row => row.path);
        if (new Set(controllerPaths).size !== controllerPaths.length || controllerPaths.some(path => path === runtime.path || paths.includes(path))) staticAtlasFailure('optional runtime path is duplicated');
        if (STATIC_ATLAS_BOOTSTRAP.assets.length + runtimeRequests + optionalTools.length > 512) staticAtlasFailure('total asset file budget exceeded');
        const totalBytes = runtimeBytes + optionalTools.reduce((total, row) => total + row.byte_count, 0) + inlineBytes + STATIC_ATLAS_BOOTSTRAP.assets.reduce((total, row) => total + row.byte_count, 0);
        const totalByteBudget = staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets?.static_assets_max_bytes, 'total asset byte budget');
        if (totalBytes > totalByteBudget) staticAtlasFailure('total asset byte budget exceeded');
        const initialBytes = runtimeBytes + inlineBytes + initial.reduce((total, row) => total + staticAtlasNonnegativeInteger(row.byte_count, `${row.asset_key} byte count`), 0);
        const initialRequestBudget = staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets?.initial_max_requests, 'initial request budget');
        const initialByteBudget = staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets?.initial_max_bytes, 'initial byte budget');
        staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets?.interaction_max_requests, 'interaction request budget');
        staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets?.interaction_max_bytes, 'interaction byte budget');
        staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets?.chunk_max_bytes, 'chunk byte budget');
        staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets?.filter_main_thread_max_ms, 'filter main-thread budget');
        if (initial.length + runtimeRequests > initialRequestBudget) staticAtlasFailure('initial request budget exceeded');
        if (initialBytes > initialByteBudget) staticAtlasFailure('initial byte budget exceeded');
        staticAtlasIndexRows();
      }
      async function staticAtlasSha256(text) {
        if (!globalThis.crypto || !globalThis.crypto.subtle || typeof TextEncoder === 'undefined') staticAtlasFailure('browser integrity support is unavailable');
        const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
        return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, '0')).join('');
      }
      async function staticAtlasBoundedGunzip(encoded, expectedByteCount, label, signal = null) {
        signal?.throwIfAborted();
        if (typeof encoded !== 'string' || !encoded.length || encoded.length % 4 !== 0 || !/^[A-Za-z0-9+/]*={0,2}$/.test(encoded)) staticAtlasFailure(`${label} compressed payload is invalid`);
        if (typeof ReadableStream === 'undefined' || typeof DecompressionStream === 'undefined' || typeof atob === 'undefined' || typeof TextDecoder === 'undefined') staticAtlasFailure(`${label} gzip decoding support is unavailable`);
        const limit = staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.chunk_max_bytes, 'chunk byte budget');
        const hasExpectedByteCount = expectedByteCount !== null && expectedByteCount !== undefined;
        const expected = hasExpectedByteCount ? staticAtlasNonnegativeInteger(expectedByteCount, `${label} decoded byte count`) : null;
        if (expected !== null && (!expected || expected > limit)) staticAtlasFailure(`${label} decoded byte count exceeds its byte budget`);
        let compressed;
        try {
          const binary = atob(encoded);
          compressed = Uint8Array.from(binary, (character) => character.charCodeAt(0));
        } catch (error) {
          staticAtlasFailure(`${label} compressed payload is invalid`);
        }
        // Keep cached bytes in memory: offline Blob reads can fail before gzip decoding.
        const source = new ReadableStream({
          start(controller) {
            controller.enqueue(compressed);
            controller.close();
          },
        });
        const reader = source.pipeThrough(new DecompressionStream('gzip')).getReader();
        const cancelRead = () => { reader.cancel().catch(() => {}); };
        signal?.addEventListener('abort', cancelRead, { once: true });
        const chunks = [];
        let actual = 0;
        try {
          while (true) {
            signal?.throwIfAborted();
            const { done, value } = await reader.read();
            signal?.throwIfAborted();
            if (done) break;
            actual += value.byteLength;
            if (actual > limit) {
              await reader.cancel();
              staticAtlasFailure(`${label} decoded payload exceeds its byte budget`);
            }
            if (expected !== null && actual > expected) {
              await reader.cancel();
              staticAtlasFailure(`${label} decoded payload exceeds its declared byte count`);
            }
            chunks.push(value);
          }
        } catch (error) {
          signal?.throwIfAborted();
          if (error instanceof Error && error.message.startsWith('Static atlas data cannot be loaded:')) throw error;
          staticAtlasFailure(`${label} compressed payload is invalid`);
        } finally {
          signal?.removeEventListener('abort', cancelRead);
        }
        if (expected !== null && actual !== expected) staticAtlasFailure(`${label} decoded byte count mismatch`);
        const decoded = new Uint8Array(actual);
        let offset = 0;
        chunks.forEach((chunk) => {
          decoded.set(chunk, offset);
          offset += chunk.byteLength;
        });
        try {
          return new TextDecoder('utf-8', { fatal: true }).decode(decoded);
        } catch (error) {
          staticAtlasFailure(`${label} decoded payload is not valid UTF-8`);
        }
      }
      function indexTransportDescriptor() {
        const row = STATIC_ATLAS_BOOTSTRAP.runtime?.optional_controllers?.index_transport;
        if (!row || typeof row !== 'object' || Array.isArray(row)
          || Object.keys(row).sort().join('|') !== 'byte_count|integrity|path'
          || typeof row.path !== 'string' || typeof row.integrity !== 'string'
          || !/^[A-Za-z0-9][A-Za-z0-9._-]*[.]atlas-index-transport[.][a-f0-9]{16}[.]js$/.test(row.path)
          || !/^sha256-[A-Za-z0-9+/]{43}=$/.test(row.integrity)
          || !Number.isSafeInteger(row.byte_count) || row.byte_count <= 0 || row.byte_count > 524288) staticAtlasFailure('Index transport identity is unavailable');
        return row;
      }
      function loadIndexTransport() {
        if (staticAtlasIndexTransport) return Promise.resolve(staticAtlasIndexTransport);
        if (staticAtlasIndexTransportRequest) return staticAtlasIndexTransportRequest;
        staticAtlasIndexTransportRequest = Promise.resolve().then(() => {
          const row = indexTransportDescriptor();
          if (!['http:', 'https:', 'file:'].includes(window.location.protocol)) staticAtlasFailure('Index transport requires HTTP, HTTPS or a local file');
          return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = `./${row.path}`;
            if (['http:', 'https:'].includes(window.location.protocol)) {
              script.integrity = row.integrity;
              script.crossOrigin = 'anonymous';
            }
            script.addEventListener('load', () => {
              try {
                const factory = globalThis.BijuxPollenomicsIndexTransport;
                if (!factory || typeof factory.create !== 'function') staticAtlasFailure('Index transport did not register');
                const controller = factory.create({bootstrap: STATIC_ATLAS_BOOTSTRAP, failure: staticAtlasFailure,
                  temporalIdentity: staticAtlasTemporalIdentity, nonnegativeInteger: staticAtlasNonnegativeInteger,
                  nativeCalendarNumber: value => typeof nativeCalendarNumber === 'function' && nativeCalendarNumber(value),
                  boundedGunzip: staticAtlasBoundedGunzip, sha256: staticAtlasSha256,
                  searchGrams: text => atlasSearchGrams(text)});
                if (!controller || !['validatePayload', 'consume'].every(key => typeof controller[key] === 'function')) staticAtlasFailure('Index transport interface is incomplete');
                staticAtlasIndexTransport = controller;
                resolve(controller);
              } catch (error) { reject(error); }
            }, {once: true});
            script.addEventListener('error', () => reject(new Error('Index transport could not be loaded. Keep all atlas files together and reload.')), {once: true});
            document.head.appendChild(script);
          });
        });
        return staticAtlasIndexTransportRequest;
      }
      function staticAtlasIndexRows() {
        const rows = STATIC_ATLAS_BOOTSTRAP.assets.filter(row => row.domain === 'indexes');
        const declared = STATIC_ATLAS_BOOTSTRAP.compatibility || {};
        if (Object.hasOwn(declared, 'search_transport_counts')) staticAtlasFailure('search transport counts belong to the bundle header');
        if (Object.hasOwn(declared, 'search_transport_schema') && (declared.search_transport_schema !== 'atlas-search-documents.v1' || declared.search_index_abi !== 'atlas-substring-postings.v1' || !['atlas-static-indexes.v3','atlas-static-indexes.v4','atlas-static-indexes.v5'].includes(declared.index_schema))) staticAtlasFailure('search documents transport declaration is invalid');
        if (Object.hasOwn(declared, 'index_transport_schema')) {
          if (declared.index_transport_schema !== 'atlas-static-index-part.v1' || rows.length < 2 || !['atlas-static-indexes.v3','atlas-static-indexes.v4','atlas-static-indexes.v5'].includes(declared.index_schema)) staticAtlasFailure('index part transport declaration is invalid');
        } else if (rows.length > 1) staticAtlasFailure('singleton index transport is duplicated');
        return rows;
      }
      function staticAtlasIndexOverhead(rows) {
        return rows.length && !staticAtlasIndexTransport
          ? {request_count: 1, byte_count: indexTransportDescriptor().byte_count}
          : {request_count: 0, byte_count: 0};
      }
      function validateStaticAtlasEdgeAssets(payload) {
        if (payload.schema_version !== STATIC_ATLAS_BOOTSTRAP.compatibility?.edge_schema) staticAtlasFailure('edge compatibility schema mismatch');
        if (payload.schema_version === 'atlas-edges-chunk.v1') {
          if (Object.hasOwn(payload, 'endpoint_node_assets') || Object.hasOwn(payload, 'endpoint_node_geometry')) staticAtlasFailure('legacy edge endpoint assets are undeclared');
          return new Map();
        }
        const references = payload.endpoint_node_assets, geometry = payload.endpoint_node_geometry;
        if (!references || typeof references !== 'object' || Array.isArray(references) || !geometry || typeof geometry !== 'object' || Array.isArray(geometry)) staticAtlasFailure('edge endpoint assets or geometry are missing');
        const endpoints = new Set(payload.records.flatMap(edge => [edge.source_record_id, edge.target_record_id]));
        for (const rows of [references, geometry]) {
          if ([...endpoints].some(id => typeof id !== 'string' || !id) || Object.keys(rows).length !== endpoints.size || Object.keys(rows).some(id => !endpoints.has(id))) staticAtlasFailure('edge endpoint asset membership is incomplete');
        }
        const nodeRows = new Map();
        for (const row of STATIC_ATLAS_BOOTSTRAP.assets) {
          if (row.domain !== 'nodes' || row.layer_kind !== 'point') continue;
          if (nodeRows.has(row.asset_key)) staticAtlasFailure('edge endpoint asset is duplicated');
          nodeRows.set(row.asset_key, row);
        }
        for (const recordId of endpoints) {
          const keys = references[recordId], hints = geometry[recordId];
          if (!Array.isArray(keys) || !keys.length || keys.some((key, index) => typeof key !== 'string' || !nodeRows.has(key) || (index > 0 && keys[index - 1] >= key))) staticAtlasFailure('edge endpoint asset references are invalid or foreign');
          if (!Array.isArray(hints) || !hints.length) staticAtlasFailure('edge endpoint geometry is incomplete');
          const declared = new Set(keys), found = new Set();
          let previous = null;
          for (const hint of hints) {
            if (!hint || Object.keys(hint).sort().join('|') !== 'asset_key|feature_index|latitude|longitude' || !declared.has(hint.asset_key) || !Number.isSafeInteger(hint.feature_index) || hint.feature_index < 0 || (previous && (hint.asset_key < previous.asset_key || (hint.asset_key === previous.asset_key && hint.feature_index <= previous.feature_index)))) staticAtlasFailure('edge endpoint geometry reference is invalid');
            found.add(hint.asset_key);
            previous = hint;
          }
          if (found.size !== declared.size) staticAtlasFailure('edge endpoint geometry asset membership is incomplete');
        }
        return nodeRows;
      }
      function validateLoadedStaticAtlasEdgeAssets() {
        const edges = STATIC_ATLAS_CHUNKS.edges;
        if (!edges || edges.schema_version !== 'atlas-edges-chunk.v2') return;
        const loaded = new Map();
        for (const part of STATIC_ATLAS_CHUNKS.nodes) {
          const positions = new Map(part.feature_indexes.map((position, index) => [position, part.features[index]]));
          if (positions.size !== part.feature_indexes.length) staticAtlasFailure('edge endpoint node positions are duplicated');
          loaded.set(part.asset_key, positions);
        }
        for (const [recordId, hints] of Object.entries(edges.endpoint_node_geometry)) {
          for (const hint of hints) {
            if (!loaded.has(hint.asset_key)) continue;
            const feature = loaded.get(hint.asset_key).get(hint.feature_index);
            if (!feature || feature.record_id !== recordId || JSON.stringify(feature.latitude ?? null) !== JSON.stringify(hint.latitude) || JSON.stringify(feature.longitude ?? null) !== JSON.stringify(hint.longitude)) staticAtlasFailure('edge endpoint geometry differs from its node record');
          }
        }
      }
      function validateStaticAtlasPayload(row, payload) {
        if (!payload || typeof payload !== 'object') staticAtlasFailure(`${row.asset_key} payload is invalid`);
        staticAtlasTemporalIdentity(payload, STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3');
        if (payload.asset_key !== row.asset_key) staticAtlasFailure(`${row.asset_key} identity mismatch`);
        if (payload.build_id !== STATIC_ATLAS_BOOTSTRAP.build_id) staticAtlasFailure(`${row.asset_key} build mismatch`);
        if (payload.scope_slug !== STATIC_ATLAS_BOOTSTRAP.scope_slug) staticAtlasFailure(`${row.asset_key} scope mismatch`);
        if (payload.version !== STATIC_ATLAS_BOOTSTRAP.version) staticAtlasFailure(`${row.asset_key} version mismatch`);
        if (row.domain === 'indexes') {
          if (!staticAtlasIndexTransport) staticAtlasFailure('index transport was not admitted before payload validation');
          staticAtlasIndexTransport.validatePayload(row, payload);
        } else if (!STATIC_ATLAS_SCHEMAS[row.domain]?.includes(payload.schema_version)) staticAtlasFailure(`${row.asset_key} schema mismatch`);
        if (row.domain === 'nodes') {
          if (!Array.isArray(payload.features) || !Array.isArray(payload.feature_indexes) || payload.features.length !== payload.feature_indexes.length) staticAtlasFailure(`${row.asset_key} feature accounting is invalid`);
          if (payload.features.length !== row.record_count || payload.layer_key !== row.layer_key || payload.layer_index !== row.layer_index || payload.layer_kind !== row.layer_kind) staticAtlasFailure(`${row.asset_key} layer accounting mismatch`);
        }
        if ((row.domain === 'edges' || row.domain === 'sequences') && (!Array.isArray(payload.records) || payload.records.length !== row.record_count)) staticAtlasFailure(`${row.asset_key} record accounting mismatch`);
        if (row.domain === 'edges') validateStaticAtlasEdgeAssets(payload);
        if (row.domain === 'details' && (!Array.isArray(payload.records) || payload.records.length !== row.record_count || payload.records.some((record) => !record || typeof record.record_id !== 'string'))) staticAtlasFailure(`${row.asset_key} detail accounting mismatch`);
        if (row.domain === 'provenance' && (!Array.isArray(payload.layers) || !Array.isArray(payload.scientific_signals) || (payload.schema_version === 'atlas-provenance-chunk.v2' && !Array.isArray(payload.detail_records)))) staticAtlasFailure(`${row.asset_key} evidence accounting mismatch`);
        staticAtlasTemporalIdentity(payload, STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3');
        if (row.domain === 'indexes' && payload.search_index_abi !== STATIC_ATLAS_BOOTSTRAP.compatibility?.search_index_abi) staticAtlasFailure('search compatibility ABI mismatch');
      }
      async function consumeStaticAtlasAsset(row, signal = null, fetchedEnvelope = null) {
        signal?.throwIfAborted();
        if (staticAtlasLoadedAssets.has(row.asset_key)) return;
        const matches = fetchedEnvelope === null
          ? STATIC_ATLAS_RAW_CHUNKS.filter((candidate) => candidate.asset_key === row.asset_key)
          : [fetchedEnvelope];
        if (matches.length !== 1) staticAtlasFailure(`${row.asset_key} script did not register exactly once`);
        const envelope = matches[0];
        if (envelope.asset_key !== row.asset_key) staticAtlasFailure(`${row.asset_key} registered identity mismatch`);
        if (envelope.payload_sha256 !== row.payload_sha256) staticAtlasFailure(`${row.asset_key} declared payload digest mismatch`);
        const payloadEncoding = row.payload_encoding || 'json';
        if ((envelope.payload_encoding || 'json') !== payloadEncoding) staticAtlasFailure(`${row.asset_key} payload encoding mismatch`);
        let payloadJson;
        if (payloadEncoding === 'json') {
          if (typeof envelope.payload_json !== 'string') staticAtlasFailure(`${row.asset_key} JSON payload is missing`);
          payloadJson = envelope.payload_json;
        } else if (payloadEncoding === 'gzip_base64') {
          if (typeof envelope.payload_gzip_base64 !== 'string') staticAtlasFailure(`${row.asset_key} compressed payload is missing`);
          payloadJson = await staticAtlasBoundedGunzip(envelope.payload_gzip_base64, row.decoded_byte_count ?? null, row.asset_key, signal);
        } else {
          staticAtlasFailure(`${row.asset_key} payload encoding is unsupported`);
        }
        signal?.throwIfAborted();
        const decodedByteCount = new TextEncoder().encode(payloadJson).byteLength;
        if (decodedByteCount > Number(STATIC_ATLAS_BOOTSTRAP.budgets.chunk_max_bytes)) staticAtlasFailure(`${row.asset_key} decoded payload exceeds its byte budget`);
        if (row.decoded_byte_count !== undefined && decodedByteCount !== row.decoded_byte_count) staticAtlasFailure(`${row.asset_key} decoded byte count mismatch`);
        if (await staticAtlasSha256(payloadJson) !== row.payload_sha256) staticAtlasFailure(`${row.asset_key} payload integrity mismatch`);
        signal?.throwIfAborted();
        let payload;
        try {
          payload = JSON.parse(payloadJson);
        } catch (error) {
          staticAtlasFailure(`${row.asset_key} payload JSON is invalid`);
        }
        if (row.domain === 'indexes') await loadIndexTransport();
        validateStaticAtlasPayload(row, payload);
        const acceptedPayload = row.domain === 'indexes' ? await staticAtlasIndexTransport.consume(row, payload, staticAtlasIndexRows()) : payload;
        signal?.throwIfAborted();
        if (row.domain === 'nodes') STATIC_ATLAS_CHUNKS.nodes.push(payload);
        else if (row.domain === 'details') STATIC_ATLAS_CHUNKS.details.push(payload);
        else if (acceptedPayload !== null) STATIC_ATLAS_CHUNKS[row.domain] = acceptedPayload;
        staticAtlasLoadedAssets.add(row.asset_key);
      }
      function loadStaticAtlasAsset(row, selectionOwned = false) {
        if (staticAtlasLoadedAssets.has(row.asset_key)) return Promise.resolve();
        const existing = staticAtlasInFlightAssets.get(row.asset_key);
        if (existing) {
          if (!selectionOwned) existing.retained = true;
          return existing.promise;
        }
        const cancellable = selectionOwned && row.domain === 'nodes'
          && ['http:', 'https:'].includes(window.location.protocol);
        const operation = { controller: cancellable ? new AbortController() : null, retained: !selectionOwned, promise: null };
        const request = cancellable
          ? fetchStaticAtlasNodeAsset(row, operation.controller.signal)
          : new Promise((resolve, reject) => {
          const script = document.createElement('script');
          script.src = `./${row.path}`;
          if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
            script.integrity = row.integrity;
            script.crossOrigin = 'anonymous';
          }
          // file:// cannot reliably enforce transport SRI; the registered envelope is
          // still checked against its manifest payload digest before it is accepted.
          script.addEventListener('load', () => consumeStaticAtlasAsset(row).then(resolve, reject), { once: true });
          script.addEventListener('error', () => reject(new Error(`Static atlas data cannot be loaded: ${row.asset_key} request failed. Reload the page; if the problem persists, redeploy the HTML and hashed assets from the same build.`)), { once: true });
          document.head.appendChild(script);
        });
        operation.promise = request.finally(() => {
          if (staticAtlasInFlightAssets.get(row.asset_key) === operation) staticAtlasInFlightAssets.delete(row.asset_key);
        });
        staticAtlasInFlightAssets.set(row.asset_key, operation);
        return operation.promise;
      }
      // Selection waiters have separate lifetimes from reusable static cache requests.
let staticAtlasSelectionController = null;
function beginStaticAtlasSelection(required) {
  staticAtlasSelectionController?.abort();
  staticAtlasSelectionController = new AbortController();
  const needed = new Set(required.map((row) => row.asset_key));
  for (const [key, operation] of staticAtlasInFlightAssets) {
    if (operation.controller && !operation.retained && !needed.has(key)) {
      // Remove before abort completion so A → B → A can start a fresh A request.
      staticAtlasInFlightAssets.delete(key);
      operation.controller.abort();
    }
  }
  return staticAtlasSelectionController.signal;
}
function waitForStaticAtlasSelection(promise, signal) {
  return new Promise((resolve, reject) => {
    const cancelled = () => reject(signal.reason);
    signal.addEventListener('abort', cancelled, { once: true });
    if (signal.aborted) cancelled();
    promise.then((value) => {
      signal.removeEventListener('abort', cancelled);
      if (signal.aborted) reject(signal.reason);
      else resolve(value);
    }, (error) => {
      signal.removeEventListener('abort', cancelled);
      reject(signal.aborted ? signal.reason : error);
    });
  });
}
async function fetchStaticAtlasNodeAsset(row, signal) {
  const response = await fetch(`./${row.path}`, {
    signal, integrity: row.integrity, credentials: 'same-origin',
  });
  signal.throwIfAborted();
  if (!response.ok) staticAtlasFailure(`${row.asset_key} request failed`);
  const text = await response.text();
  signal.throwIfAborted();
  if (new TextEncoder().encode(text).byteLength !== row.byte_count) staticAtlasFailure(`${row.asset_key} script byte count mismatch`);
  if (await staticAtlasSha256(text) !== row.sha256) staticAtlasFailure(`${row.asset_key} script integrity mismatch`);
  signal.throwIfAborted();
  // This is the exact publisher's data envelope, never JavaScript evaluation.
  const prefix = 'globalThis.__BIJUX_ATLAS_RAW_CHUNKS__=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push(';
  if (!text.startsWith(prefix) || !text.endsWith(');\n')) staticAtlasFailure(`${row.asset_key} registration wrapper is invalid`);
  let envelope;
  try {
    envelope = JSON.parse(text.slice(prefix.length, -3));
  } catch (error) {
    staticAtlasFailure(`${row.asset_key} registration JSON is invalid`);
  }
  if (!envelope || typeof envelope !== 'object' || Array.isArray(envelope)) staticAtlasFailure(`${row.asset_key} registration envelope is invalid`);
  await consumeStaticAtlasAsset(row, signal, envelope);
}

      if (!STATIC_ATLAS_INLINE) {
        validateStaticAtlasBootstrap();
        for (const row of STATIC_ATLAS_BOOTSTRAP.assets.filter((candidate) => candidate.initial_load === true)) {
          await loadStaticAtlasAsset(row);
        }
        if (!STATIC_ATLAS_CHUNKS.provenance || !STATIC_ATLAS_CHUNKS.edges || !STATIC_ATLAS_CHUNKS.sequences) staticAtlasFailure('required startup metadata domains are incomplete');
        for (const domain of ['edges', 'sequences']) {
          const payload = STATIC_ATLAS_CHUNKS[domain];
          if (!['available', 'unavailable'].includes(payload.status) || !Array.isArray(payload.records)) staticAtlasFailure(`${domain} availability declaration is invalid`);
          if (payload.status === 'unavailable' && payload.records.length) staticAtlasFailure(`${domain} unavailable payload is not empty`);
          if (payload.status === 'available' && !payload.records.length) staticAtlasFailure(`${domain} available payload is empty`);
        }
        if (!Array.isArray(STATIC_ATLAS_CHUNKS.provenance.scientific_signals)) staticAtlasFailure('evidence metadata domains are incomplete');
        if (STATIC_ATLAS_CHUNKS.provenance.schema_version === 'atlas-provenance-chunk.v2' && !Array.isArray(STATIC_ATLAS_CHUNKS.provenance.detail_records)) staticAtlasFailure('legacy detail metadata is incomplete');
      }
      function hydrateStaticAtlasLayers(layerKind) {
        const partsByLayer = new Map();
        STATIC_ATLAS_CHUNKS.nodes
          .filter((part) => part.layer_kind === layerKind)
          .forEach((part) => {
            const current = partsByLayer.get(part.layer_index) || [];
            part.features.forEach((feature, index) => {
              if (part.layer_kind === 'point') staticAtlasSearchFeatureKeys.set(feature, `d:${part.layer_index}:${part.feature_indexes[index]}`);
              current.push([part.feature_indexes[index], feature]);
            });
            partsByLayer.set(part.layer_index, current);
          });
        return [...STATIC_ATLAS_CHUNKS.provenance.layers]
          .filter((entry) => entry.layer_kind === layerKind)
          .sort((left, right) => left.layer_index - right.layer_index)
          .map((entry) => {
            const indexedFeatures = partsByLayer.get(entry.layer_index) || [];
            indexedFeatures.sort((left, right) => left[0] - right[0]);
            const features = indexedFeatures.map((row) => row[1]);
            const layer = { ...entry.layer, static_loaded_feature_count: features.length, static_complete: features.length === entry.feature_count };
            if (layerKind === 'point') return { ...layer, features };
            return { ...layer, geojson: { ...(entry.layer.geojson || {}), features } };
          });
      }
      const SCOPE_KEY = "nordic";
      const COUNTRIES = ["Sweden","Norway","Finland","Denmark"];

      const NATIVE_LRA_BINDING = JSON.parse(document.getElementById('atlas-native-lra-binding').textContent);
function sourcePollenTableAvailable(table) {
  return Boolean(table && typeof table === 'object' && table.status !== 'unavailable'
    && Array.isArray(table.fields) && Array.isArray(table.records)
    && Number.isInteger(table.record_count) && table.record_count === table.records.length);
}

function sourcePollenExportAvailable(focus) {
  const tabs = focus?.detailTabs;
  return Boolean(focus?.kind === 'point' && focus.recordId
    && sourcePollenTableAvailable(tabs?.pollen_composition)
    && ['sample_id', 'source_value', 'source_unit'].every(field => tabs.pollen_composition.fields.includes(field))
    && sourcePollenTableAvailable(tabs?.chronology)
    && (tabs.chronology.fields.includes('comparability_status') || Object.prototype.hasOwnProperty.call(tabs.chronology.common_fields || {}, 'comparability_status'))
    && sourcePollenTableAvailable(tabs?.samples?.samples)
    && tabs.samples.samples.fields.includes('sample_id')
    && tabs?.provenance && tabs.provenance.status !== 'unavailable');
}

function sourcePollenDecodedTable(table, decodeRow) {
  if (!sourcePollenTableAvailable(table)) throw Error('source_pollen_table_unavailable');
  if (table.fields.some(field => typeof field !== 'string') || new Set(table.fields).size !== table.fields.length) throw Error('source_pollen_table_fields_invalid');
  return {
    record_count: table.record_count,
    records: table.records.map(row => decodeRow(table, row)),
  };
}

function buildSourcePollenRecordExport(focus, selection, decodeRow) {
  if (!sourcePollenExportAvailable(focus)) throw Error('source_pollen_record_export_unavailable');
  const tabs = focus.detailTabs;
  return {
    schema_version: 'source-pollen-record-export.v1',
    record_id: focus.recordId,
    feature_identity: { layer_key: focus.layerKey, feature_key: focus.featureKey },
    title: focus.title,
    selection,
    source_provenance: { ...tabs.provenance },
    record_scope: 'complete_source_record_not_filtered_to_map_time_window',
    temporal_support: {
      chronology_scope: 'all_source_claims_including_contextual_and_refused',
      interval_semantics: tabs.chronology.interval_semantics || null,
      interpolation_allowed: false,
      site_range_is_continuous_support: false,
    },
    source_semantics: {
      unit_policy: 'literal_source_unit_per_observation',
      denominator_policy: 'literal_source_denominator_and_status; null_remains_null',
      aggregation_policy: tabs.pollen_composition.aggregation_posture || 'source_observations_without_reaggregation',
      classification_status: tabs.pollen_composition.classification_status || 'not_asserted',
    },
    samples: sourcePollenDecodedTable(tabs.samples.samples, decodeRow),
    chronology_claims: sourcePollenDecodedTable(tabs.chronology, decodeRow),
    pollen_observations: sourcePollenDecodedTable(tabs.pollen_composition, decodeRow),
    source_variables: sourcePollenTableAvailable(tabs.pollen_composition.variables)
      ? sourcePollenDecodedTable(tabs.pollen_composition.variables, decodeRow) : null,
    collection_units: sourcePollenTableAvailable(tabs.samples.collection_units)
      ? sourcePollenDecodedTable(tabs.samples.collection_units, decodeRow) : null,
    datasets: sourcePollenTableAvailable(tabs.samples.datasets)
      ? sourcePollenDecodedTable(tabs.samples.datasets, decodeRow) : null,
  };
}

function sourcePollenRecordFilename(recordId) {
  return `${String(recordId).replace(/[^A-Za-z0-9._-]+/g, '-')}.pollen-series.json`;
}

function sourceRecordFocusFromHash(params, allowedTabs) {
  const layerKey = params.get('focus_layer');
  const featureKey = params.get('focus_feature');
  const recordId = params.get('focus_record');
  if (!layerKey || !featureKey || !recordId) return null;
  const tab = params.get('focus_tab');
  return { kind: 'point', layerKey, featureKey, recordId, tab: allowedTabs.includes(tab) ? tab : 'overview' };
}

function writeSourceRecordFocusHash(params, focus, tab) {
  if (focus?.kind !== 'point' || !focus.layerKey || !focus.featureKey || !focus.recordId) return;
  params.set('focus_layer', focus.layerKey);
  params.set('focus_feature', focus.featureKey);
  params.set('focus_record', focus.recordId);
  if (tab !== 'overview') params.set('focus_tab', tab);
}

// External URL navigation reuses the complete atlas initialization boundary.
function createAtlasURLStateController({ readURL, publishURL, replayURL }) {
  let appliedURL = readURL();
  let replayPending = false;
  function observe() {
    if (replayPending || readURL() === appliedURL) return false;
    replayPending = true;
    replayURL();
    return true;
  }
  function canPublish() {
    if (replayPending) return false;
    return !observe();
  }
  function publish(hash) {
    if (!canPublish()) return false;
    const next = new URL(appliedURL);
    next.hash = hash;
    if (next.href !== appliedURL) {
      publishURL(next.href);
      appliedURL = readURL();
    }
    return true;
  }
  return Object.freeze({ observe, canPublish, publish });
}

      let nativeLraController = null;
      let signedNativeTime = null;
      let signedNativeTimeControls = null;
      const POINT_LAYERS = hydrateStaticAtlasLayers('point');
      const POLYGON_LAYERS = hydrateStaticAtlasLayers('polygon');
      const MODELED_CONTEXT = JSON.parse(document.getElementById('atlas-modeled-context-binding').textContent);
      const INITIAL_BOUNDS = [[54.0,4.0],[72.0,35.0]];
      const ALL_LAYERS = [...POINT_LAYERS, ...POLYGON_LAYERS];
      const ATLAS_EVIDENCE = STATIC_ATLAS_INLINE
        ? { details_status: 'unavailable', details_reason_code: 'record_level_evidence_not_available', classifications_status: 'unavailable', classifications_reason_code: 'accepted_scientific_classifications_not_available', detail_records: [], scientific_signals: [] }
        : STATIC_ATLAS_CHUNKS.provenance;
      const SCIENTIFIC_SIGNALS = Object.freeze([...(ATLAS_EVIDENCE.scientific_signals || [])]);
      const SCIENTIFIC_SIGNAL_IDS = SCIENTIFIC_SIGNALS.map((signal) => signal.signal_id);
      const DEFAULT_SCIENTIFIC_SIGNAL_IDS = SCIENTIFIC_SIGNALS.filter((signal) => signal.resolution === 'whole').map((signal) => signal.signal_id);
      const SCIENTIFIC_RESOLUTION_ORDER = Object.freeze(['whole', 'group', 'subgroup', 'role', 'taxon']);
      const DETAIL_RECORDS = new Map((ATLAS_EVIDENCE.detail_records || []).map((record) => [record.record_id, record]));
      const GOVERNED_EDGE_RECORDS = Object.freeze(STATIC_ATLAS_INLINE ? [] : STATIC_ATLAS_CHUNKS.edges.records.map((edge) => Object.freeze({ ...edge })));
      const GOVERNED_SEQUENCE_RECORDS = Object.freeze(STATIC_ATLAS_INLINE ? [] : STATIC_ATLAS_CHUNKS.sequences.records.map((sequence) => Object.freeze({ ...sequence })));
      const GOVERNED_EDGE_ELIGIBILITY_COUNT = GOVERNED_EDGE_RECORDS.length;
      const DETAIL_TAB_DEFINITIONS = [
        ['overview', 'Overview'],
        ['samples', 'Samples'],
        ['chronology', 'Chronology'],
        ['pollen_composition', 'Pollen/composition'],
        ['relation', 'Relation'],
        ['classification', 'Classification'],
        ['provenance', 'Provenance'],
      ];
      const DEFAULT_COUNTRIES = [...COUNTRIES];
      const DEFAULT_LAYER_KEYS = ALL_LAYERS.filter((layer) => layer.default_enabled !== false).map((layer) => layer.key);
      const LAYER_GROUP_DEFINITIONS = [
        { key: 'primary-evidence', label: 'Human aDNA' },
        { key: 'animal-domesticated-evidence', label: 'Domesticated animal aDNA' },
        { key: 'animal-comparator-evidence', label: 'Comparator animal aDNA' },
        { key: 'animal-progenitor-evidence', label: 'Wild and progenitor animal aDNA' },
        { key: 'animal-chronology-context', label: 'Animal source chronology' },
        { key: 'candidate-ranking', label: 'Sweden lake ranking' },
        { key: 'environmental-context', label: 'Environmental context' },
        { key: 'archaeology-context', label: 'Archaeology context' },
        { key: 'orientation', label: 'Orientation layers' },
      ];
      const ANIMAL_EVIDENCE_LAYER_GROUPS = new Set(['animal-domesticated-evidence', 'animal-comparator-evidence', 'animal-progenitor-evidence']);
      const ANIMAL_CHRONOLOGY_LAYER_GROUP = 'animal-chronology-context';
      const ANIMAL_LAYER_GROUPS = new Set([...ANIMAL_EVIDENCE_LAYER_GROUPS, ANIMAL_CHRONOLOGY_LAYER_GROUP]);
      const ANIMAL_SPECIES = Array.from(
        new Map(
          POINT_LAYERS
            .filter((layer) => (
              ANIMAL_LAYER_GROUPS.has(layer.group)
              && (!isAnimalSourceChronologyLayer(layer) || animalSourceChronologyLayerIsValid(layer))
              && (layer.species_latin_name || layer.project_species_latin_name)
            ))
            .map((layer) => [
              layer.species_latin_name || layer.project_species_latin_name,
              {
                latinName: layer.species_latin_name || layer.project_species_latin_name,
                commonName: layer.species_common_name || layer.project_species_common_name || layer.label || layer.project_species_latin_name,
                fill: layer.style && layer.style.fill ? layer.style.fill : '#475569',
                stroke: layer.style && layer.style.stroke ? layer.style.stroke : '#1e293b',
                animalScope: layer.animal_scope || '',
              },
            ])
        ).values()
      );
      const ANIMAL_COORDINATE_CONFIDENCES = Array.from(
        new Set(
          POINT_LAYERS
            .filter((layer) => ANIMAL_LAYER_GROUPS.has(layer.group))
            .flatMap((layer) => layer.static_facets?.coordinate_confidences || [])
        )
      );
      const ANIMAL_TEMPORAL_WINDOWS = Array.from(
        new Set(
          POINT_LAYERS
            .filter((layer) => ANIMAL_LAYER_GROUPS.has(layer.group))
            .flatMap((layer) => layer.static_facets?.temporal_window_labels || [])
        )
      );
      const TIME_MIN_BP = 0;
      const TIME_MAX_BP = 2700000;
      const TIME_HAS_DATA = true;
      const DEFAULT_TIME_START_BP = 0;
      const DEFAULT_TIME_INTERVAL_YEARS = 2700000;
      const TIME_INTERVAL_MAX = 2700000;
      const map = L.map('map', { preferCanvas: true, zoomControl: false, maxZoom: 20 });
      let initialMapFitPending = false;
      let mapViewReady = false;
      map.whenReady(() => { mapViewReady = true; });
      // Attribution owns an intrinsic row, independent of responsive map overlays.
      document.getElementById('map-provider-credit').appendChild(map.attributionControl.getContainer());
      if (window.ResizeObserver) {
        let mapResizeFrame = null;
        const mapViewportResize = new ResizeObserver(() => {
          if (mapResizeFrame !== null) return;
          mapResizeFrame = requestAnimationFrame(() => {
            mapResizeFrame = null;
            map.invalidateSize({ animate: false, pan: false });
            if (initialMapFitPending) resetView();
          });
        });
        mapViewportResize.observe(document.querySelector('.map-viewport'));
      }
      const basemaps = {
        street: L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>', maxZoom: 19 }),
        terrain: L.tileLayer('https://tile.opentopomap.org/{z}/{x}/{y}.png', { attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> | DEM: SRTM, Sonny | Map style: &copy; <a href="https://opentopomap.org/">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>)', maxZoom: 17 })
      };
      const BASEMAP_NAMES = [...Object.keys(basemaps), 'none'];
      const BASEMAP_FALLBACK_ORDER = ['street', 'terrain', 'none'];
      const DEFAULT_BASEMAP = 'street';
      const MAX_PROVIDER_TILE_ERRORS = 3;
      const mapZoom = L.control.zoom({ position: 'bottomright' }).addTo(map);
      const mapScale = L.control.scale({ imperial: false }).addTo(map);
      document.getElementById('map-zoom-controls').appendChild(mapZoom.getContainer());
      document.getElementById('map-distance-scale').appendChild(mapScale.getContainer());
      map.createPane('pointPane').style.zIndex = 650;
      map.createPane('circlePane').style.zIndex = 500;
      map.createPane('edgePane').style.zIndex = 540;
      map.createPane('polygonPane').style.zIndex = 420;
      map.createPane('boundaryPane').style.zIndex = 430;
      const boundaryRenderer = L.svg({ pane: 'boundaryPane' });
      const circleLayerGroup = L.layerGroup().addTo(map);
      let renderedPointGroups = [];
      let renderedEdgeLayers = [];
      let renderedPolygonLayers = [];
      let renderedFittablePolygonLayers = [];
      let visiblePointEntries = [];
      let retainedNeighborRecordCountries = new Map();
      let visiblePolygonFeatureEntries = [];
      let highlightedPointEntry = null;
      const sidebar = document.getElementById('sidebar');
      const mobilePanelCloseButton = document.getElementById('mobile-panel-close');
      const mobileScrim = document.getElementById('mobile-scrim');
      let mobilePanelReturnFocus = null;
      const mobileLayoutQuery = window.matchMedia('(max-width: 900px)');
      const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      const panelToggleButton = document.getElementById('panel-toggle');
      const viewControls = document.getElementById('view-controls');
      const timeControls = document.getElementById('time-controls');
      const basemapSwitch = document.getElementById('basemap-switch');
      const appShell = document.querySelector('.app-shell');
      const helpToggleButton = document.getElementById('help-toggle');
      const helpDialog = document.getElementById('help-dialog');
      const helpCloseButton = document.getElementById('help-close');
      const helpReturnButton = document.getElementById('help-return');
      let helpDialogReturnFocus = null;
      const legendBody = document.getElementById('legend-body');
      const legendToggleButton = document.getElementById('legend-toggle');
      const countryFilters = document.getElementById('country-filters');
      const scientificFilters = document.getElementById('scientific-filters');
      const scientificActions = document.getElementById('scientific-actions');
      const scientificStatus = document.getElementById('scientific-status');
      const scientificSummary = document.getElementById('scientific-summary');
      const sourceChronologyShortcuts = document.getElementById('source-chronology-shortcuts');
      const countryPairFilter = document.getElementById('country-pair-filter');
      const crossBorderOnlyCheckbox = document.getElementById('cross-border-only');
      const relationSummary = document.getElementById('relation-summary');
      const relationFilterStatus = document.getElementById('relation-filter-status');
      const relationEventDefinitionControl = document.getElementById('relation-event-definition-filter');
      const relationEventDefinitionStatus = document.getElementById('relation-event-definition-status');
      const relationFilterControls = {
        scenario: document.getElementById('relation-scenario-filter'),
        status: document.getElementById('relation-status-filter'),
        sourceCountry: document.getElementById('relation-source-country-filter'),
        targetCountry: document.getElementById('relation-target-country-filter'),
      };
      const layerFilters = document.getElementById('dock-layer-filters');
      const animalFilterSummary = document.getElementById('animal-filter-summary');
      const animalScopeFilters = document.getElementById('animal-scope-filters');
      const animalSpeciesFilters = document.getElementById('animal-species-filters');
      const animalConfidenceFilters = document.getElementById('animal-confidence-filters');
      const animalTemporalWindowFilters = document.getElementById('animal-temporal-window-filters');
      const animalNordicOnlyCheckbox = document.getElementById('animal-nordic-only');
      const animalEvidenceMetrics = document.getElementById('animal-evidence-metrics');
      const animalEvidenceConfidence = document.getElementById('animal-evidence-confidence');
      const animalEvidenceState = document.getElementById('animal-evidence-state');
      const legendItems = document.getElementById('legend-items');
      const topbarSearch = document.getElementById('topbar-search');
      const searchToggleButton = document.getElementById('search-toggle');
      const searchInput = document.getElementById('search-input');
      const searchClearButton = document.getElementById('search-clear');
      const searchResults = document.getElementById('search-results');
      const searchCount = document.getElementById('search-count');
      const controlPanelSummary = document.getElementById('control-panel-summary');
      const dockLayerSummary = document.getElementById('dock-layer-summary');
      const dockTimeSummary = document.getElementById('dock-time-summary');
      const slider = document.getElementById('diameter-slider');
      const diameterValue = document.getElementById('diameter-value');
      const radiusValue = document.getElementById('radius-value');
      const timeStartSlider = document.getElementById('time-start-slider');
      const timeStartValue = document.getElementById('time-start-value');
      const timeIntervalSlider = document.getElementById('time-interval-slider');
      const timeIntervalValue = document.getElementById('time-interval-value');
      const timePlaybackToggle = document.getElementById('time-playback-toggle');
      const timeStepOlder = document.getElementById('time-step-older');
      const timeStepNewer = document.getElementById('time-step-newer');
      const timeStepperStatus = document.getElementById('time-stepper-status');
      const timeRecordCount = document.getElementById('time-record-count');
      const sourceChronologyControls = document.getElementById('source-chronology-controls');
      const sourceChronologySummary = document.getElementById('source-chronology-summary');
      const sourceChronologyLevel = document.getElementById('source-chronology-level');
      const sourceChronologyCodeFields = document.getElementById('source-chronology-code-fields');
      const sourceChronologyCode = document.getElementById('source-chronology-code');
      const sourceChronologyTaxonFields = document.getElementById('source-chronology-taxon-fields');
      const sourceLabelPresetControls = document.getElementById('source-label-preset-controls');
      const sourceLabelPresetState = document.getElementById('source-label-preset-state');
      const sourceChronologyTaxonQuery = document.getElementById('source-chronology-taxon-query');
      const sourceChronologyTaxon = document.getElementById('source-chronology-taxon');
      const sourceChronologyTaxonShortcuts = document.getElementById('source-chronology-taxon-shortcuts');
      const sourceRecordConcentrationToggle = document.getElementById('source-record-concentration-toggle');
      const sourceChronologyState = document.getElementById('source-chronology-state');
      const sourceChronologyGlobalDenominator = document.getElementById('source-chronology-global-denominator');
      const sourceTimeDensity = document.getElementById('source-time-density');
      const sourceTimeDensityCaption = document.getElementById('source-time-density-caption');
      const sourceTimeDensityBars = document.getElementById('source-time-density-bars');
      const modeledContextControls = document.getElementById('modeled-context-controls');
      const modeledContextSummary = document.getElementById('modeled-context-summary');
      const modeledContextFamily = document.getElementById('modeled-context-family');
      const modeledContextMetric = document.getElementById('modeled-context-metric');
      const modeledContextWindow = document.getElementById('modeled-context-window');
      const modeledContextToggle = document.getElementById('modeled-context-toggle');
      const modeledContextPlayback = document.getElementById('modeled-context-playback');
      const modeledContextDownload = document.getElementById('modeled-context-download');
      const modeledContextState = document.getElementById('modeled-context-state');
      const modeledContextLegend = document.getElementById('modeled-context-legend');
      const densityOpacitySlider = document.getElementById('density-opacity-slider');
      const densityOpacityValue = document.getElementById('density-opacity-value');
      const emptyState = document.getElementById('empty-state');
      const atlasCaptureRole = document.getElementById('atlas-capture-role');
      const atlasCaptureTime = document.getElementById('atlas-capture-time');
      const atlasCaptureTitle = document.getElementById('atlas-capture-title');
      const atlasCaptureCounts = document.getElementById('atlas-capture-counts');
      const atlasCaptureKey = document.getElementById('atlas-capture-key');
      const atlasCaptureCaveat = document.getElementById('atlas-capture-caveat');
      const densityRamp = document.getElementById('density-ramp');
      const countrySummary = document.getElementById('country-summary');
      const topbarStatePill = document.getElementById('topbar-state-pill');
      const focusCard = document.getElementById('focus-card');
      const focusTitle = document.getElementById('focus-title');
      const focusSubtitle = document.getElementById('focus-subtitle');
      const focusMeta = document.getElementById('focus-meta');
      const focusTabs = document.getElementById('focus-tabs');
      const focusDetail = document.getElementById('focus-detail');
      const focusPreviousButton = document.getElementById('focus-previous');
      const focusNextButton = document.getElementById('focus-next');
      const focusZoomButton = document.getElementById('focus-zoom');
      const focusSourceLink = document.getElementById('focus-source-link');
      const focusCloseButton = document.getElementById('focus-close');
      const focusExportButton = document.getElementById('focus-export');
      const focusCopyLinkButton = document.getElementById('focus-copy-link');
      const focusExportStatus = document.getElementById('focus-export-status');
      const selectionReadout = document.getElementById('selection-readout');
      const zoomReadout = document.getElementById('zoom-readout');
      const centerReadout = document.getElementById('center-readout');
      const cursorReadout = document.getElementById('cursor-readout');
      const basemapReadout = document.getElementById('basemap-readout');
      function parseHashState() {
        const raw = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : '';
        const params = new URLSearchParams(raw);
        return {
          focus: sourceRecordFocusFromHash(params, DETAIL_TAB_DEFINITIONS.map(([key]) => key)),
          edgeFocus: edgeFocusFromHash(params, DETAIL_TAB_DEFINITIONS.map(([key]) => key)),
          countries: params.get('countries'),
          layers: params.get('layers'),
          scientificSignals: params.get('scientific_signals'),
          scientificPins: params.getAll('scientific_pins'),
          countryPair: params.get('country_pair'),
          relationFilters: relationFiltersFromHash(params),
          relationEventDefinition: relationEventDefinitionFromHash(params),
          evidenceDisplay: evidenceDisplayFromHash(params),
          crossBorder: params.get('cross_border'),
          animalSpecies: params.get('animal_species'),
          animalScope: params.get('animal_scope'),
          animalConfidence: params.get('animal_confidence'),
          animalTemporalWindow: params.get('animal_time_window') || params.get('animal_chronology'),
          animalNordic: params.get('animal_nordic'),
          diameter: params.get('diameter'),
          timeStart: params.get('time_start'),
          timeInterval: params.get('time_interval'),
          modeledContext: params.get('modeled_context'),
          modeledFamily: params.get('modeled_family'),
          modeledMetric: params.get('modeled_metric'),
          sourceChronologyLevel: params.get('source_chronology_level'),
          sourceChronologyCode: params.get('source_ecological_code'),
          sourceChronologyTaxon: params.get('source_taxon'),
          sourceChronologyPreset: params.get('source_label_preset'),
          sourceRecordConcentration: params.get('source_record_concentration'),
          density: params.get('density'),
          basemap: params.get('basemap'),
          panel: params.get('panel'),
          legend: params.get('legend'),
        };
      }
      function normalizedSetFromList(raw, allowed, fallbackValues) {
        if (String(raw || '').trim() === 'none') return new Set();
        const allowedSet = new Set(allowed);
        const values = String(raw || '')
          .split(',')
          .map((value) => value.trim())
          .filter((value) => value && allowedSet.has(value));
        return new Set(values.length ? values : fallbackValues);
      }
      function normalizedSingleValue(raw, allowed, fallbackValue) {
        const value = String(raw || '').trim();
        return allowed.includes(value) ? value : fallbackValue;
      }
      function atlasCountryPairKey(leftCountry, rightCountry) {
        return [String(leftCountry || ''), String(rightCountry || '')].sort().join('|');
      }
      function atlasEdgeVisible(edge, countries, countryPair, crossBorder, signalIds) {
        if (!edge || (!countries.has(edge.source_country) && !countries.has(edge.target_country))) return false;
        if (countryPair !== 'all' && atlasCountryPairKey(edge.source_country, edge.target_country) !== countryPair) return false;
        if (crossBorder && (Object.prototype.hasOwnProperty.call(edge, 'candidate_status')
          ? edge.cross_border !== true : edge.source_country === edge.target_country)) return false;
        return signalIds.has(edge.signal_id);
      }
      function atlasRetainedNeighborRecordCountries(edges, countries) {
        const retained = new Map();
        edges.forEach((edge) => {
          if (Object.prototype.hasOwnProperty.call(edge, 'candidate_status')
            ? edge.cross_border !== true : edge.source_country === edge.target_country) return;
          if (countries.has(edge.source_country) && !countries.has(edge.target_country)) {
            retained.set(String(edge.target_record_id), edge.target_country);
          } else if (countries.has(edge.target_country) && !countries.has(edge.source_country)) {
            retained.set(String(edge.source_record_id), edge.source_country);
          }
        });
        return retained;
      }
      function atlasFilterStateSnapshot(countries, signalIds, countryPair, crossBorder) {
        return {
          countries: [...countries].sort(),
          scientific_signal_ids: [...signalIds].sort(),
          country_pair: countryPair,
          cross_border_only: Boolean(crossBorder),
        };
      }
      function atlasFilterStateEquals(left, right) {
        return JSON.stringify(left) === JSON.stringify(right);
      }
      function scientificCueGlyph(cue) {
        return { circle: '●', square: '■', triangle: '▲', diamond: '◆', cross: '✚', ring: '◎' }[cue] || '●';
      }
      function finiteControlNumber(value) {
        if (value === null || value === undefined || typeof value === 'boolean') return null;
        if (typeof value === 'string' && !value.trim()) return null;
        if (typeof value !== 'number' && typeof value !== 'string') return null;
        const numeric = Number(value);
        return Number.isFinite(numeric) ? numeric : null;
      }
      function clampDiameter(value) {
        const numeric = finiteControlNumber(value);
        const selected = numeric === null ? 20 : numeric;
        return Math.max(0, Math.min(100, Math.round(selected / 5) * 5));
      }
      function clampTimeInterval(value) {
        const numeric = finiteControlNumber(value);
        const selected = numeric === null ? DEFAULT_TIME_INTERVAL_YEARS : numeric;
        return Math.max(1, Math.min(TIME_INTERVAL_MAX, Math.round(selected)));
      }
      function defaultPanelCollapsed() {
        return true;
      }
      function panelPreferenceFromHash() {
        const raw = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : '';
        const panel = new URLSearchParams(raw).get('panel');
        if (panel === 'collapsed') return true;
        if (panel === 'open') return false;
        return null;
      }
      function clampTimeStart(value, intervalYears) {
        const maxStart = Math.max(TIME_MIN_BP, TIME_MAX_BP - intervalYears);
        const numeric = finiteControlNumber(value);
        const selected = numeric === null ? DEFAULT_TIME_START_BP : numeric;
        return Math.max(TIME_MIN_BP, Math.min(maxStart, Math.round(selected)));
      }
      function timeWindowEndBp() {
        if (typeof signedNativeTime !== 'undefined' && signedNativeTime !== null) return signedNativeTime.window()[1];
        return Math.min(TIME_MAX_BP, timeStartBp + timeIntervalYears);
      }
      function timeFilterUsesFullExtent() {
        return timeStartBp <= TIME_MIN_BP && timeWindowEndBp() >= TIME_MAX_BP;
      }
      function globalTimePlaybackExtent() {
        return { time_min_bp: TIME_MIN_BP, time_max_bp: TIME_MAX_BP, selection_key: 'global' };
      }
      function selectedTimePlaybackExtent() {
        const selection = sourceChronologyPlaybackSelection();
        return selection || globalTimePlaybackExtent();
      }
      function clampPlaybackTimeStart(value, intervalYears, extent = selectedTimePlaybackExtent()) {
        const interval = clampTimeInterval(intervalYears);
        const maximumStart = Math.max(extent.time_min_bp, extent.time_max_bp - interval);
        const numeric = finiteControlNumber(value);
        const selected = numeric === null ? maximumStart : numeric;
        return Math.max(extent.time_min_bp, Math.min(maximumStart, Math.round(selected)));
      }
      function oldestPlaybackStart(intervalYears, extent = selectedTimePlaybackExtent()) {
        return Math.max(extent.time_min_bp, extent.time_max_bp - clampTimeInterval(intervalYears));
      }
      function nextPlaybackTimeStart(currentStart, intervalYears, extent = selectedTimePlaybackExtent()) {
        const start = clampPlaybackTimeStart(currentStart, intervalYears, extent);
        return Math.max(extent.time_min_bp, start - clampTimeInterval(intervalYears));
      }
      function previousPlaybackTimeStart(currentStart, intervalYears, extent = selectedTimePlaybackExtent()) {
        const start = clampPlaybackTimeStart(currentStart, intervalYears, extent);
        return Math.min(oldestPlaybackStart(intervalYears, extent), start + clampTimeInterval(intervalYears));
      }
      const MAX_AUTOMATIC_PLAYBACK_FRAMES = 1000;
      function automaticPlaybackFrameCount(intervalYears, extent = selectedTimePlaybackExtent()) {
        if (!TIME_HAS_DATA) return 0;
        const interval = clampTimeInterval(intervalYears);
        const span = Math.max(0, extent.time_max_bp - extent.time_min_bp);
        if (interval >= span) return 1;
        return Math.ceil(span / interval);
      }
      function automaticTimePlaybackInterval() {
        if (
          typeof modeledContextActive !== 'undefined'
          && modeledContextActive
          && typeof modeledContextPreviousTime !== 'undefined'
          && modeledContextPreviousTime
        ) return modeledContextPreviousTime.timeIntervalYears;
        return timeIntervalYears;
      }
      function automaticTimePlaybackBlockReason() {
        if (reducedMotionQuery.matches) return 'Reduced motion is active; use the BP controls for manual navigation.';
        const frameCount = automaticPlaybackFrameCount(automaticTimePlaybackInterval());
        if (frameCount <= 1) return 'The selected chronology extent fits within one frame; use the BP controls for manual navigation.';
        if (frameCount > MAX_AUTOMATIC_PLAYBACK_FRAMES) {
          return `${frameCount} exact frames exceed the ${MAX_AUTOMATIC_PLAYBACK_FRAMES}-frame automatic limit; use manual BP navigation.`;
        }
        return '';
      }
      function refreshTimePlaybackControl() {
        const blockReason = automaticTimePlaybackBlockReason();
        const automaticAvailable = TIME_HAS_DATA && !blockReason;
        timePlaybackToggle.disabled = !automaticAvailable;
        timePlaybackToggle.title = blockReason;
        if (timePlaybackTimer === null) {
          timePlaybackToggle.setAttribute('aria-pressed', 'false');
          timePlaybackToggle.textContent = reducedMotionQuery.matches
            ? 'Reduced motion · manual only'
            : blockReason ? 'Manual BP navigation only' : 'Play oldest → present';
        }
      }
      let timePlaybackTimer = null;
      let timePlaybackExtent = null;
      function stopTimePlayback() {
        if (timePlaybackTimer !== null) window.clearTimeout(timePlaybackTimer);
        timePlaybackTimer = null;
        timePlaybackExtent = null;
        refreshTimePlaybackControl();
      }
      async function advanceTimePlayback() {
        if (timePlaybackTimer === null) return;
        const currentSelection = selectedTimePlaybackExtent();
        if (!timePlaybackExtent || currentSelection.selection_key !== timePlaybackExtent.selection_key) {
          stopTimePlayback();
          return;
        }
        const nextStart = nextPlaybackTimeStart(timeStartBp, timeIntervalYears, timePlaybackExtent);
        if (nextStart === timeStartBp) {
          stopTimePlayback();
          return;
        }
        timeStartBp = nextStart;
        await renderMapState();
        if (timePlaybackTimer !== null && timeStartBp <= timePlaybackExtent.time_min_bp) {
          stopTimePlayback();
        } else if (timePlaybackTimer !== null) {
          timePlaybackTimer = window.setTimeout(advanceTimePlayback, 900);
        }
      }
      async function startTimePlayback() {
        if (!TIME_HAS_DATA) {
          stopTimePlayback();
          return;
        }
        deactivateModeledContext();
        if (automaticTimePlaybackBlockReason()) {
          stopTimePlayback();
          return;
        }
        timePlaybackExtent = selectedTimePlaybackExtent();
        timeStartBp = oldestPlaybackStart(timeIntervalYears, timePlaybackExtent);
        timePlaybackToggle.setAttribute('aria-pressed', 'true');
        timePlaybackToggle.textContent = 'Pause playback';
        timePlaybackTimer = -1;
        await renderMapState();
        if (timePlaybackTimer !== null) {
          timePlaybackTimer = window.setTimeout(advanceTimePlayback, 900);
        }
      }
      function refreshTimeControls() {
        if (typeof signedNativeTime !== 'undefined' && signedNativeTime !== null) {
          [timeStartBp] = signedNativeTime.window();
          if (signedNativeTimeControls) signedNativeTimeControls.refresh();
          return;
        }
        if (!TIME_HAS_DATA) {
          timeStartSlider.disabled = true;
          timeIntervalSlider.disabled = true;
          timePlaybackToggle.disabled = true;
          dockTimeSummary.textContent = 'No BP dates available';
          timeStartValue.textContent = '--';
          timeIntervalValue.textContent = '--';
          return;
        }
        const navigationExtent = selectedTimePlaybackExtent();
        const navigationSpan = Math.max(1, navigationExtent.time_max_bp - navigationExtent.time_min_bp);
        const captureInterval = document.documentElement.classList.contains('atlas-capture-mode');
        if (captureInterval) {
          timeIntervalYears = Math.max(0, Math.min(Number(timeIntervalYears), navigationSpan));
          const maximumStart = Math.max(navigationExtent.time_min_bp, navigationExtent.time_max_bp - timeIntervalYears);
          timeStartBp = Math.max(navigationExtent.time_min_bp, Math.min(maximumStart, Number(timeStartBp)));
        } else {
          timeIntervalYears = Math.min(clampTimeInterval(timeIntervalYears), navigationSpan);
          timeStartBp = clampPlaybackTimeStart(timeStartBp, timeIntervalYears, navigationExtent);
        }
        timeStartSlider.min = String(navigationExtent.time_min_bp);
        timeStartSlider.max = String(Math.max(navigationExtent.time_min_bp, navigationExtent.time_max_bp - timeIntervalYears));
        timeStartSlider.step = captureInterval ? 'any' : '1';
        timeStartSlider.value = String(timeStartBp);
        timeIntervalSlider.min = captureInterval ? '0' : '1';
        timeIntervalSlider.max = String(navigationSpan);
        timeIntervalSlider.step = captureInterval ? 'any' : '1';
        timeIntervalSlider.value = String(timeIntervalYears);
        const endBp = timeWindowEndBp();
        dockTimeSummary.textContent = `[${timeStartBp}, ${endBp}] BP`;
        timeStartValue.textContent = `[${timeStartBp}, ${endBp}] BP`;
        timeIntervalValue.textContent = `${timeIntervalYears} years`;
        timeStepOlder.disabled = timeStartBp >= oldestPlaybackStart(timeIntervalYears, navigationExtent);
        timeStepNewer.disabled = timeStartBp <= navigationExtent.time_min_bp;
        refreshTimePlaybackControl();
      }
      const initialState = parseHashState();
      const atlasURLState = createAtlasURLStateController({
        readURL: () => window.location.href,
        publishURL: (href) => window.history.replaceState(null, '', href),
        replayURL: () => window.location.reload(),
      });
      window.addEventListener('hashchange', atlasURLState.observe);
      window.addEventListener('popstate', atlasURLState.observe);
      const MODELED_CONTEXT_WINDOWS = Object.freeze(Array.isArray(MODELED_CONTEXT.windows_oldest_to_present) ? [...MODELED_CONTEXT.windows_oldest_to_present] : []);
      const MODELED_CONTEXT_FAMILIES = Object.freeze(Array.isArray(MODELED_CONTEXT.metric_families) ? [...MODELED_CONTEXT.metric_families] : []);
      const MODELED_CONTEXT_PALETTE = Object.freeze(Array.isArray(MODELED_CONTEXT.palette) ? [...MODELED_CONTEXT.palette] : []);
      const MODELED_CONTEXT_COUNTRIES = Object.freeze(['Denmark', 'Finland', 'Norway', 'Sweden']);
      function modeledContextFamilyByKey(key) {
        return MODELED_CONTEXT_FAMILIES.find((family) => modeledContextRecord(family) && family.key === key) || null;
      }
      const defaultModeledContextFamily = modeledContextFamilyByKey(MODELED_CONTEXT.default_metric_family_key) || MODELED_CONTEXT_FAMILIES[0] || null;
      const initialModeledContextFamily = modeledContextFamilyByKey(initialState.modeledFamily) || defaultModeledContextFamily;
      const initialModeledContextMetrics = modeledContextRecord(initialModeledContextFamily) && Array.isArray(initialModeledContextFamily.metrics)
        ? initialModeledContextFamily.metrics
        : [];
      let modeledContextFamilyKey = modeledContextRecord(initialModeledContextFamily) ? String(initialModeledContextFamily.key || '') : '';
      let modeledContextMetricKey = initialModeledContextMetrics.some((metric) => modeledContextRecord(metric) && metric.key === initialState.modeledMetric)
        ? initialState.modeledMetric
        : (modeledContextRecord(initialModeledContextFamily) ? String(initialModeledContextFamily.default_metric_key || '') : '');
      let modeledContextActive = false;
      let modeledContextWindowIndex = 0;
      let modeledContextPlaybackTimer = null;
      let modeledContextPreviousTime = null;
      function modeledContextRecord(value) {
        return value !== null && typeof value === 'object' && !Array.isArray(value) ? value : null;
      }
      function modeledContextNonnegativeInteger(value) {
        return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 ? value : null;
      }
      function modeledContextCountMapIsValid(counts, keys, expectedTotal) {
        const record = modeledContextRecord(counts);
        if (!record || !Number.isSafeInteger(expectedTotal) || expectedTotal < 0) return false;
        const recordKeys = Object.keys(record);
        if (recordKeys.length !== keys.length || keys.some((key) => !Object.hasOwn(record, key))) return false;
        return keys.reduce((total, key) => {
          const count = modeledContextNonnegativeInteger(record[key]);
          return count === null ? Number.NaN : total + count;
        }, 0) === expectedTotal;
      }
      function modeledContextWindowSpan(sourceWindow) {
        const record = modeledContextRecord(sourceWindow);
        if (!record) return null;
        const start = modeledContextNonnegativeInteger(record.time_start_bp);
        const end = modeledContextNonnegativeInteger(record.time_end_bp);
        if (start === null || end === null || end <= start) return null;
        return { timeStartBp: start, timeIntervalYears: end - start };
      }
      function modeledContextQualityContractIsValid() {
        const classes = MODELED_CONTEXT.quality_classes;
        const counts = MODELED_CONTEXT.quality_class_counts;
        if (MODELED_CONTEXT.schema_version !== 'modeled-context-manifest.v3') return false;
        if (MODELED_CONTEXT.no_pollen_data_display_posture !== 'null_not_zero') return false;
        if (!Array.isArray(classes) || classes.join('|') !== 'high|low|no_pollen_data') return false;
        const featureCount = modeledContextNonnegativeInteger(MODELED_CONTEXT.feature_count);
        return featureCount !== null && modeledContextCountMapIsValid(counts, classes, featureCount);
      }
      function modeledContextCountryContractIsValid() {
        const cellCount = modeledContextNonnegativeInteger(MODELED_CONTEXT.cell_count);
        const featureCount = modeledContextNonnegativeInteger(MODELED_CONTEXT.feature_count);
        const countryCounts = modeledContextRecord(MODELED_CONTEXT.country_cell_counts);
        const countryQualityCounts = modeledContextRecord(MODELED_CONTEXT.country_quality_class_counts);
        if (cellCount !== 75 || featureCount !== cellCount * MODELED_CONTEXT_WINDOWS.length) return false;
        if (!modeledContextCountMapIsValid(countryCounts, MODELED_CONTEXT_COUNTRIES, cellCount)) return false;
        if (!countryQualityCounts || Object.keys(countryQualityCounts).length !== MODELED_CONTEXT_COUNTRIES.length) return false;
        const classes = MODELED_CONTEXT.quality_classes;
        if (!Array.isArray(classes)) return false;
        return MODELED_CONTEXT_COUNTRIES.every((country) => (
          Object.hasOwn(countryQualityCounts, country)
          && modeledContextCountMapIsValid(
            countryQualityCounts[country],
            classes,
            countryCounts[country] * MODELED_CONTEXT_WINDOWS.length
          )
        ));
      }
      function modeledContextWindowsContractIsValid() {
        if (MODELED_CONTEXT_WINDOWS.length !== 25 || !modeledContextQualityContractIsValid() || !modeledContextCountryContractIsValid()) return false;
        const labels = new Set();
        const classes = MODELED_CONTEXT.quality_classes;
        const countryCounts = MODELED_CONTEXT.country_cell_counts;
        const globalQualityTotals = Object.fromEntries(classes.map((qualityClass) => [qualityClass, 0]));
        const globalCountryQualityTotals = Object.fromEntries(MODELED_CONTEXT_COUNTRIES.map((country) => [country, Object.fromEntries(classes.map((qualityClass) => [qualityClass, 0]))]));
        let previousSpan = null;
        for (const sourceWindow of MODELED_CONTEXT_WINDOWS) {
          const record = modeledContextRecord(sourceWindow);
          const span = modeledContextWindowSpan(sourceWindow);
          if (!record || !span || typeof record.label !== 'string' || !record.label.trim() || record.label !== record.label.trim() || labels.has(record.label)) return false;
          if (previousSpan && span.timeStartBp + span.timeIntervalYears !== previousSpan.timeStartBp) return false;
          labels.add(record.label);
          previousSpan = span;
          const featureCount = modeledContextNonnegativeInteger(record.feature_count);
          const noPollenCount = modeledContextNonnegativeInteger(record.no_pollen_data_count);
          if (featureCount !== MODELED_CONTEXT.cell_count || noPollenCount === null) return false;
          if (!modeledContextCountMapIsValid(record.quality_class_counts, classes, featureCount)) return false;
          if (record.quality_class_counts.no_pollen_data !== noPollenCount) return false;
          if (!modeledContextCountMapIsValid(record.country_counts, MODELED_CONTEXT_COUNTRIES, featureCount)) return false;
          if (MODELED_CONTEXT_COUNTRIES.some((country) => record.country_counts[country] !== countryCounts[country])) return false;
          const countryQualityCounts = modeledContextRecord(record.country_quality_class_counts);
          if (!countryQualityCounts || Object.keys(countryQualityCounts).length !== MODELED_CONTEXT_COUNTRIES.length) return false;
          const windowQualityTotals = Object.fromEntries(classes.map((qualityClass) => [qualityClass, 0]));
          for (const country of MODELED_CONTEXT_COUNTRIES) {
            if (!Object.hasOwn(countryQualityCounts, country) || !modeledContextCountMapIsValid(countryQualityCounts[country], classes, countryCounts[country])) return false;
            for (const qualityClass of classes) {
              const count = countryQualityCounts[country][qualityClass];
              windowQualityTotals[qualityClass] += count;
              globalCountryQualityTotals[country][qualityClass] += count;
            }
          }
          for (const qualityClass of classes) {
            if (windowQualityTotals[qualityClass] !== record.quality_class_counts[qualityClass]) return false;
            globalQualityTotals[qualityClass] += record.quality_class_counts[qualityClass];
          }
        }
        return classes.every((qualityClass) => (
          globalQualityTotals[qualityClass] === MODELED_CONTEXT.quality_class_counts[qualityClass]
          && MODELED_CONTEXT_COUNTRIES.every((country) => (
            globalCountryQualityTotals[country][qualityClass] === MODELED_CONTEXT.country_quality_class_counts[country][qualityClass]
          ))
        ));
      }
      function modeledContextPaletteContractIsValid() {
        if (MODELED_CONTEXT_PALETTE.length === 0) return false;
        const labels = new Set();
        let previousMaximum = -1;
        for (const entry of MODELED_CONTEXT_PALETTE) {
          const record = modeledContextRecord(entry);
          if (!record || typeof record.maximum !== 'number' || !Number.isFinite(record.maximum)) return false;
          if (record.maximum < 0 || record.maximum <= previousMaximum || record.maximum > 100) return false;
          if (typeof record.label !== 'string' || !record.label.trim() || labels.has(record.label)) return false;
          if (typeof record.color !== 'string' || !/^#[0-9a-f]{6}$/i.test(record.color)) return false;
          labels.add(record.label);
          previousMaximum = record.maximum;
        }
        return previousMaximum === 100;
      }
      function modeledContextFamilyContractIsValid() {
        const familyCount = modeledContextNonnegativeInteger(MODELED_CONTEXT.metric_family_count);
        const metricCount = modeledContextNonnegativeInteger(MODELED_CONTEXT.metric_count);
        if (familyCount !== 3 || MODELED_CONTEXT_FAMILIES.length !== familyCount || metricCount === null) return false;
        const familyKeys = new Set();
        const metricKeys = new Set();
        let observedMetricCount = 0;
        for (const family of MODELED_CONTEXT_FAMILIES) {
          const record = modeledContextRecord(family);
          if (!record || typeof record.key !== 'string' || !record.key.trim() || record.key !== record.key.trim() || familyKeys.has(record.key)) return false;
          if (typeof record.label !== 'string' || !record.label.trim()) return false;
          if (!Array.isArray(record.metrics) || modeledContextNonnegativeInteger(record.metric_count) !== record.metrics.length || record.metrics.length === 0) return false;
          if (typeof record.default_metric_key !== 'string' || !record.default_metric_key.trim()) return false;
          const familyMetricKeys = new Set();
          for (const metric of record.metrics) {
            const metricRecord = modeledContextRecord(metric);
            if (!metricRecord || typeof metricRecord.key !== 'string' || !metricRecord.key.trim() || metricRecord.key !== metricRecord.key.trim() || familyMetricKeys.has(metricRecord.key) || metricKeys.has(metricRecord.key)) return false;
            if (typeof metricRecord.label !== 'string' || !metricRecord.label.trim()) return false;
            if (typeof metricRecord.source_label !== 'string' || !metricRecord.source_label.trim()) return false;
            familyMetricKeys.add(metricRecord.key);
            metricKeys.add(metricRecord.key);
          }
          if (!familyMetricKeys.has(record.default_metric_key)) return false;
          familyKeys.add(record.key);
          observedMetricCount += record.metrics.length;
        }
        return observedMetricCount === metricCount
          && familyKeys.has(MODELED_CONTEXT.default_metric_family_key)
          && currentModeledContextMetric() !== null;
      }
      function modeledContextAvailable() {
        return MODELED_CONTEXT.status === 'available'
          && modeledContextQualityContractIsValid()
          && modeledContextWindowsContractIsValid()
          && modeledContextPaletteContractIsValid()
          && modeledContextFamilyContractIsValid();
      }
      function currentModeledContextWindow() {
        return MODELED_CONTEXT_WINDOWS[modeledContextWindowIndex] || null;
      }
      function currentModeledContextFamily() {
        return modeledContextFamilyByKey(modeledContextFamilyKey);
      }
      function currentModeledContextMetric() {
        const family = currentModeledContextFamily();
        return modeledContextRecord(family) && Array.isArray(family.metrics)
          ? family.metrics.find((metric) => modeledContextRecord(metric) && metric.key === modeledContextMetricKey) || null
          : null;
      }
      function isModeledContextFeature(layer, properties) {
        return Boolean(
          layer.key === MODELED_CONTEXT.layer_key
          && String(properties.dataset_id || '') === String(MODELED_CONTEXT.dataset_id || '')
        );
      }
      function modeledContextFeatureVisible(layer, properties) {
        if (!modeledContextActive || layer.key !== MODELED_CONTEXT.layer_key) return true;
        const window = currentModeledContextWindow();
        return Boolean(window && isModeledContextFeature(layer, properties) && properties.time_label === window.label);
      }
      function modeledContextNumber(value) {
        return typeof value === 'number' && Number.isFinite(value) ? value : null;
      }
      function modeledContextEstimate(properties) {
        if (!properties || properties.quality_class === 'no_pollen_data') return null;
        const values = modeledContextRecord(properties.reconstruction_values);
        const value = values ? modeledContextNumber(values[modeledContextMetricKey]) : null;
        return value !== null && value >= 0 && value <= 100 ? value : null;
      }
      function modeledContextStandardError(properties) {
        if (!properties || properties.quality_class === 'no_pollen_data') return null;
        const values = modeledContextRecord(properties.standard_errors);
        const value = values ? modeledContextNumber(values[modeledContextMetricKey]) : null;
        return value !== null && value >= 0 ? value : null;
      }
      function modeledContextFillColor(value) {
        const numeric = modeledContextNumber(value);
        if (numeric === null || numeric < 0 || numeric > 100) return '#cbd5e1';
        if (!modeledContextPaletteContractIsValid()) return '#cbd5e1';
        const entry = MODELED_CONTEXT_PALETTE.find((candidate) => numeric <= candidate.maximum);
        return entry ? entry.color : '#d97706';
      }
      function stopModeledContextPlayback() {
        if (modeledContextPlaybackTimer !== null) window.clearTimeout(modeledContextPlaybackTimer);
        modeledContextPlaybackTimer = null;
        modeledContextPlayback.setAttribute('aria-pressed', 'false');
        modeledContextPlayback.textContent = 'Play 25 source windows';
      }
      function deactivateModeledContext({ restoreTime = true } = {}) {
        stopModeledContextPlayback();
        modeledContextActive = false;
        const previousTime = modeledContextPreviousTime;
        modeledContextPreviousTime = null;
        if (restoreTime && previousTime) {
          timeStartBp = previousTime.timeStartBp;
          timeIntervalYears = previousTime.timeIntervalYears;
        }
      }
      function admittedModeledContextWindowIndex(value) {
        return typeof value === 'number'
          && Number.isSafeInteger(value)
          && value >= 0
          && value < MODELED_CONTEXT_WINDOWS.length
          ? value
          : null;
      }
      async function selectModeledContextWindow(index) {
        if (!modeledContextAvailable()) return;
        const nextIndex = admittedModeledContextWindowIndex(index);
        if (nextIndex === null) return;
        if (!modeledContextActive) {
          modeledContextPreviousTime = { timeStartBp, timeIntervalYears };
        }
        modeledContextWindowIndex = nextIndex;
        const sourceWindow = currentModeledContextWindow();
        const sourceSpan = modeledContextWindowSpan(sourceWindow);
        if (!sourceSpan) return;
        modeledContextActive = true;
        timeStartBp = sourceSpan.timeStartBp;
        timeIntervalYears = sourceSpan.timeIntervalYears;
        activeLayerKeys.add(MODELED_CONTEXT.layer_key);
        await renderMapState();
      }
      async function advanceModeledContextPlayback() {
        if (modeledContextPlaybackTimer === null) return;
        if (modeledContextWindowIndex >= MODELED_CONTEXT_WINDOWS.length - 1) {
          stopModeledContextPlayback();
          return;
        }
        await selectModeledContextWindow(modeledContextWindowIndex + 1);
        if (modeledContextPlaybackTimer !== null) {
          modeledContextPlaybackTimer = window.setTimeout(advanceModeledContextPlayback, 900);
        }
      }
      async function startModeledContextPlayback() {
        if (!modeledContextAvailable() || reducedMotionQuery.matches) {
          stopModeledContextPlayback();
          return;
        }
        stopTimePlayback();
        modeledContextPlaybackTimer = -1;
        modeledContextPlayback.setAttribute('aria-pressed', 'true');
        modeledContextPlayback.textContent = 'Pause source-window playback';
        await selectModeledContextWindow(0);
        if (modeledContextPlaybackTimer !== null) {
          modeledContextPlaybackTimer = window.setTimeout(advanceModeledContextPlayback, 900);
        }
      }
      function modeledContextFrameFeatures() {
        const sourceWindow = currentModeledContextWindow();
        if (!modeledContextActive || !sourceWindow) return [];
        const layer = POLYGON_LAYERS.find((candidate) => candidate.key === MODELED_CONTEXT.layer_key);
        if (!layer || !layer.geojson || !Array.isArray(layer.geojson.features)) return [];
        return layer.geojson.features
          .filter((feature) => {
            const properties = feature && feature.properties ? feature.properties : {};
            return polygonGeometryIsAdmitted(feature)
              && isModeledContextFeature(layer, properties)
              && properties.time_label === sourceWindow.label
              && activeCountries.has(properties.country);
          })
          .sort((left, right) => String(left.properties.record_id || '').localeCompare(String(right.properties.record_id || '')));
      }
      function modeledContextFrameGeoJson() {
        const sourceWindow = currentModeledContextWindow();
        const metricFamily = currentModeledContextFamily();
        const metric = currentModeledContextMetric();
        const sourceFeatures = modeledContextFrameFeatures();
        const features = sourceFeatures.map((feature) => {
          if (!feature.properties || feature.properties.quality_class !== 'no_pollen_data') return feature;
          const properties = {
            ...feature.properties,
            reconstruction_values: Object.fromEntries(Object.keys(feature.properties.reconstruction_values || {}).map((key) => [key, null])),
            standard_errors: Object.fromEntries(Object.keys(feature.properties.standard_errors || {}).map((key) => [key, null])),
          };
          return { ...feature, properties };
        });
        const countryCounts = {};
        const qualityClassCounts = {};
        features.forEach((feature) => {
          const country = String(feature.properties.country || 'UNASSIGNED');
          countryCounts[country] = (countryCounts[country] || 0) + 1;
          const qualityClass = String(feature.properties.quality_class || 'UNAVAILABLE');
          qualityClassCounts[qualityClass] = (qualityClassCounts[qualityClass] || 0) + 1;
        });
        return {
          type: 'FeatureCollection',
          schema_version: MODELED_CONTEXT.download_schema_version,
          modeled_context: {
            dataset_id: MODELED_CONTEXT.dataset_id,
            dataset_doi: MODELED_CONTEXT.dataset_doi,
            method_citation: MODELED_CONTEXT.method_citation,
            method_doi: MODELED_CONTEXT.method_doi,
            metric_family_key: metricFamily.key,
            metric_family_label: metricFamily.label,
            metric_key: metric.key,
            metric_label: metric.label,
            metric_source_label: metric.source_label,
            metric_definition: metric.definition,
            value_unit: MODELED_CONTEXT.value_unit,
            metric_count_denominator: MODELED_CONTEXT.metric_count,
            estimate_standard_error_pair_count_denominator: MODELED_CONTEXT.estimate_standard_error_pair_count,
            land_cover_pft_reconciliation_count_denominator: MODELED_CONTEXT.land_cover_pft_reconciliation_count,
            source_window: sourceWindow,
            country_counts: Object.fromEntries(Object.entries(countryCounts).sort()),
            quality_class_counts: Object.fromEntries(Object.entries(qualityClassCounts).sort()),
            quality_class_count_denominator: features.length,
            evidence_role: 'context_only',
            propagation_use_allowed: false,
            interpolation_allowed: false,
            quality_classes: MODELED_CONTEXT.quality_classes,
            source_quality_class_counts: MODELED_CONTEXT.quality_class_counts,
            no_pollen_data_display_posture: 'null_not_zero',
          },
          features,
        };
      }
      function modeledContextFrameQualitySummary() {
        const counts = { high: 0, low: 0, no_pollen_data: 0 };
        modeledContextFrameFeatures().forEach((feature) => {
          const qualityClass = String(feature.properties?.quality_class || '');
          if (Object.hasOwn(counts, qualityClass)) counts[qualityClass] += 1;
        });
        return counts;
      }
      function downloadModeledContextFrame() {
        if (!modeledContextActive) return;
        const payload = modeledContextFrameGeoJson();
        const sourceWindow = currentModeledContextWindow();
        const windowSlug = String(sourceWindow.label).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        const metricSlug = String(modeledContextMetricKey).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: 'application/geo+json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `pangaea-937075-${metricSlug}-${windowSlug}.geojson`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
      }
      function renderModeledContextControls() {
        const available = modeledContextAvailable();
        modeledContextControls.hidden = !available;
        if (!available) return;
        const metricFamily = currentModeledContextFamily();
        const metric = currentModeledContextMetric();
        modeledContextFamily.innerHTML = MODELED_CONTEXT_FAMILIES.map((family) => `<option value="${escapeHtml(family.key)}" ${family.key === modeledContextFamilyKey ? 'selected' : ''}>${escapeHtml(family.label)} · ${family.metric_count} metrics</option>`).join('');
        modeledContextMetric.innerHTML = metricFamily.metrics.map((candidate) => `<option value="${escapeHtml(candidate.key)}" ${candidate.key === modeledContextMetricKey ? 'selected' : ''}>${escapeHtml(candidate.source_label)} · ${escapeHtml(candidate.key)}</option>`).join('');
        modeledContextWindow.innerHTML = MODELED_CONTEXT_WINDOWS.map((sourceWindow, index) => `<option value="${index}" ${index === modeledContextWindowIndex ? 'selected' : ''}>${escapeHtml(sourceWindow.label)} · ${sourceWindow.feature_count} cells</option>`).join('');
        modeledContextToggle.setAttribute('aria-pressed', String(modeledContextActive));
        modeledContextToggle.textContent = modeledContextActive ? 'Hide modeled metric' : 'Show modeled metric';
        modeledContextPlayback.disabled = !modeledContextActive || reducedMotionQuery.matches;
        modeledContextPlayback.title = reducedMotionQuery.matches
          ? 'Reduced motion is active; select published source windows manually.'
          : '';
        modeledContextDownload.disabled = !modeledContextActive || modeledContextFrameFeatures().length === 0;
        const sourceWindow = currentModeledContextWindow();
        const frameQuality = modeledContextFrameQualitySummary();
        const visibleCellCount = modeledContextFrameFeatures().length;
        modeledContextSummary.textContent = modeledContextActive && sourceWindow ? `${metric.key} · ${sourceWindow.label}` : `PANGAEA 937075 · ${metric.key}`;
        const modeledContextStateText = modeledContextActive && sourceWindow
          ? `${visibleCellCount} visible cells · ${frameQuality.no_pollen_data}/${visibleCellCount} explicitly have no pollen data and render as unavailable, never zero · ${metric.source_label} (${metric.key}) percentage cover with source standard error · ${MODELED_CONTEXT.metric_count} source metrics reconciled · context only · no interpolation or propagation`
          : 'Context mode is off. Select Show modeled metric to inspect exact published windows.';
        modeledContextState.textContent = reducedMotionQuery.matches
          ? `${modeledContextStateText} Automatic source-window playback is disabled by the reduced-motion preference; manual window selection and frame download remain available.`
          : modeledContextStateText;
        modeledContextLegend.hidden = !modeledContextActive;
        modeledContextLegend.innerHTML = modeledContextActive && sourceWindow
          ? `<div class="legend-group-label">${escapeHtml(sourceWindow.label)} · ${escapeHtml(metric.source_label)} (${escapeHtml(metric.key)}) · ${escapeHtml(MODELED_CONTEXT.value_unit)}</div>${MODELED_CONTEXT_PALETTE.map((entry) => `<div class="legend-item legend-item--compact"><span class="legend-swatch" style="background:${escapeHtml(entry.color)};border-color:#334155;"></span><span>${escapeHtml(entry.label)}</span></div>`).join('')}<div class="legend-item legend-item--compact"><span class="legend-swatch" style="background:#cbd5e1;border-color:#334155;"></span><span>No pollen data · N/A, not 0</span></div>`
          : '';
      }
      const SOURCE_CHRONOLOGY_LEVEL_ORDER = Object.freeze([
        'source_sample_presence',
        'source_ecological_code',
        'source_taxon',
      ]);
      const SOURCE_CHRONOLOGY_LEVEL_LABELS = Object.freeze({
        source_sample_presence: 'Source sample pollen presence',
        source_ecological_code: 'Literal source ecological code',
        source_taxon: 'Source-reported taxon or pollen type',
      });
      function sourceChronologyCount(value) {
        return Number.isSafeInteger(value) && value >= 0 ? value : null;
      }
      function sourceChronologyTimeValue(value) {
        return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
      }
      function sourceChronologyExtentIsValid(row) {
        const nodeCount = sourceChronologyCount(row?.node_count);
        if (nodeCount === null) return false;
        const minimum = sourceChronologyTimeValue(row.time_min_bp);
        const maximum = sourceChronologyTimeValue(row.time_max_bp);
        if (nodeCount === 0) return row.time_min_bp === null && row.time_max_bp === null;
        return minimum !== null && maximum !== null && minimum <= maximum;
      }
      function sourceChronologyAggregateIsValid(row, { density = true } = {}) {
        if (!row || typeof row !== 'object' || Array.isArray(row)) return false;
        const siteCount = sourceChronologyCount(row.site_count);
        const nodeCount = sourceChronologyCount(row.node_count);
        const observationCount = sourceChronologyCount(row.observation_denominator);
        if (siteCount === null || nodeCount === null || observationCount === null) return false;
        if (row.site_count_semantics !== 'unique_site_union' || !sourceChronologyExtentIsValid(row)) return false;
        if (nodeCount === 0) {
          if (siteCount !== 0 || observationCount !== 0) return false;
        } else if (siteCount === 0 || siteCount > nodeCount || observationCount === 0) return false;
        return !density || sourceChronologyTimeDensityIsValid(row.time_density, row);
      }
      const SOURCE_CHRONOLOGY_COUNTRIES = Object.freeze([
        Object.freeze(['SE', 'Sweden']),
        Object.freeze(['DK', 'Denmark']),
        Object.freeze(['NO', 'Norway']),
        Object.freeze(['FI', 'Finland']),
      ]);
      function sourceChronologyCountryRowsAreValid(rows, aggregate) {
        if (!Array.isArray(rows) || rows.length !== SOURCE_CHRONOLOGY_COUNTRIES.length) return false;
        if (!rows.every((row, index) => (
          row?.country_code === SOURCE_CHRONOLOGY_COUNTRIES[index][0]
          && row.value === SOURCE_CHRONOLOGY_COUNTRIES[index][1]
          && sourceChronologyAggregateIsValid(row, { density: false })
        ))) return false;
        for (const field of ['site_count', 'node_count', 'observation_denominator']) {
          if (rows.reduce((total, row) => total + row[field], 0) !== aggregate[field]) return false;
        }
        const populated = rows.filter((row) => row.node_count > 0);
        if (aggregate.node_count === 0) return populated.length === 0;
        return Math.min(...populated.map((row) => row.time_min_bp)) === aggregate.time_min_bp
          && Math.max(...populated.map((row) => row.time_max_bp)) === aggregate.time_max_bp;
      }
      function sourceChronologyAccountabilityIsValid(row, { density = true } = {}) {
        return sourceChronologyAggregateIsValid(row, { density })
          && sourceChronologyCountryRowsAreValid(row.country_counts, row);
      }
      function sourceChronologyTimeDensityIsValid(density, facet) {
        if (!density || density.schema_version !== 'source-chronology-time-density.v1') return false;
        if (density.temporal_direction !== 'oldest_to_present' || density.interval_semantics !== '[younger_bp, older_bp]') return false;
        if (density.bin_admission !== 'closed_interval_overlap' || density.bins_are_additive !== false) return false;
        if (density.node_count !== facet.node_count || density.observation_denominator !== facet.observation_denominator) return false;
        if (density.time_min_bp !== facet.time_min_bp || density.time_max_bp !== facet.time_max_bp) return false;
        if (!Array.isArray(density.bins)) return false;
        const expectedBinCount = facet.node_count === 0 ? 0 : (facet.time_min_bp === facet.time_max_bp ? 1 : 12);
        if (density.bins.length !== expectedBinCount) return false;
        return density.bins.every((row, index) => {
          if (!row || row.ordinal !== index) return false;
          const younger = sourceChronologyTimeValue(row.younger_bp);
          const older = sourceChronologyTimeValue(row.older_bp);
          if (younger === null || older === null || younger > older) return false;
          if (sourceChronologyCount(row.node_count) === null || sourceChronologyCount(row.observation_denominator) === null) return false;
          if (index === 0 && older !== facet.time_max_bp) return false;
          if (index === density.bins.length - 1 && younger !== facet.time_min_bp) return false;
          if (index > 0 && density.bins[index - 1].younger_bp !== older) return false;
          return true;
        });
      }
      function sourceChronologyFacetRowsAreValid(rows, { featureKey = false, taxon = false } = {}) {
        if (!Array.isArray(rows)) return false;
        const values = new Set();
        return rows.every((row) => {
          if (!row || typeof row !== 'object' || typeof row.value !== 'string' || !row.value.trim() || values.has(row.value)) return false;
          values.add(row.value);
          if (!sourceChronologyAccountabilityIsValid(row)) return false;
          if (featureKey && (typeof row.feature_key !== 'string' || !row.feature_key.trim())) return false;
          if (taxon && (typeof row.source_taxon_id !== 'string' || !/^\d+$/.test(row.source_taxon_id) || typeof row.label !== 'string' || !row.label.trim())) return false;
          return true;
        });
      }
      function sourceChronologyUnitRowsAreValid(rows, aggregate) {
        if (!Array.isArray(rows)) return false;
        const values = new Set();
        if (!rows.every((row) => {
          if (!row || typeof row.value !== 'string' || !row.value.trim() || values.has(row.value)) return false;
          values.add(row.value);
          return sourceChronologyCount(row.node_count) !== null
            && sourceChronologyCount(row.observation_denominator) !== null;
        })) return false;
        return rows.reduce((total, row) => total + row.node_count, 0) === aggregate.node_count
          && rows.reduce((total, row) => total + row.observation_denominator, 0) === aggregate.observation_denominator;
      }
      function sourceChronologySha256IdentityIsValid(value) {
        return typeof value === 'string' && /^sha256:[0-9a-f]{64}$/.test(value);
      }
      function sourceChronologyLiteralPostureIsValid(row) {
        return row?.membership_semantics === 'literal_source_label_membership'
          && row.accepted_classification === false
          && row.aggregation_is_abundance === false
          && row.propagation_allowed === false;
      }
      function sourceChronologyIntegerIdsAreValid(values) {
        return Array.isArray(values)
          && values.every((value) => Number.isSafeInteger(value) && value >= 0)
          && new Set(values).size === values.length;
      }
      function sourceChronologyDerivedFacet(rows) {
        const populated = rows.filter((row) => row.node_count > 0);
        return {
          node_count: rows.reduce((total, row) => total + row.node_count, 0),
          observation_denominator: rows.reduce((total, row) => total + row.observation_denominator, 0),
          time_min_bp: populated.length ? Math.min(...populated.map((row) => row.time_min_bp)) : null,
          time_max_bp: populated.length ? Math.max(...populated.map((row) => row.time_max_bp)) : null,
        };
      }
      function sourceChronologyDerivedCountsMatch(actual, rows) {
        const expected = sourceChronologyDerivedFacet(rows);
        return ['node_count', 'observation_denominator', 'time_min_bp', 'time_max_bp']
          .every((field) => actual[field] === expected[field]);
      }
      function sourceChronologyDerivedSiteBoundsMatch(actual, rows) {
        const lowerBound = rows.length ? Math.max(...rows.map((row) => row.site_count)) : 0;
        const upperBound = rows.reduce((total, row) => total + row.site_count, 0);
        return actual.site_count >= lowerBound && actual.site_count <= upperBound;
      }
      function sourceChronologyPresetContractIsValid(layer) {
        const facets = layer.facet_metadata;
        const catalog = facets.source_label_preset_catalog;
        const accountability = facets.source_label_preset_accountability;
        const expectedPresetKeys = ['avena', 'hordeum', 'triticum', 'secale', 'cerealia'];
        if (!catalog || !accountability) return false;
        if (catalog.schema_version !== 'neotoma-source-label-presets.v1' || catalog.source !== 'neotoma') return false;
        if (!sourceChronologyLiteralPostureIsValid(catalog) || !sourceChronologyLiteralPostureIsValid(accountability)) return false;
        if (catalog.source_snapshot_id !== layer.source_snapshot_id || catalog.build_id !== layer.build_id) return false;
        if (![catalog.definition_sha256, catalog.content_sha256].every(sourceChronologySha256IdentityIsValid)) return false;
        if (accountability.schema_version !== 'neotoma-source-label-preset-accountability.v1' || accountability.catalog_content_sha256 !== catalog.content_sha256) return false;
        if (catalog.source_taxon_count !== 21 || catalog.preset_count !== 5 || catalog.membership_count !== 24) return false;
        if (accountability.source_taxon_count !== catalog.source_taxon_count || accountability.preset_count !== catalog.preset_count || accountability.membership_count !== catalog.membership_count) return false;
        if (!Array.isArray(catalog.source_taxa) || catalog.source_taxa.length !== catalog.source_taxon_count) return false;
        if (!Array.isArray(catalog.presets) || !Array.isArray(accountability.presets) || catalog.presets.length !== 5 || accountability.presets.length !== 5) return false;
        const presetKeys = catalog.presets.map((row) => row?.key);
        if (presetKeys.join('|') !== expectedPresetKeys.join('|') || accountability.presets.map((row) => row?.key).join('|') !== presetKeys.join('|')) return false;
        const taxaById = new Map();
        for (const taxon of catalog.source_taxa) {
          if (!taxon || !Number.isSafeInteger(taxon.source_taxon_id) || taxon.source_taxon_id < 0 || taxaById.has(taxon.source_taxon_id)) return false;
          if (typeof taxon.source_reported_name !== 'string' || !taxon.source_reported_name.trim()) return false;
          if (!Array.isArray(taxon.preset_keys) || new Set(taxon.preset_keys).size !== taxon.preset_keys.length || taxon.preset_keys.some((key) => !expectedPresetKeys.includes(key))) return false;
          taxaById.set(taxon.source_taxon_id, taxon);
        }
        if (taxaById.size !== catalog.source_taxon_count) return false;
        const exactFacetsById = new Map(facets.source_taxa.map((row) => [Number(row.source_taxon_id), row]));
        if (exactFacetsById.size !== facets.source_taxa.length) return false;
        for (const [taxonId, taxon] of taxaById) {
          const exactFacet = exactFacetsById.get(taxonId);
          if (exactFacet && exactFacet.label !== taxon.source_reported_name) return false;
        }
        for (let index = 0; index < catalog.presets.length; index += 1) {
          const definition = catalog.presets[index];
          const account = accountability.presets[index];
          if (!sourceChronologyLiteralPostureIsValid(definition) || !sourceChronologyLiteralPostureIsValid(account)) return false;
          if (typeof definition.label !== 'string' || !definition.label.trim() || account.label !== definition.label || account.key !== definition.key) return false;
          if (!sourceChronologyIntegerIdsAreValid(definition.member_taxon_ids) || definition.member_taxon_count !== definition.member_taxon_ids.length) return false;
          if (account.member_taxon_count !== definition.member_taxon_count || JSON.stringify(account.member_taxon_ids) !== JSON.stringify(definition.member_taxon_ids)) return false;
          if (!sourceChronologyAccountabilityIsValid(account)) return false;
          if (definition.member_taxon_ids.some((taxonId) => !taxaById.has(taxonId) || !taxaById.get(taxonId).preset_keys.includes(definition.key))) return false;
          if ([...taxaById.values()].some((taxon) => taxon.preset_keys.includes(definition.key) !== definition.member_taxon_ids.includes(taxon.source_taxon_id))) return false;
          const memberFacets = definition.member_taxon_ids.map((taxonId) => exactFacetsById.get(taxonId)).filter(Boolean);
          if (!sourceChronologyDerivedCountsMatch(account, memberFacets) || !sourceChronologyDerivedSiteBoundsMatch(account, memberFacets)) return false;
          for (let countryIndex = 0; countryIndex < SOURCE_CHRONOLOGY_COUNTRIES.length; countryIndex += 1) {
            const countryFacets = memberFacets.map((row) => row.country_counts[countryIndex]);
            if (!sourceChronologyDerivedCountsMatch(account.country_counts[countryIndex], countryFacets) || !sourceChronologyDerivedSiteBoundsMatch(account.country_counts[countryIndex], countryFacets)) return false;
          }
        }
        const union = accountability.union;
        const allTaxonIds = [...taxaById.keys()];
        if (!sourceChronologyLiteralPostureIsValid(union) || union?.key !== 'all-governed-source-labels' || typeof union.label !== 'string' || !union.label.trim()) return false;
        if (!sourceChronologyIntegerIdsAreValid(union.member_taxon_ids) || union.member_taxon_count !== catalog.source_taxon_count || JSON.stringify(union.member_taxon_ids) !== JSON.stringify(allTaxonIds)) return false;
        if (!sourceChronologyAccountabilityIsValid(union)) return false;
        const unionFacets = allTaxonIds.map((taxonId) => exactFacetsById.get(taxonId)).filter(Boolean);
        if (!sourceChronologyDerivedCountsMatch(union, unionFacets) || !sourceChronologyDerivedSiteBoundsMatch(union, unionFacets)) return false;
        for (let countryIndex = 0; countryIndex < SOURCE_CHRONOLOGY_COUNTRIES.length; countryIndex += 1) {
          const countryFacets = unionFacets.map((row) => row.country_counts[countryIndex]);
          if (!sourceChronologyDerivedCountsMatch(union.country_counts[countryIndex], countryFacets) || !sourceChronologyDerivedSiteBoundsMatch(union.country_counts[countryIndex], countryFacets)) return false;
        }
        return true;
      }
      function sourceChronologyLayerContractIsValid(layer) {
        if (!layer || layer.semantic_role !== 'source_chronology_context') return false;
        if (!SOURCE_CHRONOLOGY_LEVEL_ORDER.includes(layer.node_level)) return false;
        if (layer.propagation_status !== 'refused' || layer.edge_count !== 0) return false;
        if (layer.temporal_direction !== 'oldest_to_present' || layer.interval_semantics !== '[younger_bp, older_bp]') return false;
        const facets = layer.facet_metadata;
        if (!facets || facets.schema_version !== 'neotoma-source-chronology-facets.v4' || facets.node_level !== layer.node_level) return false;
        if (!sourceChronologyAccountabilityIsValid(facets)) return false;
        if (sourceChronologyCount(layer.count) !== facets.node_count) return false;
        if (!sourceChronologyUnitRowsAreValid(facets.source_unit_counts, facets)) return false;
        if (layer.node_level === 'source_sample_presence' && layer.default_enabled !== true) return false;
        if (layer.node_level === 'source_ecological_code') {
          if (layer.default_enabled !== false || !sourceChronologyFacetRowsAreValid(facets.source_ecological_codes, { featureKey: true })) return false;
        } else if (!Array.isArray(facets.source_ecological_codes) || facets.source_ecological_codes.length !== 0) return false;
        if (layer.node_level === 'source_taxon') {
          if (layer.default_enabled !== false || !sourceChronologyFacetRowsAreValid(facets.source_taxa, { taxon: true }) || !sourceChronologyPresetContractIsValid(layer)) return false;
        } else if (!Array.isArray(facets.source_taxa) || facets.source_taxa.length !== 0) return false;
        return true;
      }
      const SOURCE_CHRONOLOGY_LAYER_VALIDATION_CACHE = new WeakMap();
      function freezeSourceChronologyMetadata(value, seen = new WeakSet()) {
        if (!value || typeof value !== 'object' || seen.has(value)) return value;
        seen.add(value);
        Object.values(value).forEach((child) => freezeSourceChronologyMetadata(child, seen));
        return Object.freeze(value);
      }
      function sourceChronologyLayerIsValid(layer) {
        if (!layer || typeof layer !== 'object') return false;
        const fingerprint = [
          layer.semantic_role,
          layer.node_level,
          layer.default_enabled,
          layer.propagation_status,
          layer.edge_count,
          layer.temporal_direction,
          layer.interval_semantics,
          layer.count,
          layer.source_snapshot_id,
          layer.build_id,
        ].join('|');
        const cached = SOURCE_CHRONOLOGY_LAYER_VALIDATION_CACHE.get(layer);
        if (cached && cached.facet_metadata === layer.facet_metadata && cached.fingerprint === fingerprint) return cached.valid;
        const valid = sourceChronologyLayerContractIsValid(layer);
        if (valid) freezeSourceChronologyMetadata(layer.facet_metadata);
        SOURCE_CHRONOLOGY_LAYER_VALIDATION_CACHE.set(layer, { facet_metadata: layer.facet_metadata, fingerprint, valid });
        return valid;
      }
      function sourceChronologyLayers() {
        return POINT_LAYERS
          .filter(sourceChronologyLayerIsValid)
          .sort((left, right) => SOURCE_CHRONOLOGY_LEVEL_ORDER.indexOf(left.node_level) - SOURCE_CHRONOLOGY_LEVEL_ORDER.indexOf(right.node_level));
      }
      function sourceChronologyLayerForLevel(level) {
        return sourceChronologyLayers().find((layer) => layer.node_level === level) || null;
      }
      function sourceChronologyTaxonIdentifierIsValid(value) {
        return (typeof value === 'string' && /^\d+$/.test(value)) || (Number.isSafeInteger(value) && value >= 0);
      }
      function sourceChronologyTaxonIdentifier(value) {
        return sourceChronologyTaxonIdentifierIsValid(value) ? Number(value) : null;
      }
      function sourceChronologyPresetForSelection(layer, presetKey) {
        if (!layer || layer.node_level !== 'source_taxon' || presetKey === 'none') return null;
        return layer.facet_metadata.source_label_preset_accountability.presets.find((row) => row.key === presetKey) || null;
      }
      function sourceChronologyCapturePresetAuthority(layer, presetKey) {
        if (presetKey === 'none') return null;
        if (!sourceChronologyLayerIsValid(layer) || layer.node_level !== 'source_taxon') throw new Error('capture source preset authority is unavailable');
        const catalog = layer.facet_metadata.source_label_preset_catalog;
        const account = sourceChronologyPresetForSelection(layer, presetKey);
        const definition = catalog.presets.find((row) => row.key === presetKey) || null;
        if (!account || !definition) throw new Error('capture source preset authority is unavailable');
        if (!sourceChronologyIntegerIdsAreValid(account.member_taxon_ids)
          || JSON.stringify(account.member_taxon_ids) !== JSON.stringify(definition.member_taxon_ids)) {
          throw new Error('capture source preset member IDs differ from the governed catalog');
        }
        if (!sourceChronologySha256IdentityIsValid(catalog.content_sha256)
          || layer.facet_metadata.source_label_preset_accountability.catalog_content_sha256 !== catalog.content_sha256) {
          throw new Error('capture source preset catalog digest differs from governed accountability');
        }
        return Object.freeze({
          memberTaxonIds: Object.freeze([...account.member_taxon_ids]),
          catalogSha256: catalog.content_sha256.slice('sha256:'.length),
        });
      }
      function sourceChronologyFacetForSelection(layer, code, taxon, presetKey = typeof activeSourceChronologyPreset === 'undefined' ? 'none' : activeSourceChronologyPreset) {
        if (!layer) return null;
        const facets = layer.facet_metadata;
        if (layer.node_level === 'source_ecological_code' && code !== 'all') {
          return facets.source_ecological_codes.find((row) => row.value === code) || null;
        }
        if (layer.node_level === 'source_taxon' && taxon !== 'all') {
          return facets.source_taxa.find((row) => row.value === taxon) || null;
        }
        if (layer.node_level === 'source_taxon' && presetKey !== 'none') {
          return sourceChronologyPresetForSelection(layer, presetKey);
        }
        return {
          site_count_semantics: facets.site_count_semantics,
          site_count: facets.site_count,
          node_count: facets.node_count,
          observation_denominator: facets.observation_denominator,
          time_min_bp: facets.time_min_bp,
          time_max_bp: facets.time_max_bp,
          time_density: facets.time_density,
          country_counts: facets.country_counts,
        };
      }
      function sourceChronologyPlaybackSelection() {
        if (typeof activeLayerKeys === 'undefined' || typeof activeSourceChronologyLevel === 'undefined') return null;
        const layer = sourceChronologyLayerForLevel(activeSourceChronologyLevel);
        if (!layer || !activeLayerKeys.has(layer.key)) return null;
        const facet = sourceChronologyFacetForSelection(layer, activeSourceChronologyCode, activeSourceChronologyTaxon);
        if (!facet || !sourceChronologyExtentIsValid(facet) || facet.node_count === 0) return null;
        const minimum = Math.floor(sourceChronologyTimeValue(facet.time_min_bp));
        const maximum = Math.ceil(sourceChronologyTimeValue(facet.time_max_bp));
        return {
          time_min_bp: minimum,
          time_max_bp: maximum,
          selection_key: [layer.key, activeSourceChronologyCode, activeSourceChronologyTaxon, activeSourceChronologyPreset, minimum, maximum].join('|'),
        };
      }
      function genericUntimedExclusion() {
        const layers = ALL_LAYERS.filter((layer) => (
          activeLayerKeys.has(layer.key)
          && layer.applies_time_filter
          && layer.semantic_role !== 'source_chronology_context'
        ));
        if (STATIC_ATLAS_INLINE) {
          const classified = { absent: 0, refused: 0, contextual: 0 };
          layers.forEach((layer) => {
            const pointFeatures = Array.isArray(layer.features) ? layer.features : [];
            const polygonFeatures = Array.isArray(layer.geojson?.features)
              ? layer.geojson.features.map((feature) => feature?.properties || {})
              : [];
            pointFeatures.concat(polygonFeatures).filter((feature) => (
              (!layer.applies_country_filter || activeCountries.has(feature.country))
            )).forEach((feature) => {
              const status = featureTimeAdmission(feature).status;
              if (Object.prototype.hasOwnProperty.call(classified, status)) classified[status] += 1;
            });
          });
          return { status: 'available', count: classified.absent + classified.refused + classified.contextual, split_status: 'available', absent_count: classified.absent, refused_count: classified.refused, contextual_count: classified.contextual };
        }
        let count = 0;
        let ambiguous = false;
        let splitUnavailable = false;
        const classified = { absent: 0, refused: 0, contextual: 0 };
        const layersByKey = new Map(layers.map((layer) => [layer.key, layer]));
        STATIC_ATLAS_BOOTSTRAP.assets
          .filter((row) => row.domain === 'nodes' && layersByKey.has(row.layer_key))
          .forEach((row) => {
            const layer = layersByKey.get(row.layer_key);
            const untimed = staticAtlasNonnegativeInteger(row.untimed_record_count, `${row.asset_key} untimed record count`);
            const split = [row.chronology_absent_record_count, row.refused_chronology_record_count, row.contextual_chronology_record_count];
            const hasSplit = split.every((value) => value !== null && value !== undefined);
            if (!layer.applies_country_filter) {
              count += untimed;
              if (hasSplit) {
                classified.absent += staticAtlasNonnegativeInteger(split[0], `${row.asset_key} absent chronology count`);
                classified.refused += staticAtlasNonnegativeInteger(split[1], `${row.asset_key} refused chronology count`);
                classified.contextual += staticAtlasNonnegativeInteger(split[2], `${row.asset_key} contextual chronology count`);
              } else splitUnavailable = true;
              return;
            }
            const countries = Array.isArray(row.country_keys)
              ? row.country_keys.filter((country) => COUNTRIES.includes(country))
              : [];
            if (countries.length && countries.every((country) => activeCountries.has(country))) {
              count += untimed;
              if (hasSplit) {
                classified.absent += staticAtlasNonnegativeInteger(split[0], `${row.asset_key} absent chronology count`);
                classified.refused += staticAtlasNonnegativeInteger(split[1], `${row.asset_key} refused chronology count`);
                classified.contextual += staticAtlasNonnegativeInteger(split[2], `${row.asset_key} contextual chronology count`);
              } else splitUnavailable = true;
              return;
            }
            if (countries.some((country) => activeCountries.has(country)) && untimed > 0) ambiguous = true;
          });
        if (ambiguous) return { status: 'unavailable', count: null, split_status: 'unavailable', absent_count: null, refused_count: null, contextual_count: null };
        return { status: 'available', count, split_status: splitUnavailable ? 'unavailable' : 'available', absent_count: splitUnavailable ? null : classified.absent, refused_count: splitUnavailable ? null : classified.refused, contextual_count: splitUnavailable ? null : classified.contextual };
      }
      function sourceChronologyUntimedExclusion(layer) {
        if (!layer || !sourceChronologyLayerIsValid(layer)) return { status: 'unavailable', count: null, split_status: 'unavailable' };
        if (STATIC_ATLAS_INLINE) {
          const candidates = (layer.features || []).filter((feature) => (
            sourceChronologyFeatureMatches(layer, feature)
            && (!layer.applies_country_filter || activeCountries.has(feature.country))
          ));
          const classified = { absent: 0, refused: 0, contextual: 0 };
          candidates.forEach((feature) => {
            const status = featureTimeAdmission(feature).status;
            if (Object.prototype.hasOwnProperty.call(classified, status)) classified[status] += 1;
          });
          return {
            status: 'available',
            count: classified.absent + classified.refused + classified.contextual,
            split_status: 'available',
            absent_count: classified.absent,
            refused_count: classified.refused,
            contextual_count: classified.contextual,
          };
        }
        const rows = STATIC_ATLAS_BOOTSTRAP.assets.filter((row) => row.domain === 'nodes' && row.layer_key === layer.key);
        let count = 0;
        let ambiguous = false;
        let splitUnavailable = false;
        const classified = { absent: 0, refused: 0, contextual: 0 };
        rows.forEach((row) => {
          const untimed = staticAtlasNonnegativeInteger(row.untimed_record_count, `${row.asset_key} untimed record count`);
          const split = [row.chronology_absent_record_count, row.refused_chronology_record_count, row.contextual_chronology_record_count];
          const hasSplit = split.every((value) => value !== null && value !== undefined);
          const countries = Array.isArray(row.country_keys) ? row.country_keys.filter((country) => country !== 'UNASSIGNED') : [];
          if (!layer.applies_country_filter || (countries.length && countries.every((country) => activeCountries.has(country)))) {
            count += untimed;
            if (hasSplit) {
              classified.absent += staticAtlasNonnegativeInteger(split[0], `${row.asset_key} absent chronology count`);
              classified.refused += staticAtlasNonnegativeInteger(split[1], `${row.asset_key} refused chronology count`);
              classified.contextual += staticAtlasNonnegativeInteger(split[2], `${row.asset_key} contextual chronology count`);
            } else splitUnavailable = true;
            return;
          }
          if (countries.some((country) => activeCountries.has(country)) && untimed > 0) ambiguous = true;
        });
        const exactFacetSelected = (
          (layer.node_level === 'source_ecological_code' && activeSourceChronologyCode !== 'all')
          || (layer.node_level === 'source_taxon' && (activeSourceChronologyTaxon !== 'all' || activeSourceChronologyPreset !== 'none'))
        );
        if (ambiguous || (exactFacetSelected && count > 0)) return { status: 'unavailable', count: null, split_status: 'unavailable' };
        return { status: 'available', count, split_status: splitUnavailable ? 'unavailable' : 'available', absent_count: splitUnavailable ? null : classified.absent, refused_count: splitUnavailable ? null : classified.refused, contextual_count: splitUnavailable ? null : classified.contextual };
      }
      function sourceChronologyFeatureMatches(layer, feature, code = activeSourceChronologyCode, taxon = activeSourceChronologyTaxon, presetKey = typeof activeSourceChronologyPreset === 'undefined' ? 'none' : activeSourceChronologyPreset) {
        if (layer.semantic_role !== 'source_chronology_context') return true;
        if (!sourceChronologyLayerIsValid(layer) || !feature || feature.semantic_role !== 'source_chronology_context') return false;
        if (feature.node_level !== layer.node_level || feature.propagation_eligible !== false || feature.candidate_generation_status !== 'refused') return false;
        if (typeof feature.candidate_refusal_reason !== 'string' || !feature.candidate_refusal_reason.trim()) return false;
        if (feature.source_snapshot_id !== layer.source_snapshot_id || feature.build_id !== layer.build_id) return false;
        if (typeof feature.node_id !== 'string' || !feature.node_id.trim() || typeof feature.record_id !== 'string' || !feature.record_id.trim()) return false;
        if (typeof feature.feature_key !== 'string' || !feature.feature_key.trim() || typeof feature.source_unit !== 'string' || !feature.source_unit.trim()) return false;
        if (layer.node_level === 'source_ecological_code') {
          if (typeof feature.source_ecological_code !== 'string' || !feature.source_ecological_code.trim()) return false;
          if (feature.source_taxon_id !== null || feature.source_reported_name !== null) return false;
          return code === 'all' || feature.source_ecological_code === code;
        }
        if (layer.node_level === 'source_taxon') {
          if (typeof feature.source_reported_name !== 'string' || !feature.source_reported_name.trim()) return false;
          if (!sourceChronologyTaxonIdentifierIsValid(feature.source_taxon_id)) return false;
          if (feature.source_ecological_code !== null) return false;
          if (taxon !== 'all') return feature.feature_key === taxon;
          const preset = sourceChronologyPresetForSelection(layer, presetKey);
          return !preset || preset.member_taxon_ids.includes(sourceChronologyTaxonIdentifier(feature.source_taxon_id));
        }
        return feature.source_ecological_code === null && feature.source_taxon_id === null && feature.source_reported_name === null;
      }
      function sourceRecordConcentrationFailure(message) {
        throw new Error(`Captured source-record concentration unavailable: ${message}`);
      }
      function sourceRecordConcentrationCompareText(left, right) {
        const leftText = String(left);
        const rightText = String(right);
        if (leftText === rightText) return 0;
        return leftText < rightText ? -1 : 1;
      }
      function sourceRecordConcentrationSelection(layer) {
        if (!layer || !sourceChronologyLayerIsValid(layer)) return null;
        const activeSourceLayers = sourceChronologyLayers().filter((candidate) => activeLayerKeys.has(candidate.key));
        if (activeSourceLayers.length !== 1 || activeSourceLayers[0].key !== layer.key) return null;
        if (layer.node_level === 'source_ecological_code' && activeSourceChronologyCode === 'all') return null;
        if (layer.node_level === 'source_taxon' && activeSourceChronologyTaxon === 'all' && activeSourceChronologyPreset === 'none') return null;
        const facet = sourceChronologyFacetForSelection(layer, activeSourceChronologyCode, activeSourceChronologyTaxon);
        if (!facet || sourceChronologyCount(facet.node_count) === null || sourceChronologyCount(facet.observation_denominator) === null) return null;
        return facet;
      }
      function sourceRecordConcentrationFacetLabel(layer) {
        if (!layer) return 'unavailable facet';
        if (layer.node_level === 'source_ecological_code') return `literal source code ${activeSourceChronologyCode}`;
        if (layer.node_level === 'source_taxon') {
          const preset = sourceChronologyPresetForSelection(layer, activeSourceChronologyPreset);
          if (preset) return `${preset.label} exact-ID union`;
          const row = layer.facet_metadata.source_taxa.find((candidate) => candidate.value === activeSourceChronologyTaxon);
          return row ? `exact source label ${row.label} (${row.source_taxon_id})` : 'unavailable exact source label';
        }
        return 'source sample pollen presence';
      }
      function sourceRecordConcentrationRadius(nodeCount) {
        const count = sourceChronologyCount(nodeCount);
        if (count === null || count < 1) sourceRecordConcentrationFailure('site node count is invalid');
        if (count === 1) return 7;
        if (count <= 4) return 10;
        if (count <= 9) return 13;
        if (count <= 24) return 16;
        return 19;
      }
      function buildSourceRecordConcentration(layer, features, viewportBounds) {
        const globalFacet = sourceRecordConcentrationSelection(layer);
        if (!globalFacet) sourceRecordConcentrationFailure('select exactly one active source level and one exact facet');
        if (!Array.isArray(features)) sourceRecordConcentrationFailure('admitted feature collection is invalid');
        const seenNodeIds = new Set();
        const siteCoordinates = new Map();
        const selectedFeatures = [];
        [...features]
          .sort((left, right) => sourceRecordConcentrationCompareText(left?.node_id || '', right?.node_id || ''))
          .forEach((feature) => {
            if (!sourceChronologyFeatureMatches(layer, feature, 'all', 'all', 'none')) sourceRecordConcentrationFailure('a loaded source node violates the active-level contract');
            const nodeId = typeof feature.node_id === 'string' ? feature.node_id.trim() : '';
            const siteId = typeof feature.record_id === 'string' ? feature.record_id.trim() : '';
            const observationCount = sourceChronologyCount(feature.observation_denominator);
            const coordinates = featureCoordinatePair(feature);
            if (!nodeId || !siteId) sourceRecordConcentrationFailure('node or site identity is missing');
            if (seenNodeIds.has(nodeId)) sourceRecordConcentrationFailure(`duplicate node identity ${nodeId}`);
            if (observationCount === null || observationCount < 1) sourceRecordConcentrationFailure(`node ${nodeId} has an invalid contributing-observation count`);
            if (!coordinates || !featureTimeWindow(feature)) sourceRecordConcentrationFailure(`node ${nodeId} has invalid spatial or BP admission`);
            seenNodeIds.add(nodeId);
            const existingCoordinates = siteCoordinates.get(siteId);
            if (existingCoordinates && (existingCoordinates.latitude !== coordinates.latitude || existingCoordinates.longitude !== coordinates.longitude)) {
              sourceRecordConcentrationFailure(`site ${siteId} has conflicting coordinates`);
            }
            siteCoordinates.set(siteId, coordinates);
            if (sourceChronologyFeatureMatches(layer, feature)) selectedFeatures.push(feature);
          });
        const sites = new Map();
        selectedFeatures.forEach((feature) => {
          if (!pointFeatureVisible(layer, feature)) return;
          const coordinates = featureCoordinatePair(feature);
          if (!coordinates) sourceRecordConcentrationFailure(`node ${feature.node_id} lost admitted coordinates`);
          if (viewportBounds && !viewportBounds.contains([coordinates.latitude, coordinates.longitude])) return;
          const siteId = feature.record_id;
          const existing = sites.get(siteId) || {
            site_id: siteId,
            latitude: coordinates.latitude,
            longitude: coordinates.longitude,
            country: feature.country || '',
            node_count: 0,
            observation_denominator: 0,
            node_ids: [],
            feature,
          };
          if (existing.country !== (feature.country || '')) sourceRecordConcentrationFailure(`site ${siteId} has conflicting country identity`);
          existing.node_count += 1;
          existing.observation_denominator += feature.observation_denominator;
          existing.node_ids.push(feature.node_id);
          sites.set(siteId, existing);
        });
        const entries = [...sites.values()]
          .map((entry) => ({ ...entry, node_ids: [...entry.node_ids].sort(sourceRecordConcentrationCompareText) }))
          .sort((left, right) => sourceRecordConcentrationCompareText(left.site_id, right.site_id));
        const visibleNodeCount = entries.reduce((total, entry) => total + entry.node_count, 0);
        const visibleObservationDenominator = entries.reduce((total, entry) => total + entry.observation_denominator, 0);
        if (visibleNodeCount > globalFacet.node_count || visibleObservationDenominator > globalFacet.observation_denominator) {
          sourceRecordConcentrationFailure('visible counts exceed the global pre-filter denominator');
        }
        return {
          status: 'available',
          entries,
          site_count: entries.length,
          visible_node_count: visibleNodeCount,
          visible_observation_denominator: visibleObservationDenominator,
          global_node_count: globalFacet.node_count,
          global_observation_denominator: globalFacet.observation_denominator,
        };
      }
      let activeCountries = normalizedSetFromList(initialState.countries, COUNTRIES, DEFAULT_COUNTRIES);
      let activeLayerKeys = normalizedSetFromList(initialState.layers, ALL_LAYERS.map((layer) => layer.key), DEFAULT_LAYER_KEYS);
      const availableSourceChronologyLevels = sourceChronologyLayers().map((layer) => layer.node_level);
      const defaultSourceChronologyLevel = availableSourceChronologyLevels.includes('source_sample_presence')
        ? 'source_sample_presence'
        : (availableSourceChronologyLevels[0] || '');
      let activeSourceChronologyLevel = normalizedSingleValue(
        initialState.sourceChronologyLevel,
        availableSourceChronologyLevels,
        defaultSourceChronologyLevel
      );
      let activeSourceChronologyCode = 'all';
      let activeSourceChronologyTaxon = 'all';
      let activeSourceChronologyPreset = 'none';
      const initialSourceChronologyLayer = sourceChronologyLayerForLevel(activeSourceChronologyLevel);
      if (initialSourceChronologyLayer && initialSourceChronologyLayer.node_level === 'source_ecological_code') {
        activeSourceChronologyCode = normalizedSingleValue(
          initialState.sourceChronologyCode,
          ['all', ...initialSourceChronologyLayer.facet_metadata.source_ecological_codes.map((row) => row.value)],
          'all'
        );
      }
      if (initialSourceChronologyLayer && initialSourceChronologyLayer.node_level === 'source_taxon') {
        activeSourceChronologyTaxon = normalizedSingleValue(
          initialState.sourceChronologyTaxon,
          ['all', ...initialSourceChronologyLayer.facet_metadata.source_taxa.map((row) => row.value)],
          'all'
        );
        if (activeSourceChronologyTaxon === 'all') {
          activeSourceChronologyPreset = normalizedSingleValue(
            initialState.sourceChronologyPreset,
            ['none', ...initialSourceChronologyLayer.facet_metadata.source_label_preset_accountability.presets.map((row) => row.key)],
            'none'
          );
        }
      }
      let sourceChronologyTaxonSearch = '';
      let sourceRecordConcentrationActive = initialState.sourceRecordConcentration === 'captured';
      let sourceRecordConcentrationSnapshot = null;
      if (initialState.sourceChronologyLevel && initialSourceChronologyLayer && initialState.layers === null) {
        sourceChronologyLayers().forEach((layer) => activeLayerKeys.delete(layer.key));
        activeLayerKeys.add(initialSourceChronologyLayer.key);
      }
      const initiallyActiveSourceChronologyLayers = sourceChronologyLayers().filter((layer) => activeLayerKeys.has(layer.key));
      if (!initialState.sourceChronologyLevel && initiallyActiveSourceChronologyLayers.length === 1) {
        activeSourceChronologyLevel = initiallyActiveSourceChronologyLayers[0].node_level;
      }
      if (initiallyActiveSourceChronologyLayers.length > 1) {
        sourceChronologyLayers().forEach((layer) => activeLayerKeys.delete(layer.key));
        if (initialSourceChronologyLayer) activeLayerKeys.add(initialSourceChronologyLayer.key);
      }
      if (sourceRecordConcentrationActive && !sourceRecordConcentrationSelection(sourceChronologyLayerForLevel(activeSourceChronologyLevel))) {
        sourceRecordConcentrationActive = false;
      }
      let activeScientificSignalIds = normalizedSetFromList(
        initialState.scientificSignals,
        SCIENTIFIC_SIGNAL_IDS,
        DEFAULT_SCIENTIFIC_SIGNAL_IDS
      );
      let scientificPinValues = initialState.scientificPins;
      let scientificPinnedIds = null, scientificCatalog = null, scientificPickerController = null;
      let scientificPickerStatus = 'not_loaded';
      let activeEvidenceDisplay = initialState.evidenceDisplay;
      const COUNTRY_PAIR_KEYS = Array.from(new Set(GOVERNED_EDGE_RECORDS.map((edge) => atlasCountryPairKey(edge.source_country, edge.target_country)))).sort();
      let activeCountryPair = normalizedSingleValue(initialState.countryPair, ['all', ...COUNTRY_PAIR_KEYS], 'all');
      let crossBorderOnly = initialState.crossBorder === 'only';
      const DEFAULT_ATLAS_FILTER_STATE = atlasFilterStateSnapshot(
        new Set(DEFAULT_COUNTRIES),
        new Set(DEFAULT_SCIENTIFIC_SIGNAL_IDS),
        'all',
        false
      );
      const DEFAULT_GOVERNED_EDGE_VISIBLE_COUNT = GOVERNED_EDGE_RECORDS.filter((edge) => atlasEdgeVisible(
        edge,
        new Set(DEFAULT_COUNTRIES),
        'all',
        false,
        new Set(DEFAULT_SCIENTIFIC_SIGNAL_IDS)
      )).length;
      let activeAnimalSpecies = normalizedSingleValue(
        initialState.animalSpecies,
        ['all', ...ANIMAL_SPECIES.map((species) => species.latinName)],
        'all'
      );
      let activeAnimalScope = normalizedSingleValue(
        initialState.animalScope,
        ['all', 'domesticated_core', 'comparator'],
        'all'
      );
      let activeAnimalConfidence = normalizedSingleValue(
        initialState.animalConfidence,
        ['all', ...ANIMAL_COORDINATE_CONFIDENCES],
        'all'
      );
      let activeAnimalTemporalWindow = normalizedSingleValue(
        initialState.animalTemporalWindow,
        ['all', ...ANIMAL_TEMPORAL_WINDOWS],
        'all'
      );
      let animalNordicOnly = initialState.animalNordic === 'only';
      let timeIntervalYears = TIME_HAS_DATA ? clampTimeInterval(initialState.timeInterval) : DEFAULT_TIME_INTERVAL_YEARS;
      let timeStartBp = TIME_HAS_DATA ? clampTimeStart(initialState.timeStart, timeIntervalYears) : DEFAULT_TIME_START_BP;
      if (NATIVE_LRA_BINDING !== null && JSON.parse(NATIVE_LRA_BINDING.bytes).schema_version === 'lra-atlas-view.v2') {
        if (STATIC_ATLAS_BOOTSTRAP.schema_version !== 'atlas-static-bootstrap.v3'
            || STATIC_ATLAS_BOOTSTRAP.temporal_profile !== 'calendar-bp1950-signed.v1'
            || STATIC_ATLAS_BOOTSTRAP.temporal_axis !== 'BP1950'
            || STATIC_ATLAS_BOOTSTRAP.native_view_sha256 !== NATIVE_LRA_BINDING.sha256) throw Error('Signed native time requires its exact static/view identity.');
        nativeSignedCalendarView(JSON.parse(NATIVE_LRA_BINDING.bytes));
        signedNativeTime = createSignedNativeTimeState([TIME_MIN_BP, TIME_MAX_BP], NATIVE_LRA_BINDING.sha256);
        timeStartBp = signedNativeTime.window()[0];
      } else if (STATIC_ATLAS_BOOTSTRAP.schema_version === 'atlas-static-bootstrap.v3') throw Error('Signed static transport requires a signed native view.');
      const initialTimeWindowIsExplicit = initialState.timeStart !== null || initialState.timeInterval !== null;
      if (TIME_HAS_DATA && !initialTimeWindowIsExplicit) focusSourceChronologyNavigation();
      const initialModeledContextIndex = MODELED_CONTEXT_WINDOWS.findIndex(
        (sourceWindow) => sourceWindow.label === initialState.modeledContext
      );
      if (modeledContextAvailable() && initialModeledContextIndex >= 0) {
        modeledContextWindowIndex = initialModeledContextIndex;
        const sourceWindow = currentModeledContextWindow();
        const sourceSpan = modeledContextWindowSpan(sourceWindow);
        if (sourceSpan) {
          modeledContextActive = true;
          modeledContextPreviousTime = {
            timeStartBp: DEFAULT_TIME_START_BP,
            timeIntervalYears: DEFAULT_TIME_INTERVAL_YEARS,
          };
          timeStartBp = sourceSpan.timeStartBp;
          timeIntervalYears = sourceSpan.timeIntervalYears;
          activeLayerKeys.add(MODELED_CONTEXT.layer_key);
        }
      }
      const initialDensityPercent = finiteControlNumber(initialState.density);
      let densityOpacity = Math.max(0, Math.min(1, (initialDensityPercent === null ? 60 : initialDensityPercent) / 100));
      let currentBasemap = BASEMAP_NAMES.includes(String(initialState.basemap || '')) ? String(initialState.basemap) : DEFAULT_BASEMAP;
      let activeBasemap = null;
      const failedBasemaps = new Set();
      const basemapErrorCounts = new Map();
      let legendCollapsed = initialState.legend !== 'expanded';
      let focusState = null;
      let pendingEdgeFocus = initialState.edgeFocus;
      let activeFocusTab = 'overview';
      let focusCardReturnFocus = null;
      const DETAIL_TABLE_PAGE_SIZE = 25;
      const detailTablePages = new Map();
      let staticAtlasLoadGeneration = 0;
      function staticAtlasLayerForRow(row) {
        return ALL_LAYERS.find((layer) => layer.key === row.layer_key) || null;
      }
      function animalSourceChronologyCountryFilterBypassed(layer, scopeKey = SCOPE_KEY) {
        return scopeKey === 'world' && isAnimalSourceChronologyLayer(layer);
      }
      function staticAtlasCountryNeeded(row, layer) {
        if (!layer.applies_country_filter || animalSourceChronologyCountryFilterBypassed(layer)) return true;
        if (!activeCountries.size) return false;
        const countryKeys = Array.isArray(row.country_keys) ? row.country_keys : [];
        if (countryKeys.some((country) => activeCountries.has(country))) return true;
        if (row.layer_kind !== 'point') return false;
        const neighborCountries = new Set(retainedNeighborRecordCountries.values());
        return countryKeys.some((country) => neighborCountries.has(country));
      }
      function staticAtlasTimeNeeded(row, layer) {
        if (!layer.applies_time_filter || !TIME_HAS_DATA) return true;
        const allRecordsAreUntimed = staticAtlasNonnegativeInteger(row.untimed_record_count, `${row.asset_key} untimed record count`) === staticAtlasNonnegativeInteger(row.record_count, `${row.asset_key} record count`);
        if (timeFilterUsesFullExtent()) {
          return layer.semantic_role !== 'source_chronology_context' || !allRecordsAreUntimed;
        }
        if (allRecordsAreUntimed) return false;
        if (row.time_min_bp === null || row.time_max_bp === null) return true;
        return Number(row.time_max_bp) >= timeStartBp && Number(row.time_min_bp) <= timeWindowEndBp();
      }
      function staticAtlasSignalNeeded(row, layer) {
        if (isAnimalLayer(layer)) {
          const layerSpecies = layer.species_latin_name || layer.project_species_latin_name || '';
          if (activeAnimalSpecies !== 'all' && layerSpecies !== activeAnimalSpecies) return false;
          if (activeAnimalScope !== 'all' && layer.animal_scope !== activeAnimalScope) return false;
        }
        if (!layer.scientific_selection_enabled || !SCIENTIFIC_SIGNALS.length) return true;
        const rowSignals = Array.isArray(row.scientific_signal_ids) ? row.scientific_signal_ids : [];
        return activeScientificSignalIds.size > 0 && rowSignals.some((signalId) => activeScientificSignalIds.has(signalId));
      }
      function staticAtlasViewportNeeded(row) {
        if (!map._loaded || !Array.isArray(row.bounds)) return true;
        const bounds = map.getBounds();
        const [south, west, north, east] = row.bounds.map(Number);
        return north >= bounds.getSouth() && south <= bounds.getNorth() && east >= bounds.getWest() && west <= bounds.getEast();
      }
      function staticAtlasNodeSelectionNeeded(row) {
        const layer = staticAtlasLayerForRow(row);
        return Boolean(layer && activeLayerKeys.has(layer.key)
          && staticAtlasCountryNeeded(row, layer) && staticAtlasTimeNeeded(row, layer)
          && staticAtlasSignalNeeded(row, layer));
      }
      function requiredStaticAtlasEdgeNodeKeys() {
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
      function requiredStaticAtlasNodeAssets() {
        if (STATIC_ATLAS_INLINE) return [];
        const endpointKeys = requiredStaticAtlasEdgeNodeKeys();
        const required = STATIC_ATLAS_BOOTSTRAP.assets.filter((row) => {
          if (row.domain !== 'nodes' || staticAtlasLoadedAssets.has(row.asset_key)) return false;
          return staticAtlasNodeSelectionNeeded(row)
            && (endpointKeys.has(row.asset_key) || staticAtlasViewportNeeded(row));
        });
        if (Object.hasOwn(STATIC_ATLAS_BOOTSTRAP.compatibility || {}, 'search_index_abi')) {
          if (STATIC_ATLAS_BOOTSTRAP.compatibility.search_index_abi !== 'atlas-substring-postings.v1') staticAtlasFailure('unsupported search ABI');
          const indexes = staticAtlasIndexRows();
          if (!indexes.length) staticAtlasFailure('published search index is missing');
          required.push(...indexes.filter(row => !staticAtlasLoadedAssets.has(row.asset_key)));
        }
        const overhead = staticAtlasIndexOverhead(required.filter(row => row.domain === 'indexes'));
        const interactionRequestBudget = staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests, 'interaction request budget');
        if (required.length + overhead.request_count > interactionRequestBudget) staticAtlasFailure(`selection requires ${required.length + overhead.request_count} requests, above the interaction budget`);
        const requiredBytes = overhead.byte_count + required.reduce((total, row) => total + staticAtlasNonnegativeInteger(row.byte_count, `${row.asset_key} byte count`), 0);
        const interactionByteBudget = staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes, 'interaction byte budget');
        if (requiredBytes > interactionByteBudget) staticAtlasFailure(`selection requires ${requiredBytes} bytes, above the interaction budget`);
        return required;
      }
      function refreshStaticAtlasLayers() {
        if (STATIC_ATLAS_INLINE) return;
        const refreshedPoints = hydrateStaticAtlasLayers('point');
        const refreshedPolygons = hydrateStaticAtlasLayers('polygon');
        for (const current of POINT_LAYERS) {
          const replacement = refreshedPoints.find((layer) => layer.key === current.key);
          if (replacement) Object.assign(current, replacement);
        }
        for (const current of POLYGON_LAYERS) {
          const replacement = refreshedPolygons.find((layer) => layer.key === current.key);
          if (replacement) Object.assign(current, replacement);
        }
      }
      async function ensureStaticAtlasSelectionLoaded() {
        let required;
        try {
          required = requiredStaticAtlasNodeAssets();
        } catch (error) {
          beginStaticAtlasSelection([]);
          throw error;
        }
        const signal = beginStaticAtlasSelection(required);
        if (required.some(row => row.domain === 'indexes')) await waitForStaticAtlasSelection(loadIndexTransport(), signal);
        signal.throwIfAborted();
        await waitForStaticAtlasSelection(Promise.all(required.map((row) => loadStaticAtlasAsset(row, true))), signal);
        signal.throwIfAborted();
        validateLoadedStaticAtlasEdgeAssets();
        refreshStaticAtlasLayers();
        return required;
      }
      const countryColors = {
        Sweden: { fill: '#2563eb', stroke: '#1d4ed8' },
        Norway: { fill: '#0f766e', stroke: '#115e59' },
        Finland: { fill: '#b45309', stroke: '#92400e' },
        Denmark: { fill: '#be123c', stroke: '#9f1239' }
      };
      function escapeHtml(value) {
        return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
      }
      function normalizedMediaLinks(value) {
        if (!Array.isArray(value)) return [];
        return value.filter((link) => link && link.label && link.url);
      }
      function mediaIconSvg(kind) {
        if (kind === 'video') {
          return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M4 6h11a2 2 0 0 1 2 2v1.2l3.4-2.26A1 1 0 0 1 22 7.77v8.46a1 1 0 0 1-1.6.83L17 14.8V16a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Zm0 2v8h11V8H4Z"/></svg>';
        }
        return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M9 4.5 7.5 6H5a2 2 0 0 0-2 2v8.5a2.5 2.5 0 0 0 2.5 2.5h13a2.5 2.5 0 0 0 2.5-2.5V8a2 2 0 0 0-2-2h-2.5L15 4.5H9Zm3 3a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Zm0 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5Z"/></svg>';
      }
      function mediaLinksHtml(value) {
        const links = normalizedMediaLinks(value);
        if (!links.length) return '';
        const items = links
          .map((link) => `<a class="popup-media-link" href="${escapeHtml(link.url)}" target="_blank" rel="noreferrer">${mediaIconSvg(String(link.kind || '').toLowerCase())}<span>${escapeHtml(link.label)}</span></a>`)
          .join('');
        return `<div><strong>Media</strong> <span class="popup-media-list">${items}</span></div>`;
      }
      function titleCaseWords(value) {
        return String(value || '')
          .split(/[_-]+/)
          .filter(Boolean)
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
      }
      function formatAnimalScope(scope) {
        if (scope === 'domesticated_core') return 'Domesticated-core';
        if (scope === 'comparator') return 'Comparator';
        return titleCaseWords(scope) || 'Unspecified';
      }
      function formatCoordinateConfidence(confidence) {
        if (confidence === 'exact') return 'Exact';
        if (confidence === 'approximate') return 'Approximate';
        if (confidence === 'inferred') return 'Inferred';
        return titleCaseWords(confidence) || 'Unspecified';
      }
      function formatCoordinateBasis(basis) {
        if (basis === 'named_site_geocoded') return 'Named-site geocoded';
        if (basis === 'named_site_geocoding') return 'Named-site geocoded';
        if (basis === 'direct_coordinates') return 'Direct coordinates';
        if (basis === 'supplementary_coordinates') return 'Supplementary coordinates';
        if (basis === 'archive_coordinates') return 'Archive coordinates';
        if (basis === 'region_only_refusal') return 'Region-only refusal';
        if (basis === 'unresolved_location') return 'Unresolved location';
        return titleCaseWords(basis) || 'Unspecified';
      }
      function animalFilterState(overrides = {}) {
        return {
          species: Object.prototype.hasOwnProperty.call(overrides, 'species') ? overrides.species : activeAnimalSpecies,
          scope: Object.prototype.hasOwnProperty.call(overrides, 'scope') ? overrides.scope : activeAnimalScope,
          confidence: Object.prototype.hasOwnProperty.call(overrides, 'confidence') ? overrides.confidence : activeAnimalConfidence,
          temporalWindow: Object.prototype.hasOwnProperty.call(overrides, 'temporalWindow') ? overrides.temporalWindow : activeAnimalTemporalWindow,
          nordicOnly: Object.prototype.hasOwnProperty.call(overrides, 'nordicOnly') ? overrides.nordicOnly : animalNordicOnly,
        };
      }
      function animalCandidateEntries() {
        const entries = [];
        POINT_LAYERS.forEach((layer) => {
          if (!isAnimalLayer(layer) || !activeLayerKeys.has(layer.key)) return;
          const sourceChronology = layer.semantic_role === 'animal_source_chronology_context' || layer.group === 'animal-chronology-context';
          if (sourceChronology && !animalSourceChronologyLayerIsValid(layer)) return;
          (layer.features || []).forEach((feature) => {
            if (sourceChronology && !animalSourceChronologyFeatureIsValid(feature)) return;
            if (layer.applies_country_filter && !animalSourceChronologyCountryFilterBypassed(layer) && !activeCountries.has(feature.country)) return;
            if (!pointFeatureInTimeWindow(layer, feature)) return;
            entries.push({ layer, feature });
          });
        });
        return entries;
      }
      function animalEntryMatchesFilters(entry, overrides = {}) {
        const state = animalFilterState(overrides);
        const feature = entry.feature;
        const species = String(feature.species_latin_name || feature.project_species_latin_name || '');
        if (state.species !== 'all' && species !== state.species) return false;
        if (state.scope !== 'all' && String(feature.animal_scope || '') !== state.scope) return false;
        if (state.confidence !== 'all' && String(feature.coordinate_confidence || '') !== state.confidence) return false;
        if (state.temporalWindow !== 'all' && String(feature.temporal_window_label || '') !== state.temporalWindow) return false;
        if (state.nordicOnly && !feature.nordic_inclusion) return false;
        return true;
      }
      function animalVisibleEntries() {
        return animalCandidateEntries().filter((entry) => animalEntryMatchesFilters(entry));
      }
      function summarizeAnimalMetrics() {
        const candidateEntries = animalCandidateEntries();
        const visibleEntries = candidateEntries.filter((entry) => animalEntryMatchesFilters(entry));
        const visibleSourceChronologyEntries = visibleEntries.filter(({ layer }) => isAnimalSourceChronologyLayer(layer));
        const visibleAtlasEvidenceEntries = visibleEntries.filter(({ layer }) => !isAnimalSourceChronologyLayer(layer));
        const visibleSpecies = new Set(
          visibleEntries
            .map(({ feature }) => String(feature.species_latin_name || feature.project_species_latin_name || '').trim())
            .filter(Boolean)
        );
        const confidenceCounts = {};
        visibleEntries.forEach(({ feature }) => {
          const key = String(feature.coordinate_confidence || '').trim() || 'unspecified';
          confidenceCounts[key] = (confidenceCounts[key] || 0) + 1;
        });
        const activeFilters = [
          activeAnimalSpecies !== 'all' ? ANIMAL_SPECIES.find((species) => species.latinName === activeAnimalSpecies)?.commonName || activeAnimalSpecies : '',
          activeAnimalScope !== 'all' ? formatAnimalScope(activeAnimalScope) : '',
          activeAnimalConfidence !== 'all' ? formatCoordinateConfidence(activeAnimalConfidence) : '',
          activeAnimalTemporalWindow !== 'all' ? activeAnimalTemporalWindow : '',
          animalNordicOnly ? 'Nordic leads only' : '',
        ].filter(Boolean);
        return {
          candidateEntries,
          visibleEntries,
          visibleSourceChronologyEntries,
          visibleAtlasEvidenceEntries,
          visibleSpecies,
          confidenceCounts,
          activeFilters,
        };
      }
      function countryStyle(country) { return countryColors[country] || { fill: '#475569', stroke: '#1e293b' }; }
      function layerColor(layer) { return layer.style && layer.style.fill ? layer.style.fill : (layer.style && layer.style.stroke ? layer.style.stroke : '#475569'); }
      function isAnimalLayer(layer) {
        return ANIMAL_LAYER_GROUPS.has(layer.group);
      }
      function isAnimalSourceChronologyLayer(layer) {
        return Boolean(
          layer
          && (
            layer.group === ANIMAL_CHRONOLOGY_LAYER_GROUP
            || layer.semantic_role === 'animal_source_chronology_context'
          )
        );
      }
      function animalSourceChronologyPostureIsValid(value) {
        return Boolean(
          value
          && value.semantic_role === 'animal_source_chronology_context'
          && value.contribution_role === 'display_only'
          && value.candidate_ranking_eligible === false
          && value.scientific_classification_eligible === false
          && value.scientific_selection_enabled === false
          && value.propagation_status === 'refused'
          && value.propagation_reason_code === 'display_only_source_chronology'
          && value.edge_count === 0
        );
      }
      function animalSourceChronologyLayerIsValid(layer) {
        if (!isAnimalSourceChronologyLayer(layer)) return false;
        return (
          layer.group === ANIMAL_CHRONOLOGY_LAYER_GROUP
          && layer.default_enabled === false
          && layer.applies_country_filter === true
          && layer.applies_time_filter === true
          && layer.circle_enabled === false
          && typeof layer.project_species_latin_name === 'string'
          && Boolean(layer.project_species_latin_name.trim())
          && layer.species_attribution_basis === 'governed_project_registry'
          && !Object.prototype.hasOwnProperty.call(layer, 'species_latin_name')
          && !Object.prototype.hasOwnProperty.call(layer, 'species_common_name')
          && !Object.prototype.hasOwnProperty.call(layer, 'animal_scope')
          && !Object.prototype.hasOwnProperty.call(layer, 'classification_id')
          && !Object.prototype.hasOwnProperty.call(layer, 'classification_status')
          && !Object.prototype.hasOwnProperty.call(layer, 'taxon_alignment_status')
          && !Object.prototype.hasOwnProperty.call(layer, 'taxon_alignment_statuses')
          && !Object.prototype.hasOwnProperty.call(layer, 'scientific_signal_ids')
          && animalSourceChronologyPostureIsValid(layer)
        );
      }
      function animalSourceChronologyFeatureIsValid(feature) {
        if (!feature || feature.semantic_role !== 'animal_source_chronology_context') return false;
        return (
          typeof feature.project_species_latin_name === 'string'
          && Boolean(feature.project_species_latin_name.trim())
          && feature.species_attribution_basis === 'governed_project_registry'
          && !Object.prototype.hasOwnProperty.call(feature, 'species_latin_name')
          && !Object.prototype.hasOwnProperty.call(feature, 'species_common_name')
          && !Object.prototype.hasOwnProperty.call(feature, 'animal_scope')
          && !Object.prototype.hasOwnProperty.call(feature, 'classification_id')
          && !Object.prototype.hasOwnProperty.call(feature, 'classification_status')
          && !Object.prototype.hasOwnProperty.call(feature, 'taxon_alignment_status')
          && !Object.prototype.hasOwnProperty.call(feature, 'taxon_alignment_statuses')
          && !Object.prototype.hasOwnProperty.call(feature, 'scientific_signal_ids')
          && animalSourceChronologyPostureIsValid(feature)
        );
      }
      function featureMatchesAnimalFilters(layer, feature) {
        if (!isAnimalLayer(layer)) return true;
        return animalEntryMatchesFilters({ layer, feature });
      }
      function syncPresetButtons() {
        document.querySelectorAll('[data-km]').forEach((button) => {
          button.classList.toggle('is-active', Number(button.dataset.km) === Number(slider.value));
        });
      }
      function syncTimePresetButtons() {
        const navigationExtent = selectedTimePlaybackExtent();
        const navigationSpan = Math.max(1, navigationExtent.time_max_bp - navigationExtent.time_min_bp);
        document.querySelectorAll('[data-time-interval]').forEach((button) => {
          const preset = button.dataset.timeInterval;
          const active = preset === 'full' ? timeIntervalYears === navigationSpan : Number(preset) === Number(timeIntervalYears);
          button.classList.toggle('is-active', active);
        });
      }
      function updatePanelToggleLabel() {
        const collapsed = sidebar.classList.contains('is-collapsed');
        if (mobileLayoutQuery.matches) {
          panelToggleButton.textContent = collapsed ? '← Show controls' : 'Hide controls →';
          return;
        }
        panelToggleButton.textContent = collapsed ? '← Show controls' : 'Hide controls →';
      }
      function syncMobilePanelState() {
        const mobileOpen = mobileLayoutQuery.matches && !sidebar.classList.contains('is-collapsed');
        panelToggleButton.setAttribute('aria-expanded', String(!sidebar.classList.contains('is-collapsed')));
        panelToggleButton.setAttribute('aria-controls', 'sidebar');
        mobileScrim.classList.toggle('is-visible', mobileOpen);
        document.body.classList.toggle('has-mobile-panel-open', mobileOpen);
      }
      function setPanelCollapsed(collapsed, persist = true) {
        if (!collapsed) {
          if (!legendCollapsed) setLegendCollapsed(true, false);
          if (!topbarSearch.hidden) setSearchOpen(false);
        }
        sidebar.classList.toggle('is-collapsed', collapsed);
        sidebar.inert = collapsed;
        updatePanelToggleLabel();
        syncMobilePanelState();
        window.setTimeout(() => map.invalidateSize(), 180);
        if (persist) syncHashState();
      }
      function closeMobilePanel() {
        setPanelCollapsed(true);
        if (mobilePanelReturnFocus) {
          mobilePanelReturnFocus.focus({ preventScroll: true });
          mobilePanelReturnFocus = null;
        }
      }
      function setLegendCollapsed(collapsed, persist = true) {
        if (!collapsed) {
          setPanelCollapsed(true, false);
          setSearchOpen(false);
          if (focusState) setFocusState(null);
        }
        legendCollapsed = collapsed;
        document.body.classList.toggle('has-legend-open', !collapsed);
        legendBody.classList.toggle('is-collapsed', collapsed);
        legendToggleButton.textContent = collapsed ? 'Expand' : 'Collapse';
        legendToggleButton.setAttribute('aria-expanded', String(!collapsed));
        if (persist) syncHashState();
      }
      function setSearchOpen(open, restoreFocus = false) {
        if (open) {
          setPanelCollapsed(true, false);
          setLegendCollapsed(true, false);
          if (focusState) setFocusState(null);
        }
        topbarSearch.hidden = !open;
        document.body.classList.toggle('has-search-open', open);
        searchToggleButton.setAttribute('aria-expanded', String(open));
        if (open) {
          searchInput.focus({ preventScroll: true });
          buildSearchResults();
          return;
        }
        searchResults.hidden = true;
        if (restoreFocus) searchToggleButton.focus({ preventScroll: true });
      }
      function openHelpDialog() {
        if (!helpDialog.hidden) return;
        helpDialogReturnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        helpDialog.hidden = false;
        appShell.inert = true;
        helpToggleButton.setAttribute('aria-expanded', 'true');
        document.body.classList.add('has-mobile-panel-open');
        helpCloseButton.focus({ preventScroll: true });
      }
      function closeHelpDialog() {
        if (helpDialog.hidden) return;
        helpDialog.hidden = true;
        appShell.inert = false;
        helpToggleButton.setAttribute('aria-expanded', 'false');
        syncMobilePanelState();
        if (helpDialogReturnFocus && helpDialogReturnFocus.isConnected) {
          helpDialogReturnFocus.focus({ preventScroll: true });
        }
        helpDialogReturnFocus = null;
      }
      function helpDialogFocusableElements() {
        return [...helpDialog.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
          .filter((element) => !element.hidden && getComputedStyle(element).display !== 'none' && getComputedStyle(element).visibility !== 'hidden');
      }
      function syncHashState() {
        if (pendingEdgeFocus) return;
        if (!atlasURLState.canPublish()) return;
        const nextHash = atlasSelectionHashParams().toString();
        atlasURLState.publish(nextHash ? `#${nextHash}` : '');
      }
      function atlasSelectionHashParams() {
        const params = new URLSearchParams();
        if (activeCountries.size !== COUNTRIES.length) params.set('countries', activeCountries.size ? [...activeCountries].join(',') : 'none');
        if (activeLayerKeys.size !== DEFAULT_LAYER_KEYS.length || DEFAULT_LAYER_KEYS.some((key) => !activeLayerKeys.has(key))) params.set('layers', activeLayerKeys.size ? [...activeLayerKeys].join(',') : 'none');
        if (activeScientificSignalIds.size !== DEFAULT_SCIENTIFIC_SIGNAL_IDS.length || DEFAULT_SCIENTIFIC_SIGNAL_IDS.some((signalId) => !activeScientificSignalIds.has(signalId))) params.set('scientific_signals', activeScientificSignalIds.size ? [...activeScientificSignalIds].join(',') : 'none');
        scientificPinValues.forEach(value => params.append('scientific_pins', value));
        if (activeCountryPair !== 'all') params.set('country_pair', activeCountryPair);
        writeRelationFilterHash(params, activeRelationFilters);
        writeRelationEventDefinitionHash(params, activeRelationEventDefinition);
        writeEvidenceDisplayHash(params, activeEvidenceDisplay);
        if (crossBorderOnly) params.set('cross_border', 'only');
        if (activeAnimalSpecies !== 'all') params.set('animal_species', activeAnimalSpecies);
        if (activeAnimalScope !== 'all') params.set('animal_scope', activeAnimalScope);
        if (activeAnimalConfidence !== 'all') params.set('animal_confidence', activeAnimalConfidence);
        if (activeAnimalTemporalWindow !== 'all') params.set('animal_time_window', activeAnimalTemporalWindow);
        if (animalNordicOnly) params.set('animal_nordic', 'only');
        if (sourceChronologyLayerForLevel(activeSourceChronologyLevel)) {
          if (activeSourceChronologyLevel !== defaultSourceChronologyLevel) params.set('source_chronology_level', activeSourceChronologyLevel);
          if (activeSourceChronologyCode !== 'all') params.set('source_ecological_code', activeSourceChronologyCode);
          if (activeSourceChronologyTaxon !== 'all') params.set('source_taxon', activeSourceChronologyTaxon);
          if (activeSourceChronologyPreset !== 'none') params.set('source_label_preset', activeSourceChronologyPreset);
          if (sourceRecordConcentrationActive) params.set('source_record_concentration', 'captured');
        }
        if (Number(slider.value) !== 20) params.set('diameter', String(Number(slider.value)));
        const modeledWindow = currentModeledContextWindow();
        if (modeledContextActive && modeledWindow) {
          params.set('modeled_context', modeledWindow.label);
          params.set('modeled_family', modeledContextFamilyKey);
          params.set('modeled_metric', modeledContextMetricKey);
        } else {
          if (!signedNativeTime && TIME_HAS_DATA && timeStartBp !== DEFAULT_TIME_START_BP) params.set('time_start', String(timeStartBp));
          if (!signedNativeTime && TIME_HAS_DATA && timeIntervalYears !== DEFAULT_TIME_INTERVAL_YEARS) params.set('time_interval', String(timeIntervalYears));
        }
        if (Math.round(densityOpacity * 100) !== 60) params.set('density', String(Math.round(densityOpacity * 100)));
        if (currentBasemap !== DEFAULT_BASEMAP) params.set('basemap', currentBasemap);
        if (sidebar.classList.contains('is-collapsed') !== defaultPanelCollapsed()) {
          params.set('panel', sidebar.classList.contains('is-collapsed') ? 'collapsed' : 'open');
        }
        if (!legendCollapsed) params.set('legend', 'expanded');
        if (nativeLraController) nativeLraController.writeHash(params);
        if (!focusCard.hidden) {
          writeSourceRecordFocusHash(params, focusState, activeFocusTab);
          writeEdgeFocusHash(params, focusState, activeFocusTab, publishedEdgeFocusBuild());
        }
        return params;
      }
      function clearHighlightedPoint() {
        if (!highlightedPointEntry || !highlightedPointEntry.marker) return;
        const entry = highlightedPointEntry;
        if (typeof entry.marker.setStyle === 'function') {
          entry.marker.setStyle({
            radius: entry.layer.key === 'aadr' ? 4.5 : 6,
            weight: 1.3,
            color: entry.layer.style.stroke,
            fillColor: entry.layer.style.fill,
            fillOpacity: 0.92,
          });
        } else if (entry.marker.getElement()) {
          entry.marker.getElement().classList.remove('is-focused');
        }
        highlightedPointEntry = null;
      }
      function highlightPointEntry(entry) {
        clearHighlightedPoint();
        if (!entry || !entry.marker) return;
        if (typeof entry.marker.setStyle === 'function') {
          entry.marker.setStyle({
            radius: (entry.layer.key === 'aadr' ? 4.5 : 6) + 2,
            weight: 2.4,
            color: '#ffffff',
            fillColor: entry.layer.style.fill,
            fillOpacity: 1,
          });
        } else if (entry.marker.getElement()) {
          entry.marker.getElement().classList.add('is-focused');
        }
        highlightedPointEntry = entry;
      }
      function stableFeatureRecordId(feature) {
        const recordId = String(feature?.record_id ?? '').trim();
        if (recordId) return recordId;
        return String(feature?.evidence_row_id ?? '').trim();
      }
      function pointFocusIdentity(layer, feature) {
        const layerKey = String(layer?.key ?? '').trim();
        const recordId = stableFeatureRecordId(feature);
        const nodeId = String(feature?.node_id ?? '').trim();
        const evidenceRowId = String(feature?.evidence_row_id ?? '').trim();
        if (!layerKey || !recordId) return null;
        return {
          layerKey,
          featureKey: nodeId
            ? `node:${nodeId}`
            : evidenceRowId
              ? `evidence:${evidenceRowId}`
              : `record:${recordId}`,
          recordId,
        };
      }
      function uniquePointEntryForFocus(entries, state) {
        if (!state || state.kind !== 'point' || !state.layerKey || !state.featureKey || !state.recordId) return null;
        const matches = entries.filter(({ layer, feature }) => {
          const identity = pointFocusIdentity(layer, feature);
          return identity
            && identity.layerKey === state.layerKey
            && identity.featureKey === state.featureKey
            && identity.recordId === state.recordId;
        });
        if (matches.length > 1) throw new Error('point focus identity is not unique');
        return matches[0] || null;
      }
      function visiblePointEntryForFocus(state = focusState) {
        return uniquePointEntryForFocus(visiblePointEntries, state);
      }
      function setFocusState(nextState) {
        pendingEdgeFocus = null;
        edgeFocusLoadState.request++;
        const opening = Boolean(nextState) && focusCard.hidden;
        if (opening) {
          const origin = document.activeElement;
          focusCardReturnFocus = topbarSearch.contains(origin) ? searchToggleButton : origin;
        }
        if (nextState) {
          setPanelCollapsed(true, false);
          mobilePanelReturnFocus = null;
          setLegendCollapsed(true, false);
          setSearchOpen(false);
        }
        focusState = nextState;
        activeFocusTab = 'overview';
        detailTablePages.clear();
        if (focusState && focusState.kind === 'point') {
          highlightPointEntry(visiblePointEntryForFocus(focusState));
        } else {
          clearHighlightedPoint();
        }
        renderFocusCard();
        if (opening && !focusCard.hidden) focusTabs.querySelector('[aria-selected="true"]').focus({ preventScroll: true });
        syncHashState();
      }
      function restoreFocusFromCard() {
        const origin = focusCardReturnFocus;
        focusCardReturnFocus = null;
        if (origin instanceof HTMLElement && origin.isConnected && origin.getClientRects().length && !origin.matches(':disabled')) {
          origin.focus({ preventScroll: true });
        } else {
          document.getElementById('map').focus({ preventScroll: true });
        }
      }
      function unavailableDetailTabs(reasonCode) {
        return Object.fromEntries(DETAIL_TAB_DEFINITIONS.map(([key]) => [key, { status: 'unavailable', reason_code: reasonCode }]));
      }
      async function ensureStaticAtlasIndexesLoaded() {
        if (STATIC_ATLAS_INLINE || STATIC_ATLAS_CHUNKS.indexes) return true;
        try {
          const candidates = staticAtlasIndexRows();
          if (!candidates.length) return false;
          const missing = candidates.filter(row => !staticAtlasLoadedAssets.has(row.asset_key));
          const overhead = staticAtlasIndexOverhead(missing);
          const requests = missing.length + overhead.request_count;
          const bytes = missing.reduce((total, row) => total + staticAtlasNonnegativeInteger(row.byte_count, `${row.asset_key} byte count`), overhead.byte_count);
          if (requests > staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests, 'interaction request budget') || bytes > staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes, 'interaction byte budget')) return false;
          await loadIndexTransport();
          await Promise.all(missing.map(row => loadStaticAtlasAsset(row)));
        } catch (error) {
          return false;
        }
        return Boolean(STATIC_ATLAS_CHUNKS.indexes && typeof STATIC_ATLAS_CHUNKS.indexes.detail_record_asset_keys === 'object');
      }
      async function detailTabsForRecordId(recordId) {
        if (!recordId) return unavailableDetailTabs('feature_record_id_not_available');
        const stored = DETAIL_RECORDS.get(recordId);
        if (stored && stored.tabs) return stored.tabs;
        if (STATIC_ATLAS_INLINE || ATLAS_EVIDENCE.details_status !== 'available') {
          return unavailableDetailTabs(ATLAS_EVIDENCE.details_reason_code || 'record_level_evidence_not_available');
        }
        let indexRequests = 0, indexBytes = 0;
        if (!STATIC_ATLAS_CHUNKS.indexes) {
          try {
            const missing = staticAtlasIndexRows().filter(row => !staticAtlasLoadedAssets.has(row.asset_key));
            const overhead = staticAtlasIndexOverhead(missing);
            indexRequests = missing.length + overhead.request_count;
            indexBytes = missing.reduce((total, row) => total + staticAtlasNonnegativeInteger(row.byte_count, `${row.asset_key} byte count`), overhead.byte_count);
          } catch (error) { return unavailableDetailTabs('detail_index_load_failed'); }
        }
        if (!(await ensureStaticAtlasIndexesLoaded())) return unavailableDetailTabs('detail_index_load_failed');
        const assetKey = STATIC_ATLAS_CHUNKS.indexes.detail_record_asset_keys?.[recordId];
        if (!assetKey) return unavailableDetailTabs('detail_record_not_indexed');
        const candidates = STATIC_ATLAS_BOOTSTRAP.assets.filter((row) => row.asset_key === assetKey && row.domain === 'details');
        if (candidates.length !== 1) return unavailableDetailTabs('detail_chunk_index_invalid');
        const row = candidates[0];
        const missingDetail = !staticAtlasLoadedAssets.has(row.asset_key);
        const requests = indexRequests + (missingDetail ? 1 : 0);
        const bytes = indexBytes + (missingDetail ? staticAtlasNonnegativeInteger(row.byte_count, `${row.asset_key} byte count`) : 0);
        if (requests > staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests, 'interaction request budget') || bytes > staticAtlasNonnegativeInteger(STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes, 'interaction byte budget')) return unavailableDetailTabs('detail_chunk_interaction_budget_exceeded');
        try {
          await loadStaticAtlasAsset(row);
        } catch (error) {
          return unavailableDetailTabs('detail_chunk_load_failed');
        }
        const payload = STATIC_ATLAS_CHUNKS.details.find((candidate) => candidate.asset_key === assetKey);
        if (!payload) return unavailableDetailTabs('detail_chunk_not_registered');
        payload.records.forEach((record) => DETAIL_RECORDS.set(record.record_id, record));
        const loaded = DETAIL_RECORDS.get(recordId);
        return loaded && loaded.tabs ? loaded.tabs : unavailableDetailTabs('detail_record_missing_from_chunk');
      }
      async function detailTabsForFeature(feature) {
        const recordId = stableFeatureRecordId(feature);
        return detailTabsForRecordId(recordId);
      }
      function detailTableShape(value) {
        return value && typeof value === 'object'
          && Number.isInteger(value.record_count)
          && Array.isArray(value.fields)
          && Array.isArray(value.records);
      }
      function detailTableText(value) {
        if (value === null) return 'null (source null)';
        if (value === undefined || value === '') return 'Unavailable';
        if (typeof value === 'object') return JSON.stringify(value);
        return String(value);
      }
      function decodedDictionaryValue(table, field, value) {
        const dictionary = table.column_dictionaries?.[field];
        if (!dictionary) return value;
        if (!Array.isArray(dictionary) || !Number.isInteger(value) || value < 0 || value >= dictionary.length) {
          throw new Error(`invalid dictionary index for ${field}`);
        }
        return dictionary[value];
      }
      function decodedListDictionaryValue(table, field, value) {
        if (!Array.isArray(table.list_dictionary_fields) || !table.list_dictionary_fields.includes(field)) return value;
        if (!Array.isArray(value) || !Array.isArray(table.list_value_dictionary)) throw new Error(`invalid list dictionary for ${field}`);
        return value.map((index) => {
          if (!Number.isInteger(index) || index < 0 || index >= table.list_value_dictionary.length) throw new Error(`invalid list dictionary index for ${field}`);
          return table.list_value_dictionary[index];
        });
      }
      function decodedSeadClaimAge(table, row) {
        const claimType = row.claim_type;
        const columns = table.source_age_value_columns_by_claim_type?.[claimType];
        const inherited = table.source_age_value_inherited_fields_by_claim_type?.[claimType];
        const dictionaries = table.source_age_value_dictionaries_by_claim_type?.[claimType] || {};
        if (!Array.isArray(columns) || !inherited || typeof inherited !== 'object' || !Array.isArray(row.source_age_value) || columns.length !== row.source_age_value.length) {
          throw new Error('invalid SEAD claim source age encoding');
        }
        const decoded = {};
        columns.forEach((field, index) => {
          const dictionary = dictionaries[field];
          const encoded = row.source_age_value[index];
          if (dictionary) {
            if (!Array.isArray(dictionary) || !Number.isInteger(encoded) || encoded < 0 || encoded >= dictionary.length) throw new Error(`invalid source age dictionary index for ${field}`);
            decoded[field] = dictionary[encoded];
          } else {
            decoded[field] = encoded;
          }
        });
        Object.entries(inherited).forEach(([sourceField, claimField]) => {
          decoded[sourceField] = row[claimField];
        });
        return decoded;
      }
      function decodedSeadClaimRelation(table, row) {
        if (!Number.isInteger(row.source_relation_path) || !Array.isArray(table.source_relation_path_dictionary)) throw new Error('invalid SEAD claim relation encoding');
        const shape = table.source_relation_path_dictionary[row.source_relation_path];
        if (!Array.isArray(shape)) throw new Error('invalid SEAD claim relation dictionary index');
        return shape.map((entry) => {
          if (!Array.isArray(entry) || entry.length !== 3) throw new Error('invalid SEAD claim relation tuple');
          const [sourceTable, key, valueField] = entry;
          const value = valueField === 'common_fields.source_site_id'
            ? table.common_fields?.source_site_id
            : row[valueField];
          return { table: sourceTable, key, value };
        });
      }
      function decodeDetailTableRow(table, encodedRow) {
        if (!Array.isArray(encodedRow) || encodedRow.length !== table.fields.length) throw new Error('encoded detail row width changed');
        const row = Object.fromEntries(table.fields.map((field, index) => [
          field,
          decodedListDictionaryValue(table, field, decodedDictionaryValue(table, field, encodedRow[index])),
        ]));
        Object.entries(table.identifier_prefixes || {}).forEach(([field, prefix]) => {
          if (!Object.prototype.hasOwnProperty.call(row, field) || typeof prefix !== 'string') throw new Error('invalid detail identifier prefix');
          if (row[field] !== null) row[field] = `${prefix}${row[field]}`;
        });
        if (table.encoding === 'sead-chronology-claim-table.v1') {
          row.source_age_value = decodedSeadClaimAge(table, row);
          row.source_relation_path = decodedSeadClaimRelation(table, row);
          return { ...(table.common_fields || {}), ...row };
        }
        if (table.encoding && table.encoding !== 'sead-source-native-observation-table.v1') throw new Error(`unsupported detail table encoding: ${table.encoding}`);
        return row;
      }
      const DETAIL_TABLE_INTERNAL_KEYS = new Set([
        'record_count', 'fields', 'records', 'encoding', 'common_fields',
        'column_dictionaries', 'list_dictionary_fields', 'list_value_dictionary',
        'identifier_prefixes', 'source_age_value_columns_by_claim_type',
        'source_age_value_inherited_fields_by_claim_type',
        'source_age_value_dictionaries_by_claim_type',
        'source_relation_path_dictionary', 'source_relation_path_value_semantics',
      ]);
      function renderDetailObjectEntries(value, valuePath, excludedKeys = new Set()) {
        return Object.entries(value).filter(([key]) => !excludedKeys.has(key)).map(([key, item]) => `<div class="focus-detail-row"><span class="focus-detail-key">${escapeHtml(key.replaceAll('_', ' '))}</span>${detailTableShape(item) ? `<div>${renderDetailTable(item, `${valuePath}.${key}`)}</div>` : `<span>${escapeHtml(detailTableText(item))}</span>`}</div>`).join('');
      }
      function renderDetailTable(table, tablePath) {
        try {
          if (!detailTableShape(table) || table.record_count !== table.records.length || table.fields.some((field) => typeof field !== 'string')) throw new Error('detail table accounting changed');
          const fields = table.encoding === 'sead-chronology-claim-table.v1'
            ? [...Object.keys(table.common_fields || {}), ...table.fields]
            : table.fields;
          const total = table.records.length;
          const pageCount = Math.max(1, Math.ceil(total / DETAIL_TABLE_PAGE_SIZE));
          const page = Math.min(Math.max(0, detailTablePages.get(tablePath) || 0), pageCount - 1);
          const start = page * DETAIL_TABLE_PAGE_SIZE;
          const end = Math.min(total, start + DETAIL_TABLE_PAGE_SIZE);
          const rows = table.records.slice(start, end).map((row) => decodeDetailTableRow(table, row));
          const heading = fields.map((field) => `<th scope="col">${escapeHtml(field.replaceAll('_', ' '))}</th>`).join('');
          const body = rows.map((row) => `<tr>${fields.map((field) => `<td class="${row[field] === null ? 'focus-detail-null' : ''}">${escapeHtml(detailTableText(row[field]))}</td>`).join('')}</tr>`).join('');
          const shown = total ? `${start + 1}–${end}` : '0';
          const escapedPath = escapeHtml(tablePath);
          const supplements = renderDetailObjectEntries(table, tablePath, DETAIL_TABLE_INTERNAL_KEYS);
          return `<div class="focus-detail-table-meta"><span>Showing ${shown} of ${total}</span><span class="focus-detail-table-actions"><button type="button" data-detail-table-page="${escapedPath}" data-page-direction="previous" tabindex="0" ${page === 0 ? 'disabled' : ''}>Previous</button><button type="button" data-detail-table-page="${escapedPath}" data-page-direction="next" tabindex="0" ${page + 1 >= pageCount ? 'disabled' : ''}>Next</button></span></div><div class="focus-detail-table-wrap"><table class="focus-detail-table"><thead><tr>${heading}</tr></thead><tbody>${body}</tbody></table></div>${supplements}`;
        } catch (error) {
          return '<div class="scientific-status">Unavailable: encoded_detail_table_invalid</div>';
        }
      }
      function renderReviewedClassificationContext(value, valuePath) {
        const unavailable = '<div class="scientific-status">Unavailable: reviewed_classification_context_invalid</div>';
        const roleIds = ['direct_crop_confirmed', 'crop_type_qualified', 'anthropogenic_indicator', 'pastoral_indicator', 'ruderal_disturbance_indicator'];
        const totals = value.crop_indicator_totals;
        const count = (number) => Number.isSafeInteger(number) && number >= 0;
        if (value.schema_version !== 'classification-reviewed-context.v1' || value.scope !== 'reviewed_source_context_only'
          || !Array.isArray(totals) || totals.length !== roleIds.length
          || !totals.every((row) => row && roleIds.includes(row.role_id)
            && typeof row.label === 'string' && row.label.trim()
            && count(row.unique_observation_count) && row.pollen_alone_proves === false
            && typeof row.unproven_claim === 'string' && row.unproven_claim.trim())
          || new Set(totals.map((row) => row.role_id)).size !== roleIds.length
          || !count(value.crop_indicator_union_observation_count)
          || !count(value.whole_pollen_category_observation_count)) return unavailable;
        const union = value.crop_indicator_union_observation_count;
        const memberships = totals.reduce((total, row) => total + row.unique_observation_count, 0);
        if (union < Math.max(...totals.map((row) => row.unique_observation_count)) || union > memberships || union > value.whole_pollen_category_observation_count) return unavailable;
        const byRole = new Map(totals.map((row) => [row.role_id, row]));
        const rows = roleIds.map((role) => {
          const row = byRole.get(role);
          return `<tr><th scope="row">${escapeHtml(row.label)}</th><td>${row.unique_observation_count}</td><td>Pollen alone does not prove ${escapeHtml(row.unproven_claim)}.</td></tr>`;
        }).join('');
        const summaryKeys = new Set(['crop_indicator_totals', 'crop_indicator_union_observation_count', 'whole_pollen_category_observation_count']);
        return `<div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>Reviewed crop and indicator context</caption><thead><tr><th scope="col">Evidence category</th><th scope="col">Unique observations</th><th scope="col">Interpretation limit</th></tr></thead><tbody>${rows}</tbody></table></div><p>Unique observations across these categories: ${union}. Categories overlap; do not add their counts.</p><p>Whole-pollen category observations: ${value.whole_pollen_category_observation_count}. These are category memberships, not pollen abundances or cultivation, grazing or other causal proof. Context review alone does not admit a pollen event or LRA input.</p>${renderDetailObjectEntries(value, valuePath, summaryKeys)}`;
      }
      function renderDetailValue(value, valuePath = 'detail') {
        if (value === null || value === undefined || value === '') return '<span>Unavailable</span>';
        if (detailTableShape(value)) return renderDetailTable(value, valuePath);
        if (Array.isArray(value)) {
          if (!value.length) return '<span>No governed rows available.</span>';
          return `<span>${escapeHtml(JSON.stringify(value))}</span>`;
        }
        if (typeof value === 'object') {
          if ((typeof value.schema_version === 'string' && value.schema_version.startsWith('classification-reviewed-context.')) || value.scope === 'reviewed_source_context_only') return renderReviewedClassificationContext(value, valuePath);
          if (value.status === 'unavailable') return `<div class="scientific-status">Unavailable: ${escapeHtml(value.reason_code || 'evidence_not_available')}</div>`;
          return renderDetailObjectEntries(value, valuePath);
        }
        return `<span>${escapeHtml(String(value))}</span>`;
      }
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
  return pollenObservationDiagramData(tabs, true);
}
// Source identity and measurement qualification is independent of the display axis.
function pollenObservationDiagramData(tabs, requireDepth = false) {
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
      if (requireDepth && !pollenDepthFinite(sample.source_depth)) { omit('source_depth_not_numeric'); continue; }
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
  const total = group.rows.length;
  group = {...group, rows:group.rows.filter(row => pollenDepthFinite(row.depth))};
  if (!group.rows.length) return '<p>No observations have numeric source depth. Original values remain in the source table; choose a source age axis explicitly where available.</p>';
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
  return `<figure style="margin:1rem 0"><figcaption><strong>${text(group.variable.source_reported_name)}</strong><br/>${text(pollenDepthGroupLabel(group))}<br/>Native variable semantics: ${text(group.variable.source_semantics)}<br/>Denominator: ${text(group.identity[8])}; status: ${text(group.identity[9])}. ${shown.length} of ${total} individual source observations drawn; ${total-group.rows.length} lack numeric source depth; all remain in the table.${pollenObservationSelectionCaption(group.rows,shown,selection)}</figcaption>${pollenObservationPlotHtml(x,y,marks,{titleId,descriptionId,title:'Native reported observation values versus source depth',description:'Individual exact-source observations, not ecological groups, reconstructed vegetation or percentages calculated from counts. Depth increases downward; values increase rightward. Separate observations at the same sample remain separate, even where marks overlap.',unit:group.identity[4],verticalLabel:"Source depth (unit not supplied)",scrollLabel:"Scrollable native value-depth plot"})}</figure>`;
}
function renderPollenDepthDiagram(tabs, selectedGroupKey = null, renderGroup = (group, ids) => pollenDepthGroupHtml(group,null,null,ids), options = {}) {
  const data = pollenObservationDiagramData(tabs);
  const unavailable = reason => `<section aria-label="Native observation diagrams"><p>Native value-depth diagram unavailable: ${escapeHtml(pollenDepthReasonText(reason))}. Original source tables remain below.</p></section>`;
  if (data.status !== 'available') return unavailable(data.reason);
  const omitted = Object.entries(data.omitted).sort().map(([reason,count]) => `${escapeHtml(pollenDepthReasonText(reason))}: ${count}`).join('; ') || 'none';
  const plotted = data.groups.reduce((total,group) => total + group.rows.length, 0);
  const summary = `<h3>Native reported observations</h3><p>${plotted} of ${data.total} source observations have joinable numeric reported values, in ${data.groups.length} exact source groups. Not charted: ${omitted}. Axis-specific omissions are reported separately. All source tables are unchanged.</p><p>Display only: the anchor fixes native variable, unit, context, dataset and collection. Source element and semantics preserve reported material; no ecological classification is accepted here. No counts are summed or converted to percentages; denominators are not invented. Missing is not zero; separate observation IDs remain separate. Depth units are not supplied. Choose any source-age axis explicitly. No age conversion, interpolation, physical-core equivalence or vegetation inference is made.</p>`;
  if (!data.groups.length) return `<section aria-label="Native observation diagrams">${summary}<p>No source group has drawable values.</p></section>`;
  const chosen = selectedGroupKey === null ? (options.requireExplicitAnchor ? null : data.groups[0]) : data.groups.find(group => group.key === selectedGroupKey);
  if (selectedGroupKey !== null && !chosen) return unavailable('selected_native_source_group_not_available');
  const groupOptions = data.groups.map(group => `<option value="${escapeHtml(group.key)}"${group === chosen ? ' selected="selected"' : ''}>${escapeHtml(pollenDepthGroupLabel(group))}</option>`).join('');
  return `<section aria-label="Native observation diagrams">${summary}<label for="native-value-depth-group">Exact native source group</label><select id="native-value-depth-group" data-pollen-depth-group="true" style="display:block;max-width:100%">${options.requireExplicitAnchor ? `<option value=""${chosen ? '' : ' selected="selected"'}>Choose an exact native source group</option>` : ''}${groupOptions}</select>${chosen ? renderGroup(chosen,options.selectedObservationIds || []) : '<p>Choose a native source group explicitly before drawing panels. No display anchor is inferred from the selected map signal.</p>'}</section>`;
}

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
function renderPollenFocusedSignal(tabs, signal, data = pollenFocusedSignalData(tabs,signal)) {
  const text = value => escapeHtml(pollenDepthText(value));
  const label = signal?.node_level === 'source_taxon' ? `native taxon ${pollenDepthText(signal.source_taxon_id)}; variables ${pollenDepthText(signal.source_variable_ids)}`
    : signal?.node_level === 'source_ecological_code' ? `literal source code ${pollenDepthText(signal.source_ecological_code)}`
    : signal?.node_level === 'source_sample_presence' ? 'sample presence without one selected taxon or ecological code' : 'native source facet unavailable';
  return `<p data-pollen-focused-signal="${data.status}"><strong>Selected map signal:</strong> ${signal ? text(label) : 'none'}; source sample ${text(signal?.source_record_id)}. ${text(data.reason)} ${data.observationIds.length} drawable source observations in ${data.groupKeys.length} native measurement groups match. ${data.unmatchedVariableIds.length} requested variables have no drawable match; ${data.ambiguousObservationIds.length} observation identities or code assignments are ambiguous. Basis: ${data.matchBasisCounts.exact_variable_taxon_unit || 0} exact variable/taxon/unit, ${data.matchBasisCounts.raw_source_code || 0} raw source code, ${data.matchBasisCounts.unique_variable_source_code || 0} uniquely supplied variable code. ${data.anchorStatus === 'ambiguous_measurement_context' ? 'Matching measurement contexts differ; choose a display anchor explicitly.' : ''} Matching groups can contain other source observations. A manual display anchor is separate from the selected map signal; neither literal source codes nor this highlight approve ecological taxonomy or a chronology.</p>`;
}

      const pollenDepthSelections = new WeakMap();
      const pollenAgeSelections = new WeakMap();
      function pollenDisplaySelection(tabs) {
        const signal = focusState?.sourceSignal;
        const owner = signal || tabs;
        const focused = pollenFocusedSignalData(tabs, signal);
        const key = pollenDepthSelections.get(owner) ?? focused.defaultAnchorKey;
        const requireExplicitAnchor = Boolean(signal?.semantic_role === 'source_chronology_context'
          && ['source_taxon','source_ecological_code'].includes(signal.node_level));
        return {owner,signal,focused,key,requireExplicitAnchor};
      }
      function renderPollenObservationDiagram(tabs) {
        const selected = pollenDisplaySelection(tabs);
        const ageKey = pollenAgeSelections.get(selected.owner) ?? null;
        return (selected.signal ? renderPollenFocusedSignal(tabs, selected.signal, selected.focused) : '')
          + renderPollenDepthDiagram(tabs, selected.key,
            (group, ids) => renderPollenAgeDiagram(tabs, group.key, ageKey, false, ids)
              + renderPollenSmallMultiples(tabs, group.key, ageKey, ids),
            {selectedObservationIds:selected.focused.observationIds,requireExplicitAnchor:selected.requireExplicitAnchor});
      }
      let sourceDetailRenderers = null;
      function renderSourceDetailContext(kind, tabs, feature) {
        const tools = currentEvidenceTools();
        if (!tools) return `<p role="status">${escapeHtml(evidenceToolsError || 'Loading source detail context…')} Original source tables remain available below.</p>`;
        sourceDetailRenderers ||= tools.sourceDetails({detailTableShape, decodeDetailTableRow, detailTableText, renderDetailTable, escapeHtml});
        return sourceDetailRenderers[kind](tabs, feature);
      }
      function renderFocusDetail() {
        const focused = document.activeElement;
        const focusedTab = focusTabs.contains(focused) ? focused.dataset.focusTab : null;
        const focusedTable = focusDetail.contains(focused) ? focused.dataset.detailTablePage : null;
        const focusedDirection = focusedTable ? focused.dataset.pageDirection : null;
        const tabs = focusState && focusState.detailTabs ? focusState.detailTabs : unavailableDetailTabs('record_level_evidence_not_available');
        if (!Object.prototype.hasOwnProperty.call(tabs, activeFocusTab)) activeFocusTab = 'overview';
        focusTabs.innerHTML = DETAIL_TAB_DEFINITIONS.map(([key, label]) => `<button id="focus-tab-${key}" class="focus-tab" type="button" role="tab" data-focus-tab="${key}" aria-selected="${String(activeFocusTab === key)}" aria-controls="focus-detail" tabindex="${activeFocusTab === key ? '0' : '-1'}">${escapeHtml(label)}</button>`).join('');
        focusDetail.setAttribute('aria-labelledby', `focus-tab-${activeFocusTab}`);
        const sourceDiagram = activeFocusTab === 'chronology' ? renderAgeDepthDiagram(tabs)
          : activeFocusTab === 'pollen_composition' ? renderPollenObservationDiagram(tabs) : '';
        const sourceOverview = activeFocusTab === 'overview' && tabs.overview?.status !== 'unavailable'
          && focusState?.sourceSignal?.semantic_role === 'source_chronology_context'
          ? renderSourceDetailContext('overview', tabs, focusState.sourceSignal) : '';
        const sampleObservations = activeFocusTab === 'samples' && tabs.overview?.source_family === 'neotoma'
          ? renderSourceDetailContext('samples', tabs) : '';
        const sourceContext = ['neotoma','sead'].includes(tabs.overview?.source_family)
          ? activeFocusTab === 'classification' ? renderSourceDetailContext('classification', tabs)
            : activeFocusTab === 'provenance' ? renderSourceDetailContext('provenance', tabs) : '' : '';
        const relationDetails = activeFocusTab === 'relation' ? renderRelationDetails(tabs.relation) : '';
        focusDetail.innerHTML = sourceOverview + sourceDiagram + relationDetails + renderDetailValue(tabs[activeFocusTab], activeFocusTab) + sampleObservations + sourceContext;
        focusDetail.dataset.detailStatus = tabs[activeFocusTab] && tabs[activeFocusTab].status === 'unavailable' ? 'unavailable' : 'available';
        focusExportButton.disabled = !sourcePollenExportAvailable(focusState);
        focusCopyLinkButton.disabled = focusState?.kind !== 'point' && focusState?.edgeShareable !== true;
        focusExportStatus.textContent = focusExportButton.disabled
          ? 'Pollen record export unavailable: complete sample, chronology and source observation tables are required.'
          : 'Download includes all source observations, samples and chronology claims, including contextual and refused claims. Map time filters do not trim this complete record.';
        if (focusState?.kind === 'edge' && !focusState.edgeShareable) focusExportStatus.textContent += ' Relation link unavailable: a published build and native relation scenario are required.';
        focusTabs.querySelectorAll('[data-focus-tab]').forEach((button) => {
          button.addEventListener('click', () => {
            activeFocusTab = button.dataset.focusTab;
            renderFocusDetail();
          });
        });
        focusDetail.querySelectorAll('[data-detail-table-page]').forEach((button) => {
          button.addEventListener('click', () => {
            const tablePath = button.dataset.detailTablePage;
            if (!tablePath) return;
            const direction = button.dataset.pageDirection === 'previous' ? -1 : 1;
            detailTablePages.set(tablePath, Math.max(0, (detailTablePages.get(tablePath) || 0) + direction));
            renderFocusDetail();
          });
        });
        focusDetail.querySelectorAll('[data-pollen-depth-group]').forEach((select) => {
          select.addEventListener('change', () => {
            const {owner} = pollenDisplaySelection(tabs);
            pollenAgeSelections.delete(owner);
            if (pollenObservationDiagramData(tabs).groups.some(group => group.key === select.value)) {
              pollenDepthSelections.set(owner, select.value);
            } else {
              pollenDepthSelections.delete(owner);
            }
            renderFocusDetail();
            focusDetail.querySelectorAll('[data-pollen-depth-group]')[0]?.focus({ preventScroll: true });
          });
        });
        focusDetail.querySelectorAll('[data-pollen-age-group]').forEach((select) => {
          select.addEventListener('change', () => {
            const native = pollenObservationDiagramData(tabs);
            const selected = pollenDisplaySelection(tabs);
            const nativeKey = selected.key ?? (selected.requireExplicitAnchor ? null : native.groups[0]?.key);
            const choices = nativeKey ? pollenAgeAxisData(tabs, nativeKey).options : [];
            if (select.value && choices.some(option => option.key === select.value)) {
              pollenAgeSelections.set(selected.owner, select.value);
            } else {
              pollenAgeSelections.delete(selected.owner);
            }
            renderFocusDetail();
            focusDetail.querySelectorAll('[data-pollen-age-group]')[0]?.focus({ preventScroll: true });
          });
        });
        if (focusedTab) {
          document.getElementById(`focus-tab-${activeFocusTab}`).focus({ preventScroll: true });
        } else if (focusedTable) {
          const replacement = [...focusDetail.querySelectorAll('[data-detail-table-page]')].find((button) => button.dataset.detailTablePage === focusedTable && button.dataset.pageDirection === focusedDirection && !button.disabled);
          (replacement || focusDetail).focus({ preventScroll: true });
        }
        syncHashState();
      }
      function renderFocusCard() {
        const pointEntry = visiblePointEntryForFocus();
        const edgeVisible = focusState && focusState.kind === 'edge'
          ? availableEdgeFocus(focusState.edgeId, visibleGovernedEdges(), visiblePointEntries) !== null
          : true;
        if (!focusState || !activeLayerKeys.has(focusState.layerKey) || (focusState.kind === 'point' && !pointEntry) || !edgeVisible) {
          if (focusState?.kind === 'edge') {
            focusState = null;
            pendingEdgeFocus = null;
            edgeFocusLoadState.request++;
            activeFocusTab = 'overview';
            focusCopyLinkButton.disabled = true;
            focusExportButton.disabled = true;
          }
          const containedFocus = focusCard.contains(document.activeElement);
          focusCard.hidden = true;
          focusSourceLink.hidden = true;
          focusPreviousButton.disabled = true;
          focusNextButton.disabled = true;
          focusTabs.innerHTML = '';
          focusDetail.innerHTML = '';
          if (containedFocus) restoreFocusFromCard();
          return;
        }
        focusCard.hidden = false;
        if (pointEntry) {
          highlightPointEntry(pointEntry);
        }
        focusTitle.textContent = focusState.title;
        focusSubtitle.textContent = focusState.subtitle;
        focusMeta.innerHTML = focusState.meta.map((row) => `<div class="focus-meta-row"><span class="focus-meta-label">${escapeHtml(row.label)}</span><span class="focus-meta-value">${escapeHtml(row.value)}</span></div>`).join('');
        renderFocusDetail();
        focusSourceLink.textContent = focusState.sourceLabel || 'Open source';
        focusSourceLink.hidden = !focusState.sourceUrl;
        focusSourceLink.href = focusState.sourceUrl || '#';
        const canStep = focusState.kind === 'point' && visiblePointEntries.length > 1;
        focusPreviousButton.disabled = !canStep;
        focusNextButton.disabled = !canStep;
      }
      async function focusPointAtVisibleIndex(index) {
        const entry = visiblePointEntries[index];
        if (!entry) return;
        const coordinates = featureCoordinatePair(entry.feature);
        if (!coordinates) return;
        const identity = pointFocusIdentity(entry.layer, entry.feature);
        if (!identity) return;
        const mediaLinks = normalizedMediaLinks(entry.feature.media_links);
        const primaryAction = entry.feature.source_url
          ? { label: 'Open source', url: entry.feature.source_url }
          : (mediaLinks[0] ? { label: `Open ${mediaLinks[0].kind === 'video' ? 'video' : 'media'}`, url: mediaLinks[0].url } : null);
        const meta = [
          { label: 'Layer', value: entry.layer.label },
          { label: 'Country', value: entry.feature.country || 'Unassigned' },
          { label: 'Coordinates', value: coordinateLabel(entry.feature, 4) },
        ];
        if (entry.neighborContext) meta.unshift({ label: 'Display role', value: 'Retained cross-border neighbor context' });
        const timeDescriptor = featureTimeDescriptor(entry.feature);
        if (timeDescriptor) meta.splice(2, 0, timeDescriptor);
        const nextFocus = {
          kind: 'point',
          ...identity,
          title: entry.feature.title || entry.layer.label,
          subtitle: entry.neighborContext
            ? `Neighbor context · ${entry.feature.country} · ${entry.feature.subtitle || 'Point record'}`
            : (entry.feature.subtitle || 'Point record'),
          meta,
          sourceUrl: primaryAction ? primaryAction.url : '',
          sourceLabel: primaryAction ? primaryAction.label : 'Open source',
          latitude: coordinates.latitude,
          longitude: coordinates.longitude,
          sourceSignal: entry.feature,
          detailTabs: unavailableDetailTabs('detail_record_loading'),
        };
        setFocusState(nextFocus);
        const request = edgeFocusLoadState.request;
        const toolsReady = loadEvidenceTools().catch(() => null);
        const detailTabs = await detailTabsForFeature(entry.feature);
        if (
          focusState
          && focusState.kind === 'point'
          && focusState.layerKey === nextFocus.layerKey
          && focusState.featureKey === nextFocus.featureKey
          && focusState.recordId === nextFocus.recordId
          && edgeFocusLoadState.request === request
          && visiblePointEntryForFocus(focusState)
        ) {
          focusState = { ...focusState, detailTabs };
          renderFocusDetail();
        }
        await toolsReady;
        if (focusState?.kind === 'point' && edgeFocusLoadState.request === request
          && focusState.layerKey === nextFocus.layerKey && focusState.featureKey === nextFocus.featureKey
          && focusState.recordId === nextFocus.recordId && visiblePointEntryForFocus(focusState)) renderFocusDetail();
      }
      function countActiveOverrides() {
        let count = 0;
        if (activeCountries.size !== COUNTRIES.length) count += 1;
        if (activeLayerKeys.size !== DEFAULT_LAYER_KEYS.length || DEFAULT_LAYER_KEYS.some((key) => !activeLayerKeys.has(key))) count += 1;
        if (scientificPinValues.length || activeScientificSignalIds.size !== DEFAULT_SCIENTIFIC_SIGNAL_IDS.length || DEFAULT_SCIENTIFIC_SIGNAL_IDS.some((signalId) => !activeScientificSignalIds.has(signalId))) count += 1;
        if (activeCountryPair !== 'all') count += 1;
        count += relationFilterFields().filter(([key]) => activeRelationFilters[key] !== null || activeRelationFilters.invalid.includes(key)).length;
        if (activeRelationEventDefinition.value !== null || activeRelationEventDefinition.invalid) count += 1;
        if (crossBorderOnly) count += 1;
        if (activeAnimalSpecies !== 'all') count += 1;
        if (activeAnimalScope !== 'all') count += 1;
        if (activeAnimalConfidence !== 'all') count += 1;
        if (activeAnimalTemporalWindow !== 'all') count += 1;
        if (animalNordicOnly) count += 1;
        if (TIME_HAS_DATA && (timeStartBp !== DEFAULT_TIME_START_BP || timeIntervalYears !== DEFAULT_TIME_INTERVAL_YEARS)) count += 1;
        if (Number(slider.value) !== 20) count += 1;
        if (Math.round(densityOpacity * 100) !== 60) count += 1;
        if (currentBasemap !== DEFAULT_BASEMAP) count += 1;
        return count;
      }
      function renderControlPanelSummary() {
        if (!controlPanelSummary) return;
        const activeOverrideCount = countActiveOverrides();
        controlPanelSummary.textContent = activeOverrideCount ? `${activeOverrideCount} active overrides` : 'Default view';
      }
      function renderCountryControls() {
        const pointCountsByCountry = Object.fromEntries(
          COUNTRIES.map((country) => [
            country,
            visiblePointEntries.filter(({ feature, neighborContext }) => !neighborContext && feature.country === country).length,
          ])
        );
        countryFilters.innerHTML = COUNTRIES.map((country) => {
          const style = countryStyle(country);
          const checked = activeCountries.has(country) ? 'checked' : '';
          return `<label class="chip-toggle"><input class="country-checkbox" type="checkbox" value="${escapeHtml(country)}" ${checked} aria-label="Toggle ${escapeHtml(country)}"><span class="chip-swatch" style="background:${escapeHtml(style.fill)};border-color:${escapeHtml(style.stroke)};"></span><span>${escapeHtml(country)}</span><span class="chip-count">${escapeHtml(String(pointCountsByCountry[country] || 0))}</span></label>`;
        }).join('');
        document.querySelectorAll('.country-checkbox').forEach((checkbox) => {
          checkbox.addEventListener('change', () => {
            if (checkbox.checked) { activeCountries.add(checkbox.value); } else { activeCountries.delete(checkbox.value); }
            renderMapState();
          });
        });
      }
      function renderScientificControls() {
        const available = ATLAS_EVIDENCE.classifications_status === 'available' && SCIENTIFIC_SIGNALS.length > 0;
        const sourceChronologyAvailable = sourceChronologyLayers().length > 0;
        scientificActions.hidden = !available;
        sourceChronologyShortcuts.hidden = !sourceChronologyAvailable;
        sourceChronologyShortcuts.querySelectorAll('[data-source-shortcut]').forEach((button) => {
          button.disabled = !sourceChronologyAvailable;
        });
        const presetLayer = sourceChronologyLayers().find((layer) => layer.node_level === 'source_taxon') || null;
        if (presetLayer) {
          sourceChronologyShortcuts.querySelectorAll('[data-source-preset]').forEach((button) => {
            button.disabled = false;
            button.classList.toggle('is-primary', button.dataset.sourcePreset === activeSourceChronologyPreset);
            button.setAttribute('aria-pressed', String(button.dataset.sourcePreset === activeSourceChronologyPreset));
          });
        }
        scientificStatus.textContent = available
          ? 'Only accepted, versioned classifications are selectable. Color is always paired with a shape cue.'
          : sourceChronologyAvailable
            ? 'Harmonized scientific classifications are awaiting qualified review. Source-native pollen-bearing sample presence, ecological-code, and exact-label chronology remains available below without asserting equivalence.'
            : 'Harmonized scientific classifications are awaiting qualified review. This scope has no source-native pollen chronology layers.';
        if (available) renderScientificPickerPanel(); else scientificFilters.innerHTML = '';
        scientificSummary.textContent = available
          ? `${activeScientificSignalIds.size} of ${SCIENTIFIC_SIGNALS.length} accepted signals selected`
          : sourceChronologyAvailable ? 'Source-native views available' : 'Accepted classifications unavailable';
      }
      function resetScientificPins() {
        scientificPinValues = []; scientificPinnedIds = null;
        scientificPickerController?.clearSearch(); scientificPickerStatus = 'not_loaded';
      }
      function scientificPickerMetadata() {
        return {pinned_ids: scientificPinnedIds === null ? null : [...scientificPinnedIds], requested_pin_values: [...scientificPinValues], status: scientificPickerStatus};
      }
      function scientificPickerSelection(tools) {
        scientificCatalog ||= tools.pickerCatalog(SCIENTIFIC_SIGNALS);
        const result = tools.pickerInitial(scientificCatalog, [...activeScientificSignalIds], scientificPinnedIds === null ? scientificPinValues : [JSON.stringify(scientificPinnedIds)]);
        scientificPickerStatus = result.error ? 'unavailable' : 'available';
        if (!result.error) scientificPinnedIds = result.state.pinnedIds;
        return result;
      }
      function renderScientificPickerPanel() {
        const panel = document.getElementById('scientific-controls'), tools = currentEvidenceTools();
        if (!panel.open) return;
        if (!tools) {
          scientificFilters.textContent = evidenceToolsError || 'Loading supplied scientific signals…';
          scientificPickerStatus = evidenceToolsError ? 'unavailable' : 'not_loaded';
          return;
        }
        scientificCatalog ||= tools.pickerCatalog(SCIENTIFIC_SIGNALS);
        scientificPickerController ||= tools.pickerMount(scientificFilters, scientificCatalog, {
          read: () => scientificPickerSelection(tools),
          change: state => {
            scientificPinnedIds = state.pinnedIds;
            scientificPinValues = [JSON.stringify(scientificPinnedIds)];
            activeScientificSignalIds = new Set(state.visibleIds);
            renderMapState();
          },
          reset: () => { resetScientificPins(); renderMapState(); }
        });
        scientificPickerController.render();
      }
      function visibleGovernedEdges() {
        const definitions = new Set(relationEventDefinitionSelection(GOVERNED_EDGE_RECORDS, activeRelationEventDefinition).selected);
        return relationFilterSelection(GOVERNED_EDGE_RECORDS, activeRelationFilters).selected
          .filter((edge) => definitions.has(edge) && atlasEdgeVisible(edge, activeCountries, activeCountryPair, crossBorderOnly, activeScientificSignalIds));
      }
      function isRetainedNeighborContext(layer, feature) {
        return Boolean(
          layer.applies_country_filter
          && !activeCountries.has(feature.country)
          && retainedNeighborRecordCountries.get(String(feature.record_id)) === feature.country
        );
      }
      function renderRelationControls() {
        const selection = relationFilterSelection(GOVERNED_EDGE_RECORDS, activeRelationFilters);
        const definitions = relationEventDefinitionSelection(GOVERNED_EDGE_RECORDS, activeRelationEventDefinition);
        const definitionRows = new Set(definitions.selected);
        const matchedCount = selection.selected.filter(row => definitionRows.has(row)).length;
        const available = !STATIC_ATLAS_INLINE && STATIC_ATLAS_CHUNKS.edges.status === 'available';
        const sequencePosture = STATIC_ATLAS_INLINE || STATIC_ATLAS_CHUNKS.sequences.status === 'unavailable'
          ? `sequences unavailable: ${STATIC_ATLAS_INLINE ? 'governed_sequence_detail_model_not_available' : STATIC_ATLAS_CHUNKS.sequences.reason_code}`
          : `${GOVERNED_SEQUENCE_RECORDS.length} governed sequences available`;
        countryPairFilter.disabled = !available;
        crossBorderOnlyCheckbox.disabled = !available;
        crossBorderOnlyCheckbox.checked = crossBorderOnly;
        relationFilterFields().forEach(([key, , , label]) => {
          const control = relationFilterControls[key];
          control.disabled = !available;
          control.innerHTML = relationFilterOptions(selection.catalog[key], activeRelationFilters[key], selection.unavailable.includes(key), label);
        });
        relationEventDefinitionControl.disabled = !available;
        relationEventDefinitionControl.innerHTML = renderRelationEventDefinitionOptions(definitions, activeRelationEventDefinition);
        relationEventDefinitionStatus.textContent = `${definitions.availableCount} rows with supplied definitions; ${definitions.missingCount} missing; ${definitions.conflictingCount} conflicting of ${definitions.retainedCount} retained rows. ${definitions.unavailable ? 'Shared event definition unavailable; no fallback.' : 'All retained keeps unavailable rows; a specific definition excludes them.'} This selects supplied events, without reclassification.`;
        relationFilterStatus.innerHTML = (selection.unavailable.length
          ? '<p>Shared relation filter unavailable: no retained native value matches the selection. No fallback selection is applied.</p>' : '')
          + `<p>${matchedCount} of ${GOVERNED_EDGE_RECORDS.length} retained relations match the event definition, scenario, status and stored endpoint-country selections. Nonselected records, including any refusal context, remain retained.</p>`
          + relationScenarioThresholds(GOVERNED_EDGE_RECORDS, activeRelationFilters.scenario);
        countryPairFilter.innerHTML = '<option value="all">All country pairs</option>' + COUNTRY_PAIR_KEYS.map((key) => `<option value="${escapeHtml(key)}" ${activeCountryPair === key ? 'selected' : ''}>${escapeHtml(key.replace('|', ' ↔ '))}</option>`).join('');
        relationSummary.textContent = available
          ? `${visibleGovernedEdges().length} of ${GOVERNED_EDGE_ELIGIBILITY_COUNT} retained rows matched by country/signal/relation filters, before endpoint time/layer/viewport display eligibility (retained denominator) · Showing ${edgeRenderSummary.shown} of ${edgeRenderSummary.viewport_count} loaded display-eligible viewport candidates (display limit ${edgeRenderSummary.limit}) · ${sequencePosture}${edgeRenderSummary.shown < edgeRenderSummary.viewport_count ? ' · Zoom in or narrow country and signal filters to inspect other candidates.' : ''}`
          : `Candidates unavailable: ${STATIC_ATLAS_INLINE ? 'governed_map_edge_model_not_available' : STATIC_ATLAS_CHUNKS.edges.reason_code} · ${sequencePosture}`;
        relationSummary.dataset.sequenceStatus = STATIC_ATLAS_INLINE ? 'unavailable' : STATIC_ATLAS_CHUNKS.sequences.status;
        relationSummary.dataset.filterMatchedCandidateCount = String(visibleGovernedEdges().length);
        relationSummary.dataset.admittedCandidateCount = String(GOVERNED_EDGE_ELIGIBILITY_COUNT);
        relationSummary.dataset.renderedCandidateCount = String(edgeRenderSummary.shown);
        relationSummary.dataset.viewportCandidateCount = String(edgeRenderSummary.viewport_count);
        relationSummary.dataset.renderLimit = String(edgeRenderSummary.limit);
      }
      function selectSourceChronologyLevel(level) {
        const layer = sourceChronologyLayerForLevel(level);
        if (!layer) return false;
        stopTimePlayback();
        if (activeSourceChronologyLevel !== layer.node_level) sourceRecordConcentrationActive = false;
        activeSourceChronologyLevel = layer.node_level;
        if (layer.node_level !== 'source_taxon') activeSourceChronologyPreset = 'none';
        sourceChronologyLayers().forEach((candidate) => activeLayerKeys.delete(candidate.key));
        activeLayerKeys.add(layer.key);
        return true;
      }
      function focusSourceChronologyNavigation() {
        const sourceExtent = sourceChronologyPlaybackSelection();
        if (!sourceExtent) return false;
        const sourceSpan = Math.max(1, sourceExtent.time_max_bp - sourceExtent.time_min_bp);
        timeIntervalYears = Math.min(sourceSpan, sourceSpan <= 2500 ? 100 : (sourceSpan <= 10000 ? 500 : 1000));
        timeStartBp = oldestPlaybackStart(timeIntervalYears, sourceExtent);
        return true;
      }
      function toggleLayerSelection(layerKey, enabled) {
        const layer = ALL_LAYERS.find((candidate) => candidate.key === layerKey);
        if (!layer) return false;
        if (enabled && layer.semantic_role === 'source_chronology_context') {
          return selectSourceChronologyLevel(layer.node_level);
        }
        if (enabled) activeLayerKeys.add(layer.key); else activeLayerKeys.delete(layer.key);
        if (!enabled && layer.semantic_role === 'source_chronology_context') {
          stopTimePlayback();
          sourceRecordConcentrationActive = false;
        }
        return true;
      }
      function renderSourceTimeDensity(layer, facet) {
        if (!layer || !facet || !sourceChronologyTimeDensityIsValid(facet.time_density, facet)) {
          sourceTimeDensity.hidden = true;
          sourceTimeDensityBars.innerHTML = '';
          sourceTimeDensityBars.removeAttribute('aria-label');
          return;
        }
        const density = facet.time_density;
        const bins = density.bins;
        const maximum = Math.max(0, ...bins.map((row) => row.node_count));
        const facetLabel = sourceRecordConcentrationFacetLabel(layer);
        sourceTimeDensity.hidden = false;
        sourceTimeDensityCaption.textContent = `${facetLabel} · oldest-to-present source-record density`;
        sourceTimeDensityBars.style.gridTemplateColumns = `repeat(${Math.max(1, bins.length)}, minmax(4px, 1fr))`;
        sourceTimeDensityBars.setAttribute(
          'aria-label',
          `${facetLabel}: ${density.node_count} source nodes and ${density.observation_denominator} contributing observations across ${bins.length} non-additive closed-overlap bins, oldest to present.`
        );
        sourceTimeDensityBars.innerHTML = bins.map((row) => {
          const height = maximum === 0 ? 3 : Math.max(3, Math.round((row.node_count / maximum) * 100));
          const label = `[${row.younger_bp}, ${row.older_bp}] BP: ${row.node_count} source nodes; ${row.observation_denominator} contributing observations`;
          return `<span class="source-time-density-bar" style="height:${height}%" role="img" aria-label="${escapeHtml(label)}" title="${escapeHtml(label)}"></span>`;
        }).join('');
      }
      function renderSourceChronologyControls() {
        const layers = sourceChronologyLayers();
        const selectedLayer = sourceChronologyLayerForLevel(activeSourceChronologyLevel);
        sourceChronologyControls.hidden = layers.length === 0;
        if (!layers.length || !selectedLayer) {
          sourceRecordConcentrationToggle.disabled = true;
          sourceChronologySummary.textContent = 'Source facets unavailable';
          sourceChronologyState.textContent = 'Source chronology controls remain unavailable because governed facet metadata is absent or invalid.';
          sourceChronologyGlobalDenominator.textContent = 'Global pre-filter denominator unavailable.';
          renderSourceTimeDensity(null, null);
          return;
        }
        sourceChronologyLevel.innerHTML = layers.map((layer) => `<option value="${escapeHtml(layer.node_level)}" ${layer.node_level === activeSourceChronologyLevel ? 'selected' : ''}>${escapeHtml(SOURCE_CHRONOLOGY_LEVEL_LABELS[layer.node_level])}</option>`).join('');
        const codeRows = selectedLayer.node_level === 'source_ecological_code' ? selectedLayer.facet_metadata.source_ecological_codes : [];
        const validCodes = ['all', ...codeRows.map((row) => row.value)];
        activeSourceChronologyCode = normalizedSingleValue(activeSourceChronologyCode, validCodes, 'all');
        sourceChronologyCodeFields.hidden = selectedLayer.node_level !== 'source_ecological_code';
        sourceChronologyCode.innerHTML = '<option value="all">All literal source codes</option>' + codeRows.map((row) => `<option value="${escapeHtml(row.value)}" ${row.value === activeSourceChronologyCode ? 'selected' : ''}>${escapeHtml(row.label)} · ${row.node_count} nodes · ${row.observation_denominator} observations</option>`).join('');
        const taxonRows = selectedLayer.node_level === 'source_taxon' ? selectedLayer.facet_metadata.source_taxa : [];
        const validTaxa = ['all', ...taxonRows.map((row) => row.value)];
        activeSourceChronologyTaxon = normalizedSingleValue(activeSourceChronologyTaxon, validTaxa, 'all');
        const presetRows = selectedLayer.node_level === 'source_taxon'
          ? selectedLayer.facet_metadata.source_label_preset_accountability.presets
          : [];
        activeSourceChronologyPreset = normalizedSingleValue(activeSourceChronologyPreset, ['none', ...presetRows.map((row) => row.key)], 'none');
        if (activeSourceChronologyTaxon !== 'all') activeSourceChronologyPreset = 'none';
        const selectedPreset = sourceChronologyPresetForSelection(selectedLayer, activeSourceChronologyPreset);
        const selectedPresetTaxonIds = new Set(selectedPreset?.member_taxon_ids || []);
        const query = sourceChronologyTaxonSearch.trim().toLowerCase();
        const queryAlternatives = query
          .split('|')
          .map((alternative) => alternative.trim().split(/\s+/).filter(Boolean))
          .filter((alternative) => alternative.length);
        const visibleTaxa = taxonRows.filter((row) => (
          row.value === activeSourceChronologyTaxon
          || selectedPresetTaxonIds.has(Number(row.source_taxon_id))
          || !queryAlternatives.length
          || queryAlternatives.some((alternative) => {
            const searchable = `${row.label} ${row.source_taxon_id}`.toLowerCase();
            return alternative.every((token) => searchable.includes(token));
          })
        ));
        sourceChronologyTaxonFields.hidden = selectedLayer.node_level !== 'source_taxon';
        sourceLabelPresetControls.innerHTML = presetRows.map((row) => `<button class="inline-button ${row.key === activeSourceChronologyPreset ? 'is-primary' : ''}" type="button" data-source-label-preset="${escapeHtml(row.key)}" aria-pressed="${String(row.key === activeSourceChronologyPreset)}">${escapeHtml(row.label)} · ${row.member_taxon_count} IDs · ${row.site_count} sites · ${row.node_count} nodes</button>`).join('');
        sourceLabelPresetState.textContent = selectedPreset
          ? `${selectedPreset.label}: exact union of ${selectedPreset.member_taxon_count} governed Neotoma taxon IDs · ${selectedPreset.site_count} unique sites · ${selectedPreset.node_count} nodes · ${selectedPreset.observation_denominator} contributing observations · literal labels only; not an accepted classification, abundance surface, flow, or propagation.`
          : 'No source-label preset selected. Exact source labels remain individually selectable; presets are literal exact-ID unions, not accepted classifications.';
        sourceLabelPresetControls.querySelectorAll('[data-source-label-preset]').forEach((button) => {
          button.addEventListener('click', () => {
            stopTimePlayback();
            activeSourceChronologyPreset = button.dataset.sourceLabelPreset === activeSourceChronologyPreset
              ? 'none'
              : normalizedSingleValue(button.dataset.sourceLabelPreset, ['none', ...presetRows.map((row) => row.key)], 'none');
            activeSourceChronologyTaxon = 'all';
            sourceChronologyTaxonSearch = '';
            sourceChronologyTaxonQuery.value = '';
            sourceRecordConcentrationActive = false;
            focusSourceChronologyNavigation();
            renderMapState();
          });
        });
        sourceChronologyTaxon.innerHTML = `<option value="all">All source-reported labels · ${taxonRows.length} facets</option>` + visibleTaxa.map((row) => `<option value="${escapeHtml(row.value)}" ${row.value === activeSourceChronologyTaxon ? 'selected' : ''}>${escapeHtml(row.label)} · source taxon ${escapeHtml(row.source_taxon_id)} · ${row.node_count} nodes · ${row.observation_denominator} observations</option>`).join('');
        sourceChronologyTaxonShortcuts.innerHTML = queryAlternatives.length
          ? visibleTaxa.map((row) => `<button class="inline-button ${row.value === activeSourceChronologyTaxon ? 'is-primary' : ''}" type="button" data-source-taxon-facet="${escapeHtml(row.value)}">${escapeHtml(row.label)} · ${escapeHtml(row.source_taxon_id)}</button>`).join('')
          : '';
        sourceChronologyTaxonShortcuts.querySelectorAll('[data-source-taxon-facet]').forEach((button) => {
          button.addEventListener('click', () => {
            stopTimePlayback();
            activeSourceChronologyTaxon = normalizedSingleValue(
              button.dataset.sourceTaxonFacet,
              validTaxa,
              'all'
            );
            activeSourceChronologyPreset = 'none';
            sourceRecordConcentrationActive = false;
            focusSourceChronologyNavigation();
            renderMapState();
          });
        });
        const selectedFacet = sourceChronologyFacetForSelection(selectedLayer, activeSourceChronologyCode, activeSourceChronologyTaxon);
        if (!selectedFacet) {
          sourceRecordConcentrationToggle.disabled = true;
          sourceChronologySummary.textContent = 'Source facet unavailable';
          sourceChronologyState.textContent = 'The selected source facet is absent from governed metadata; no source chronology records are shown.';
          sourceChronologyGlobalDenominator.textContent = 'Global pre-filter denominator unavailable.';
          renderSourceTimeDensity(null, null);
          return;
        }
        renderSourceTimeDensity(selectedLayer, selectedFacet);
        const unitCount = selectedLayer.facet_metadata.source_unit_counts.length;
        const untimedExclusion = sourceChronologyUntimedExclusion(selectedLayer);
        const extentLabel = `[${selectedFacet.time_min_bp}, ${selectedFacet.time_max_bp}] BP`;
        const visibleSourceEntries = visiblePointEntries.filter(({ layer, neighborContext }) => !neighborContext && layer.key === selectedLayer.key);
        const visibleObservationCounts = visibleSourceEntries.map(({ feature }) => sourceChronologyCount(feature.observation_denominator));
        const visibleObservationDenominator = visibleObservationCounts.every((count) => count !== null)
          ? visibleObservationCounts.reduce((total, count) => total + count, 0)
          : null;
        const visibleObservationLabel = visibleObservationDenominator === null ? 'unavailable' : String(visibleObservationDenominator);
        const activeWindowLabel = `[${timeStartBp}, ${timeWindowEndBp()}] BP`;
        const untimedLabel = untimedExclusion.status === 'available'
          ? untimedExclusion.split_status === 'available'
            ? `${untimedExclusion.count} source nodes without admitted numeric chronology excluded (${untimedExclusion.absent_count} absent, ${untimedExclusion.refused_count} refused, ${untimedExclusion.contextual_count} contextual)`
            : `${untimedExclusion.count} source nodes without admitted numeric chronology excluded; absent/refused/contextual split unavailable for this legacy report`
          : 'source-node count without admitted numeric chronology unavailable for this exact filtered selection';
        sourceChronologySummary.textContent = `${visibleSourceEntries.length} of ${selectedFacet.node_count} nodes visible · ${selectedFacet.site_count} unique sites · ${activeWindowLabel}`;
        const concentrationEligible = sourceRecordConcentrationSelection(selectedLayer) !== null;
        sourceRecordConcentrationToggle.disabled = !concentrationEligible;
        sourceRecordConcentrationToggle.setAttribute('aria-pressed', String(sourceRecordConcentrationActive));
        sourceRecordConcentrationToggle.textContent = sourceRecordConcentrationActive
          ? 'Hide captured source-record concentration'
          : 'Show captured source-record concentration';
        sourceRecordConcentrationToggle.title = concentrationEligible
          ? 'Group admitted records at identical source sites without interpolation or value weighting.'
          : 'Choose exactly one active source level and, for code or taxon views, one exact source facet.';
        const countryAccountability = selectedFacet.country_counts.map((row) => `${row.country_code}: ${row.site_count} sites / ${row.node_count} nodes / ${row.observation_denominator} observations`).join(' · ');
        sourceChronologyGlobalDenominator.textContent = `Global pre-filter denominator: ${selectedFacet.site_count} unique sites, ${selectedFacet.node_count} source nodes, and ${selectedFacet.observation_denominator} contributing observations for ${sourceRecordConcentrationFacetLabel(selectedLayer)} · ${countryAccountability} · ${untimedLabel}.`;
        if (sourceRecordConcentrationActive && sourceRecordConcentrationSnapshot?.status === 'available') {
          const snapshot = sourceRecordConcentrationSnapshot;
          const countryLabel = activeCountries.size ? [...activeCountries].sort().join(', ') : 'no active countries';
          sourceChronologyState.textContent = `${snapshot.site_count} sites · ${snapshot.visible_node_count} raw visible source nodes · ${snapshot.visible_observation_denominator} contributing observations · current viewport · [${timeStartBp}, ${timeWindowEndBp()}] BP · ${countryLabel} · ${sourceRecordConcentrationFacetLabel(selectedLayer)} · captured source-record concentration only`;
        } else if (sourceRecordConcentrationActive && sourceRecordConcentrationSnapshot?.status === 'refused') {
          sourceChronologyState.textContent = `${sourceRecordConcentrationSnapshot.reason} No concentration symbols were rendered.`;
        } else {
          sourceChronologyState.textContent = `${visibleSourceEntries.length} source nodes and ${visibleObservationLabel} contributing observations visible in ${activeWindowLabel} · ${selectedFacet.site_count} unique sites, ${selectedFacet.node_count} nodes, and ${selectedFacet.observation_denominator} observations in the global selected-facet denominator before country and BP-window filters · ${unitCount} literal source units · source playback extent ${extentLabel} · ${untimedLabel} · chronology context only`;
        }
      }
      function refreshTimeStepperStatus() {
        if (!TIME_HAS_DATA) {
          timeStepperStatus.disabled = true;
          timeStepperStatus.textContent = 'No BP chronology available';
          return;
        }
        const layers = sourceChronologyLayers();
        timeStepperStatus.disabled = false;
        timeStepperStatus.setAttribute('aria-controls', layers.length ? 'source-chronology-controls' : 'time-controls');
        timeStepperStatus.title = layers.length ? 'Open source chronology controls' : 'Open temporal window controls';
        const selectedLayer = sourceChronologyLayerForLevel(activeSourceChronologyLevel);
        const activeWindow = `[${timeStartBp}, ${timeWindowEndBp()}] BP`;
        if (layers.length === 0) {
          timeStepperStatus.textContent = `Complete atlas chronology · ${activeWindow} · choose a shorter span to explore change`;
          return;
        }
        if (!selectedLayer || !activeLayerKeys.has(selectedLayer.key)) {
          timeStepperStatus.textContent = `Source chronology off · ${activeWindow} · complete atlas extent`;
          return;
        }
        const selectedFacet = sourceChronologyFacetForSelection(selectedLayer, activeSourceChronologyCode, activeSourceChronologyTaxon);
        if (!selectedFacet) {
          timeStepperStatus.textContent = `Selected source facet unavailable · ${activeWindow}`;
          return;
        }
        let visibleNodeCount;
        let visibleObservationDenominator;
        if (sourceRecordConcentrationActive && sourceRecordConcentrationSnapshot?.status === 'available') {
          visibleNodeCount = sourceRecordConcentrationSnapshot.visible_node_count;
          visibleObservationDenominator = sourceRecordConcentrationSnapshot.visible_observation_denominator;
        } else {
          const visible = visiblePointEntries.filter(({ layer, neighborContext }) => !neighborContext && layer.key === selectedLayer.key);
          visibleNodeCount = visible.length;
          const observationCounts = visible.map(({ feature }) => sourceChronologyCount(feature.observation_denominator));
          visibleObservationDenominator = observationCounts.every((count) => count !== null)
            ? observationCounts.reduce((total, count) => total + count, 0)
            : null;
        }
        const visibleObservationLabel = visibleObservationDenominator === null ? 'unavailable' : visibleObservationDenominator;
        timeStepperStatus.textContent = `${sourceRecordConcentrationFacetLabel(selectedLayer)} · ${visibleNodeCount}/${selectedFacet.node_count} nodes · ${visibleObservationLabel}/${selectedFacet.observation_denominator} observations · ${activeWindow}`;
      }
      function renderLayerControls() {
        layerFilters.innerHTML = LAYER_GROUP_DEFINITIONS
          .map((group) => {
            const layers = ALL_LAYERS.filter((layer) => layer.group === group.key);
            if (!layers.length) return '';
            const cards = layers.map((layer) => {
              const checked = activeLayerKeys.has(layer.key) ? 'checked' : '';
              const sourceChronologyInvalid = layer.semantic_role === 'source_chronology_context' && !sourceChronologyLayerIsValid(layer);
              const animalChronologyInvalid = isAnimalSourceChronologyLayer(layer) && !animalSourceChronologyLayerIsValid(layer);
              const swatchColor = layerColor(layer);
              const swatchBorder = layer.style && layer.style.stroke ? layer.style.stroke : swatchColor;
              return `<label class="dock-layer-chip"><input class="layer-checkbox" type="checkbox" value="${escapeHtml(layer.key)}" ${checked} ${sourceChronologyInvalid || animalChronologyInvalid ? 'disabled' : ''} aria-label="Toggle ${escapeHtml(layer.label)}"><span class="chip-swatch" style="background:${escapeHtml(swatchColor)};border-color:${escapeHtml(swatchBorder)};"></span><span>${escapeHtml(layer.label)}</span></label>`;
            }).join('');
            return `<div class="legend-group"><div class="legend-group-label">${escapeHtml(group.label)}</div><div class="dock-layer-grid">${cards}</div></div>`;
          })
          .join('');
        dockLayerSummary.textContent = activeLayerKeys.size ? `${activeLayerKeys.size} layers enabled` : 'No layers enabled';
        document.querySelectorAll('.layer-checkbox').forEach((checkbox) => {
          checkbox.addEventListener('change', () => {
            const layer = ALL_LAYERS.find((candidate) => candidate.key === checkbox.value);
            if (!toggleLayerSelection(checkbox.value, checkbox.checked)) return;
            if (layer && layer.semantic_role === 'source_chronology_context') renderLayerControls();
            renderMapState();
          });
        });
      }
      function renderAnimalEvidencePanel(metrics) {
        if (!animalEvidenceMetrics || !animalEvidenceConfidence || !animalEvidenceState) return;
        const confidenceEntries = Object.entries(metrics.confidenceCounts).sort((left, right) => right[1] - left[1]);
        animalEvidenceMetrics.innerHTML = [
          { value: metrics.visibleAtlasEvidenceEntries.length, label: 'Visible atlas evidence points' },
          { value: metrics.visibleSourceChronologyEntries.length, label: 'Visible source chronology points' },
          { value: metrics.visibleSpecies.size, label: 'Visible species' },
          { value: metrics.candidateEntries.length - metrics.visibleEntries.length, label: 'Filtered out by current posture' },
        ]
          .map((item) => `<div class="animal-insight-stat"><span class="animal-insight-stat-value">${escapeHtml(String(item.value))}</span><span class="animal-insight-stat-label">${escapeHtml(item.label)}</span></div>`)
          .join('');
        animalEvidenceConfidence.innerHTML = confidenceEntries.length
          ? confidenceEntries
              .map(([confidence, count]) => `<span class="animal-insight-chip"><span>${escapeHtml(formatCoordinateConfidence(confidence))}</span><strong>${escapeHtml(String(count))}</strong></span>`)
              .join('')
          : '<span class="animal-insight-copy">No animal points remain visible under the current filter state.</span>';
        animalEvidenceState.textContent = metrics.activeFilters.length
          ? metrics.activeFilters.join(' · ')
          : 'Default animal posture';
      }
      function renderAnimalControls() {
        if (!ANIMAL_SPECIES.length) {
          animalFilterSummary.textContent = 'No mapped animal evidence shipped';
          animalScopeFilters.innerHTML = '<span class="search-meta">No mapped animal layers available.</span>';
          animalSpeciesFilters.innerHTML = '';
          animalConfidenceFilters.innerHTML = '';
          animalTemporalWindowFilters.innerHTML = '';
          animalEvidenceMetrics.innerHTML = '';
          animalEvidenceConfidence.innerHTML = '<span class="animal-insight-copy">No mapped animal points are available in this bundle.</span>';
          animalEvidenceState.textContent = 'No animal evidence';
          animalNordicOnlyCheckbox.checked = false;
          animalNordicOnlyCheckbox.disabled = true;
          return;
        }
        const metrics = summarizeAnimalMetrics();
        animalNordicOnlyCheckbox.disabled = false;
        const scopeOptions = [
          { value: 'all', label: 'All animal records' },
          { value: 'domesticated_core', label: 'Domesticated-core only' },
          { value: 'comparator', label: 'Comparator only' },
        ];
        animalScopeFilters.innerHTML = scopeOptions
          .map((option) => {
            const count = metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { scope: option.value })).length;
            return `<button class="preset-button ${activeAnimalScope === option.value ? 'is-active' : ''}" type="button" data-animal-scope="${escapeHtml(option.value)}">${escapeHtml(option.label)} <span class="chip-count">${escapeHtml(String(count))}</span></button>`;
          })
          .join('');
        const speciesButtons = [
          `<button class="preset-button ${activeAnimalSpecies === 'all' ? 'is-active' : ''}" type="button" data-animal-species="all">All species <span class="chip-count">${escapeHtml(String(metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { species: 'all' })).length))}</span></button>`,
          ...ANIMAL_SPECIES.map((species) => {
            const count = metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { species: species.latinName })).length;
            return `<button class="preset-button ${activeAnimalSpecies === species.latinName ? 'is-active' : ''}" type="button" data-animal-species="${escapeHtml(species.latinName)}"><span class="chip-swatch" style="background:${escapeHtml(species.fill)};border-color:${escapeHtml(species.stroke)};"></span>${escapeHtml(String(species.commonName))} <span class="chip-count">${escapeHtml(String(count))}</span></button>`;
          }),
        ];
        animalSpeciesFilters.innerHTML = speciesButtons.join('');
        const confidenceButtons = [
          `<button class="preset-button ${activeAnimalConfidence === 'all' ? 'is-active' : ''}" type="button" data-animal-confidence="all">All confidence <span class="chip-count">${escapeHtml(String(metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { confidence: 'all' })).length))}</span></button>`,
          ...ANIMAL_COORDINATE_CONFIDENCES.map((confidence) => {
            const count = metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { confidence })).length;
            return `<button class="preset-button ${activeAnimalConfidence === confidence ? 'is-active' : ''}" type="button" data-animal-confidence="${escapeHtml(confidence)}">${escapeHtml(formatCoordinateConfidence(confidence))} <span class="chip-count">${escapeHtml(String(count))}</span></button>`;
          }),
        ];
        animalConfidenceFilters.innerHTML = confidenceButtons.join('');
        const temporalWindowButtons = [
          `<button class="preset-button ${activeAnimalTemporalWindow === 'all' ? 'is-active' : ''}" type="button" data-animal-temporal-window="all">All temporal windows</button>`,
          ...ANIMAL_TEMPORAL_WINDOWS.map((label) => `<button class="preset-button ${activeAnimalTemporalWindow === label ? 'is-active' : ''}" type="button" data-animal-temporal-window="${escapeHtml(label)}">${escapeHtml(label)}</button>`),
        ];
        animalTemporalWindowFilters.innerHTML = temporalWindowButtons.join('');
        animalNordicOnlyCheckbox.checked = animalNordicOnly;
        animalFilterSummary.textContent = `${metrics.visibleAtlasEvidenceEntries.length} atlas evidence · ${metrics.visibleSourceChronologyEntries.length} source chronology · ${metrics.visibleSpecies.size} species visible`;
        renderAnimalEvidencePanel(metrics);
        document.querySelectorAll('[data-animal-scope]').forEach((button) => {
          button.addEventListener('click', () => {
            activeAnimalScope = button.dataset.animalScope;
            renderMapState();
          });
        });
        document.querySelectorAll('[data-animal-species]').forEach((button) => {
          button.addEventListener('click', () => {
            activeAnimalSpecies = button.dataset.animalSpecies;
            renderMapState();
          });
        });
        document.querySelectorAll('[data-animal-confidence]').forEach((button) => {
          button.addEventListener('click', () => {
            activeAnimalConfidence = button.dataset.animalConfidence;
            renderMapState();
          });
        });
        document.querySelectorAll('[data-animal-temporal-window]').forEach((button) => {
          button.addEventListener('click', () => {
            activeAnimalTemporalWindow = button.dataset.animalTemporalWindow;
            renderMapState();
          });
        });
      }
      function applyLayerPreset(preset) {
        if (preset === 'evidence') {
          activeLayerKeys = new Set(
            ALL_LAYERS
              .filter((layer) => ['primary-evidence', 'animal-domesticated-evidence', 'animal-comparator-evidence', 'animal-progenitor-evidence'].includes(layer.group))
              .map((layer) => layer.key)
          );
        }
        if (preset === 'context') {
          activeLayerKeys = new Set(
            ALL_LAYERS
              .filter((layer) => ['primary-evidence', 'animal-domesticated-evidence', 'animal-comparator-evidence', 'animal-progenitor-evidence', 'animal-chronology-context', 'environmental-context', 'archaeology-context'].includes(layer.group))
              .map((layer) => layer.key)
          );
        }
        if (preset === 'orientation') {
          activeLayerKeys = new Set(
            ALL_LAYERS
              .filter((layer) => ['primary-evidence', 'animal-domesticated-evidence', 'animal-comparator-evidence', 'animal-progenitor-evidence', 'orientation'].includes(layer.group))
              .map((layer) => layer.key)
          );
        }
        if (preset === 'all') {
          activeLayerKeys = new Set(ALL_LAYERS.map((layer) => layer.key));
        }
        const selectedSourceLayer = sourceChronologyLayerForLevel(activeSourceChronologyLevel);
        const activeSourceLayerCount = sourceChronologyLayers().filter((layer) => activeLayerKeys.has(layer.key)).length;
        if (activeSourceLayerCount > 1) {
          sourceChronologyLayers().forEach((layer) => activeLayerKeys.delete(layer.key));
          if (selectedSourceLayer) activeLayerKeys.add(selectedSourceLayer.key);
        }
        if (!selectedSourceLayer || !activeLayerKeys.has(selectedSourceLayer.key)) sourceRecordConcentrationActive = false;
        renderLayerControls();
        renderMapState();
      }
      function renderLegend() {
        const renderedLayerKeys = new Set([
          ...visiblePointEntries.map(({ layer }) => layer.key),
          ...visiblePolygonFeatureEntries.map(({ layer }) => layer.key),
        ]);
        const activeLegendLayers = ALL_LAYERS.filter((layer) => renderedLayerKeys.has(layer.key));
        const concentrationLayer = sourceChronologyLayerForLevel(activeSourceChronologyLevel);
        const renderLayerCue = (layer) => {
          if (layer.kind === 'country-boundaries') {
            return [...activeCountries].sort().map((country) => {
              const style = countryStyle(country);
              return `<div class="legend-item legend-item--compact" data-legend-country="${escapeHtml(country)}"><span class="legend-boundary-cue" style="color:${escapeHtml(style.stroke)};"></span><span>${escapeHtml(country)} boundary</span></div>`;
            }).join('');
          }
          const fill = layerColor(layer);
          const stroke = layer.style.stroke || fill;
          const acceptanceFill = layer.style.circleFill || fill;
          const acceptanceStroke = layer.style.circleStroke || stroke;
          const acceptanceCue = POINT_LAYERS.includes(layer) && layer.circle_enabled && Number(slider.value) > 0
            ? `<span class="legend-acceptance-cue" data-legend-acceptance-layer="${escapeHtml(layer.key)}" title="Acceptance ring for ${escapeHtml(layer.label)}" style="color:${escapeHtml(acceptanceStroke)};background:${escapeHtml(acceptanceFill)};"></span>`
            : '';
          return `<div class="legend-item" data-legend-layer="${escapeHtml(layer.key)}"><span class="legend-swatch" style="background:${escapeHtml(fill)};border-color:${escapeHtml(stroke)};"></span>${acceptanceCue}<span>${escapeHtml(layer.label)}: ${escapeHtml(layer.description)} ${layer.coverage_label ? `(${escapeHtml(layer.coverage_label)})` : ''}</span></div>`;
        };
        const renderGroup = (label, layers) => layers.length
          ? `<div class="legend-group"><div class="legend-group-label">${escapeHtml(label)}</div><div class="legend-list">${layers.map(renderLayerCue).join('')}</div></div>`
          : '';
        const clusterLegendSection = visiblePointEntries.length > 0
          ? '<div class="legend-group"><div class="legend-group-label">Map grouping</div><div class="legend-item legend-item--compact"><span class="legend-cluster-cue">12</span><span>Numbered circles group same-layer records at the current zoom; the number is a record count, not abundance.</span></div></div>'
          : '';
        const visibleScientificEdges = visibleGovernedEdges();
        const relationLegendSection = visibleScientificEdges.length
          ? '<div class="legend-group"><div class="legend-group-label">Evidence relations</div><div class="legend-item">Lines connect evidence endpoints; they are relations, not reconstructed movement paths.</div></div>'
          : '';
        const visibleScientificSignalIds = new Set([
          ...visiblePointEntries.flatMap(({ feature }) => Array.isArray(feature.scientific_signal_ids) ? feature.scientific_signal_ids : []),
          ...visibleScientificEdges.map((edge) => edge.signal_id),
        ]);
        const visibleScientificSignals = SCIENTIFIC_SIGNALS.filter((signal) => activeScientificSignalIds.has(signal.signal_id) && visibleScientificSignalIds.has(signal.signal_id));
        const scientificLegendSection = visibleScientificSignals.length
          ? `<div class="legend-group"><div class="legend-group-label">Accepted scientific comparison</div><div class="legend-list">${visibleScientificSignals.map((signal) => `<div class="legend-item"><span class="scientific-cue" data-cue="${escapeHtml(signal.non_color_cue)}" style="color:${escapeHtml(signal.color)}">${escapeHtml(scientificCueGlyph(signal.non_color_cue))}</span><span>${escapeHtml(signal.label)} · ${escapeHtml(signal.resolution)} · ${escapeHtml(signal.feature_key)}</span></div>`).join('')}</div></div>`
          : '';
        const sourceConcentrationLegendSection = concentrationLayer && sourceRecordConcentrationActive && sourceRecordConcentrationSnapshot?.status === 'available'
          ? `<div class="legend-group"><div class="legend-group-label">Captured source-record concentration</div><div class="legend-list">${[[7, '1 raw visible node at one source site'], [10, '2–4 nodes'], [13, '5–9 nodes'], [16, '10–24 nodes'], [19, '25+ nodes']].map(([size, label]) => `<div class="legend-item"><span class="legend-swatch" data-legend-concentration-size="${size}" style="width:${size}px;height:${size}px;background:${escapeHtml(layerColor(concentrationLayer))};border-color:${escapeHtml(concentrationLayer.style.stroke || layerColor(concentrationLayer))};"></span><span>${label}</span></div>`).join('')}<div class="legend-item"><span>${sourceRecordConcentrationSnapshot.visible_observation_denominator} contributing observations for visible symbols; ${sourceRecordConcentrationSnapshot.global_observation_denominator} in the global pre-filter facet denominator. Values are not weighted.</span></div></div></div>`
          : '';
        const neighborContextLegendSection = visiblePointEntries.some(({ neighborContext }) => neighborContext)
          ? '<div class="legend-group"><div class="legend-group-label">Cross-border context</div><div class="legend-item">Dimmed, labeled neighboring endpoints are retained for selected cross-border relations. They are excluded from focal-country point counts.</div></div>'
          : '';
        legendItems.innerHTML = `${clusterLegendSection}${scientificLegendSection}${relationLegendSection}${sourceConcentrationLegendSection}${neighborContextLegendSection}${LAYER_GROUP_DEFINITIONS
          .map((group) => renderGroup(group.label, activeLegendLayers.filter((layer) => layer.group === group.key)))
          .join('')}` || '<div class="legend-item"><span>No layers are visible. Restore defaults or enable one or more layers.</span></div>';
        const visibleRaaDensityLayer = visiblePolygonFeatureEntries.find(({ layer }) => layer.key === 'raa-archaeology')?.layer || null;
        densityRamp.hidden = !visibleRaaDensityLayer;
        const densityRampDescription = document.getElementById('density-ramp-description');
        if (densityRampDescription) densityRampDescription.textContent = visibleRaaDensityLayer?.density_count_label || 'RAÄ density-count posture unavailable.';
      }
      function sourceChronologyPopupHtml(feature) {
        if (!feature || feature.semantic_role !== 'source_chronology_context') return '';
        const values = [
          ['Node level', SOURCE_CHRONOLOGY_LEVEL_LABELS[feature.node_level] || feature.node_level],
          ['Source record', feature.source_record_id],
          ['Feature key', feature.feature_key],
          ['Literal ecological code', feature.source_ecological_code],
          ['Source-reported label', feature.source_reported_name],
          ['Source taxon identifier', feature.source_taxon_id],
          ['Literal source unit', feature.source_unit],
          ['Contributing observations', feature.observation_denominator],
          ['Chronology', featureTimeLabel(feature)],
        ].filter(([, value]) => valueIsAvailable(value));
        const rows = values.map(([label, value]) => `<div class="popup-row"><span class="popup-row-label">${escapeHtml(label)}</span><span class="popup-row-value">${escapeHtml(value)}</span></div>`).join('');
        return `<div class="popup-section"><span class="popup-section-title">Source-native chronology context</span>${rows}<div class="popup-row"><span class="popup-row-label">Interpretation posture</span><span class="popup-row-value">Chronology context only; propagation use refused.</span></div></div>`;
      }
      function animalSourceChronologyPopupHtml(feature, layer = null) {
        if (!animalSourceChronologyFeatureIsValid(feature)) return '';
        const sourceRows = availablePopupRows(Array.isArray(feature.popup_rows) ? feature.popup_rows : []);
        const identityRows = [
          { label: 'Project accession', value: feature.project_accession },
          { label: 'Repository sample', value: feature.repo_stable_sample_id },
          { label: 'Project-registry species attribution', value: feature.project_species_latin_name },
          { label: 'Source-native identity kind', value: feature.source_native_identity_kind },
          { label: 'Source-native taxon ID', value: feature.source_native_tax_id },
          { label: 'Source-native scientific name', value: feature.source_native_scientific_name },
          { label: 'Source-native taxonomy status', value: feature.source_native_taxonomy_status },
          { label: 'Chronology', value: featureTimeLabel(feature) },
          { label: 'Coordinate basis', value: formatCoordinateBasis(feature.coordinate_basis || '') },
          { label: 'Coordinate confidence', value: formatCoordinateConfidence(feature.coordinate_confidence || '') },
        ].filter((row) => valueIsAvailable(row.value));
        const seenLabels = new Set(identityRows.map((row) => row.label));
        const rows = identityRows.concat(sourceRows.filter((row) => !seenLabels.has(row.label)));
        const rowHtml = rows.map((row) => `<div class="popup-row"><span class="popup-row-label">${escapeHtml(row.label || '')}</span><span class="popup-row-value">${escapeHtml(row.value)}</span></div>`).join('');
        const traceabilityArtifact = typeof layer?.traceability_artifact === 'string' ? layer.traceability_artifact.trim() : '';
        const traceabilityHtml = traceabilityArtifact ? `<div class="popup-row"><span class="popup-row-label">Accountability</span><span class="popup-row-value"><a href="./${escapeHtml(traceabilityArtifact)}" target="_blank" rel="noreferrer">Open chronology accountability and refusals</a></span></div>` : '';
        return `<div class="popup-card"><div class="popup-headline"><span class="popup-kicker">Animal source chronology</span><div class="popup-title">${escapeHtml(feature.title || feature.repo_stable_sample_id || '')}</div><div class="popup-subtitle">${escapeHtml(feature.project_species_common_name || feature.project_species_latin_name || '')}</div></div><div class="popup-badges"><span class="popup-badge">Display-only chronology</span><span class="popup-badge">Project-registry species attribution</span></div><div class="popup-section"><span class="popup-section-title">Source sample and chronology</span>${rowHtml}<div class="popup-row"><span class="popup-row-label">Scientific posture</span><span class="popup-row-value">Project species attribution is not an accepted source-native taxonomic classification. This layer is excluded from candidate ranking, accepted scientific comparison, sequences, edges, propagation, migration, and causal claims.</span></div><div class="popup-row"><span class="popup-row-label">Coordinates</span><span class="popup-row-value">${escapeHtml(coordinateLabel(feature, 6))}</span></div>${traceabilityHtml}${mediaLinksHtml(feature.media_links)}</div>${feature.source_url ? `<div class="popup-section"><span class="popup-section-title">Source link</span><div class="popup-row"><span class="popup-row-value"><a href="${escapeHtml(feature.source_url)}" target="_blank" rel="noreferrer">Open source record</a></span></div></div>` : ''}</div>`;
      }
      function popupHtml(feature, layer = null) {
        if (feature.semantic_role === 'animal_source_chronology_context') {
          return animalSourceChronologyPopupHtml(feature, layer);
        }
        const rows = Array.isArray(feature.popup_rows) ? feature.popup_rows : [];
        const scientificRows = scientificSignalsForFeature(feature);
        const sourceChronologyHtml = typeof sourceChronologyPopupHtml === 'function'
          ? sourceChronologyPopupHtml(feature)
          : '';
        const scientificHtml = scientificRows.length
          ? `<div class="popup-section"><span class="popup-section-title">Accepted scientific signals</span>${scientificRows.map((signal) => `<div class="popup-row"><span class="popup-row-label">${escapeHtml(signal.resolution)}</span><span class="popup-row-value"><span class="scientific-cue" data-cue="${escapeHtml(signal.non_color_cue)}" style="color:${escapeHtml(signal.color)}">${escapeHtml(scientificCueGlyph(signal.non_color_cue))}</span> ${escapeHtml(signal.label)} · ${escapeHtml(signal.feature_key)}</span></div>`).join('')}</div>`
          : '';
        if (feature.species_latin_name) {
          const warningRows = availablePopupRows(rows).filter((row) => row.label === 'Warning');
          const detailRows = availablePopupRows(rows).filter((row) => row.label !== 'Warning');
          const primaryRows = [
            { label: 'Paper', value: feature.paper_title || '' },
            { label: 'DOI', value: feature.paper_doi || '' },
            { label: 'Project accession', value: Array.isArray(feature.project_accessions) ? feature.project_accessions.join(', ') : '' },
            { label: 'Coordinate basis', value: formatCoordinateBasis(feature.coordinate_basis || '') },
            { label: 'Coordinate confidence', value: formatCoordinateConfidence(feature.coordinate_confidence || '') },
            { label: 'Source locator', value: feature.source_locator || '' },
          ].filter((row) => valueIsAvailable(row.value));
          const detailValue = (label) => detailRows.find((row) => row.label === label)?.value;
          const secondaryRows = [
            { label: 'Chronology', value: feature.time_label || '' },
            { label: 'Chronology evidence class', value: detailValue('Chronology evidence class') ?? feature.temporal_semantics?.evidence_class ?? '' },
            { label: 'Chronology precision posture', value: detailValue('Chronology precision posture') ?? feature.temporal_semantics?.precision_posture ?? '' },
            { label: 'Temporal comparison posture', value: detailValue('Temporal comparison posture') ?? feature.temporal_comparability_posture ?? feature.temporal_semantics?.comparability_posture ?? '' },
            { label: 'Temporal comparison note', value: detailValue('Temporal comparison note') ?? feature.temporal_comparison_note ?? feature.temporal_semantics?.comparison_note ?? '' },
            { label: 'Source-native taxa', value: Array.isArray(feature.source_native_taxon_labels) ? feature.source_native_taxon_labels.join(', ') : '' },
            { label: 'Taxon alignment', value: Array.isArray(feature.taxon_alignment_statuses) ? feature.taxon_alignment_statuses.join(', ').replaceAll('_', ' ') : '' },
            { label: 'Mapped sample identifiers', value: Array.isArray(feature.sample_record_ids) ? feature.sample_record_ids.join(', ') : '' },
            { label: 'Original place text', value: feature.original_place_text || '' },
            { label: 'Resolved place text', value: feature.resolved_place_text || '' },
            { label: 'Source support', value: feature.source_support_status || '' },
            { label: 'Interpretation', value: detailRows.find((row) => row.label === 'Interpretation')?.value ?? '' },
            { label: 'Source evidence text', value: feature.exact_source_text || '' },
          ].filter((row) => valueIsAvailable(row.value));
          const renderRows = (items) => items.map((row) => `<div class="popup-row"><span class="popup-row-label">${escapeHtml(row.label)}</span><span class="popup-row-value">${escapeHtml(row.value)}</span></div>`).join('');
          return `<div class="popup-card"><div class="popup-headline"><span class="popup-kicker">Animal atlas evidence</span><div class="popup-title">${escapeHtml(feature.title || '')}</div><div class="popup-subtitle">${escapeHtml(feature.subtitle || '')}</div></div><div class="popup-badges"><span class="popup-badge">${escapeHtml(feature.species_common_name || feature.species_latin_name || 'Animal evidence')}</span><span class="popup-badge">${escapeHtml(formatAnimalScope(feature.animal_scope || ''))}</span><span class="popup-badge">${escapeHtml(formatCoordinateConfidence(feature.coordinate_confidence || ''))}</span>${feature.nordic_inclusion ? '<span class="popup-badge">Nordic lead</span>' : '<span class="popup-badge popup-badge--warning">Non-Nordic context</span>'}</div><div class="popup-section"><span class="popup-section-title">Citation and provenance</span>${renderRows(primaryRows)}</div><div class="popup-section"><span class="popup-section-title">Sample and locality detail</span>${renderRows(secondaryRows)}<div class="popup-row"><span class="popup-row-label">Coordinates</span><span class="popup-row-value">${escapeHtml(coordinateLabel(feature, 6))}</span></div>${mediaLinksHtml(feature.media_links)}</div>${scientificHtml}${warningRows.length ? `<div class="popup-section"><span class="popup-section-title">Warnings and caveats</span><div class="popup-warning-list">${warningRows.map((row) => `<div class="popup-warning">${escapeHtml(row.value)}</div>`).join('')}</div></div>` : ''}${feature.source_url ? `<div class="popup-section"><span class="popup-section-title">Source link</span><div class="popup-row"><span class="popup-row-value"><a href="${escapeHtml(feature.source_url)}" target="_blank" rel="noreferrer">Open article or source record</a></span></div></div>` : ''}</div>`;
        }
        const rowHtml = availablePopupRows(rows).map((row) => `<div><strong>${escapeHtml(row.label || '')}</strong> ${escapeHtml(row.value)}</div>`).join('');
        return `<div class="popup-grid"><div><strong>Name</strong> ${escapeHtml(feature.title || '')}</div><div><strong>Type</strong> ${escapeHtml(feature.subtitle || '')}</div>${rowHtml}${sourceChronologyHtml}${scientificHtml}<div><strong>Coords</strong> ${escapeHtml(coordinateLabel(feature, 6))}</div>${mediaLinksHtml(feature.media_links)}${feature.source_url ? `<div><strong>Source</strong> <a href="${escapeHtml(feature.source_url)}" target="_blank" rel="noreferrer">Open</a></div>` : ''}</div>`;
      }
      function polygonPopupHtml(layer, properties) {
        const rows = Array.isArray(properties.popup_rows) ? properties.popup_rows : [];
        const rowHtml = availablePopupRows(rows).map((row) => `<div><strong>${escapeHtml(row.label || '')}</strong> ${escapeHtml(row.value)}</div>`).join('');
        const isPublishedModel = isModeledContextFeature(layer, properties);
        const metric = currentModeledContextMetric();
        const estimate = modeledContextEstimate(properties);
        const standardError = modeledContextStandardError(properties);
        const modeledRows = isPublishedModel && metric
          ? `<div><strong>Selected source metric</strong> ${escapeHtml(metric.source_label)} (${escapeHtml(metric.key)})</div><div><strong>Estimate</strong> ${estimate === null ? 'Unavailable' : `${escapeHtml(estimate.toFixed(2))}%`}</div><div><strong>Source standard error</strong> ${standardError === null ? 'Unavailable' : `${escapeHtml(standardError.toFixed(2))} percentage points`}</div><div><strong>Metric definition</strong> ${escapeHtml(metric.definition || 'Unavailable in the companion source mapping table')}</div><div><strong>Evidence role</strong> Context only; not a pollen observation or propagation input</div><div><strong>Interpolation</strong> Not allowed between published windows</div><div><strong>Method</strong> <a href="${escapeHtml(MODELED_CONTEXT.method_doi)}" target="_blank" rel="noreferrer">${escapeHtml(MODELED_CONTEXT.method_citation)}</a></div><div><strong>Quality class</strong> ${escapeHtml(properties.quality_class === 'no_pollen_data' ? 'No pollen data — modeled values are N/A, not zero' : properties.quality_class || 'Unavailable in normalized row')}</div>`
          : '';
        return `<div class="popup-grid"><div><strong>Layer</strong> ${escapeHtml(layer.label)}</div><div><strong>Name</strong> ${escapeHtml(properties.name || '')}</div><div><strong>Type</strong> ${escapeHtml(properties.category || properties.geometry_type || '')}</div>${rowHtml}${modeledRows}${properties.source_url ? `<div><strong>Source</strong> <a href="${escapeHtml(properties.source_url)}" target="_blank" rel="noreferrer">Open</a></div>` : ''}</div>`;
      }
      function densityFillColor(count, maxCount) {
        if (count === null || maxCount === null) return '#cbd5e1';
        if (!maxCount || count <= 0) return '#fee2e2';
        const ratio = count / maxCount;
        if (ratio >= 0.75) return '#7f1d1d';
        if (ratio >= 0.55) return '#b91c1c';
        if (ratio >= 0.35) return '#ef4444';
        if (ratio >= 0.20) return '#f87171';
        if (ratio >= 0.08) return '#fca5a5';
        return '#fee2e2';
      }
      function finiteTimeValue(value) {
        return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
      }
      function valueIsAvailable(value) {
        return value !== null && value !== undefined && !(typeof value === 'string' && !value.trim());
      }
      function availablePopupRows(rows) {
        return rows.filter((row) => row && valueIsAvailable(row.value));
      }
      function finiteCoordinateValue(value, minimum, maximum) {
        if (value === null || value === undefined || typeof value === 'boolean') return null;
        if (typeof value === 'string' && !value.trim()) return null;
        if (typeof value !== 'number' && typeof value !== 'string') return null;
        const numeric = Number(value);
        return Number.isFinite(numeric) && numeric >= minimum && numeric <= maximum ? numeric : null;
      }
      function featureCoordinatePair(feature) {
        const latitude = finiteCoordinateValue(feature.latitude, -90, 90);
        const longitude = finiteCoordinateValue(feature.longitude, -180, 180);
        return latitude === null || longitude === null ? null : { latitude, longitude };
      }
      function coordinateLabel(feature, precision) {
        const coordinates = featureCoordinatePair(feature);
        return coordinates ? `${coordinates.latitude.toFixed(precision)}, ${coordinates.longitude.toFixed(precision)}` : 'Unavailable';
      }
      function finiteCountValue(value) {
        return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 ? value : null;
      }
      function countDisplayValue(count, countLabel) {
        if (typeof countLabel === 'string' && countLabel.trim()) return countLabel.trim();
        const numeric = finiteCountValue(count);
        return numeric === null ? 'Unavailable' : String(numeric);
      }
      function mappedPointCountLabel(value) {
        const count = finiteCountValue(value);
        return count === null ? 'mapped count unavailable' : `${count} mapped point${count === 1 ? '' : 's'}`;
      }
      function localityExportRecords(payload) {
        if (!payload || !['adna-locality-summary-export.v1','adna-locality-summary-export.v2'].includes(payload.schema_version) || !Array.isArray(payload.localities)) throw new Error('Unsupported locality export wrapper');
        return payload.localities.map(row=>{
          if (!row || typeof row !== 'object' || Array.isArray(row) || (Object.prototype.hasOwnProperty.call(row,'schema_version') && row.schema_version !== payload.schema_version)) throw new Error('Locality wrapper and record schemas disagree');
          const view = {...structuredClone(row),schema_version:payload.schema_version};
          if (row.chronology && typeof row.chronology === 'object' && !Array.isArray(row.chronology)) {
            for (const key of ['time_start_bp','time_end_bp','time_mean_bp']) {
              if (Object.prototype.hasOwnProperty.call(view,key) && view[key] !== row.chronology[key]) throw new Error('Locality display projection disagrees with source hull');
              view[key] = view.chronology[key] ?? null;
            }
            if (!Object.prototype.hasOwnProperty.call(view,'time_label')) view.time_label = row.chronology.original_text ?? '';
          }
          return view;
        });
      }
      function featureTimeAdmission(feature) {
        if (typeof signedNativeTime !== 'undefined' && signedNativeTime !== null) {
          try {
            if (Object.prototype.hasOwnProperty.call(feature,'temporal_semantics')) return {status:'refused',window:null};
            const source = nativeCalendarSupport(feature.source_calendar_support, 'closed_age_support');
            const window = nativeCalendarSupport(feature.declared_calendar_support, 'declared_stationarity_envelope');
            if (feature.data_kind !== 'synthetic' || feature.evidence_role !== 'model_output' || feature.scientific_acceptance !== 'not_evaluated'
                || feature.age_type !== 'calendar_bp' || feature.time_start_bp !== window[0] || feature.time_end_bp !== window[1]
                || JSON.stringify(feature.source_age_support_bp) !== JSON.stringify([source])
                || source[0] < window[0] || source[1] > window[1]) return {status:'refused',window:null};
            return {status:'valid',window:{start:window[0],end:window[1]}};
          } catch(error) {return {status:'refused',window:null};}
        }
        if (Object.prototype.hasOwnProperty.call(feature,'source_calendar_support') || Object.prototype.hasOwnProperty.call(feature,'declared_calendar_support')) return {status:'refused',window:null};
        if (feature?.type === 'FeatureCollection') return {status:'refused',window:null};
        if (feature?.type === 'Feature') {
          const versions = {'adna-sample-geojson.v1':'adna-sample-record-export.v1','adna-sample-geojson.v2':'adna-sample-record-export.v2'};
          const properties = feature.properties;
          if (!properties || typeof properties !== 'object' || Array.isArray(properties)) return {status:'refused',window:null};
          const sample = typeof properties.schema_version === 'string' && properties.schema_version.startsWith('adna-sample-record-export.');
          if (Object.prototype.hasOwnProperty.call(feature,'schema_version') && typeof feature.schema_version !== 'string') return {status:'refused',window:null};
          const reservedSchema = typeof feature.schema_version === 'string' && ['adna-sample-record-export.','adna-locality-summary-export.','adna-sample-geojson.','adna-sample-geojson-collection.'].some(prefix=>feature.schema_version.startsWith(prefix));
          if (Object.prototype.hasOwnProperty.call(feature,'schema_version') && (sample || reservedSchema) && versions[feature.schema_version] !== properties.schema_version) return {status:'refused',window:null};
          return featureTimeAdmission(properties);
        }
        if (Object.prototype.hasOwnProperty.call(feature,'schema_version') && typeof feature.schema_version !== 'string') return {status:'refused',window:null};
        const semantics = feature?.temporal_semantics;
        let posture = '';
        let refusalReason = '';
        if (semantics && typeof semantics === 'object' && !Array.isArray(semantics)) {
          if (['schema_version','comparability_posture','refusal_reason_code'].some(key=>Object.prototype.hasOwnProperty.call(semantics,key) && typeof semantics[key] !== 'string')) return {status:'refused',window:null};
          if (Object.prototype.hasOwnProperty.call(semantics,'schema_version') && semantics.schema_version !== 'temporal-semantics.v1') return {status:'refused',window:null};
          posture = typeof semantics.comparability_posture === 'string'
            ? semantics.comparability_posture.trim()
            : '';
          refusalReason = typeof semantics.refusal_reason_code === 'string'
            ? semantics.refusal_reason_code.trim()
            : '';
        }
        if (Object.prototype.hasOwnProperty.call(feature,'temporal_semantics')) {
          if (!semantics || typeof semantics !== 'object' || Array.isArray(semantics)) return {status:'refused',window:null};
        }
        if (posture === 'refused' || refusalReason) return {status:'refused',window:null};
        const exportSchema = feature.schema_version;
        const reservedExport = typeof exportSchema === 'string' && ['adna-sample-record-export.','adna-locality-summary-export.','adna-sample-geojson.','adna-sample-geojson-collection.'].some(prefix=>exportSchema.startsWith(prefix));
        const hasSampleChronologies = Object.prototype.hasOwnProperty.call(feature,'sample_chronologies');
        if (hasSampleChronologies && feature.chronology_role !== 'locality_sample_coverage_hull') return {status:'refused',window:null};
        const ownedLocality = hasSampleChronologies && feature.chronology_role === 'locality_sample_coverage_hull' && (!reservedExport || exportSchema === 'adna-locality-summary-export.v2');
        if (!ownedLocality) {
          if (Object.prototype.hasOwnProperty.call(feature,'temporal_semantics') && !['numeric_interval','numeric_interval_with_caveat','mixed_interval_and_context'].includes(posture)) return {status:'contextual',window:null};
        }
        if (['adna-sample-record-export.v1','adna-locality-summary-export.v1'].includes(exportSchema)) return {status:'contextual',window:null};
        if (exportSchema === 'adna-sample-record-export.v2') {
          const support = feature.sample_chronology, identity = feature.sample_identity;
          if (!support || typeof support !== 'object' || Array.isArray(support) || support.schema_version !== 'adna-sample-chronology-support.v1' || !identity || typeof identity !== 'object' || Array.isArray(identity)) return {status:'refused',window:null};
          const identifier = feature.genetic_id, namespace = feature.sample_namespace;
          if (typeof identifier !== 'string' || !identifier.trim() || typeof namespace !== 'string' || !namespace.trim() || support.sample_id !== identifier || identity.stable_token !== identifier || identity.namespace !== namespace || (Object.prototype.hasOwnProperty.call(feature,'sample_id') && feature.sample_id !== identifier)) return {status:'refused',window:null};
          for (const key of ['master_id','group_id','accession_lineage']) {
            if (!Object.prototype.hasOwnProperty.call(feature,key) || !Object.prototype.hasOwnProperty.call(identity,key) || JSON.stringify(feature[key]) !== JSON.stringify(identity[key])) return {status:'refused',window:null};
          }
          if (['master_id','group_id'].some(key=>typeof feature[key] !== 'string')) return {status:'refused',window:null};
          for (const [key,value] of Object.entries(identity)) {
            if (!['namespace','stable_token','accession_lineage'].includes(key) && Object.prototype.hasOwnProperty.call(feature,key) && (typeof feature[key] !== typeof value || JSON.stringify(feature[key]) !== JSON.stringify(value))) return {status:'refused',window:null};
          }
          if (!Array.isArray(identity.accession_lineage) || identity.accession_lineage.some(value=>typeof value !== 'string') || typeof feature.source_family !== 'string') return {status:'refused',window:null};
          const supportText = ['source_release','provenance_path','provenance_locator','provenance_excerpt','provenance_kind','chronology_strength','normalization_status','conflict_note','reference_epoch','age_type','calibration_status','model'];
          if (supportText.some(key=>Object.prototype.hasOwnProperty.call(support,key) && typeof support[key] !== 'string')) return {status:'refused',window:null};
          const chronology = support.chronology;
          if (!chronology || typeof chronology !== 'object' || Array.isArray(chronology)) return {status:'refused',window:null};
          const textFields = ['original_text','date_stddev_bp','source_mean_bp_text','dating_basis','evidence_class','precision_posture','refusal_reason_code'];
          if (textFields.some(key=>!Object.prototype.hasOwnProperty.call(chronology,key) || typeof chronology[key] !== 'string')) return {status:'refused',window:null};
          for (const key of ['time_start_bp','time_end_bp','time_mean_bp']) {
            const value = chronology[key];
            if (!Object.prototype.hasOwnProperty.call(chronology,key) || (value !== null && !Number.isSafeInteger(value)) || !Object.prototype.hasOwnProperty.call(feature,key) || feature[key] !== value) return {status:'refused',window:null};
          }
          if (chronology.refusal_reason_code) return {status:'refused',window:null};
          if (chronology.time_start_bp === null && chronology.time_end_bp === null) return {status:'contextual',window:null};
          const start = finiteTimeValue(chronology.time_start_bp), end = finiteTimeValue(chronology.time_end_bp);
          if (start === null || end === null || start > end || (chronology.time_mean_bp !== null && chronology.time_mean_bp < 0)) return {status:'refused',window:null};
          if (!['sample_precise_point','sample_precise_interval','sample_approximate_or_modeled','contextual_interval'].includes(chronology.precision_posture)) return {status:'contextual',window:null};
          return {status:'valid',window:{start,end}};
        }
        if (typeof exportSchema === 'string' && ['adna-sample-record-export.','adna-locality-summary-export.','adna-sample-geojson.','adna-sample-geojson-collection.'].some(prefix=>exportSchema.startsWith(prefix)) && exportSchema !== 'adna-locality-summary-export.v2') return {status:'refused',window:null};
        if (exportSchema === 'adna-locality-summary-export.v2' && (!Object.prototype.hasOwnProperty.call(feature,'sample_chronologies') || Object.prototype.hasOwnProperty.call(feature,'localities'))) return {status:'refused',window:null};
        if (exportSchema === 'adna-locality-summary-export.v2') {
          const identities = ['identity','locality_identity'].filter(key=>Object.prototype.hasOwnProperty.call(feature,key)).map(key=>feature[key]);
          for (const identity of identities) {
            if (!identity || typeof identity !== 'object' || Array.isArray(identity) || ['namespace','stable_token'].some(key=>typeof identity[key] !== 'string' || !identity[key].trim()) || typeof identity.locality_text !== 'string' || (identity.political_entity !== null && typeof identity.political_entity !== 'string') || !Array.isArray(identity.source_anchor_tokens) || identity.source_anchor_tokens.some(value=>typeof value !== 'string')) return {status:'refused',window:null};
            for (const [outer,inner] of [['locality_namespace','namespace'],['locality_token','stable_token'],['political_entity','political_entity']]) {
              if (Object.prototype.hasOwnProperty.call(feature,outer) && feature[outer] !== identity[inner] && !(outer === 'political_entity' && feature[outer] === '' && identity[inner] === null)) return {status:'refused',window:null};
            }
          }
          if (identities.length === 2 && ['namespace','stable_token','locality_text','political_entity','source_anchor_tokens'].some(key=>JSON.stringify(identities[0][key]) !== JSON.stringify(identities[1][key]))) return {status:'refused',window:null};
          if (Object.prototype.hasOwnProperty.call(feature,'political_entity') && feature.political_entity !== null && typeof feature.political_entity !== 'string') return {status:'refused',window:null};
        }
        if (Object.prototype.hasOwnProperty.call(feature,'sample_chronology')) return {status:'refused',window:null};
        if (Object.prototype.hasOwnProperty.call(feature, 'sample_chronologies')) {
          if (feature.chronology_role !== 'locality_sample_coverage_hull' || !Array.isArray(feature.sample_chronologies)) return {status:'refused',window:null};
          const identifiers = Object.prototype.hasOwnProperty.call(feature,'sample_ids') ? feature.sample_ids : feature.sample_record_ids;
          if (!Array.isArray(identifiers) || identifiers.some(value => typeof value !== 'string' || !value.trim()) || new Set(identifiers).size !== identifiers.length) return {status:'refused',window:null};
          if (feature.sample_count !== undefined && feature.sample_count !== null && (!Number.isSafeInteger(feature.sample_count) || feature.sample_count !== identifiers.length)) return {status:'refused',window:null};
          const allowed = new Set(identifiers);
          const seen = new Set();
          const windows = [];
          for (const support of feature.sample_chronologies) {
            if (!support || support.schema_version !== 'adna-sample-chronology-support.v1' || !allowed.has(support.sample_id) || seen.has(support.sample_id)) return {status:'refused',window:null};
            seen.add(support.sample_id);
            const supportTextFields = ['source_release','provenance_path','provenance_locator','provenance_excerpt','provenance_kind','chronology_strength','normalization_status','conflict_note','reference_epoch','age_type','calibration_status','model'];
            if (supportTextFields.some(key=>Object.prototype.hasOwnProperty.call(support,key) && typeof support[key] !== 'string')) return {status:'refused',window:null};
            const chronology = support.chronology;
            if (!chronology || typeof chronology !== 'object' || Array.isArray(chronology)) return {status:'refused',window:null};
            const chronologyTextFields = ['original_text','date_stddev_bp','source_mean_bp_text','dating_basis','evidence_class','precision_posture','refusal_reason_code'];
            if (chronologyTextFields.some(key=>Object.prototype.hasOwnProperty.call(chronology,key) && typeof chronology[key] !== 'string')) return {status:'refused',window:null};
            if (['time_start_bp','time_end_bp','time_mean_bp'].some(key=>chronology[key] !== null && chronology[key] !== undefined && !Number.isSafeInteger(chronology[key]))) return {status:'refused',window:null};
            if (chronology.refusal_reason_code) continue;
            if ((chronology.time_start_bp === null || chronology.time_start_bp === undefined) && (chronology.time_end_bp === null || chronology.time_end_bp === undefined)) continue;
            const start = finiteTimeValue(chronology.time_start_bp);
            const end = finiteTimeValue(chronology.time_end_bp);
            if (start === null || end === null || start > end) return {status:'refused',window:null};
            const numericPostures = ['sample_precise_point','sample_precise_interval','sample_approximate_or_modeled','contextual_interval'];
            if (!numericPostures.includes(chronology.precision_posture)) continue;
            windows.push({start,end,sample_id:support.sample_id});
          }
          if (seen.size !== allowed.size) return {status:'refused',window:null};
          if (!windows.length) return {status:'contextual',window:null};
          return {status:'valid',window:{start:Math.min(...windows.map(value=>value.start)),end:Math.max(...windows.map(value=>value.end))},windows};
        }
        const startDeclared = Object.prototype.hasOwnProperty.call(feature, 'time_start_bp');
        const endDeclared = Object.prototype.hasOwnProperty.call(feature, 'time_end_bp');
        if (startDeclared || endDeclared) {
          const rawStart = feature.time_start_bp;
          const rawEnd = feature.time_end_bp;
          const startAbsent = rawStart === null || rawStart === undefined;
          const endAbsent = rawEnd === null || rawEnd === undefined;
          if (!startAbsent || !endAbsent) {
            const start = finiteTimeValue(rawStart);
            const end = finiteTimeValue(rawEnd);
            if (start === null || end === null || start > end) return { status: 'refused', window: null };
            if (!['numeric_interval', 'numeric_interval_with_caveat', 'mixed_interval_and_context'].includes(posture)) return { status: 'contextual', window: null };
            return { status: 'valid', window: { start, end } };
          }
        }
        for (const field of ['time_mean_bp', 'time_year_bp']) {
          if (!Object.prototype.hasOwnProperty.call(feature, field)) continue;
          const rawValue = feature[field];
          if (rawValue === null || rawValue === undefined) continue;
          const value = finiteTimeValue(rawValue);
          if (value === null) return { status: 'refused', window: null };
          if (!['numeric_interval', 'numeric_interval_with_caveat', 'mixed_interval_and_context'].includes(posture)) return { status: 'contextual', window: null };
          return { status: 'valid', window: { start: value, end: value } };
        }
        if (semantics && typeof semantics === 'object' && !Array.isArray(semantics) && Object.keys(semantics).length) {
          if (['numeric_interval', 'numeric_interval_with_caveat', 'mixed_interval_and_context'].includes(posture)) return { status: 'refused', window: null };
          return { status: 'contextual', window: null };
        }
        return { status: 'absent', window: null };
      }
      function featureTimeWindow(feature) {
        return featureTimeAdmission(feature).window;
      }
      function featureInTimeWindow(layer, feature) {
        const admission = featureTimeAdmission(feature);
        if (admission.status === 'refused') return false;
        if (['absent', 'contextual'].includes(admission.status) && layer.semantic_role === 'source_chronology_context') return false;
        if (!layer.applies_time_filter || !TIME_HAS_DATA) return true;
        if (['absent', 'contextual'].includes(admission.status)) {
          return timeFilterUsesFullExtent();
        }
        const featureWindow = admission.window;
        const activeWindow = { start: timeStartBp, end: timeWindowEndBp() };
        const occurrenceWindows = admission.windows || [featureWindow];
        return occurrenceWindows.some(window => window.end >= activeWindow.start && window.start <= activeWindow.end);
      }
      function featureTimeLabel(feature) {
        const admission = featureTimeAdmission(feature);
        if (admission.status === 'refused') return '';
        if (feature.time_label) return String(feature.time_label);
        const window = admission.window;
        if (!window) return '';
        return window.start === window.end ? `${window.start} BP` : `${window.start}-${window.end} BP`;
      }
      function featureTimeDescriptor(feature) {
        const value = featureTimeLabel(feature);
        if (!value) return null;
        return { label: featureTimeWindow(feature) ? 'Date' : 'Chronology context', value };
      }
      function pointFeatureInTimeWindow(layer, feature) {
        return featureInTimeWindow(layer, feature);
      }
      function featureMatchesScientificSelection(layer, feature) {
        if (!layer.scientific_selection_enabled || !SCIENTIFIC_SIGNALS.length) return true;
        const signalIds = Array.isArray(feature.scientific_signal_ids) ? feature.scientific_signal_ids : [];
        return activeScientificSignalIds.size > 0 && signalIds.some((signalId) => activeScientificSignalIds.has(signalId));
      }
      function scientificSignalsForFeature(feature) {
        const signalIds = Array.isArray(feature.scientific_signal_ids) ? feature.scientific_signal_ids : [];
        return SCIENTIFIC_SIGNALS.filter((signal) => activeScientificSignalIds.has(signal.signal_id) && signalIds.includes(signal.signal_id));
      }
      function pointFeatureVisible(layer, feature) {
        return (
          activeLayerKeys.has(layer.key)
          && (layer.semantic_role !== 'exploratory_lra_model_anchor' || (nativeLraController && nativeLraController.anchorVisible(feature.record_id)))
          && (!((layer.semantic_role === 'animal_source_chronology_context' || layer.group === 'animal-chronology-context')) || (animalSourceChronologyLayerIsValid(layer) && animalSourceChronologyFeatureIsValid(feature)))
          && featureCoordinatePair(feature) !== null
          && (!layer.applies_country_filter || animalSourceChronologyCountryFilterBypassed(layer) || activeCountries.has(feature.country) || isRetainedNeighborContext(layer, feature))
          && pointFeatureInTimeWindow(layer, feature)
          && sourceChronologyFeatureMatches(layer, feature)
          && featureMatchesAnimalFilters(layer, feature)
          && featureMatchesScientificSelection(layer, feature)
        );
      }
      function polygonFeatureVisible(layer, properties) {
        const country = properties.country || '';
        return (
          activeLayerKeys.has(layer.key)
          && (!layer.applies_country_filter || activeCountries.has(country))
          && modeledContextFeatureVisible(layer, properties)
          && featureInTimeWindow(layer, properties)
        );
      }
      function geoJsonPositionIsAdmitted(value) {
        return Boolean(
          Array.isArray(value)
          && value.length >= 2
          && finiteCoordinateValue(value[0], -180, 180) !== null
          && finiteCoordinateValue(value[1], -90, 90) !== null
        );
      }
      function geoJsonRingIsAdmitted(value) {
        if (!Array.isArray(value) || value.length < 4 || !value.every((position) => geoJsonPositionIsAdmitted(position))) return false;
        const first = value[0];
        const last = value[value.length - 1];
        return Number(first[0]) === Number(last[0]) && Number(first[1]) === Number(last[1]);
      }
      function polygonGeometryIsAdmitted(feature) {
        const geometry = feature && feature.geometry;
        if (!geometry || !Array.isArray(geometry.coordinates) || !geometry.coordinates.length) return false;
        if (geometry.type === 'Polygon') return geometry.coordinates.every((ring) => geoJsonRingIsAdmitted(ring));
        if (geometry.type === 'MultiPolygon') {
          return geometry.coordinates.every((polygon) => Array.isArray(polygon) && polygon.length > 0 && polygon.every((ring) => geoJsonRingIsAdmitted(ring)));
        }
        return false;
      }
      function removeRenderedLayers() {
        renderedPointGroups.forEach((group) => map.removeLayer(group));
        renderedEdgeLayers.forEach((layer) => map.removeLayer(layer));
        renderedPolygonLayers.forEach((layer) => map.removeLayer(layer));
        renderedPointGroups = [];
        renderedEdgeLayers = [];
        renderedPolygonLayers = [];
        renderedFittablePolygonLayers = [];
        circleLayerGroup.clearLayers();
        visiblePointEntries = [];
        visiblePolygonFeatureEntries = [];
        highlightedPointEntry = null;
        sourceRecordConcentrationSnapshot = null;
      }
      function createClusterGroup(layer) {
        return L.markerClusterGroup({
          showCoverageOnHover: false,
          spiderfyOnMaxZoom: true,
          maxClusterRadius: 56,
          disableClusteringAtZoom: 10,
          iconCreateFunction(cluster) {
            const count = cluster.getChildCount();
            const size = count > 100 ? 44 : count > 25 ? 38 : 32;
            return L.divIcon({ html: `<div class="cluster-pill" style="width:${size}px;height:${size}px;background:${layer.style.fill};">${count}</div>`, className: '', iconSize: [size, size] });
          }
        });
      }
      function sourceRecordConcentrationPopupHtml(entry, snapshot, layer) {
        return `<div class="popup-grid"><div><strong>Captured source-record concentration</strong> ${escapeHtml(entry.site_id)}</div><div><strong>Source level and facet</strong> ${escapeHtml(SOURCE_CHRONOLOGY_LEVEL_LABELS[layer.node_level])} · ${escapeHtml(sourceRecordConcentrationFacetLabel(layer))}</div><div><strong>Raw visible node count</strong> ${entry.node_count}</div><div><strong>Contributing-observation denominator</strong> ${entry.observation_denominator}</div><div><strong>Global pre-filter denominator</strong> ${snapshot.global_node_count} source nodes · ${snapshot.global_observation_denominator} contributing observations</div><div><strong>Active filters</strong> Current viewport · [${timeStartBp}, ${timeWindowEndBp()}] BP · ${escapeHtml(activeCountries.size ? [...activeCountries].sort().join(', ') : 'no active countries')}</div><div><strong>Interpretation</strong> Non-interpolated captured source-record concentration only; not abundance, absence, propagation, flow, or heat. Reported values are not weighted.</div></div>`;
      }
      function renderSourceRecordConcentrationLayer(layer) {
        try {
          const snapshot = buildSourceRecordConcentration(layer, layer.features, map.getBounds());
          sourceRecordConcentrationSnapshot = snapshot;
          const siteLayer = L.layerGroup();
          snapshot.entries.forEach((site) => {
            const radius = sourceRecordConcentrationRadius(site.node_count);
            const marker = L.circleMarker([site.latitude, site.longitude], {
              pane: 'pointPane',
              radius,
              color: layer.style.stroke,
              weight: 1.8,
              fillColor: layer.style.fill,
              fillOpacity: 0.72,
            });
            marker.bindPopup(sourceRecordConcentrationPopupHtml(site, snapshot, layer), { maxWidth: 380 });
            const feature = {
              ...site.feature,
              title: site.site_id,
              subtitle: 'Captured source-record concentration at one source site',
              observation_denominator: site.observation_denominator,
              source_record_concentration_node_count: site.node_count,
              time_start_bp: null,
              time_end_bp: null,
              time_label: null,
            };
            const entry = { layer, feature, marker };
            marker.on('click', () => focusPointAtVisibleIndex(visiblePointEntries.indexOf(entry)));
            siteLayer.addLayer(marker);
            visiblePointEntries.push(entry);
          });
          if (evidenceDisplayDecision(activeEvidenceDisplay).drawNodes && siteLayer.getLayers().length > 0) {
            siteLayer.addTo(map);
            renderedPointGroups.push(siteLayer);
          }
        } catch (error) {
          sourceRecordConcentrationSnapshot = {
            status: 'refused',
            reason: error instanceof Error ? error.message : 'Captured source-record concentration failed closed.',
          };
        }
      }
      function renderPointLayers() {
        const diameterKm = Number(slider.value);
        const radiusMeters = (diameterKm * 1000) / 2;
        POINT_LAYERS.forEach((layer) => {
          if (sourceRecordConcentrationActive && layer.key === sourceChronologyLayerForLevel(activeSourceChronologyLevel)?.key) {
            renderSourceRecordConcentrationLayer(layer);
            return;
          }
          const clusterGroup = createClusterGroup(layer);
          const neighborGroup = L.layerGroup();
          layer.features.forEach((feature) => {
            if (!pointFeatureVisible(layer, feature)) return;
            const neighborContext = isRetainedNeighborContext(layer, feature);
            const coordinates = featureCoordinatePair(feature);
            if (!coordinates) return;
            const latLng = [coordinates.latitude, coordinates.longitude];
            const scientificSignals = scientificSignalsForFeature(feature);
            const nativeModel = layer.semantic_role === 'exploratory_lra_model_anchor';
            const nativeRole = nativeModel && nativeLraController.selectedRowsForAnchor(feature.record_id)[0]?.role;
            const marker = nativeModel
              ? L.marker(latLng, {pane: 'pointPane', title: `Exploratory ${nativeRole} model; synthetic display anchor`,
                  icon: L.divIcon({className: 'atlas-native-lra-marker', html: `<span data-lra-anchor-id="${escapeHtml(feature.record_id)}" data-lra-role="${escapeHtml(nativeRole)}" style="display:block;background:white;border:2px solid #111827;border-radius:4px;text-align:center;font-weight:bold;color:#111827">${nativeRole === 'regional' ? 'R' : 'L'}</span>`, iconSize: [26, 26]})})
              : scientificSignals.length
              ? L.marker(latLng, {
                  pane: 'pointPane',
                  icon: L.divIcon({
                    className: 'atlas-scientific-marker',
                    html: scientificSignals.map((signal) => `<span class="scientific-cue" data-cue="${escapeHtml(signal.non_color_cue)}" style="color:${escapeHtml(signal.color)}" title="${escapeHtml(signal.label)}">${escapeHtml(scientificCueGlyph(signal.non_color_cue))}</span>`).join(''),
                    iconSize: [Math.max(24, scientificSignals.length * 22), 24],
                  }),
                })
              : L.circleMarker(latLng, { pane: 'pointPane', radius: layer.key === 'aadr' ? 4.5 : 6, color: layer.style.stroke, weight: 1.3, fillColor: layer.style.fill, fillOpacity: 0.92 });
            const popupFeature = nativeModel ? {...feature, popup_rows: [
              ...(feature.popup_rows || []).filter(row => !String(row.label).startsWith('Mean ')),
              ...nativeLraController.selectedRowsForAnchor(feature.record_id).filter(row => row.statistic === 'mean').map(row => ({
                label: `Mean ${row.taxon}${row.spatial_support.ring ? ` · ring ${row.spatial_support.ring.inner_m}–${row.spatial_support.ring.outer_m} m` : ''} (${row.native_unit})`,
                value: row.native_value === null ? 'N/A (source statistic unavailable)' : row.native_value,
              })),
            ]} : feature;
            if (neighborContext) {
              if (typeof marker.setStyle === 'function') marker.setStyle({ opacity: 0.45, fillOpacity: 0.25 });
              else marker.setOpacity(0.45);
              marker.bindTooltip(`Neighbor context · ${escapeHtml(feature.country)}`, { permanent: true, direction: 'top', className: 'atlas-neighbor-context-label' });
            }
            marker.bindPopup(`${neighborContext ? `<div class="popup-grid"><div><strong>Display role</strong> Neighbor context · ${escapeHtml(feature.country)}</div></div>` : ''}${popupHtml(popupFeature, layer)}`, { maxWidth: 360 });
            const entry = { layer, feature, marker, neighborContext };
            marker.on('click', () => {
              focusPointAtVisibleIndex(visiblePointEntries.indexOf(entry));
            });
            if (neighborContext) neighborGroup.addLayer(marker); else clusterGroup.addLayer(marker);
            visiblePointEntries.push(entry);
            if (evidenceDisplayDecision(activeEvidenceDisplay).drawNodes && !neighborContext && layer.circle_enabled && diameterKm > 0) {
              const circle = L.circle(latLng, { pane: 'circlePane', radius: radiusMeters, color: layer.style.circleStroke, weight: 1, opacity: 0.55, fillColor: layer.style.circleFill, fillOpacity: 0.12, interactive: false });
              circleLayerGroup.addLayer(circle);
            }
          });
          if (evidenceDisplayDecision(activeEvidenceDisplay).drawNodes && clusterGroup.getLayers().length > 0) { clusterGroup.addTo(map); renderedPointGroups.push(clusterGroup); }
          if (evidenceDisplayDecision(activeEvidenceDisplay).drawNodes && neighborGroup.getLayers().length > 0) { neighborGroup.addTo(map); renderedPointGroups.push(neighborGroup); }
        });
      }
      function scientificSignalById(signalId) {
        return SCIENTIFIC_SIGNALS.find((signal) => signal.signal_id === signalId) || null;
      }
      function edgeScientificPresentation(edge) {
        const status = edge.candidate_status || edge.status || 'candidate';
        const directionalStatus = ['definite_candidate', 'possible_candidate'].includes(status);
        const native = Object.prototype.hasOwnProperty.call(edge, 'candidate_status');
        const directional = directionalStatus && (native ? edge.directional_arrow_allowed === true : edge.directional_arrow_allowed !== false);
        const indeterminate = status === 'indeterminate_order';
        const refused = ['unresolved', 'excluded_spatial', 'excluded_temporal_nonpositive', 'excluded_temporal_too_large'].includes(status);
        const scenario = typeof edge.scenario_id === 'string' && edge.scenario_id.trim() ? edge.scenario_id : null;
        const candidateInterpretation = native && directional && scenario
          ? `Under scenario ${scenario}, these governed observations form a candidate propagation link. This relation is consistent with spatiotemporal succession; it does not demonstrate a migration route, transport mechanism, local establishment, cultivation, or causation.`
          : 'Candidate succession under the governed rule; not proof of migration or causation.';
        const interpretation = indeterminate
          ? 'Order is indeterminate; this endpoint connection has no direction and is not a migration route.'
          : refused ? `No candidate succession is admitted for ${status}; this endpoint connection is not proof of migration or causation.`
          : candidateInterpretation;
        const wholePollenLimit = native && edge.resolution === 'whole_pollen'
          ? ' Whole-pollen comparison is an exploratory aggregate of heterogeneous taxa; it does not establish taxon-level equivalence.'
          : '';
        return {
          status,
          dashArray: indeterminate ? '2 7' : status === 'possible_candidate' ? '10 7' : null,
          separator: directional ? ' → ' : ' — ',
          label: indeterminate ? 'Indeterminate order (no direction)' : status,
          relationLabel: directional ? 'Candidate relation' : 'Endpoint connection',
          interpretation: interpretation + wholePollenLimit,
        };
      }
      function providedEdgeFields(edge, keys) {
        return Object.fromEntries(keys.filter((key) => Object.prototype.hasOwnProperty.call(edge, key)).map((key) => [key, edge[key]]));
      }
      function mergeEdgeDetailTab(tab, fields) {
        if (!Object.keys(fields).length) return tab;
        const merged = { ...tab, ...fields };
        if (tab?.status === 'unavailable') {
          if (!Object.prototype.hasOwnProperty.call(fields, 'status')) merged.status = 'partial';
          merged.evidence_availability = 'partial';
          if (Object.prototype.hasOwnProperty.call(tab, 'reason_code')) merged.availability_reason_code = tab.reason_code;
        }
        return merged;
      }
      let edgeRenderSummary = { shown: 0, viewport_count: 0, limit: 128 };
      // Limit Leaflet primitives without changing scientific selection or exports.
function atlasEdgeIntersectsViewport(map, coordinates) {
  const [first, second] = coordinates.map((point) => map.latLngToContainerPoint(point));
  const size = map.getSize();
  if (![first.x, first.y, second.x, second.y, size.x, size.y].every(Number.isFinite) || size.x < 0 || size.y < 0) {
    throw new Error('Atlas edge rendering requires finite viewport coordinates.');
  }
  // Clip the displayed projected segment, including crossings with both ends outside.
  // Projection (including any world offset) belongs to the same map as L.polyline.
  let start = 0, end = 1;
  for (const [origin, delta, maximum] of [
    [first.x, second.x - first.x, size.x],
    [first.y, second.y - first.y, size.y],
  ]) {
    if (delta === 0) {
      if (origin < 0 || origin > maximum) return false;
    } else {
      const a = -origin / delta, b = (maximum - origin) / delta;
      start = Math.max(start, Math.min(a, b));
      end = Math.min(end, Math.max(a, b));
      if (start > end) return false;
    }
  }
  return true;
}
function atlasEdgeRenderSelection(edges, entriesByRecordId, zoom, coordinatePair, intersectsViewport) {
  if (!Number.isFinite(zoom)) throw new Error('Atlas edge rendering requires a finite zoom.');
  const limit = zoom < 5 ? 128 : zoom < 8 ? 256 : 512;
  const eligible = edges.flatMap((edge) => {
    const source = entriesByRecordId.get(String(edge.source_record_id));
    const target = entriesByRecordId.get(String(edge.target_record_id));
    if (!source || !target) return [];
    const a = coordinatePair(source.feature), b = coordinatePair(target.feature);
    if (!a || !b) return [];
    const coordinates = [a, b].map((point) => [point.latitude, point.longitude]);
    if (intersectsViewport && !intersectsViewport(coordinates)) return [];
    return [{ edge, source, target }];
  });
  // Uncapped order is retained; capped membership uses literal scientific IDs,
  // independent of publication order, locale, or analytical rank.
  const ordered = eligible.length <= limit ? eligible : [...eligible].sort((left, right) => {
    const a = String(left.edge.edge_id), b = String(right.edge.edge_id);
    return a < b ? -1 : a > b ? 1 : 0;
  });
  return { rows: ordered.slice(0, limit), viewport_count: eligible.length, limit };
}

function edgeEvidencePopupHtml(edge, signal, presentation) {
  const text = value => escapeHtml(typeof value === 'string' && value.trim() ? value : 'Unavailable');
  const number = value => typeof value === 'number' && Number.isFinite(value);
  const pair = relationEndpointPair(edge);
  function age(event) {
    if (!event || event.comparability_status !== 'comparable') return 'Unavailable (no comparable canonical event age)';
    const [younger, older] = [event.younger_bp, event.older_bp];
    if (![younger, older].every(value => number(value) && value >= 0) || younger > older) return 'Unavailable (invalid canonical event interval)';
    return `${younger === older ? younger : `${younger}–${older}`} BP`;
  }
  const directional = presentation.separator === ' → ';
  const countryPosture = Object.prototype.hasOwnProperty.call(edge, 'candidate_status') && typeof edge.cross_border === 'boolean'
    ? edge.cross_border ? 'Cross-border' : 'Domestic' : 'Country-pair posture unavailable';
  const endpoints = ['source', 'target'].map((prefix, index) => {
    const event = pair?.[index];
    const label = directional ? index === 0 ? 'Older endpoint' : 'Younger endpoint' : index === 0 ? 'Source endpoint' : 'Target endpoint';
    return `<div><strong>${label}</strong> ${text(event?.site_id)} · ${escapeHtml(age(event))}</div>`;
  }).join('');
  const distance = number(edge.distance_km_unrounded) && edge.distance_km_unrounded >= 0
    ? `${edge.distance_km_unrounded} km` : 'Unavailable';
  const [minimum, maximum] = [edge.minimum_lag_years, edge.maximum_lag_years];
  const lag = [minimum, maximum].every(number) && minimum <= maximum
    ? `${minimum} to ${maximum} years` : 'Unavailable';
  const details = edge.relation_details;
  const thresholds = details?.basis === 'derived_governed_evaluator_branch_explanation'
    && details.scenario_id === edge.scenario_id
    && [details.maximum_distance_km, details.maximum_lag_years].every(value => number(value) && value >= 0)
    ? ` · maximum distance ${details.maximum_distance_km} km; maximum lag ${details.maximum_lag_years} years` : '';
  return `<div class="popup-grid"><div><strong>${directional ? 'Candidate spatiotemporal succession' : escapeHtml(presentation.relationLabel)}</strong> ${escapeHtml(edge.edge_id)}</div><div><strong>Signal and resolution</strong> ${text(signal?.label || edge.signal_id)} · ${text(edge.resolution)}</div>${endpoints}<div><strong>Countries</strong> ${escapeHtml(countryPosture)} · ${text(edge.source_country)}${presentation.separator}${text(edge.target_country)}</div><div><strong>Distance</strong> ${escapeHtml(distance)}</div><div><strong>Directional lag bounds</strong> ${escapeHtml(lag)}</div><div><strong>Scenario</strong> ${text(edge.scenario_id)}${escapeHtml(thresholds)}</div><div><strong>Certainty / interval status</strong> ${escapeHtml(presentation.label)}</div><div><strong>Interpretation</strong> ${escapeHtml(presentation.interpretation)}</div><button type="button" class="inline-button" data-compare-edge="${escapeHtml(edge.edge_id)}">Compare evidence</button></div>`;
}

function renderRelationDetails(tab) {
  const object = (value) => value && typeof value === 'object' && !Array.isArray(value);
  const text = (value) => escapeHtml(value === undefined ? 'Unavailable (not supplied)' : value === null ? 'null (no numeric value)' : typeof value === 'object' ? JSON.stringify(value) : String(value));
  const pair = relationEndpointPair(tab), [source, target] = pair || [];
  const endpoints = pair !== null;
  const fields = [
    ['Event ID', 'event_id'], ['Source record ID', 'source_record_id'],
    ['Site ID', 'site_id'], ['Source family', 'source_family'],
    ['Source snapshot', 'source_snapshot_id'], ['Country', 'country_code'],
    ['Chronology claim ID', 'chronology_claim_id'], ['Younger BP', 'younger_bp'],
    ['Older BP', 'older_bp'], ['Comparability', 'comparability_status'],
    ['Event type', 'event_type'], ['Resolution', 'resolution'], ['Feature', 'feature_key'],
  ];
  const endpointHtml = endpoints
    ? `<div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>Canonical relation endpoints</caption><thead><tr><th scope="col">Field</th><th scope="col">Source endpoint</th><th scope="col">Target endpoint</th></tr></thead><tbody>${fields.map(([label, key]) => `<tr><th scope="row">${text(label)}</th><td>${text(source[key])}</td><td>${text(target[key])}</td></tr>`).join('')}</tbody></table></div>`
    : '<p>Canonical endpoint comparison unavailable: matching event, source record and site identities were not supplied. Map-node ages are not substituted.</p>';
  const details = tab?.relation_details;
  const ids = ['spatial_threshold', 'chronology_available', 'positive_lag_possible', 'positive_lag_certain', 'lag_within_limit_possible', 'lag_within_limit_certain'];
  const states = new Set(['pass', 'qualify', 'refuse', 'not_evaluated', 'unavailable']);
  const number = (value) => typeof value === 'number' && Number.isFinite(value);
  const supplied = endpoints && object(details)
    && details.basis === 'derived_governed_evaluator_branch_explanation'
    && typeof tab.scenario_id === 'string' && tab.scenario_id.trim() && details.scenario_id === tab.scenario_id
    && number(details.maximum_distance_km) && details.maximum_distance_km >= 0
    && number(details.maximum_lag_years) && details.maximum_lag_years >= 0
    && Array.isArray(details.predicates) && details.predicates.length === ids.length
    && details.predicates.every((row, index) => object(row) && row.predicate_id === ids[index]
      && typeof row.label === 'string' && row.label.trim() && states.has(row.status)
      && (row.observed === null || number(row.observed)) && (row.threshold === null || number(row.threshold)));
  const predicateHtml = supplied
    ? `<p>Scenario ${text(details.scenario_id)}: maximum distance ${text(details.maximum_distance_km)} km; maximum lag ${text(details.maximum_lag_years)} years. Derived governed evaluator branch explanation, not recorded execution telemetry. These supplied statuses do not confer scientific admission.</p><div class="focus-detail-table-wrap"><table class="focus-detail-table"><caption>Scenario predicates</caption><thead><tr><th scope="col">Predicate</th><th scope="col">Status</th><th scope="col">Observed value</th><th scope="col">Threshold</th></tr></thead><tbody>${details.predicates.map((row) => `<tr><th scope="row">${text(row.label)}</th><td>${text(row.status)}</td><td>${text(row.observed)}</td><td>${text(row.threshold)}</td></tr>`).join('')}</tbody></table></div><p>not_evaluated denotes a later check skipped by the evaluator branch; unavailable denotes missing evidence. Neither means pass. Endpoint lines are not reconstructed movement paths.</p>`
    : '<p>Scenario predicate explanation unavailable: this record has no complete, matching governed explanation. Legacy or missing checks are not inferred from a candidate label.</p>';
  return `<section aria-label="Relation endpoint and predicate comparison">${endpointHtml}${predicateHtml}</section>`;
}

function relationEndpointPair(tab) {
  const object = value => value && typeof value === 'object' && !Array.isArray(value);
  const source = tab?.source_event, target = tab?.target_event;
  const joined = (event, prefix) => object(event)
    && ['event_id', 'source_record_id', 'site_id'].every((key) => typeof event[key] === 'string' && event[key].trim()
      && event[key] === tab[`${prefix}_${key === 'source_record_id' ? 'record_id' : key}`]);
  return joined(source, 'source') && joined(target, 'target') ? [source, target] : null;
}


// A shared relation is restored only within its published build and exact scenario.
const edgeFocusLoadState = {request: 0, generation: 0, restoring: null};
function publishedEdgeFocusBuild() {
  const build = typeof STATIC_ATLAS_BOOTSTRAP === 'undefined' ? null : STATIC_ATLAS_BOOTSTRAP.build_id;
  return typeof build === 'string' && /^atlas-[a-f0-9]{64}$/.test(build) ? build : null;
}
function edgeFocusFromHash(params, allowedTabs) {
  const keys = ['focus_edge', 'focus_scenario', 'focus_build'];
  if (!keys.some(key => params.has(key))) return null;
  const invalid = {kind: 'edge', unavailable: true};
  if (keys.some(key => params.getAll(key).length !== 1 || !params.get(key).trim())
    || ['focus_layer', 'focus_feature', 'focus_record'].some(key => params.has(key))
    || params.getAll('focus_tab').length > 1) return invalid;
  const tab = params.get('focus_tab') || 'overview';
  if (!allowedTabs.includes(tab)) return invalid;
  return {kind: 'edge', edgeId: params.get('focus_edge'), scenarioId: params.get('focus_scenario'), atlasBuildId: params.get('focus_build'), tab};
}
function writeEdgeFocusHash(params, focus, tab, build) {
  if (focus?.kind !== 'edge' || focus.edgeShareable !== true || typeof build !== 'string'
    || !/^atlas-[a-f0-9]{64}$/.test(build) || focus.atlasBuildId !== build
    || ![focus.edgeId, focus.scenarioId].every(value => typeof value === 'string' && value.trim())) return false;
  params.set('focus_edge', focus.edgeId);
  params.set('focus_scenario', focus.scenarioId);
  params.set('focus_build', build);
  if (tab !== 'overview') params.set('focus_tab', tab);
  return true;
}
function availableEdgeFocus(edgeId, edges, entries) {
  const matches = edges.filter(edge => edge.edge_id === edgeId);
  if (matches.length !== 1) return null;
  const edge = matches[0];
  const endpoints = ['source_record_id', 'target_record_id'].map(key => entries.filter(entry => entry.feature.record_id === edge[key]));
  return endpoints.every(rows => rows.length === 1) ? {edge, source: endpoints[0][0]} : null;
}
function edgeFocusSelection(request, build, edges, entries) {
  if (!request || request.unavailable || !build || request.atlasBuildId !== build
    || ![request.edgeId, request.scenarioId].every(value => typeof value === 'string' && value.trim())) return null;
  const selected = availableEdgeFocus(request.edgeId, edges, entries);
  return selected && Object.prototype.hasOwnProperty.call(selected.edge, 'candidate_status')
    && selected.edge.scenario_id === request.scenarioId ? selected : null;
}


function relationFilterFields() {
  return [
    ['scenario', 'relation_scenario', 'scenario_id', 'scenario'],
    ['status', 'relation_status', 'candidate_status', 'candidate status'],
    ['sourceCountry', 'relation_source_country', 'source_country_code', 'stored source endpoint country'],
    ['targetCountry', 'relation_target_country', 'target_country_code', 'stored target endpoint country'],
  ];
}
function relationFiltersFromHash(params) {
  const filters = {invalid: []};
  relationFilterFields().forEach(([key, parameter]) => {
    filters[key] = params.has(parameter) ? params.get(parameter) : null;
    if (params.getAll(parameter).length > 1) filters.invalid.push(key);
  });
  return filters;
}
const activeRelationFilters = relationFiltersFromHash(new URLSearchParams());
function resetRelationFilters() {
  Object.assign(activeRelationFilters, relationFiltersFromHash(new URLSearchParams()));
}
function writeRelationFilterHash(params, filters) {
  relationFilterFields().forEach(([key, parameter]) => {
    if (filters.invalid.includes(key)) {
      params.append(parameter, filters[key]);
      params.append(parameter, filters[key]);
    } else if (filters[key] !== null) params.set(parameter, filters[key]);
  });
}
function relationFilterSelection(records, filters) {
  const fields = relationFilterFields();
  const native = records.filter(row => Object.prototype.hasOwnProperty.call(row, 'candidate_status'));
  const catalog = Object.fromEntries(fields.map(([key, , column]) => [key,
    [...new Set(native.map(row => row[column]).filter(value => typeof value === 'string' && value.trim()
      && (!['sourceCountry', 'targetCountry'].includes(key) || ['DK', 'FI', 'NO', 'SE'].includes(value))))].sort(),
  ]));
  const unavailable = fields.filter(([key]) => filters.invalid.includes(key)
    || (filters[key] !== null && !catalog[key].includes(filters[key]))).map(([key]) => key);
  const selected = unavailable.length ? [] : records.filter(row => fields.every(([key, , column]) => filters[key] === null
    || (Object.prototype.hasOwnProperty.call(row, 'candidate_status') && row[column] === filters[key])));
  return {catalog, unavailable, selected};
}
function relationFilterMetadata(records, filters) {
  return {...Object.fromEntries(relationFilterFields().map(([key]) => [key, filters[key]])),
    unavailable_fields: relationFilterSelection(records, filters).unavailable};
}
function relationFilterOptions(values, selected, unavailable, label) {
  return (unavailable ? `<option value="" selected disabled>Unavailable shared ${escapeHtml(label)}</option>` : '')
    + `<option value="" ${!unavailable && selected === null ? 'selected' : ''}>All retained</option>`
    + values.map(value => `<option value="${escapeHtml(value)}" ${!unavailable && selected === value ? 'selected' : ''}>${escapeHtml(value)}</option>`).join('');
}
function relationScenarioThresholds(records, selectedScenario) {
  const scenarios = relationFilterSelection(records, relationFiltersFromHash(new URLSearchParams())).catalog.scenario;
  const selected = selectedScenario === null ? scenarios : scenarios.filter(id => id === selectedScenario);
  if (!selected.length) return '<p>Scenario rule and thresholds unavailable.</p>';
  return selected.map(id => {
    const rows = records.filter(row => Object.prototype.hasOwnProperty.call(row, 'candidate_status') && row.scenario_id === id);
    const details = rows.map(row => row.relation_details);
    const valid = details.every(value => value && value.basis === 'derived_governed_evaluator_branch_explanation' && value.scenario_id === id
      && [value.maximum_distance_km, value.maximum_lag_years].every(number => typeof number === 'number' && Number.isFinite(number) && number >= 0));
    const consistent = valid && details.every(value => value.maximum_distance_km === details[0].maximum_distance_km && value.maximum_lag_years === details[0].maximum_lag_years);
    const rule = details[0]?.rule_type;
    const ruleLabel = typeof rule === 'string' && rule.trim() && details.every(value => value?.rule_type === rule) ? rule : 'unavailable';
    return `<p><strong>${escapeHtml(id)}</strong> · Rule: ${escapeHtml(valid ? ruleLabel : 'unavailable')} · ${consistent
      ? `maximum distance ${escapeHtml(String(details[0].maximum_distance_km))} km; maximum lag ${escapeHtml(String(details[0].maximum_lag_years))} years`
      : 'Thresholds unavailable: missing or conflicting supplied scenario metadata.'}</p>`;
  }).join('');
}

      // Select supplied event definitions without estimating or reclassifying events.
function relationEventDefinitionTuple(value) {
  if (!Array.isArray(value) || value.length !== 4
    || !value.every(part => typeof part === 'string' && part.trim())
    || !['reported_positive_observation', 'derived_first_observed', 'derived_threshold_crossing'].includes(value[0])) return null;
  return value;
}
function relationEventDefinitionValue(value) {
  if (typeof value !== 'string') return null;
  try {
    const tuple = relationEventDefinitionTuple(JSON.parse(value));
    return tuple === null ? null : JSON.stringify(tuple);
  } catch { return null; }
}
function relationEventDefinitionFromHash(params) {
  const values = params.getAll('relation_event_definition');
  const value = values.length ? values[0] : null;
  return {value, invalid: values.length > 1 || (value !== null && relationEventDefinitionValue(value) === null), duplicate: values.length > 1};
}
function writeRelationEventDefinitionHash(params, state) {
  params.delete('relation_event_definition');
  if (state.value !== null) {
    params.append('relation_event_definition', state.value);
    if (state.duplicate) params.append('relation_event_definition', state.value);
  }
}
function relationEventDefinitionSelection(edges, state) {
  const result = {selected: [], catalog: [], retainedCount: Array.isArray(edges) ? edges.length : null,
    availableCount: 0, missingCount: 0, conflictingCount: 0, unavailable: false};
  if (!Array.isArray(edges)) return {...result, unavailable: true};
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const text = value => typeof value === 'string' && value.trim();
  const fields = ['event_type', 'threshold_profile_id', 'measurement_semantics_id', 'method_compatibility_key'];
  const identities = new Map(), conflicting = new Set(), ids = new Map();
  const rows = edges.map(edge => {
    const row = {edge, status: 'missing', value: null, events: []};
    if (!object(edge)) return row;
    if (text(edge.edge_id)) {
      if (ids.has(edge.edge_id)) { ids.get(edge.edge_id).status = 'conflicting'; row.status = 'conflicting'; }
      else ids.set(edge.edge_id, row);
    }
    if (!Object.hasOwn(edge, 'candidate_status')) return row;
    if (!text(edge.edge_id)) return {...row, status: 'conflicting'};
    const details = edge.relation_details;
    if (!object(details) || details.event_definition === undefined || details.event_definition === null) return row;
    if (details.basis !== 'derived_governed_evaluator_branch_explanation' || !text(edge.scenario_id)
      || details.scenario_id !== edge.scenario_id || !object(details.event_definition)) return {...row, status: 'conflicting'};
    const tuple = fields.map(key => details.event_definition[key]);
    if (tuple.some(value => value === undefined || value === null)) return row;
    if (relationEventDefinitionTuple(tuple) === null || edge.threshold_profile_id !== tuple[1]) return {...row, status: 'conflicting'};
    for (const side of ['source', 'target']) {
      const event = edge[`${side}_event`];
      if (event === undefined || event === null) return row;
      if (!object(event)) return {...row, status: 'conflicting'};
      const pairs = [['event_id', `${side}_event_id`], ['site_id', `${side}_site_id`],
        ['source_record_id', `${side}_record_id`], ['resolution', 'resolution'], ['feature_key', 'feature_key']];
      if (!pairs.every(([key, column]) => text(edge[column]) && event[key] === edge[column])) return {...row, status: 'conflicting'};
      if (!fields.every((key, index) => (index >= 2 && !Object.hasOwn(event, key)) || event[key] === tuple[index])) return {...row, status: 'conflicting'};
      const signature = JSON.stringify([...pairs.map(([key]) => event[key]), ...tuple]);
      if (identities.has(event.event_id) && identities.get(event.event_id) !== signature) conflicting.add(event.event_id);
      identities.set(event.event_id, signature);
      row.events.push(event.event_id);
    }
    if (row.status !== 'conflicting') { row.status = 'available'; row.value = JSON.stringify(tuple); }
    return row;
  });
  const catalog = new Map();
  for (const row of rows) {
    if (row.events.some(id => conflicting.has(id))) row.status = 'conflicting';
    result[`${row.status}Count`]++;
    if (row.status === 'available') catalog.set(row.value, (catalog.get(row.value) || 0) + 1);
  }
  result.catalog = [...catalog].sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0).map(([value, count]) => {
    const [type, threshold, measurement, method] = JSON.parse(value);
    return {value, count, label: `${type.replaceAll('_', ' ')}; threshold ${threshold}; measurement ${measurement}; method compatibility ${method}`};
  });
  const requested = state.value === null ? null : relationEventDefinitionValue(state.value);
  result.unavailable = state.invalid === true || state.duplicate === true || (state.value !== null && (requested === null || !catalog.has(requested)));
  result.selected = result.unavailable ? [] : rows.filter(row => requested === null || (row.status === 'available' && row.value === requested)).map(row => row.edge);
  return result;
}
function renderRelationEventDefinitionOptions(data, state) {
  const text = value => escapeHtml(String(value));
  const requested = relationEventDefinitionValue(state.value);
  return (data.unavailable ? '<option value="" selected disabled>Unavailable shared event definition</option>' : '')
    + `<option value="" ${!data.unavailable && state.value === null ? 'selected' : ''}>All retained</option>`
    + data.catalog.map(row => `<option value="${text(row.value)}" ${!data.unavailable && row.value === requested ? 'selected' : ''}>${text(row.label)} (${row.count})</option>`).join('');
}

const activeRelationEventDefinition = relationEventDefinitionFromHash(new URLSearchParams());
function resetRelationEventDefinition() {
  Object.assign(activeRelationEventDefinition, relationEventDefinitionFromHash(new URLSearchParams()));
}
function relationEventDefinitionMetadata(edges, state) {
  return {...state, unavailable: relationEventDefinitionSelection(edges, state).unavailable};
}

      // Drawing choices do not select, classify or discard retained evidence.
function evidenceDisplayState(values) {
  const requested = Array.isArray(values) && values.every(value => typeof value === 'string') ? [...values] : null;
  const mode = requested === null || requested.length > 1 ? null : requested.length ? requested[0] : 'both';
  const available = ['nodes', 'edges', 'both'].includes(mode);
  const reason = available ? null : mode === 'density'
    ? 'Density is unavailable: no governed density product is supplied. Source-record concentration and modeled overlays are different products.'
    : 'Drawing mode unavailable: the shared selection must contain one known, nonempty mode.';
  return Object.freeze({values: requested === null ? null : Object.freeze(requested), mode,
    status: available ? 'available' : 'unavailable', reason});
}

function evidenceDisplayFromHash(params) {
  return evidenceDisplayState(params.getAll('display_mode'));
}

function resetEvidenceDisplay() {
  return evidenceDisplayState([]);
}

function evidenceDisplayDecision(state) {
  const current = evidenceDisplayState(state?.values);
  return {mode: current.mode, status: current.status, reason: current.reason,
    drawNodes: current.status === 'available' && current.mode !== 'edges',
    drawEdges: current.status === 'available' && current.mode !== 'nodes'};
}

function writeEvidenceDisplayHash(params, state) {
  const current = evidenceDisplayState(state?.values);
  params.delete('display_mode');
  if (current.values === null) params.append('display_mode', '');
  else current.values.forEach(value => params.append('display_mode', value));
  return params;
}

function evidenceDisplayMetadata(state) {
  const current = evidenceDisplayState(state?.values);
  return {...evidenceDisplayDecision(current), requestedValues: current.values === null ? null : [...current.values],
    scope: 'drawing_only_retained_evidence_unchanged'};
}

function renderEvidenceDisplayControls(state) {
  const current = evidenceDisplayState(state?.values), text = value => escapeHtml(String(value));
  const options = [['nodes', 'Nodes'], ['edges', 'Edges'], ['both', 'Nodes and edges'], ['density', 'Density (unavailable)']];
  const placeholder = current.mode === null || !options.some(([value]) => value === current.mode)
    ? '<option value="" selected disabled>Unavailable shared drawing mode</option>' : '';
  const detail = current.reason === null ? '' : ` ${text(current.reason)}`;
  return `<label for="evidence-display-mode">Evidence drawing mode</label><select id="evidence-display-mode" aria-describedby="evidence-display-status">${placeholder}${options.map(([value, label]) => `<option value="${value}"${current.mode === value ? ' selected' : ''}>${label}</option>`).join('')}</select><p id="evidence-display-status" role="status">Drawing only: retained records, endpoint matching, counts, detail views and data exports are unchanged. Other context layers remain separate.${detail}</p>`;
}

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

      function renderEvidenceDisplayPanel() {
        const container = document.getElementById('evidence-display-controls');
        const decision = evidenceDisplayDecision(activeEvidenceDisplay);
        container.innerHTML = renderEvidenceDisplayControls(activeEvidenceDisplay);
        container.querySelector('#evidence-display-mode').addEventListener('change', event => {
          activeEvidenceDisplay = evidenceDisplayState([event.target.value]);
          renderMapState();
        });
        const mapElement = document.getElementById('map');
        mapElement.dataset.evidenceDisplayMode = decision.mode || 'unavailable';
        mapElement.dataset.evidenceDisplayStatus = decision.status;
        mapElement.dataset.drawingEnabledPointCount = String(decision.drawNodes ? visiblePointEntries.length : 0);
        topbarStatePill.setAttribute('role', decision.status === 'unavailable' ? 'alert' : 'status');
        if (decision.status === 'unavailable') topbarStatePill.textContent = decision.reason;
        else if (decision.mode !== 'both') topbarStatePill.textContent = `${visiblePointEntries.length} display-eligible point entries · Drawing ${decision.mode} only`;
      }

      let evidenceTools = null, evidenceToolsRequest = null, evidenceToolsError = null;
      function currentEvidenceTools() {
        if (!evidenceTools && typeof relationSummaryData === 'function') {
          evidenceTools = Object.freeze({countryData: relationSummaryData, countryHtml: renderRelationSummary,
            timeData: relationTimeSummaryData, timeHtml: renderRelationTimeSummary,
            pickerCatalog: scientificPickerCatalog, pickerSearch: scientificPickerSearch,
            pickerInitial: scientificPickerInitialState, pickerAction: scientificPickerAction,
            pickerHtml: renderScientificPicker, pickerMount: mountScientificPicker, sourceDetails: createSourceRecordDetails,
            selectionExport: prepareAtlasSelectionExport});
        }
        return evidenceTools;
      }
      function evidenceToolsDescriptor() {
        const row = STATIC_ATLAS_BOOTSTRAP.runtime?.optional_controllers?.evidence_tools;
        if (!row || typeof row !== 'object' || Array.isArray(row)
          || Object.keys(row).sort().join('|') !== 'byte_count|integrity|path'
          || typeof row.path !== 'string' || typeof row.integrity !== 'string'
          || !/^[A-Za-z0-9][A-Za-z0-9._-]*[.]atlas-evidence-tools[.][a-f0-9]{16}[.]js$/.test(row.path)
          || !/^sha256-[A-Za-z0-9+/]{43}=$/.test(row.integrity)
          || !Number.isSafeInteger(row.byte_count) || row.byte_count <= 0 || row.byte_count > 524288) {
          throw new Error('Evidence tools transport identity is unavailable. Keep all atlas files from the same build together.');
        }
        return row;
      }
      function loadEvidenceTools() {
        if (currentEvidenceTools()) return Promise.resolve(evidenceTools);
        if (evidenceToolsRequest) return evidenceToolsRequest;
        evidenceToolsRequest = Promise.resolve().then(() => {
          const row = evidenceToolsDescriptor();
          if (!['http:', 'https:', 'file:'].includes(window.location.protocol)) throw new Error('Evidence tools require HTTP, HTTPS or a local file.');
          return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = `./${row.path}`;
            if (['http:', 'https:'].includes(window.location.protocol)) {
              script.integrity = row.integrity;
              script.crossOrigin = 'anonymous';
            }
            // Local-file script transport follows the main runtime policy; SRI is
            // enforced by the browser for HTTP and HTTPS distributions.
            script.addEventListener('load', () => {
              try {
                if (typeof globalThis.BijuxPollenomicsEvidenceTools !== 'function') throw new Error('Evidence tools did not register.');
                const tools = globalThis.BijuxPollenomicsEvidenceTools(escapeHtml, scientificCueGlyph);
                if (!tools || !['countryData', 'countryHtml', 'timeData', 'timeHtml', 'pickerCatalog', 'pickerSearch', 'pickerInitial', 'pickerAction', 'pickerHtml', 'pickerMount', 'sourceDetails', 'selectionExport'].every(key => typeof tools[key] === 'function')) throw new Error('Evidence tools interface is incomplete.');
                evidenceTools = tools;
                resolve(tools);
              } catch (error) { reject(error); }
            }, {once: true});
            script.addEventListener('error', () => reject(new Error('Evidence tools could not be loaded. Keep all atlas files together and reload.')), {once: true});
            document.head.appendChild(script);
          });
        }).catch(error => { evidenceToolsError = String(error.message || error); throw error; });
        return evidenceToolsRequest;
      }
      function renderRelationTimeSummaryPanel() {
        const container = document.getElementById('relation-time-summary');
        if (!container) return;
        const tools = currentEvidenceTools();
        container.innerHTML = tools ? tools.timeHtml(tools.timeData(visibleGovernedEdges()))
          : `<p>${escapeHtml(evidenceToolsError || 'Open this panel to load the endpoint age summary.')}</p>`;
      }
      function renderEvidenceToolPanels() {
        renderRelationCountrySummary();
        renderRelationTimeSummaryPanel();
      }
      function renderRelationCountrySummary() {
        const container = document.getElementById('relation-country-summary');
        if (!container) return;
        const tools = currentEvidenceTools();
        if (!tools) {
          container.innerHTML = `<p>${escapeHtml(evidenceToolsError || 'Open this panel to load the country summary.')}</p>`;
          return;
        }
        const edges = visibleGovernedEdges();
        const href = (edgeId, scenarioId) => {
          if (!atlasURLState.canPublish()) return null;
          const build = publishedEdgeFocusBuild();
          if (!edgeFocusSelection({edgeId, scenarioId, atlasBuildId: build}, build, edges, visiblePointEntries)) return null;
          const params = atlasSelectionHashParams();
          ['focus_layer', 'focus_feature', 'focus_record', 'focus_tab'].forEach(key => params.delete(key));
          if (!writeEdgeFocusHash(params, {kind: 'edge', edgeId, scenarioId, atlasBuildId: build, edgeShareable: true}, 'relation', build)) return null;
          return `#${params.toString()}`;
        };
        container.innerHTML = tools.countryHtml(tools.countryData(edges), href, DETAIL_TABLE_PAGE_SIZE);
      }
      async function openEdgeDetail(edge, source, compare = false, fromSharedLink = false) {
        if (!fromSharedLink) pendingEdgeFocus = null;
        const signal = scientificSignalById(edge.signal_id), presentation = edgeScientificPresentation(edge);
        const request = ++edgeFocusLoadState.request, generation = edgeFocusLoadState.generation;
        const loadedTabs = await detailTabsForRecordId(String(edge.edge_id));
        const currentEdges = visibleGovernedEdges().filter(row => row.edge_id === edge.edge_id);
        if (request !== edgeFocusLoadState.request || generation !== edgeFocusLoadState.generation
          || !visiblePointEntries.includes(source)
          || !['source_record_id', 'target_record_id'].every(key => visiblePointEntries.filter(entry => entry.feature.record_id === edge[key]).length === 1)
          || currentEdges.length !== 1 || currentEdges[0] !== edge) return false;
        const tabs = loadedTabs.overview?.reason_code === 'detail_record_not_indexed'
          ? unavailableDetailTabs('edge_detail_evidence_not_available')
          : { ...loadedTabs };
        tabs.overview = mergeEdgeDetailTab(tabs.overview, {
          ...providedEdgeFields(edge, ['source_event_id', 'target_event_id', 'feature_key', 'resolution']),
          edge_id: edge.edge_id,
          signal: signal ? signal.label : edge.signal_id,
          interpretation: presentation.interpretation,
        });
        tabs.relation = mergeEdgeDetailTab(tabs.relation, {
          ...providedEdgeFields(edge, ['source_event', 'target_event', 'relation_details']),
          ...providedEdgeFields(edge, [
            'source_event_id', 'target_event_id', 'source_site_id', 'target_site_id',
            'source_country_code', 'target_country_code', 'feature_key', 'resolution',
            'source_age_bp', 'target_age_bp', 'source_age_interval_bp', 'target_age_interval_bp',
            'source_younger_bp', 'source_older_bp', 'target_younger_bp', 'target_older_bp',
            'distance_km_unrounded', 'distance_km_display', 'distance_algorithm',
            'distance_library', 'distance_library_version', 'minimum_lag_years', 'maximum_lag_years',
            'candidate_status', 'reason_code', 'scenario_id', 'threshold_profile_id',
            'temporal_contract_version', 'classification_contract_version', 'propagation_contract_version',
            'schema_version', 'build_id', 'directional_arrow_allowed', 'route_interpretation_allowed', 'map_geometry_role',
          ]),
          source_record_id: edge.source_record_id,
          target_record_id: edge.target_record_id,
          source_country: edge.source_country,
          target_country: edge.target_country,
          status: presentation.status,
          ...providedEdgeFields(edge, ['predicates']),
        });
        tabs.provenance = mergeEdgeDetailTab(tabs.provenance,
          providedEdgeFields(edge, ['source_provenance', 'target_provenance', 'source_dataset_versions', 'event_manifest_digest', 'config_digest', 'producer_version', 'build_id'])
        );
        setFocusState({
          kind: 'edge',
          edgeId: edge.edge_id,
          scenarioId: edge.scenario_id,
          atlasBuildId: publishedEdgeFocusBuild(),
          edgeShareable: Object.prototype.hasOwnProperty.call(edge, 'candidate_status') && Boolean(publishedEdgeFocusBuild()) && [edge.edge_id, edge.scenario_id].every(value => typeof value === 'string' && value.trim()),
          layerKey: source.layer.key,
          title: signal ? signal.label : edge.signal_id,
          subtitle: `${edge.source_country}${presentation.separator}${edge.target_country} ${presentation.relationLabel.toLowerCase()}`,
          meta: [
            { label: 'Relation ID', value: edge.edge_id },
            { label: 'Status', value: presentation.label },
            { label: 'Cue', value: signal ? `${scientificCueGlyph(signal.non_color_cue)} ${signal.non_color_cue}` : 'Unassigned' },
          ],
          sourceUrl: '',
          detailTabs: tabs,
        });
        if (compare) {
          activeFocusTab = 'relation';
          renderFocusDetail();
          document.getElementById('focus-tab-relation')?.focus({ preventScroll: true });
        }
        return true;
      }
      async function restoreEdgeFocus(request) {
        const generation = edgeFocusLoadState.generation;
        if (edgeFocusLoadState.restoring === generation) return false;
        edgeFocusLoadState.restoring = generation;
        try {
          const selected = edgeFocusSelection(request, publishedEdgeFocusBuild(), visibleGovernedEdges(), visiblePointEntries);
          if (!selected) {
            topbarStatePill.textContent = 'Shared relation is unavailable under this published build, scenario and current filters.';
            topbarStatePill.setAttribute('role', 'status');
            return false;
          }
          if (!await openEdgeDetail(selected.edge, selected.source, false, true)) return false;
          activeFocusTab = request.tab;
          renderFocusDetail();
          syncHashState();
          return true;
        } finally {
          if (edgeFocusLoadState.generation === generation && pendingEdgeFocus === request) pendingEdgeFocus = null;
          if (edgeFocusLoadState.restoring === generation) edgeFocusLoadState.restoring = null;
        }
      }
      function renderEdgeLayers() {
        edgeRenderSummary = { shown: 0, viewport_count: 0, limit: 128 };
        if (STATIC_ATLAS_INLINE || STATIC_ATLAS_CHUNKS.edges.status !== 'available') return;
        const entriesByRecordId = new Map(
          visiblePointEntries
            .filter((entry) => entry.feature.record_id)
            .map((entry) => [String(entry.feature.record_id), entry])
        );
        const selection = atlasEdgeRenderSelection(
          visibleGovernedEdges(), entriesByRecordId,
          map._loaded ? map.getZoom() : 0, featureCoordinatePair,
          map._loaded ? (coordinates) => atlasEdgeIntersectsViewport(map, coordinates) : null
        );
        const drawEdges = evidenceDisplayDecision(activeEvidenceDisplay).drawEdges;
        edgeRenderSummary = { shown: drawEdges ? selection.rows.length : 0, viewport_count: selection.viewport_count, limit: selection.limit };
        if (!drawEdges) return;
        selection.rows.forEach(({ edge, source, target }) => {
          const signal = scientificSignalById(edge.signal_id);
          const color = signal ? signal.color : '#6d28d9';
          const presentation = edgeScientificPresentation(edge);
          const line = L.polyline(
            [featureCoordinatePair(source.feature), featureCoordinatePair(target.feature)].map((coordinates) => [coordinates.latitude, coordinates.longitude]),
            {
              pane: 'edgePane',
              color,
              weight: 2.5,
              opacity: 0.82,
              dashArray: presentation.dashArray,
            }
          );
          line.bindPopup(edgeEvidencePopupHtml(edge, signal, presentation));
          line.on('click', () => openEdgeDetail(edge, source));
          line.on('popupopen', ({ popup }) => {
            const button = popup.getElement()?.querySelector('[data-compare-edge]');
            if (!button || button.dataset.compareEdge !== edge.edge_id) return;
            button.onclick = async (event) => {
              event.preventDefault();
              event.stopPropagation();
              await openEdgeDetail(edge, source, true);
            };
          });
          line.addTo(map);
          renderedEdgeLayers.push(line);
        });
      }
      function renderPolygonLayers() {
        POLYGON_LAYERS.forEach((layer) => {
          const visibleFeatures = (layer.geojson.features || []).filter((feature) => polygonGeometryIsAdmitted(feature) && polygonFeatureVisible(layer, feature.properties || {}));
          if (!visibleFeatures.length) return;
          visibleFeatures.forEach((feature) => visiblePolygonFeatureEntries.push({ layer, feature }));
          let geoJsonLayer;
          if (layer.kind === 'country-boundaries') {
            geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
              pane: 'boundaryPane',
              renderer: boundaryRenderer,
              style(feature) {
                const country = feature.properties.country || '';
                if (document.documentElement.classList.contains('atlas-capture-mode')) {
                  return { color: '#64748b', weight: 1.1, fillColor: '#f8fafc', fillOpacity: 0.025, opacity: 0.62 };
                }
                const style = countryStyle(country);
                return { color: style.stroke, weight: 1.4, fillColor: style.fill, fillOpacity: 0.04, opacity: 0.72 };
              },
              onEachFeature(feature, featureLayer) {
                featureLayer.bindPopup(`<div class="popup-grid"><div><strong>Country</strong> ${escapeHtml(feature.properties.name || '')}</div><div><strong>Filter state</strong> ${activeCountries.has(feature.properties.country) ? 'Visible' : 'Hidden'}</div></div>`);
                featureLayer.on('click', () => {
                  const bounds = featureLayer.getBounds();
                  setFocusState({
                    kind: 'polygon',
                    layerKey: layer.key,
                    title: feature.properties.name || layer.label,
                    subtitle: 'Country boundary',
                    meta: [
                      { label: 'Layer', value: layer.label },
                      { label: 'Country', value: feature.properties.country || 'Unassigned' },
                      { label: 'State', value: activeCountries.has(feature.properties.country) ? 'Visible' : 'Hidden' },
                    ],
                    sourceUrl: '',
                    bounds: bounds.isValid() ? [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]] : null,
                  });
                });
              }
            });
          } else if (layer.kind === 'density') {
            geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
              pane: 'polygonPane',
              style(feature) {
                const count = finiteCountValue(feature.properties.count);
                const maxCount = finiteCountValue(layer.max_count);
                return { color: layer.style.stroke, weight: 1.1, fillColor: densityFillColor(count, maxCount), fillOpacity: densityOpacity, opacity: 0.75 };
              },
              onEachFeature(feature, featureLayer) {
                const densityValueLabel = layer.density_value_label || 'Records';
                const authorityLabel = layer.source_authority_admitted === false
                  ? `Degraded display only · ${layer.authority_status || 'unknown'} authority`
                  : 'Admitted source authority';
                const densityWarning = Array.isArray(layer.display_warning_codes) && layer.display_warning_codes.length
                  ? layer.display_warning_codes.join(', ').replaceAll('_', ' ')
                  : 'None';
                featureLayer.bindPopup(`<div class="popup-grid"><div><strong>Layer</strong> ${escapeHtml(layer.label)}</div><div><strong>Country</strong> ${escapeHtml(feature.properties.country || '')}</div><div><strong>${escapeHtml(densityValueLabel)}</strong> ${escapeHtml(countDisplayValue(feature.properties.count, feature.properties.count_label))}</div><div><strong>Authority</strong> ${escapeHtml(authorityLabel)}</div><div><strong>Count warning</strong> ${escapeHtml(densityWarning)}</div></div>`);
                featureLayer.on('click', () => {
                  const bounds = featureLayer.getBounds();
                  setFocusState({
                    kind: 'polygon',
                    layerKey: layer.key,
                    title: feature.properties.country || layer.label,
                    subtitle: 'Density cell',
                    meta: [
                      { label: 'Layer', value: layer.label },
                      { label: 'Country', value: feature.properties.country || 'Unassigned' },
                      { label: densityValueLabel, value: countDisplayValue(feature.properties.count, feature.properties.count_label) },
                      { label: 'Authority', value: authorityLabel },
                      { label: 'Count warning', value: densityWarning },
                    ],
                    sourceUrl: '',
                    bounds: bounds.isValid() ? [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]] : null,
                  });
                });
              }
            });
          } else {
            geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
              pane: 'polygonPane',
              style(feature) {
                const properties = feature && feature.properties ? feature.properties : {};
                if (modeledContextActive && isModeledContextFeature(layer, properties)) {
                  return { color: '#334155', weight: 0.9, fillColor: modeledContextFillColor(modeledContextEstimate(properties)), fillOpacity: 0.72, opacity: 0.88 };
                }
                return { color: layer.style.stroke, weight: 1.1, fillColor: layer.style.fill || 'rgba(100, 116, 139, 0.14)', fillOpacity: 0.28, opacity: 0.85 };
              },
              onEachFeature(feature, featureLayer) {
                featureLayer.bindPopup(polygonPopupHtml(layer, feature.properties || {}));
                featureLayer.on('click', () => {
                  const properties = feature.properties || {};
                  const bounds = featureLayer.getBounds();
                  setFocusState({
                    kind: 'polygon',
                    layerKey: layer.key,
                    title: properties.name || layer.label,
                    subtitle: properties.category || properties.geometry_type || 'Polygon record',
                    meta: [
                      { label: 'Layer', value: layer.label },
                      { label: 'Country', value: properties.country || 'Unassigned' },
                      { label: 'Type', value: properties.category || properties.geometry_type || 'Polygon record' },
                    ].concat(featureTimeDescriptor(properties) ? [featureTimeDescriptor(properties)] : []),
                    sourceUrl: properties.source_url || '',
                    bounds: bounds.isValid() ? [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]] : null,
                  });
                });
              }
            });
          }
          geoJsonLayer.addTo(map);
          renderedPolygonLayers.push(geoJsonLayer);
          if (layer.kind !== 'country-boundaries') renderedFittablePolygonLayers.push(geoJsonLayer);
        });
      }
      function activeBounds() {
        const latLngs = visiblePointEntries
          .map((entry) => featureCoordinatePair(entry.feature))
          .filter((coordinates) => coordinates !== null)
          .map((coordinates) => [coordinates.latitude, coordinates.longitude]);
        renderedFittablePolygonLayers.forEach((layer) => {
          const bounds = layer.getBounds();
          if (bounds.isValid()) {
            latLngs.push([bounds.getSouth(), bounds.getWest()]);
            latLngs.push([bounds.getNorth(), bounds.getEast()]);
          }
        });
        return latLngs.length ? L.latLngBounds(latLngs) : null;
      }
      function updateStats() {
        const enabledLayers = ALL_LAYERS.filter((layer) => activeLayerKeys.has(layer.key)).length;
        const focalPoints = visiblePointEntries.filter(({ neighborContext }) => !neighborContext);
        const neighborCount = visiblePointEntries.length - focalPoints.length;
        const visibleAnimalCount = focalPoints.filter(({ layer }) => isAnimalLayer(layer)).length;
        const timedVisiblePoints = focalPoints.filter(({ layer, feature }) => layer.applies_time_filter && featureTimeWindow(feature)).length;
        const timedVisiblePolygons = POLYGON_LAYERS.reduce((count, layer) => {
          if (!activeLayerKeys.has(layer.key) || !layer.applies_time_filter) return count;
          const features = Array.isArray(layer.geojson && layer.geojson.features) ? layer.geojson.features : [];
          return count + features.filter((feature) => {
            const properties = feature && feature.properties ? feature.properties : {};
            return featureTimeWindow(properties) && polygonFeatureVisible(layer, properties);
          }).length;
        }, 0);
        const timedVisibleCount = timedVisiblePoints + timedVisiblePolygons;
        let timeRecordSummary = TIME_HAS_DATA
          ? `${timedVisibleCount} time-aware records are visible in the active BP window.`
          : 'No time-aware records are available for BP filtering.';
        if (TIME_HAS_DATA && !timeFilterUsesFullExtent()) {
          const untimedExclusion = genericUntimedExclusion();
          timeRecordSummary += untimedExclusion.status === 'available'
            ? untimedExclusion.split_status === 'available'
              ? ` ${untimedExclusion.count} records without admitted numeric BP chronology are excluded (${untimedExclusion.absent_count} absent, ${untimedExclusion.refused_count} refused, ${untimedExclusion.contextual_count} contextual).`
              : ` ${untimedExclusion.count} records without admitted numeric BP chronology are excluded; the absent/refused/contextual split is unavailable for this legacy report.`
            : ' The exact number of records excluded without admitted numeric BP chronology is unavailable for this country selection.';
        }
        const playbackBlockReason = automaticTimePlaybackBlockReason();
        timeRecordCount.textContent = playbackBlockReason
          ? `${timeRecordSummary} Automatic playback is disabled. ${playbackBlockReason}`
          : timeRecordSummary;
        const visiblePolygonLayers = renderedPolygonLayers.length;
        selectionReadout.textContent = neighborCount
          ? `${focalPoints.length} focal ${focalPoints.length === 1 ? 'point' : 'points'} · ${neighborCount} labeled neighbor context · ${visibleAnimalCount} animal · ${visiblePolygonLayers} overlays`
          : `${focalPoints.length} points · ${visibleAnimalCount} animal · ${visiblePolygonLayers} overlays`;
        selectionReadout.dataset.governedEdgeEligibility = String(GOVERNED_EDGE_ELIGIBILITY_COUNT);
        selectionReadout.dataset.visibleGovernedEdges = String(renderedEdgeLayers.length);
        topbarStatePill.textContent = `${activeCountries.size} countries · ${enabledLayers} layers · ${focalPoints.length} visible ${focalPoints.length === 1 ? 'point' : 'points'}`;
        countrySummary.textContent = activeCountries.size === COUNTRIES.length ? 'All countries visible' : activeCountries.size ? `${activeCountries.size} countries active` : 'No countries active';
      }
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

      function buildSearchResults() {
        const query = searchInput.value.trim().toLowerCase();
        searchClearButton.hidden = !query;
        const {focalCount, neighborCount} = publishedSearchCounts();
        if (!query) {
          searchCount.textContent = neighborCount
            ? `${focalCount} focal ${focalCount === 1 ? 'point' : 'points'} and sites · ${neighborCount} labeled neighbor context`
            : `${focalCount} visible points and sites`;
          searchResults.hidden = true;
          searchResults.innerHTML = '';
          return;
        }
        const matches = publishedSearchResults(query);
        searchCount.textContent = neighborCount
          ? `${matches.length} matches · ${focalCount} focal visible · ${neighborCount} neighbor context`
          : `${matches.length} matches · ${focalCount} visible`;
        searchResults.hidden = false;
        searchResults.innerHTML = matches.map(({ layer, feature, neighborContext }, index) => {
          const timeDescriptor = featureTimeDescriptor(feature);
          const timeBadge = timeDescriptor ? `<span class="search-badge">${escapeHtml(timeDescriptor.label)}: ${escapeHtml(timeDescriptor.value)}</span>` : '';
          return `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(feature.subtitle || 'Unspecified type')}</span><div class="search-result-meta"><span class="search-badge">${escapeHtml(layer.label)}</span><span class="search-badge">${escapeHtml(feature.country || 'Unassigned')}</span>${neighborContext ? '<span class="search-badge">Neighbor context</span>' : ''}${timeBadge}</div></button>`;
        }).join('') || '<div class="summary-item"><span>No visible records match the current query.</span></div>';
        searchResults.querySelectorAll('[data-search-index]').forEach((button, index) => {
          button.addEventListener('click', () => {
            const match = matches[index];
            if (!match) return;
            const coordinates = featureCoordinatePair(match.feature);
            if (!coordinates) return;
            focusPointAtVisibleIndex(visiblePointEntries.indexOf(match));
            map.flyTo([coordinates.latitude, coordinates.longitude], Math.max(map.getZoom(), 8), { duration: 0.7, ...(reducedMotionQuery.matches ? { animate: false } : {}) });
            window.setTimeout(() => match.marker.openPopup(), 250);
            setSearchOpen(false);
          });
        });
      }
      function renderSelectionEmptyStatePanel(loadStatus = 'ready') {
        let input = {loadStatus};
        if (loadStatus === 'ready') {
          const decision = evidenceDisplayDecision(activeEvidenceDisplay);
          const narrowedTime = TIME_HAS_DATA && !timeFilterUsesFullExtent();
          input = {loadStatus, countryCount: activeCountries.size,
            selectedLayers: ALL_LAYERS.filter(layer => activeLayerKeys.has(layer.key)),
            scientificSignalCount: SCIENTIFIC_SIGNALS.length, selectedScientificSignalCount: activeScientificSignalIds.size,
            pointCount: visiblePointEntries.length, polygonLayerCount: renderedPolygonLayers.length,
            retainedRelationCount: visibleGovernedEdges().length, relationViewportCount: edgeRenderSummary.viewport_count,
            drawnRelationCount: edgeRenderSummary.shown, drawNodes: decision.drawNodes, drawEdges: decision.drawEdges,
            timeFilterActive: narrowedTime, untimedExclusion: narrowedTime ? genericUntimedExclusion() : null};
        }
        const summary = selectionEmptyState(input);
        emptyState.hidden = summary.hidden;
        emptyState.dataset.reason = summary.reason;
        emptyState.innerHTML = renderSelectionEmptyState(summary);
      }
      async function renderMapState() {
        const generation = ++staticAtlasLoadGeneration;
        edgeFocusLoadState.generation = generation;
        retainedNeighborRecordCountries = atlasRetainedNeighborRecordCountries(visibleGovernedEdges(), activeCountries);
        topbarStatePill.textContent = 'Loading selected evidence…';
        topbarStatePill.setAttribute('aria-live', 'polite');
        document.getElementById('map').setAttribute('aria-busy', 'true');
        renderSelectionEmptyStatePanel('loading');
        try {
          const requested = await ensureStaticAtlasSelectionLoaded();
          if (generation !== staticAtlasLoadGeneration) return;
          const started = performance.now();
          renderLoadedMapState();
          const duration = performance.now() - started;
          const loaded = STATIC_ATLAS_INLINE
            ? POINT_LAYERS.reduce((total, layer) => total + (Array.isArray(layer.features) ? layer.features.length : 0), 0)
              + POLYGON_LAYERS.reduce((total, layer) => total + (Array.isArray(layer.geojson?.features) ? layer.geojson.features.length : 0), 0)
            : ALL_LAYERS.reduce((total, layer) => total + staticAtlasNonnegativeInteger(layer.static_loaded_feature_count, `${layer.key} loaded feature count`), 0);
          const admitted = STATIC_ATLAS_INLINE
            ? loaded
            : ALL_LAYERS.reduce((total, layer) => total + staticAtlasNonnegativeInteger(layer.static_feature_count, `${layer.key} admitted feature count`), 0);
          selectionReadout.dataset.staticLoad = `${loaded}/${admitted}`;
          selectionReadout.dataset.staticLoadRequestedAssetCount = String(requested.length);
          selectionReadout.dataset.filterRenderMs = String(Math.round(duration));
          selectionReadout.dataset.filterRenderBudgetExceeded = String(duration > Number(STATIC_ATLAS_BOOTSTRAP.budgets.filter_main_thread_max_ms));
          if (pendingEdgeFocus) await restoreEdgeFocus(pendingEdgeFocus);
        } catch (error) {
          if (generation !== staticAtlasLoadGeneration) return;
          topbarStatePill.textContent = error instanceof Error ? error.message : 'Static atlas selection failed to load.';
          topbarStatePill.setAttribute('role', 'alert');
          renderSelectionEmptyStatePanel('unavailable');
          console.error(error);
        } finally {
          if (generation === staticAtlasLoadGeneration) document.getElementById('map').setAttribute('aria-busy', 'false');
        }
      }
      function renderLoadedMapState() {
        refreshTimeControls();
        if (nativeLraController) nativeLraController.render();
        removeRenderedLayers();
        renderPointLayers();
        renderEdgeLayers();
        renderPolygonLayers();
        renderCountryControls();
        renderScientificControls();
        renderRelationControls();
        renderAnimalControls();
        renderSourceChronologyControls();
        refreshTimeStepperStatus();
        renderModeledContextControls();
        renderLegend();
        renderControlPanelSummary();
        updateStats();
        renderEvidenceDisplayPanel();
        preparePublishedSearch();
        buildSearchResults();
        renderFocusCard();
        syncPresetButtons();
        syncTimePresetButtons();
        diameterValue.textContent = `${Number(slider.value)} km diameter`;
        radiusValue.textContent = `${(Number(slider.value) / 2).toFixed(1)} km`;
        densityOpacityValue.textContent = `${Math.round(densityOpacity * 100)}%`;
        renderSelectionEmptyStatePanel();
        syncHashState();
        renderEvidenceToolPanels();
        if (document.documentElement.classList.contains('atlas-capture-mode') && atlasCapturePresentation !== null) {
          renderAtlasCaptureOverlay(atlasCaptureSnapshot());
        }
      }
      function atlasSelectionExportSnapshot() {
        const snapshot = atlasCaptureSnapshot();
        return {...snapshot, ready: snapshot.ready && !['loading', 'loading_unavailable'].includes(emptyState.dataset.reason),
          selection_generation: staticAtlasLoadGeneration, selection_hash: atlasSelectionHashParams().toString(),
          acceptance_diameter_km: Number(slider.value),
          relation_availability: {status: STATIC_ATLAS_CHUNKS.edges?.status ?? null,
            reason_code: STATIC_ATLAS_CHUNKS.edges?.reason_code ?? null}};
      }
      function atlasSelectionExportOwner(transportOverhead = {request_count: 0, byte_count: 0}) {
        if (STATIC_ATLAS_INLINE) throw Error('Published selection chunks are unavailable in this map.');
        return {bootstrap: STATIC_ATLAS_BOOTSTRAP, transportOverhead, snapshot: atlasSelectionExportSnapshot,
          assetNeeded: staticAtlasNodeSelectionNeeded, isLoaded: row => staticAtlasLoadedAssets.has(row.asset_key),
          loadAsset: row => loadStaticAtlasAsset(row, false),
          readAsset: row => STATIC_ATLAS_CHUNKS.nodes.find(part => part.asset_key === row.asset_key),
          layerForAsset: row => {
            const matches = ATLAS_EVIDENCE.layers.filter(entry => entry.layer_kind === row.layer_kind && entry.layer_index === row.layer_index);
            if (matches.length !== 1) throw Error('Published selection layer identity is ambiguous.');
            return matches[0].layer;
          },
          featureSelected: (layer, feature, kind) => kind === 'point' ? pointFeatureVisible(layer, feature)
            : polygonGeometryIsAdmitted(feature) && polygonFeatureVisible(layer, feature.properties || {}),
          relations: () => ({retained_count: GOVERNED_EDGE_RECORDS.length, records: visibleGovernedEdges()}),
          endpointEligible: (edge, entries) => atlasEdgeRenderSelection([edge],
            new Map(entries.filter(entry => entry.feature.record_id).map(entry => [String(entry.feature.record_id), entry])),
            map.getZoom(), featureCoordinatePair, null).rows.length === 1};
      }
      async function downloadAtlasSelection() {
        const button = document.getElementById('selection-export'), status = document.getElementById('selection-export-status');
        if (button.disabled) return;
        button.disabled = true;
        status.textContent = 'Preparing the complete selection…';
        try {
          const expected = JSON.stringify(atlasSelectionExportSnapshot());
          const unchanged = () => {if (JSON.stringify(atlasSelectionExportSnapshot()) !== expected) throw Error('Selection changed; request the download again.');};
          const overhead = currentEvidenceTools() ? {request_count: 0, byte_count: 0}
            : {request_count: 1, byte_count: evidenceToolsDescriptor().byte_count};
          if (overhead.request_count > STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_requests
            || overhead.byte_count > STATIC_ATLAS_BOOTSTRAP.budgets.interaction_max_bytes) throw Error('Selection tools exceed the interaction budget.');
          const tools = await loadEvidenceTools();
          unchanged();
          const result = await tools.selectionExport(atlasSelectionExportOwner(overhead));
          unchanged();
          const url = URL.createObjectURL(new Blob([result.text], {type: 'application/json'}));
          const link = document.createElement('a');
          link.href = url;
          link.download = 'pollenomics-selection.json';
          try {link.click();} finally {window.setTimeout(() => URL.revokeObjectURL(url), 1000);}
          status.textContent = `${result.counts.selected_public_rows} public map rows and ${result.counts.selected_relation_rows} retained relation rows downloaded with selection metadata. Full source series are separate.`;
        } catch (error) {
          status.textContent = error instanceof Error ? error.message : 'Selection download failed; no partial download was produced.';
        } finally {button.disabled = false;}
      }
      const ATLAS_CAPTURE_API_VERSION = typeof signedNativeTime !== 'undefined' && signedNativeTime !== null ? 'atlas-capture.v2' : 'atlas-capture.v1';
      let atlasCapturePresentation = null;
      function captureFrameNumber(value, label) {
        if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) throw new Error(`${label} must be a finite non-negative number`);
        return value;
      }
      function captureFrameCountries(value) {
        if (value === undefined) return [...activeCountries].sort();
        if (!Array.isArray(value) || value.length === 0) throw new Error('capture countries must be a non-empty array');
        const countries = [...new Set(value.map((country) => String(country)))].sort();
        if (countries.some((country) => !COUNTRIES.includes(country))) throw new Error('capture countries contain an unsupported country');
        return countries;
      }
      function captureFrameWindow(frameSpec) {
        const youngerBp = captureFrameNumber(frameSpec.time_start_bp, 'capture time_start_bp');
        const olderBp = captureFrameNumber(frameSpec.time_end_bp, 'capture time_end_bp');
        if (youngerBp > olderBp) throw new Error('capture BP interval must satisfy time_start_bp <= time_end_bp');
        return { youngerBp, olderBp };
      }
      function captureFrameView(value) {
        if (value === undefined) return null;
        if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('capture view is invalid');
        const { latitude, longitude, zoom } = value;
        if (typeof latitude !== 'number' || !Number.isFinite(latitude) || latitude < -90 || latitude > 90 || typeof longitude !== 'number' || !Number.isFinite(longitude) || longitude < -180 || longitude > 180 || typeof zoom !== 'number' || !Number.isFinite(zoom) || zoom < 0 || zoom > 20) {
          throw new Error('capture view is invalid');
        }
        return { latitude, longitude, zoom };
      }
      function normalizeAtlasCaptureFrame(frameSpec) {
        if (typeof signedNativeTime !== 'undefined' && signedNativeTime !== null) throw Error('signed_native_media_capture_unsupported');
        if (!frameSpec || typeof frameSpec !== 'object' || Array.isArray(frameSpec)) throw new Error('capture frame must be an object');
        const storyKind = String(frameSpec.story_kind || '');
        if (storyKind === 'candidate_succession') throw new Error('candidate_succession_capture_not_releasable');
        if (!['source_chronology', 'modeled_context'].includes(storyKind)) throw new Error('capture story_kind is unsupported');
        const basemap = frameSpec.basemap === undefined ? 'none' : String(frameSpec.basemap);
        if (!BASEMAP_NAMES.includes(basemap)) throw new Error('capture basemap is unsupported');
        const common = {
          storyKind,
          basemap,
          countries: captureFrameCountries(frameSpec.countries),
          view: captureFrameView(frameSpec.view),
        };
        if (storyKind === 'source_chronology') {
          const sourceLevel = String(frameSpec.source_level || '');
          const sourceLayer = sourceChronologyLayerForLevel(sourceLevel);
          if (!sourceLayer) throw new Error('capture source_level is unavailable');
          let sourceCode = 'all';
          let sourceTaxon = 'all';
          let sourcePreset = 'none';
          let sourcePresetAuthority = null;
          if (sourceLevel === 'source_ecological_code') {
            const validCodes = ['all', ...sourceLayer.facet_metadata.source_ecological_codes.map((row) => row.value)];
            sourceCode = String(frameSpec.source_code || 'all');
            if (!validCodes.includes(sourceCode)) throw new Error('capture source_code is unavailable');
          } else if (sourceLevel === 'source_taxon') {
            const validTaxa = ['all', ...sourceLayer.facet_metadata.source_taxa.map((row) => row.value)];
            sourceTaxon = String(frameSpec.source_taxon || 'all');
            if (!validTaxa.includes(sourceTaxon)) throw new Error('capture source_taxon is unavailable');
            const validPresets = ['none', ...sourceLayer.facet_metadata.source_label_preset_accountability.presets.map((row) => row.key)];
            sourcePreset = String(frameSpec.source_preset || 'none');
            if (!validPresets.includes(sourcePreset)) throw new Error('capture source_preset is unavailable');
            if (sourceTaxon !== 'all' && sourcePreset !== 'none') throw new Error('capture cannot combine an exact source taxon and a source-label preset');
            sourcePresetAuthority = sourceChronologyCapturePresetAuthority(sourceLayer, sourcePreset);
          }
          const frameWindow = captureFrameWindow(frameSpec);
          const facet = sourceChronologyFacetForSelection(sourceLayer, sourceCode, sourceTaxon, sourcePreset);
          if (!facet || !sourceChronologyExtentIsValid(facet) || facet.node_count === 0) throw new Error('capture source facet has no chronological evidence');
          const minimum = sourceChronologyTimeValue(facet.time_min_bp);
          const maximum = sourceChronologyTimeValue(facet.time_max_bp);
          if (frameWindow.youngerBp < minimum || frameWindow.olderBp > maximum) throw new Error('capture BP interval exceeds the selected source extent');
          return { ...common, sourceLevel, sourceCode, sourceTaxon, sourcePreset, sourcePresetAuthority, frameWindow };
        }
        if (!modeledContextAvailable()) throw new Error('modeled_context_capture_not_available');
        const sourceWindowLabel = String(frameSpec.source_window_label || '');
        const sourceWindowIndex = MODELED_CONTEXT_WINDOWS.findIndex((sourceWindow) => sourceWindow.label === sourceWindowLabel);
        if (sourceWindowIndex < 0) throw new Error('capture modeled-context source window is unavailable');
        const sourceWindow = MODELED_CONTEXT_WINDOWS[sourceWindowIndex];
        if (!Number.isInteger(frameSpec.no_pollen_data_count) || frameSpec.no_pollen_data_count < 0 || frameSpec.no_pollen_data_count > sourceWindow.feature_count || frameSpec.no_pollen_data_count !== sourceWindow.no_pollen_data_count) {
          throw new Error('capture modeled-context no-pollen denominator differs');
        }
        const family = modeledContextFamilyByKey(String(frameSpec.metric_family_key || modeledContextFamilyKey));
        if (!family) throw new Error('capture modeled-context metric family is unavailable');
        const metricKey = String(frameSpec.metric_key || family.default_metric_key);
        if (!family.metrics.some((metric) => metric.key === metricKey)) throw new Error('capture modeled-context metric is unavailable');
        return { ...common, sourceWindowIndex, familyKey: family.key, metricKey };
      }
      async function awaitAtlasCaptureReady() {
        const mapElement = document.getElementById('map');
        if (mapElement.getAttribute('aria-busy') === 'true') {
          await new Promise((resolve, reject) => {
            const timeout = window.setTimeout(() => {
              observer.disconnect();
              reject(new Error('atlas capture readiness timed out'));
            }, 30000);
            const observer = new MutationObserver(() => {
              if (mapElement.getAttribute('aria-busy') === 'true') return;
              window.clearTimeout(timeout);
              observer.disconnect();
              resolve();
            });
            observer.observe(mapElement, { attributes: true, attributeFilter: ['aria-busy'] });
          });
        }
        if (document.fonts && document.fonts.ready) await document.fonts.ready;
        window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
        map.invalidateSize({ animate: false });
        await new Promise((resolve) => window.requestAnimationFrame(() => window.requestAnimationFrame(resolve)));
        window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
        map.invalidateSize({ animate: false });
        await new Promise((resolve) => window.requestAnimationFrame(() => window.requestAnimationFrame(resolve)));
        return atlasCaptureSnapshot();
      }
      function atlasCaptureSnapshot() {
        const sourceLayer = sourceChronologyLayerForLevel(activeSourceChronologyLevel);
        const sourceFacet = sourceLayer
          ? sourceChronologyFacetForSelection(sourceLayer, activeSourceChronologyCode, activeSourceChronologyTaxon)
          : null;
        const sourcePresetAuthority = activeSourceChronologyLevel === 'source_taxon' && activeSourceChronologyPreset !== 'none'
          ? sourceChronologyCapturePresetAuthority(sourceLayer, activeSourceChronologyPreset)
          : null;
        const visibleSourceEntries = visiblePointEntries.filter(({ layer, neighborContext }) => !neighborContext && layer.semantic_role === 'source_chronology_context');
        const visibleSourceSiteCount = new Set(visibleSourceEntries.map(({ feature }) => feature.record_id)).size;
        const visibleSourceObservationValues = visibleSourceEntries.map(({ feature }) => sourceChronologyCount(feature.observation_denominator));
        const visibleSourceObservationDenominator = visibleSourceObservationValues.every((value) => value !== null)
          ? visibleSourceObservationValues.reduce((total, value) => total + value, 0)
          : null;
        const sourceWindow = modeledContextActive ? currentModeledContextWindow() : null;
        const orientationLayerKeys = atlasCaptureOrientationKeys();
        const sourceChronologyAvailable = Boolean(
          !modeledContextActive
          && sourceLayer
          && activeLayerKeys.has(sourceLayer.key)
          && sourceFacet
        );
        const evidenceLayerKey = modeledContextActive
          ? MODELED_CONTEXT.layer_key
          : (sourceChronologyAvailable ? sourceLayer.key : null);
        const mapBounds = document.getElementById('map').getBoundingClientRect();
        const overlayElement = document.getElementById('atlas-capture-overlay');
        const overlayBounds = overlayElement.getBoundingClientRect();
        const overlayVisible = overlayBounds.width > 0 && overlayBounds.height > 0;
        const overlayContentBounded = [...overlayElement.children].every((child) => {
          const bounds = child.getBoundingClientRect();
          return bounds.left >= overlayBounds.left
            && bounds.right <= overlayBounds.right
            && bounds.top >= overlayBounds.top
            && bounds.bottom <= overlayBounds.bottom;
        });
        const overlayOverlapsMap = overlayVisible
          && overlayBounds.left < mapBounds.right
          && overlayBounds.right > mapBounds.left
          && overlayBounds.top < mapBounds.bottom
          && overlayBounds.bottom > mapBounds.top;
        return {
          capture_api_version: ATLAS_CAPTURE_API_VERSION,
          ...(typeof signedNativeTime !== 'undefined' && signedNativeTime !== null ? {temporal_profile:'calendar-bp1950-signed.v1',temporal_axis:'BP1950',native_view_sha256:NATIVE_LRA_BINDING.sha256,native_lra:nativeLraController ? nativeLraController.snapshot() : null} : {}),
          build_id: STATIC_ATLAS_BOOTSTRAP.build_id,
          scope_slug: STATIC_ATLAS_BOOTSTRAP.scope_slug,
          relation_filters: relationFilterMetadata(GOVERNED_EDGE_RECORDS, activeRelationFilters),
          relation_event_definition: relationEventDefinitionMetadata(GOVERNED_EDGE_RECORDS, activeRelationEventDefinition),
          scientific_picker: scientificPickerMetadata(),
          evidence_display: evidenceDisplayMetadata(activeEvidenceDisplay),
          version: STATIC_ATLAS_BOOTSTRAP.version,
          ready: document.getElementById('map').getAttribute('aria-busy') !== 'true',
          basemap: currentBasemap,
          view: {
            latitude: map.getCenter().lat,
            longitude: map.getCenter().lng,
            zoom: map.getZoom(),
          },
          countries: [...activeCountries].sort(),
          time_window_bp: { younger_bp: timeStartBp, older_bp: timeWindowEndBp() },
          source_chronology: sourceChronologyAvailable ? {
            level: activeSourceChronologyLevel,
            source_code: activeSourceChronologyLevel === 'source_ecological_code' ? activeSourceChronologyCode : null,
            source_taxon: activeSourceChronologyLevel === 'source_taxon' ? activeSourceChronologyTaxon : null,
            source_preset: activeSourceChronologyLevel === 'source_taxon' && activeSourceChronologyPreset !== 'none' ? activeSourceChronologyPreset : null,
            source_preset_member_taxon_ids: sourcePresetAuthority ? [...sourcePresetAuthority.memberTaxonIds] : null,
            source_preset_catalog_sha256: sourcePresetAuthority ? sourcePresetAuthority.catalogSha256 : null,
            facet_site_count: sourceFacet ? sourceFacet.site_count : null,
            facet_node_count: sourceFacet ? sourceFacet.node_count : null,
            facet_observation_denominator: sourceFacet ? sourceFacet.observation_denominator : null,
            visible_site_count: visibleSourceSiteCount,
            visible_node_count: visibleSourceEntries.length,
            visible_observation_denominator: visibleSourceObservationDenominator,
          } : null,
          modeled_context: sourceWindow ? {
            window_index: modeledContextWindowIndex,
            window_label: sourceWindow.label,
            feature_count: sourceWindow.feature_count,
            no_pollen_data_count: sourceWindow.no_pollen_data_count,
            metric_family_key: modeledContextFamilyKey,
            metric_key: modeledContextMetricKey,
            evidence_role: 'context_only',
            interpolation_allowed: false,
            propagation_use_allowed: false,
          } : null,
          visible_point_count: visiblePointEntries.filter(({ neighborContext }) => !neighborContext).length,
          visible_neighbor_context_point_count: visiblePointEntries.filter(({ neighborContext }) => neighborContext).length,
          visible_polygon_layer_count: renderedPolygonLayers.length,
          visible_polygon_feature_count: visiblePolygonFeatureEntries.length,
          visible_source_chronology_point_count: visibleSourceEntries.length,
          visible_modeled_context_feature_count: visiblePolygonFeatureEntries.filter(({ layer, feature }) => modeledContextActive && isModeledContextFeature(layer, feature.properties || {})).length,
          visible_modeled_no_pollen_data_count: modeledContextActive ? modeledContextFrameQualitySummary().no_pollen_data : null,
          capture_layers: {
            active_keys: [...activeLayerKeys].sort(),
            evidence_layer_key: evidenceLayerKey,
            orientation_keys: [...orientationLayerKeys].sort(),
          },
          capture_presentation: atlasCapturePresentationSnapshot(),
          capture_layout: {
            overlay_visible: overlayVisible,
            overlay_bounded: overlayVisible
              && overlayBounds.left >= 0
              && overlayBounds.right <= window.innerWidth
              && overlayBounds.top >= 0
              && overlayBounds.bottom <= window.innerHeight,
            overlay_content_bounded: overlayContentBounded,
            overlay_content_overflow: overlayElement.scrollWidth > overlayElement.clientWidth
              || overlayElement.scrollHeight > overlayElement.clientHeight,
            overlay_overlaps_map: overlayOverlapsMap,
            map_bounded: mapBounds.left >= 0
              && mapBounds.right <= window.innerWidth
              && mapBounds.top >= 0
              && mapBounds.bottom <= window.innerHeight,
            map_width_px: Math.round(mapBounds.width),
            map_height_px: Math.round(mapBounds.height),
            scroll_x_px: Math.round(window.scrollX),
            scroll_y_px: Math.round(window.scrollY),
            viewport_width_px: window.innerWidth,
            viewport_height_px: window.innerHeight,
          },
          visible_governed_candidate_count: renderedEdgeLayers.length,
          scientific_posture: {
            classifications_status: ATLAS_EVIDENCE.classifications_status,
            classifications_reason_code: ATLAS_EVIDENCE.classifications_reason_code,
            observation_chronology_is_propagation: false,
          },
        };
      }
      function atlasCaptureOrientationKeys() {
        return ALL_LAYERS.filter((layer) => layer.group === 'orientation').map((layer) => layer.key);
      }
      function atlasCaptureSourceTitle(sourceLayer) {
        if (!sourceLayer) return 'Neotoma source chronology evidence';
        if (sourceLayer.node_level === 'source_ecological_code') {
          const row = sourceLayer.facet_metadata.source_ecological_codes.find((candidate) => candidate.value === activeSourceChronologyCode);
          return row ? `Neotoma ${row.value} — ${row.label}` : `Neotoma ${activeSourceChronologyCode}`;
        }
        if (sourceLayer.node_level === 'source_taxon') {
          const preset = sourceChronologyPresetForSelection(sourceLayer, activeSourceChronologyPreset);
          if (preset) return `Neotoma literal exact-ID union — ${preset.label}`;
          const row = sourceLayer.facet_metadata.source_taxa.find((candidate) => candidate.value === activeSourceChronologyTaxon);
          return row ? `Neotoma exact source-reported taxon — ${row.label}` : 'Neotoma exact source-reported taxon';
        }
        return 'Neotoma source sample presence';
      }
      function atlasCaptureKeyItemHtml(item) {
        const label = `<span class="atlas-capture-key-label">${escapeHtml(item.label)}</span>`;
        if (item.cue === 'point') {
          return `<span class="atlas-capture-key-item" data-capture-cue="point"><span class="atlas-capture-swatch atlas-capture-swatch--point" style="background:${escapeHtml(item.fill)};border-color:${escapeHtml(item.stroke)};"></span>${label}</span>`;
        }
        if (item.cue === 'cluster-count') {
          return `<span class="atlas-capture-key-item" data-capture-cue="cluster-count"><span class="atlas-capture-cluster-cue" style="background:${escapeHtml(item.fill)};border-color:${escapeHtml(item.stroke)};">12</span>${label}</span>`;
        }
        if (item.cue === 'line') {
          return `<span class="atlas-capture-key-item" data-capture-cue="line"><span class="atlas-capture-boundary-cue"></span>${label}</span>`;
        }
        return `<span class="atlas-capture-key-item" data-capture-cue="area"><span class="atlas-capture-swatch" style="background:${escapeHtml(item.fill)};border-color:${escapeHtml(item.stroke)};"></span>${label}</span>`;
      }
      function atlasCapturePresentationSnapshot() {
        if (atlasCapturePresentation === null) return null;
        const keyItems = [...atlasCaptureKey.querySelectorAll('.atlas-capture-key-item')].map((item) => {
          const cue = item.querySelector('.atlas-capture-swatch, .atlas-capture-cluster-cue, .atlas-capture-boundary-cue');
          const style = cue ? window.getComputedStyle(cue) : null;
          return {
            label: item.querySelector('.atlas-capture-key-label')?.textContent || '',
            cue: item.getAttribute('data-capture-cue') || '',
            fill: style?.backgroundColor || '',
            stroke: item.getAttribute('data-capture-cue') === 'line' ? (style?.borderTopColor || '') : (style?.borderColor || ''),
          };
        });
        return {
          schema_version: atlasCapturePresentation.schema_version,
          null_handling: atlasCapturePresentation.null_handling,
          interpolation_allowed: atlasCapturePresentation.interpolation_allowed,
          propagation_use_allowed: atlasCapturePresentation.propagation_use_allowed,
          evidence_role: atlasCapturePresentation.evidence_role,
          role_label: atlasCaptureRole.textContent || '',
          title: atlasCaptureTitle.textContent || '',
          time_label: atlasCaptureTime.textContent || '',
          counts_label: atlasCaptureCounts.textContent || '',
          key_labels: keyItems.map((item) => item.label),
          key_items: keyItems,
          caveat: atlasCaptureCaveat.textContent || '',
        };
      }
      function commitAtlasCapturePresentation(presentation, keyItems) {
        atlasCapturePresentation = Object.freeze({
          schema_version: 'atlas-capture-presentation.v1',
          null_handling: 'null_not_zero',
          interpolation_allowed: false,
          propagation_use_allowed: false,
          ...presentation,
        });
        atlasCaptureRole.textContent = atlasCapturePresentation.role_label;
        atlasCaptureTime.textContent = atlasCapturePresentation.time_label;
        atlasCaptureTitle.textContent = atlasCapturePresentation.title;
        atlasCaptureCounts.textContent = atlasCapturePresentation.counts_label;
        atlasCaptureKey.innerHTML = keyItems.map(atlasCaptureKeyItemHtml).join('');
        atlasCaptureCaveat.textContent = atlasCapturePresentation.caveat;
      }
      function modeledContextPublishedCellCountLabel(snapshot) {
        const value = snapshot && snapshot.modeled_context ? snapshot.modeled_context.feature_count : null;
        return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 ? String(value) : 'unavailable';
      }
      function renderAtlasCaptureOverlay(snapshot) {
        const { younger_bp: youngerBp, older_bp: olderBp } = snapshot.time_window_bp;
        const timeLabel = `[${youngerBp}, ${olderBp}] BP · oldest → present`;
        if (snapshot.source_chronology) {
          const sourceLayer = sourceChronologyLayerForLevel(snapshot.source_chronology.level);
          const layerFill = sourceLayer ? layerColor(sourceLayer) : '#1f5ed8';
          const layerStroke = sourceLayer?.style?.stroke || layerFill;
          const visibleObservations = snapshot.source_chronology.visible_observation_denominator;
          const visibleObservationLabel = visibleObservations === null ? 'unavailable' : String(visibleObservations);
          const sourceCaveat = snapshot.source_chronology.source_preset
            ? 'Literal exact-ID source-label union only · not an accepted classification or abundance · no interpolation, flow, propagation, migration, or causation inference.'
            : 'Observed source records only · site, node, and display-cluster counts are not abundance · no interpolation, flow, propagation, migration, or causation inference.';
          const keyItems = [
            { label: 'source record', cue: 'point', fill: layerFill, stroke: layerStroke },
            { label: 'records grouped at current zoom', cue: 'cluster-count', fill: layerFill, stroke: layerStroke },
            { label: 'country boundary', cue: 'line', fill: null, stroke: '#64748b' },
          ];
          commitAtlasCapturePresentation({
            evidence_role: 'observation_chronology',
            role_label: 'Observed source chronology',
            title: atlasCaptureSourceTitle(sourceLayer),
            time_label: timeLabel,
            counts_label: `${snapshot.source_chronology.visible_site_count}/${snapshot.source_chronology.facet_site_count} unique source sites · ${snapshot.source_chronology.visible_node_count}/${snapshot.source_chronology.facet_node_count} governed source nodes in this interval · ${visibleObservationLabel}/${snapshot.source_chronology.facet_observation_denominator} contributing observations`,
            caveat: sourceCaveat,
          }, keyItems);
          return;
        }
        const metric = currentModeledContextMetric();
        const sourceWindow = currentModeledContextWindow();
        const qualityCounts = modeledContextFrameQualitySummary();
        const title = metric
          ? `PANGAEA 937075 modeled context — ${metric.label}`
          : 'PANGAEA 937075 modeled context';
        const keyItems = [
          ...MODELED_CONTEXT_PALETTE.map((entry) => ({ label: entry.label, cue: 'area', fill: entry.color, stroke: '#334155' })),
          { label: 'no pollen data · N/A, not 0', cue: 'area', fill: '#cbd5e1', stroke: '#334155' },
          { label: 'country boundary', cue: 'line', fill: null, stroke: '#64748b' },
        ];
        commitAtlasCapturePresentation({
          evidence_role: 'modeled_context',
          role_label: 'Modeled context · published source window',
          title,
          time_label: timeLabel,
          counts_label: `${snapshot.visible_modeled_context_feature_count}/${modeledContextPublishedCellCountLabel(snapshot)} published cells visible · ${qualityCounts.no_pollen_data} explicitly have no pollen data · ${sourceWindow?.label || 'source window unavailable'}`,
          caveat: 'Published modeled cells are context only, not an observed pollen trajectory · no atlas interpolation, flow, propagation, migration, or causation inference.',
        }, keyItems);
      }
      async function applyAtlasCaptureFrame(frameSpec) {
        const captureFrame = normalizeAtlasCaptureFrame(frameSpec);
        stopTimePlayback();
        stopModeledContextPlayback();
        closeHelpDialog();
        setSearchOpen(false, false);
        setFocusState(null);
        map.closePopup();
        sourceRecordConcentrationActive = false;
        sourceRecordConcentrationSnapshot = null;
        atlasCapturePresentation = null;
        document.documentElement.classList.add('atlas-capture-mode');
        window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
        map.invalidateSize({ animate: false });
        activeCountries = new Set(captureFrame.countries);
        setBasemap(captureFrame.basemap, { sync: false });
        if (captureFrame.storyKind === 'source_chronology') {
          deactivateModeledContext();
          selectSourceChronologyLevel(captureFrame.sourceLevel);
          const sourceLayer = sourceChronologyLayerForLevel(captureFrame.sourceLevel);
          activeLayerKeys = new Set(atlasCaptureOrientationKeys());
          if (sourceLayer) activeLayerKeys.add(sourceLayer.key);
          if (captureFrame.sourceLevel === 'source_ecological_code') {
            activeSourceChronologyCode = captureFrame.sourceCode;
          } else if (captureFrame.sourceLevel === 'source_taxon') {
            activeSourceChronologyTaxon = captureFrame.sourceTaxon;
            activeSourceChronologyPreset = captureFrame.sourcePreset;
            sourceChronologyTaxonSearch = '';
          }
          timeStartBp = captureFrame.frameWindow.youngerBp;
          timeIntervalYears = captureFrame.frameWindow.olderBp - captureFrame.frameWindow.youngerBp;
        } else {
          activeLayerKeys = new Set(atlasCaptureOrientationKeys());
          activeLayerKeys.add(MODELED_CONTEXT.layer_key);
          modeledContextFamilyKey = captureFrame.familyKey;
          modeledContextMetricKey = captureFrame.metricKey;
          await selectModeledContextWindow(captureFrame.sourceWindowIndex);
        }
        if (captureFrame.view) {
          map.setView([captureFrame.view.latitude, captureFrame.view.longitude], captureFrame.view.zoom, { animate: false });
        }
        setPanelCollapsed(true, false);
        setLegendCollapsed(true, false);
        await renderMapState();
        renderAtlasCaptureOverlay(atlasCaptureSnapshot());
        return awaitAtlasCaptureReady();
      }
      globalThis.BijuxPollenomicsAtlasCapture = Object.freeze({
        version: ATLAS_CAPTURE_API_VERSION,
        applyFrame: applyAtlasCaptureFrame,
        awaitReady: awaitAtlasCaptureReady,
        snapshot: atlasCaptureSnapshot,
      });
      function updateBasemapReadout(message) {
        basemapReadout.textContent = message;
      }
      function nextBasemapAfter(name) {
        for (const candidate of BASEMAP_FALLBACK_ORDER) {
          if (candidate === name) continue;
          if (candidate === 'none' || !failedBasemaps.has(candidate)) return candidate;
        }
        return 'none';
      }
      function setBasemap(name, options = {}) {
        const requested = BASEMAP_NAMES.includes(String(name)) ? String(name) : 'none';
        if (options.manual && requested !== 'none') {
          failedBasemaps.delete(requested);
          basemapErrorCounts.set(requested, 0);
        }
        if (activeBasemap && basemaps[activeBasemap]) {
          map.removeLayer(basemaps[activeBasemap]);
        }
        currentBasemap = requested;
        activeBasemap = null;
        if (requested === 'none') {
          updateBasemapReadout(options.reason || 'Basemap degraded: no basemap. Evidence data unaffected.');
        } else {
          activeBasemap = requested;
          basemaps[requested].addTo(map);
          updateBasemapReadout(options.reason || `${requested} loading`);
        }
        document.querySelectorAll('.basemap-button').forEach((button) => button.classList.toggle('is-active', button.dataset.basemap === requested));
        if (options.sync !== false) syncHashState();
      }
      Object.entries(basemaps).forEach(([name, layer]) => {
        layer.on('loading', () => {
          if (activeBasemap === name) updateBasemapReadout(`${name} loading`);
        });
        layer.on('load', () => {
          if (activeBasemap !== name) return;
          basemapErrorCounts.set(name, 0);
          updateBasemapReadout(`${name} available`);
        });
        layer.on('tileerror', () => {
          if (activeBasemap !== name) return;
          const failureCount = (basemapErrorCounts.get(name) || 0) + 1;
          basemapErrorCounts.set(name, failureCount);
          updateBasemapReadout(`${name} tile failure ${failureCount}/${MAX_PROVIDER_TILE_ERRORS}`);
          if (failureCount < MAX_PROVIDER_TILE_ERRORS) return;
          failedBasemaps.add(name);
          const fallback = nextBasemapAfter(name);
          setBasemap(fallback, {
            reason: fallback === 'none'
              ? `Basemap degraded: ${name} unavailable; no-basemap mode active. Evidence data unaffected.`
              : `Basemap degraded: ${name} unavailable; using ${fallback}. Evidence data unaffected.`,
          });
        });
      });
      document.querySelectorAll('.basemap-button').forEach((button) => button.classList.toggle('is-active', button.dataset.basemap === currentBasemap));
      function fitMapBounds(bounds) {
        const mapRect = document.getElementById('map').getBoundingClientRect();
        const validRect = (rect) => ['left', 'top', 'right', 'bottom'].every((key) => Number.isFinite(rect[key])) && rect.right >= rect.left && rect.bottom >= rect.top;
        const unavailable = () => {
          if (!mapViewReady) {
            // A hidden initial viewport still needs a valid Leaflet view before data rendering.
            map.setView(L.latLngBounds(INITIAL_BOUNDS).getCenter(), 0, { animate: false });
            initialMapFitPending = true;
          }
          topbarStatePill.textContent = 'Fit unavailable: the map has no usable area.';
          topbarStatePill.setAttribute('role', 'status');
        };
        if (!validRect(mapRect)) { unavailable(); return; }
        let topPadding = 36, bottomPadding = 36;
        for (const selector of ['.map-topbar', '.map-status']) {
          const panel = document.querySelector(selector);
          if (!panel || panel.hidden || !panel.getClientRects().length) continue;
          const style = getComputedStyle(panel);
          if (style.display === 'none' || style.visibility !== 'visible' || !(Number(style.opacity) > 0)) continue;
          const rect = panel.getBoundingClientRect();
          if (!validRect(rect)) { unavailable(); return; }
          const overlaps = Math.min(mapRect.right, rect.right) > Math.max(mapRect.left, rect.left)
            && Math.min(mapRect.bottom, rect.bottom) > Math.max(mapRect.top, rect.top);
          if (!overlaps) continue;
          if (selector === '.map-topbar') topPadding = Math.max(36, Math.min(mapRect.bottom, rect.bottom) - mapRect.top + 36);
          else bottomPadding = Math.max(36, mapRect.bottom - Math.max(mapRect.top, rect.top) + 36);
        }
        if (mapRect.right - mapRect.left <= 72 || mapRect.bottom - mapRect.top <= topPadding + bottomPadding) { unavailable(); return; }
        map.fitBounds(bounds, {
          padding: [36, 36],
          ...(topPadding > 36 ? { paddingTopLeft: [36, topPadding] } : {}),
          ...(bottomPadding > 36 ? { paddingBottomRight: [36, bottomPadding] } : {}),
          ...(reducedMotionQuery.matches ? { animate: false } : {}),
        });
        initialMapFitPending = false;
        if (topbarStatePill.textContent === 'Fit unavailable: the map has no usable area.') topbarStatePill.textContent = 'Map view fitted.';
      }
      function fitToActive() {
        const bounds = activeBounds();
        if (bounds && bounds.isValid()) fitMapBounds(bounds);
      }
      function resetView() { fitMapBounds(INITIAL_BOUNDS); }
      async function restoreDefaults() {
        edgeFocusLoadState.request++;
        if (focusState?.kind === 'edge' || pendingEdgeFocus) setFocusState(null);
        stopTimePlayback();
        deactivateModeledContext();
        activeCountries = new Set(DEFAULT_COUNTRIES);
        activeLayerKeys = new Set(DEFAULT_LAYER_KEYS);
        activeScientificSignalIds = new Set(DEFAULT_SCIENTIFIC_SIGNAL_IDS);
        resetScientificPins();
        activeCountryPair = 'all';
        resetRelationFilters();
        resetRelationEventDefinition();
        activeEvidenceDisplay = resetEvidenceDisplay();
        crossBorderOnly = false;
        crossBorderOnlyCheckbox.checked = false;
        activeAnimalSpecies = 'all';
        activeAnimalScope = 'all';
        activeAnimalConfidence = 'all';
        activeAnimalTemporalWindow = 'all';
        animalNordicOnly = false;
        animalNordicOnlyCheckbox.checked = false;
        activeSourceChronologyLevel = defaultSourceChronologyLevel;
        activeSourceChronologyCode = 'all';
        activeSourceChronologyTaxon = 'all';
        activeSourceChronologyPreset = 'none';
        sourceChronologyTaxonSearch = '';
        sourceRecordConcentrationActive = false;
        sourceRecordConcentrationSnapshot = null;
        sourceChronologyTaxonQuery.value = '';
        slider.value = 20;
        timeStartBp = DEFAULT_TIME_START_BP;
        timeIntervalYears = DEFAULT_TIME_INTERVAL_YEARS;
        if (signedNativeTime) signedNativeTime.set(signedNativeTime.extent());
        focusSourceChronologyNavigation();
        densityOpacity = 0.6;
        densityOpacitySlider.value = '60';
        setPanelCollapsed(defaultPanelCollapsed(), false);
        searchInput.value = '';
        setSearchOpen(false);
        if (currentBasemap !== DEFAULT_BASEMAP) setBasemap(DEFAULT_BASEMAP, { manual: true });
        renderCountryControls();
        renderLayerControls();
        await renderMapState();
        const restoredState = atlasFilterStateSnapshot(activeCountries, activeScientificSignalIds, activeCountryPair, crossBorderOnly);
        if (!atlasFilterStateEquals(restoredState, DEFAULT_ATLAS_FILTER_STATE)) throw new Error('Atlas default filter state did not restore exactly.');
        if (visibleGovernedEdges().length !== DEFAULT_GOVERNED_EDGE_VISIBLE_COUNT) throw new Error('Atlas default candidate count did not restore exactly.');
        selectionReadout.dataset.resetRestoredEligibility = String(GOVERNED_EDGE_ELIGIBILITY_COUNT);
        selectionReadout.dataset.resetRestoredVisibleEdges = String(DEFAULT_GOVERNED_EDGE_VISIBLE_COUNT);
        resetView();
      }
      document.getElementById('countries-all').addEventListener('click', () => { activeCountries = new Set(COUNTRIES); renderCountryControls(); renderMapState(); });
      document.getElementById('countries-none').addEventListener('click', () => { activeCountries = new Set(); renderCountryControls(); renderMapState(); });
      document.getElementById('countries-fit').addEventListener('click', fitToActive);
      document.getElementById('scientific-whole').addEventListener('click', () => {
        activeScientificSignalIds = new Set(DEFAULT_SCIENTIFIC_SIGNAL_IDS);
        resetScientificPins();
        renderMapState();
      });
      document.getElementById('scientific-clear').addEventListener('click', () => {
        activeScientificSignalIds = new Set();
        resetScientificPins();
        renderMapState();
      });
      document.getElementById('scientific-controls').addEventListener('toggle', event => {
        if (!event.currentTarget.open || ATLAS_EVIDENCE.classifications_status !== 'available' || !SCIENTIFIC_SIGNALS.length) return;
        renderScientificControls();
        loadEvidenceTools().then(renderScientificControls, renderScientificControls);
      });
      document.querySelectorAll('[data-source-shortcut]').forEach((button) => {
        button.addEventListener('click', () => {
          const shortcut = button.dataset.sourceShortcut;
          const targetLevel = shortcut === 'sample'
            ? 'source_sample_presence'
            : (shortcut === 'taxa' ? 'source_taxon' : 'source_ecological_code');
          if (!selectSourceChronologyLevel(targetLevel)) return;
          sourceChronologyTaxonSearch = '';
          sourceChronologyTaxonQuery.value = sourceChronologyTaxonSearch;
          if (targetLevel === 'source_ecological_code') {
            activeSourceChronologyPreset = 'none';
            const layer = sourceChronologyLayerForLevel(targetLevel);
            activeSourceChronologyCode = normalizedSingleValue(
              shortcut,
              ['all', ...layer.facet_metadata.source_ecological_codes.map((row) => row.value)],
              'all'
            );
          } else if (shortcut === 'taxa') {
            activeSourceChronologyTaxon = 'all';
            activeSourceChronologyPreset = 'none';
          }
          focusSourceChronologyNavigation();
          renderLayerControls();
          renderMapState();
          sourceChronologyControls.open = true;
        });
      });
      document.querySelectorAll('[data-source-preset]').forEach((button) => {
        button.addEventListener('click', () => {
          const layer = sourceChronologyLayerForLevel('source_taxon');
          if (!layer || !selectSourceChronologyLevel('source_taxon')) return;
          const validPresetKeys = layer.facet_metadata.source_label_preset_accountability.presets.map((row) => row.key);
          activeSourceChronologyPreset = normalizedSingleValue(button.dataset.sourcePreset, validPresetKeys, 'none');
          activeSourceChronologyTaxon = 'all';
          sourceChronologyTaxonSearch = '';
          sourceChronologyTaxonQuery.value = '';
          sourceRecordConcentrationActive = false;
          focusSourceChronologyNavigation();
          renderLayerControls();
          renderMapState();
          sourceChronologyControls.open = true;
        });
      });
      relationFilterFields().forEach(([key]) => {
        relationFilterControls[key].addEventListener('change', () => {
          activeRelationFilters[key] = relationFilterControls[key].value || null;
          activeRelationFilters.invalid = activeRelationFilters.invalid.filter(field => field !== key);
          renderMapState();
        });
      });
      relationEventDefinitionControl.addEventListener('change', () => {
        Object.assign(activeRelationEventDefinition, relationEventDefinitionFromHash(new URLSearchParams(
          relationEventDefinitionControl.value ? {relation_event_definition: relationEventDefinitionControl.value} : {}
        )));
        renderMapState();
      });
      countryPairFilter.addEventListener('change', () => {
        activeCountryPair = normalizedSingleValue(countryPairFilter.value, ['all', ...COUNTRY_PAIR_KEYS], 'all');
        renderMapState();
      });
      crossBorderOnlyCheckbox.addEventListener('change', () => {
        crossBorderOnly = crossBorderOnlyCheckbox.checked;
        renderMapState();
      });
      document.getElementById('fit-active').addEventListener('click', fitToActive);
      searchToggleButton.addEventListener('click', () => {
        setSearchOpen(topbarSearch.hidden, !topbarSearch.hidden);
      });
      document.getElementById('reset-view').addEventListener('click', resetView);
      document.getElementById('restore-defaults').addEventListener('click', restoreDefaults);
      document.getElementById('copy-link').addEventListener('click', async () => {
        syncHashState();
        const button = document.getElementById('copy-link');
        const previous = button.textContent;
        try {
          await navigator.clipboard.writeText(window.location.href);
          button.textContent = 'Link copied';
        } catch (error) {
          button.textContent = 'Copy failed';
        }
        window.setTimeout(() => { button.textContent = previous; }, 1400);
      });
      document.querySelectorAll('details[data-evidence-tools]').forEach(panel => {
        panel.addEventListener('toggle', () => {
          if (!panel.open) return;
          const containers = panel.querySelectorAll('#relation-country-summary, #relation-time-summary');
          if (!currentEvidenceTools()) containers.forEach(container => { container.textContent = evidenceToolsError || 'Loading evidence tools…'; });
          loadEvidenceTools().then(() => { if (panel.open) renderEvidenceToolPanels(); }, () => { if (panel.open) renderEvidenceToolPanels(); });
        });
      });
      document.getElementById('fullscreen-toggle').addEventListener('click', async () => {
        const target = document.querySelector('.map-stage');
        if (!document.fullscreenElement) { await target.requestFullscreen(); } else { await document.exitFullscreen(); }
      });
      document.querySelectorAll('.basemap-button').forEach((button) => button.addEventListener('click', () => setBasemap(button.dataset.basemap, { manual: true })));
      panelToggleButton.addEventListener('click', () => {
        const opening = sidebar.classList.contains('is-collapsed');
        if (mobileLayoutQuery.matches && opening) mobilePanelReturnFocus = panelToggleButton;
        setPanelCollapsed(!opening);
        if (mobileLayoutQuery.matches && opening) mobilePanelCloseButton.focus({ preventScroll: true });
      });
      basemapReadout.addEventListener('click', () => {
        if (mobileLayoutQuery.matches) mobilePanelReturnFocus = basemapReadout;
        setPanelCollapsed(false);
        viewControls.open = true;
        basemapSwitch.scrollIntoView({
          block: 'nearest',
          behavior: 'auto',
        });
        const activeButton = basemapSwitch.querySelector('.basemap-button.is-active');
        if (activeButton) activeButton.focus({ preventScroll: true });
      });
      timeStepperStatus.addEventListener('click', () => {
        if (mobileLayoutQuery.matches) mobilePanelReturnFocus = timeStepperStatus;
        setPanelCollapsed(false);
        if (sourceChronologyLayers().length === 0) {
          timeControls.open = true;
          timeControls.scrollIntoView({
            block: 'nearest',
            behavior: reducedMotionQuery.matches || document.documentElement.classList.contains('atlas-capture-mode') ? 'auto' : 'smooth',
          });
          const intervalPreset = timeControls.querySelector('[data-time-interval="1000"]');
          if (intervalPreset) intervalPreset.focus({ preventScroll: true });
          return;
        }
        sourceChronologyControls.open = true;
        sourceChronologyControls.scrollIntoView({
          block: 'nearest',
          behavior: reducedMotionQuery.matches || document.documentElement.classList.contains('atlas-capture-mode') ? 'auto' : 'smooth',
        });
        sourceChronologyLevel.focus({ preventScroll: true });
      });
      helpToggleButton.addEventListener('click', openHelpDialog);
      helpCloseButton.addEventListener('click', closeHelpDialog);
      helpReturnButton.addEventListener('click', closeHelpDialog);
      helpDialog.addEventListener('click', (event) => {
        if (event.target === helpDialog) closeHelpDialog();
      });
      mobilePanelCloseButton.addEventListener('click', closeMobilePanel);
      mobileScrim.addEventListener('click', closeMobilePanel);
      slider.addEventListener('input', renderMapState);
      function applyGlobalTimeStartInput() {
        stopTimePlayback();
        deactivateModeledContext();
        timeStartBp = clampTimeStart(timeStartSlider.value, timeIntervalYears);
        renderMapState();
      }
      function applyGlobalTimeIntervalInput() {
        stopTimePlayback();
        deactivateModeledContext();
        timeIntervalYears = clampTimeInterval(timeIntervalSlider.value);
        renderMapState();
      }
      timeStartSlider.addEventListener('input', applyGlobalTimeStartInput);
      timeIntervalSlider.addEventListener('input', applyGlobalTimeIntervalInput);
      timePlaybackToggle.addEventListener('click', () => {
        if (timePlaybackTimer === null) startTimePlayback(); else stopTimePlayback();
      });
      timeStepOlder.addEventListener('click', async () => {
        const restoreFocus = document.activeElement === timeStepOlder;
        stopTimePlayback();
        deactivateModeledContext();
        timeStartBp = previousPlaybackTimeStart(timeStartBp, timeIntervalYears);
        await renderMapState();
        if (restoreFocus && timeStepOlder.disabled && !timeStepNewer.disabled) timeStepNewer.focus({ preventScroll: true });
      });
      timeStepNewer.addEventListener('click', async () => {
        const restoreFocus = document.activeElement === timeStepNewer;
        stopTimePlayback();
        deactivateModeledContext();
        timeStartBp = nextPlaybackTimeStart(timeStartBp, timeIntervalYears);
        await renderMapState();
        if (restoreFocus && timeStepNewer.disabled && !timeStepOlder.disabled) timeStepOlder.focus({ preventScroll: true });
      });
      modeledContextFamily.addEventListener('change', () => {
        const family = modeledContextFamilyByKey(modeledContextFamily.value);
        if (!family) return;
        modeledContextFamilyKey = family.key;
        modeledContextMetricKey = family.default_metric_key;
        renderMapState();
      });
      modeledContextMetric.addEventListener('change', () => {
        const family = currentModeledContextFamily();
        if (!family || !family.metrics.some((metric) => metric.key === modeledContextMetric.value)) return;
        modeledContextMetricKey = modeledContextMetric.value;
        renderMapState();
      });
      modeledContextToggle.addEventListener('click', () => {
        if (modeledContextActive) {
          deactivateModeledContext();
          renderMapState();
        } else {
          stopTimePlayback();
          selectModeledContextWindow(modeledContextWindowIndex);
        }
      });
      modeledContextWindow.addEventListener('change', () => {
        stopModeledContextPlayback();
        selectModeledContextWindow(Number(modeledContextWindow.value));
      });
      modeledContextPlayback.addEventListener('click', () => {
        if (modeledContextPlaybackTimer === null) startModeledContextPlayback(); else stopModeledContextPlayback();
      });
      modeledContextDownload.addEventListener('click', downloadModeledContextFrame);
      document.getElementById('selection-export').addEventListener('click', downloadAtlasSelection);
      sourceChronologyLevel.addEventListener('change', () => {
        if (!selectSourceChronologyLevel(sourceChronologyLevel.value)) return;
        focusSourceChronologyNavigation();
        renderLayerControls();
        renderMapState();
      });
      sourceChronologyCode.addEventListener('change', () => {
        const layer = sourceChronologyLayerForLevel('source_ecological_code');
        if (!layer) return;
        stopTimePlayback();
        activeSourceChronologyCode = normalizedSingleValue(
          sourceChronologyCode.value,
          ['all', ...layer.facet_metadata.source_ecological_codes.map((row) => row.value)],
          'all'
        );
        sourceRecordConcentrationActive = false;
        focusSourceChronologyNavigation();
        renderMapState();
      });
      sourceChronologyTaxonQuery.addEventListener('input', () => {
        sourceChronologyTaxonSearch = sourceChronologyTaxonQuery.value;
        if (sourceChronologyTaxonSearch.trim()) activeSourceChronologyPreset = 'none';
        renderSourceChronologyControls();
      });
      sourceChronologyTaxon.addEventListener('change', () => {
        const layer = sourceChronologyLayerForLevel('source_taxon');
        if (!layer) return;
        stopTimePlayback();
        activeSourceChronologyTaxon = normalizedSingleValue(
          sourceChronologyTaxon.value,
          ['all', ...layer.facet_metadata.source_taxa.map((row) => row.value)],
          'all'
        );
        activeSourceChronologyPreset = 'none';
        sourceRecordConcentrationActive = false;
        focusSourceChronologyNavigation();
        renderMapState();
      });
      sourceRecordConcentrationToggle.addEventListener('click', () => {
        const layer = sourceChronologyLayerForLevel(activeSourceChronologyLevel);
        if (!sourceRecordConcentrationSelection(layer)) {
          sourceRecordConcentrationActive = false;
          renderMapState();
          return;
        }
        sourceRecordConcentrationActive = !sourceRecordConcentrationActive;
        renderMapState();
      });
      densityOpacitySlider.addEventListener('input', () => { densityOpacity = Number(densityOpacitySlider.value) / 100; renderMapState(); });
      animalNordicOnlyCheckbox.addEventListener('change', () => {
        animalNordicOnly = animalNordicOnlyCheckbox.checked;
        renderMapState();
      });
      document.querySelectorAll('[data-km]').forEach((button) => {
        button.addEventListener('click', () => {
          slider.value = button.dataset.km;
          renderMapState();
        });
      });
      document.querySelectorAll('[data-time-interval]').forEach((button) => {
        button.addEventListener('click', () => {
          stopTimePlayback();
          deactivateModeledContext();
          const preset = button.dataset.timeInterval;
          const navigationExtent = selectedTimePlaybackExtent();
          timeIntervalYears = preset === 'full'
            ? Math.max(1, navigationExtent.time_max_bp - navigationExtent.time_min_bp)
            : Number(preset);
          renderMapState();
        });
      });
      searchInput.addEventListener('input', buildSearchResults);
      searchClearButton.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.focus();
        buildSearchResults();
      });
      searchInput.addEventListener('focus', buildSearchResults);
      searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
          event.preventDefault();
          setSearchOpen(false, true);
          return;
        }
        if (event.key === 'Enter') {
          const firstResult = searchResults.querySelector('[data-search-index]');
          if (firstResult) firstResult.click();
        }
      });
      document.addEventListener('click', (event) => {
        if (!searchResults.contains(event.target) && event.target !== searchInput) {
          searchResults.hidden = true;
        }
      });
      focusCloseButton.addEventListener('click', () => setFocusState(null));
      focusCopyLinkButton.addEventListener('click', async () => {
        if (focusCopyLinkButton.disabled) return;
        if (focusState?.kind === 'edge' && document.getElementById('map').getAttribute('aria-busy') === 'true') {
          focusExportStatus.textContent = 'Relation link unavailable while selected evidence is loading.';
          return;
        }
        if (focusState?.kind === 'edge' && !edgeFocusSelection(focusState, publishedEdgeFocusBuild(), visibleGovernedEdges(), visiblePointEntries)) {
          setFocusState(null);
          topbarStatePill.textContent = 'Relation link unavailable under the current filters.';
          return;
        }
        syncHashState();
        try {
          await navigator.clipboard.writeText(window.location.href);
          focusExportStatus.textContent = focusState?.kind === 'edge' ? 'Relation link copied.' : 'Record link copied.';
        } catch {
          focusExportStatus.textContent = focusState?.kind === 'edge' ? 'Copy this relation link from your browser address bar.' : 'Copy this record link from your browser address bar.';
        }
      });
      focusExportButton.addEventListener('click', () => {
        try {
          if (focusCard.hidden) throw Error('selected_record_not_visible');
          syncHashState();
          const selection = {
            atlas_build_id: STATIC_ATLAS_BOOTSTRAP.build_id || null,
            shared_url: window.location.href,
            countries: [...activeCountries].sort(),
            layers: [...activeLayerKeys].sort(),
            scientific_signals: [...activeScientificSignalIds].sort(),
            relation_filters: relationFilterMetadata(GOVERNED_EDGE_RECORDS, activeRelationFilters),
            relation_event_definition: relationEventDefinitionMetadata(GOVERNED_EDGE_RECORDS, activeRelationEventDefinition),
            scientific_picker: scientificPickerMetadata(),
            evidence_display: evidenceDisplayMetadata(activeEvidenceDisplay),
            map_window_bp: TIME_HAS_DATA ? [timeStartBp, timeWindowEndBp()] : null,
            selected_detail_section: activeFocusTab,
            basemap: currentBasemap,
          };
          const payload = buildSourcePollenRecordExport(focusState, selection, decodeDetailTableRow);
          const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = sourcePollenRecordFilename(focusState.recordId);
          link.click();
          window.setTimeout(() => URL.revokeObjectURL(url), 1000);
          focusExportStatus.textContent = `${payload.pollen_observations.record_count} source observations downloaded with ${payload.chronology_claims.record_count} chronology claims.`;
        } catch (error) {
          focusExportStatus.textContent = error instanceof Error ? error.message : 'Source pollen export failed.';
        }
      });
      focusTabs.addEventListener('keydown', (event) => {
        if (!event.target.matches('[data-focus-tab]')) return;
        const keys = DETAIL_TAB_DEFINITIONS.map(([key]) => key);
        const index = keys.indexOf(event.target.dataset.focusTab);
        let nextIndex;
        if (event.key === 'ArrowRight') nextIndex = (index + 1) % keys.length;
        else if (event.key === 'ArrowLeft') nextIndex = (index + keys.length - 1) % keys.length;
        else if (event.key === 'Home') nextIndex = 0;
        else if (event.key === 'End') nextIndex = keys.length - 1;
        else return;
        event.preventDefault();
        activeFocusTab = keys[nextIndex];
        renderFocusDetail();
      });
      focusPreviousButton.addEventListener('click', () => {
        if (!focusState || focusState.kind !== 'point' || !visiblePointEntries.length) return;
        const currentIndex = visiblePointEntries.indexOf(visiblePointEntryForFocus(focusState));
        if (currentIndex < 0) return;
        const nextIndex = (currentIndex - 1 + visiblePointEntries.length) % visiblePointEntries.length;
        focusPointAtVisibleIndex(nextIndex);
      });
      focusNextButton.addEventListener('click', () => {
        if (!focusState || focusState.kind !== 'point' || !visiblePointEntries.length) return;
        const currentIndex = visiblePointEntries.indexOf(visiblePointEntryForFocus(focusState));
        if (currentIndex < 0) return;
        const nextIndex = (currentIndex + 1) % visiblePointEntries.length;
        focusPointAtVisibleIndex(nextIndex);
      });
      focusZoomButton.addEventListener('click', () => {
        if (!focusState) return;
        if (focusState.kind === 'polygon' && focusState.bounds) {
          map.fitBounds(focusState.bounds, { padding: [32, 32], ...(reducedMotionQuery.matches ? { animate: false } : {}) });
          return;
        }
        if (Number.isFinite(focusState.latitude) && Number.isFinite(focusState.longitude)) {
          map.flyTo([focusState.latitude, focusState.longitude], Math.max(map.getZoom(), 8), { duration: 0.7, ...(reducedMotionQuery.matches ? { animate: false } : {}) });
        }
      });
      map.on('zoomend', () => {
        zoomReadout.textContent = map.getZoom().toFixed(1);
        centerReadout.textContent = `${map.getCenter().lat.toFixed(3)}, ${map.getCenter().lng.toFixed(3)}`;
      });
      map.on('moveend', () => {
        centerReadout.textContent = `${map.getCenter().lat.toFixed(3)}, ${map.getCenter().lng.toFixed(3)}`;
        renderMapState();
      });
      map.on('mousemove', (event) => { cursorReadout.textContent = `${event.latlng.lat.toFixed(3)}, ${event.latlng.lng.toFixed(3)}`; });
      document.addEventListener('fullscreenchange', () => window.setTimeout(() => map.invalidateSize(), 160));
      document.addEventListener('keydown', (event) => {
        if (event.key === 'Tab' && !helpDialog.hidden) {
          const focusable = helpDialogFocusableElements();
          if (!focusable.length) {
            event.preventDefault();
            return;
          }
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (event.shiftKey && (document.activeElement === first || !helpDialog.contains(document.activeElement))) {
            event.preventDefault();
            last.focus();
          } else if (!event.shiftKey && (document.activeElement === last || !helpDialog.contains(document.activeElement))) {
            event.preventDefault();
            first.focus();
          }
          return;
        }
        if (event.key === '?') {
          event.preventDefault();
          openHelpDialog();
          return;
        }
        if (event.key === 'Escape' && !helpDialog.hidden) {
          closeHelpDialog();
          return;
        }
        if (event.key === 'Escape' && !focusCard.hidden && focusCard.contains(document.activeElement)) {
          event.preventDefault();
          setFocusState(null);
          return;
        }
        if (event.key === 'Escape' && !topbarSearch.hidden) {
          setSearchOpen(false, true);
          return;
        }
        if (event.key === 'Escape' && mobileLayoutQuery.matches && !sidebar.classList.contains('is-collapsed')) {
          closeMobilePanel();
        }
      });
      mobileLayoutQuery.addEventListener('change', () => {
        if (panelPreferenceFromHash() === null) {
          setPanelCollapsed(defaultPanelCollapsed(), false);
          return;
        }
        updatePanelToggleLabel();
      });
      reducedMotionQuery.addEventListener('change', () => {
        if (reducedMotionQuery.matches) {
          stopTimePlayback();
          stopModeledContextPlayback();
        }
        refreshTimePlaybackControl();
        renderModeledContextControls();
      });
      document.querySelectorAll('[data-layer-preset]').forEach((button) => {
        button.addEventListener('click', () => applyLayerPreset(button.dataset.layerPreset));
      });
      legendToggleButton.addEventListener('click', () => setLegendCollapsed(!legendCollapsed));
      window.addEventListener('resize', () => window.setTimeout(() => {
        map.invalidateSize();
        if (initialMapFitPending) resetView();
      }, 120));
      Object.assign(activeRelationFilters, initialState.relationFilters);
      Object.assign(activeRelationEventDefinition, initialState.relationEventDefinition);
      if (NATIVE_LRA_BINDING !== null) {
        if (await staticAtlasSha256(NATIVE_LRA_BINDING.bytes) !== NATIVE_LRA_BINDING.sha256) throw Error('Native LRA view byte identity mismatch.');
        const nativeView = JSON.parse(NATIVE_LRA_BINDING.bytes);
        nativeLraController = createNativeLraController(nativeView, NATIVE_LRA_BINDING.sha256, {
          sha256: staticAtlasSha256,
          globalContext: () => ({time_window_bp: signedNativeTime ? signedNativeTime.window() : [timeStartBp, timeWindowEndBp()], active_layer_keys: [...activeLayerKeys], ...(signedNativeTime ? {temporal_profile:'calendar-bp1950-signed.v1',temporal_axis:'BP1950'} : {})}),
          restoreTime: params => {signedNativeTime.restore(params);timeStartBp=signedNativeTime.window()[0];},
          writeTime: params => signedNativeTime.write(params),
          changed: () => renderMapState(),
        });
        nativeLraController.restoreHash(new URLSearchParams(window.location.hash.slice(1)));
        if (signedNativeTime) signedNativeTimeControls = mountSignedNativeTimeControls(signedNativeTime, () => {timeStartBp=signedNativeTime.window()[0];renderMapState();});
        nativeLraController.mount();
        window.__BIJUX_LRA_VIEW__ = Object.freeze({snapshot: nativeLraController.snapshot, setSelection: nativeLraController.setSelection, exportSelection: nativeLraController.exportSelection});
      }
      densityOpacitySlider.value = String(Math.round(densityOpacity * 100));
      slider.value = String(clampDiameter(initialState.diameter));
      setPanelCollapsed(panelPreferenceFromHash() ?? defaultPanelCollapsed(), false);
      renderCountryControls();
      renderLayerControls();
      setBasemap(currentBasemap, { sync: false });
      setLegendCollapsed(legendCollapsed, false);
      resetView();
      await renderMapState();
      if (!initialState.edgeFocus && initialState.focus) {
        const requestedEntry = uniquePointEntryForFocus(visiblePointEntries, initialState.focus);
        if (requestedEntry) {
          await focusPointAtVisibleIndex(visiblePointEntries.indexOf(requestedEntry));
          activeFocusTab = initialState.focus.tab;
          renderFocusDetail();
          syncHashState();
        } else {
          topbarStatePill.textContent = 'Shared record is unavailable under the current filters.';
        }
      }
      zoomReadout.textContent = map.getZoom().toFixed(1);
      centerReadout.textContent = `${map.getCenter().lat.toFixed(3)}, ${map.getCenter().lng.toFixed(3)}`;
      })().catch((error) => {
        const failure = document.createElement('main');
        failure.setAttribute('role', 'alert');
        failure.setAttribute('aria-live', 'assertive');
        failure.style.cssText = 'margin:24px;padding:20px;border:2px solid #b42344;border-radius:16px;background:#fff;color:#18253d;font:16px/1.6 system-ui,sans-serif;';
        failure.textContent = error instanceof Error ? error.message : 'Static atlas initialization failed. Reload the page or redeploy the complete atlas build.';
        document.body.prepend(failure);
        console.error(error);
      });
    
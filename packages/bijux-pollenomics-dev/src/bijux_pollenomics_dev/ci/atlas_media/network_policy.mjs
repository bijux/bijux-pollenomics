export function classifyNetworkRequest(params, authority) {
  const url = String(params?.request?.url || '');
  const method = String(params?.request?.method || '');
  const resourceType = String(params?.resourceType || params?.type || '');
  let allowed = false;
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'data:') {
      allowed = method === 'GET';
    } else if (parsed.protocol === 'blob:') {
      allowed = method === 'GET' && blobHasExactOrigin(parsed, authority.origin);
    } else if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      allowed = method === 'GET'
        && parsed.origin === authority.origin
        && authority.allowedPaths.has(parsed.pathname)
        && parsed.search === ''
        && parsed.username === ''
        && parsed.password === '';
    }
  } catch {
    allowed = false;
  }
  return {
    allowed,
    receipt: {
      url,
      scheme: parsedField(url, 'protocol'),
      host: parsedField(url, 'hostname'),
      port: parsedPort(url),
      path: parsedField(url, 'pathname'),
      query: parsedField(url, 'search'),
      method,
      resource_type: resourceType,
    },
  };
}

function parsedField(url, field) {
  try {
    const value = new URL(url)[field];
    if (field === 'protocol') return value.slice(0, -1);
    if (field === 'hostname' && value === '') return null;
    return value;
  } catch {
    return null;
  }
}

function parsedPort(url) {
  try {
    const value = new URL(url).port;
    return value === '' ? null : Number(value);
  } catch {
    return null;
  }
}

function blobHasExactOrigin(parsed, expectedOrigin) {
  try {
    return new URL(parsed.pathname).origin === expectedOrigin;
  } catch {
    return false;
  }
}

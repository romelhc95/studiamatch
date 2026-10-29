const SAFE_POSTGREST_CODE = /^(?:PGRST[0-9]{3}|[0-9A-Z]{5})$/;
const MAX_ERROR_BODY_BYTES = 8192;
const SAFE_APPLICATION_CODES = Object.freeze({
  rpc_arguments_invalid: 'RPC_ARGUMENTS_INVALID',
  rpc_gateway_unavailable: 'RPC_GATEWAY_UNAVAILABLE',
  rpc_method_rejected: 'RPC_METHOD_REJECTED',
  rpc_not_allowlisted: 'RPC_NOT_ALLOWLISTED',
  rpc_replay_rejected: 'RPC_REPLAY_REJECTED',
  rpc_signature_invalid: 'RPC_SIGNATURE_INVALID',
  rpc_signature_required: 'RPC_SIGNATURE_REQUIRED',
  rpc_signed_wrapper_required: 'RPC_SIGNED_WRAPPER_REQUIRED',
});

function classifyPayload(payload) {
  const candidate = payload && typeof payload === 'object' && !Array.isArray(payload)
    ? payload.code
    : null;
  return typeof candidate === 'string' && SAFE_POSTGREST_CODE.test(candidate)
    ? candidate
    : 'UNCLASSIFIED';
}

export async function readSafePostgrestErrorDiagnostic(response) {
  try {
    const body = response.clone().body;
    if (!body) return { code: 'UNCLASSIFIED', bodyClass: 'NO_BODY' };
    const reader = body.getReader();
    const chunks = [];
    let byteLength = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      byteLength += value.byteLength;
      if (byteLength > MAX_ERROR_BODY_BYTES) {
        void reader.cancel().catch(() => {});
        return { code: 'UNCLASSIFIED', bodyClass: 'OVERSIZED' };
      }
      chunks.push(Buffer.from(value));
    }
    let payload;
    try {
      payload = JSON.parse(Buffer.concat(chunks, byteLength).toString('utf8'));
    } catch {
      return { code: 'UNCLASSIFIED', bodyClass: 'INVALID_JSON' };
    }
    const code = classifyPayload(payload);
    if (code === 'UNCLASSIFIED' && payload && typeof payload === 'object' && !Array.isArray(payload)
      && typeof payload.code === 'string' && Object.hasOwn(SAFE_APPLICATION_CODES, payload.code)) {
      return {
        code,
        bodyClass: 'ALLOWLISTED_APPLICATION_CODE',
        applicationCode: SAFE_APPLICATION_CODES[payload.code],
      };
    }
    return { code, bodyClass: code === 'UNCLASSIFIED' ? 'CODE_UNRECOGNIZED' : 'ALLOWLISTED_CODE' };
  } catch {
    return { code: 'UNCLASSIFIED', bodyClass: 'READ_FAILED' };
  }
}

export async function readSafePostgrestErrorCode(response) {
  return (await readSafePostgrestErrorDiagnostic(response)).code;
}

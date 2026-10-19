const postgrestRoot = 'http://h3req1-c03-postgrest:3000/';

const FETCH_ERROR_CODES = new Set([
  'ABORT_ERR',
  'ECONNREFUSED',
  'ECONNRESET',
  'EAI_AGAIN',
  'EHOSTUNREACH',
  'ENETUNREACH',
  'ENOTFOUND',
  'ETIMEDOUT',
  'UND_ERR_CONNECT_TIMEOUT',
]);
const ERROR_BODY_LIMIT_BYTES = 8192;
const SAFE_SERVER_ERROR_CODE = /^(?:PGRST[0-9]{3}|[A-Z0-9]{5})$/;

export function classifyHttpStatus(status) {
  if (Number.isInteger(status) && status >= 200 && status < 300) return 'OK';
  if (Number.isInteger(status) && status >= 100 && status <= 599) return `HTTP_${status}`;
  return 'HTTP_STATUS_INVALID';
}

export function classifyFetchFailure(error) {
  const code = error?.cause?.code;
  if (typeof code === 'string' && FETCH_ERROR_CODES.has(code)) return code;
  if (error?.name === 'AbortError' || error?.name === 'TimeoutError') return 'TIMEOUT';
  return 'FETCH_FAILED';
}

async function readAllowlistedErrorCode(response) {
  let reader;
  try {
    if (typeof response?.body?.getReader !== 'function') return null;
    // BYOB bounds bytes delivered to this probe; a default reader may hand back
    // a single chunk larger than the remaining allowance before it can cancel.
    reader = response.body.getReader({ mode: 'byob' });
    const chunks = [];
    let bytesRead = 0;

    while (true) {
      const result = await reader.read(new Uint8Array(ERROR_BODY_LIMIT_BYTES - bytesRead));
      if (result.done) break;
      if (!(result.value instanceof Uint8Array) || result.value.byteLength === 0
        || result.value.byteLength > ERROR_BODY_LIMIT_BYTES - bytesRead) {
        await reader.cancel();
        return null;
      }
      bytesRead += result.value.byteLength;
      if (bytesRead >= ERROR_BODY_LIMIT_BYTES) {
        await reader.cancel();
        return null;
      }
      chunks.push(result.value);
    }

    const bytes = new Uint8Array(bytesRead);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const payload = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return null;
    return typeof payload.code === 'string' && SAFE_SERVER_ERROR_CODE.test(payload.code)
      ? payload.code
      : null;
  } catch {
    if (reader) {
      try {
        await reader.cancel();
      } catch {
        // Keep the diagnostic closed if the response stream cannot be cancelled.
      }
    }
    return null;
  } finally {
    if (reader) {
      try {
        reader.releaseLock();
      } catch {
        // Releasing a disturbed stream is best-effort; no body data is exposed.
      }
    }
  }
}

export async function probePostgrest(fetchImpl = globalThis.fetch) {
  try {
    const response = await fetchImpl(postgrestRoot, { signal: AbortSignal.timeout(2000) });
    const statusCode = classifyHttpStatus(response.status);
    if (statusCode === 'OK' || statusCode === 'HTTP_STATUS_INVALID') {
      return `phase=postgrest-probe|error_code=${statusCode}`;
    }
    const serverErrorCode = await readAllowlistedErrorCode(response);
    return `phase=postgrest-probe|error_code=${statusCode}${serverErrorCode ? `_${serverErrorCode}` : ''}`;
  } catch (error) {
    return `phase=postgrest-probe|error_code=${classifyFetchFailure(error)}`;
  }
}

if (process.argv[1] && new URL(import.meta.url).pathname === process.argv[1]) {
  const result = await probePostgrest();
  process.stdout.write(`${result}\n`);
  process.exitCode = result === 'phase=postgrest-probe|error_code=OK' ? 0 : 1;
}

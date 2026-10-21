const EXPECTED_ROOT_ASSET = 'C03 synthetic public asset /';

export async function pagesWorkerRootProbe(fetchPagesRoot) {
  if (typeof fetchPagesRoot !== 'function') {
    return { ready: false, status: 0, assetMatches: false };
  }

  try {
    const response = await fetchPagesRoot();
    const body = await response.text();
    const assetMatches = response.status === 200 && body === EXPECTED_ROOT_ASSET;
    return { ready: assetMatches, status: response.status, assetMatches };
  } catch {
    return { ready: false, status: 0, assetMatches: false };
  }
}

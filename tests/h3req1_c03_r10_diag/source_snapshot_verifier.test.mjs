import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import {
  mkdtempSync,
  mkdirSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { verifySourceSnapshot } from './source_snapshot_verifier.mjs';

const digest = (value) => createHash('sha256').update(value).digest('hex');

function createFixture({ extraFiles = [] } = {}) {
  const root = mkdtempSync(join(tmpdir(), 'h3-r10-snapshot-test-'));
  mkdirSync(join(root, 'tests'), { recursive: true });
  const sourcePath = 'tests/fixture.sql';
  const source = 'SELECT 1;\n';
  writeFileSync(join(root, sourcePath), source);
  const manifestPath = 'tests/fixture.sha256';
  const manifest = `${digest(source)}  ${sourcePath}\n`;
  writeFileSync(join(root, manifestPath), manifest);
  for (const [path, contents] of extraFiles) {
    const absolutePath = join(root, path);
    mkdirSync(join(absolutePath, '..'), { recursive: true });
    writeFileSync(absolutePath, contents);
  }
  return { root, manifestPath, manifest, sourcePath };
}

function verify(fixture, historicalExtras = []) {
  return verifySourceSnapshot({
    root: fixture.root,
    manifestPath: fixture.manifestPath,
    expectedManifestSha256: digest(fixture.manifest),
    historicalExtras,
  });
}

test('accepts exact manifest files with no unlisted files', async () => {
  const fixture = createFixture();
  try {
    assert.deepEqual(await verify(fixture), { ok: true, error_code: 'VERIFIED_1_0' });
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
});

test('accepts only hash-pinned historical extras outside the manifest', async () => {
  const contents = '{"lock":true}\n';
  const extraPath = 'supabase/functions/admin-invite/deno.json';
  const fixture = createFixture({ extraFiles: [[extraPath, contents]] });
  try {
    assert.deepEqual(await verify(fixture, [{ path: extraPath, sha256: digest(contents) }]), {
      ok: true,
      error_code: 'VERIFIED_1_1',
    });
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
});

test('rejects an unknown unlisted file', async () => {
  const fixture = createFixture({ extraFiles: [['unexpected.txt', 'unexpected']] });
  try {
    assert.deepEqual(await verify(fixture), { ok: false, error_code: 'FILE_SET_MISMATCH' });
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
});

test('rejects a changed historical extra', async () => {
  const fixture = createFixture({ extraFiles: [['legacy.json', 'changed']] });
  try {
    assert.deepEqual(await verify(fixture, [{ path: 'legacy.json', sha256: digest('original') }]), {
      ok: false,
      error_code: 'HISTORICAL_EXTRA_HASH_MISMATCH',
    });
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
});

test('rejects symlinks and source content drift', async () => {
  const symlinkFixture = createFixture();
  try {
    symlinkSync('fixture.sql', join(symlinkFixture.root, 'tests', 'link.sql'));
    assert.deepEqual(await verify(symlinkFixture), { ok: false, error_code: 'SYMLINK_PRESENT' });
  } finally {
    rmSync(symlinkFixture.root, { recursive: true, force: true });
  }

  const driftFixture = createFixture();
  try {
    writeFileSync(join(driftFixture.root, driftFixture.sourcePath), 'SELECT 2;\n');
    assert.deepEqual(await verify(driftFixture), { ok: false, error_code: 'SOURCE_HASH_MISMATCH' });
  } finally {
    rmSync(driftFixture.root, { recursive: true, force: true });
  }
});

test('rejects a changed manifest digest', async () => {
  const fixture = createFixture();
  try {
    assert.deepEqual(await verifySourceSnapshot({
      root: fixture.root,
      manifestPath: fixture.manifestPath,
      expectedManifestSha256: '0'.repeat(64),
    }), { ok: false, error_code: 'MANIFEST_HASH_MISMATCH' });
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
});

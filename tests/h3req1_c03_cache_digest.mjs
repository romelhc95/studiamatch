import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createReadStream, lstatSync, readdirSync, readlinkSync } from 'node:fs';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export async function digestDirectory(rootPath, allowedRootPaths = [rootPath]) {
  const root = resolve(rootPath);
  const allowedRoots = allowedRootPaths.map((path) => resolve(path));
  const rootStat = lstatSync(root);
  assert(rootStat.isDirectory() && !rootStat.isSymbolicLink(), 'dependency root must be a real directory');
  const hash = createHash('sha256');
  let entriesSeen = 0;

  async function visit(directory, relative) {
    const names = readdirSync(directory).sort();
    for (const name of names) {
      const absolute = join(directory, name);
      const path = relative ? `${relative}/${name}` : name;
      const stat = lstatSync(absolute);
      const mode = stat.mode & 0o7777;
      entriesSeen += 1;
      if (stat.isSymbolicLink()) {
        const target = readlinkSync(absolute);
        const resolvedTarget = resolve(dirname(absolute), target);
        assert(allowedRoots.some((allowedRoot) => resolvedTarget === allowedRoot
          || resolvedTarget.startsWith(`${allowedRoot}${sep}`)), 'dependency symlink escapes approved dependency roots');
        hash.update(`link\0${path}\0${mode}\0${target}\0`);
      } else if (stat.isDirectory()) {
        hash.update(`dir\0${path}\0${mode}\0`);
        await visit(absolute, path);
      } else if (stat.isFile()) {
        hash.update(`file\0${path}\0${mode}\0${stat.size}\0`);
        const stream = createReadStream(absolute);
        for await (const chunk of stream) hash.update(chunk);
        hash.update('\0');
      } else {
        throw new Error('unsupported filesystem entry in dependency tree');
      }
    }
  }

  await visit(root, '');
  assert(entriesSeen > 0, 'dependency root must not be empty');
  return hash.digest('hex');
}

export async function digestDirectories(directories) {
  const result = {};
  const roots = Object.fromEntries(Object.entries(directories)
    .map(([name, root]) => [name, resolve(root)]));
  const allowedRoots = Object.values(roots);
  for (const name of Object.keys(roots).sort()) {
    result[name] = await digestDirectory(roots[name], allowedRoots);
  }
  return result;
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  const roots = {};
  for (const item of process.argv.slice(2)) {
    const separator = item.indexOf('=');
    assert(separator > 0, 'expected each dependency root as name=path');
    const name = item.slice(0, separator);
    assert(!Object.hasOwn(roots, name), 'duplicate dependency root name');
    roots[name] = item.slice(separator + 1);
  }
  process.stdout.write(`${JSON.stringify(await digestDirectories(roots))}\n`);
}

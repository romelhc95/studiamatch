import { createHash } from 'node:crypto';

export function isolateQuotaCounters(counters, epoch) {
  const isolate = digest => createHash('sha256').update(`${epoch}:${digest}`).digest('hex');
  return counters.map(counter => ({
    ...counter,
    digest: isolate(counter.digest),
    ...(counter.shard ? { shard: isolate(counter.shard) } : {}),
  }));
}

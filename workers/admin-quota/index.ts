// Internal service binding ONLY. No routes/workers.dev and no secrets in storage.
interface Storage {
  transaction<T>(callback: (transaction: {
    get<T>(key: string): Promise<T | undefined>;
    put(key: string, value: unknown): Promise<void>;
    delete(key: string): Promise<boolean>;
  }) => Promise<T>): Promise<T>;
  setAlarm(time: number): Promise<void>;
}
interface State { storage: Storage }
interface Namespace { idFromName(name: string): unknown; get(id: unknown): { fetch(request: Request): Promise<Response> } }
interface Env { ADMIN_QUOTA_COUNTER: Namespace }
interface Counter { kind: string; digest: string; shard?: string }
const RULES: Record<string, { limit: number; milliseconds: number }> = {
  entry: { limit: 300, milliseconds: 60000 },
  'login-ip': { limit: 20, milliseconds: 600000 },
  'login-account-ip': { limit: 10, milliseconds: 600000 },
  callback: { limit: 10, milliseconds: 600000 },
  mfa: { limit: 10, milliseconds: 600000 },
  password: { limit: 10, milliseconds: 600000 },
  'rpc-read': { limit: 120, milliseconds: 60000 },
  'rpc-write': { limit: 30, milliseconds: 60000 },
};
type Ledger = Record<string, number[]>;
function json(status: number, allowed: boolean, retry?: number): Response {
  return new Response(JSON.stringify({ allowed }), { status, headers: {
    'Content-Type': 'application/json', 'Cache-Control': 'no-store',
    ...(retry ? { 'Retry-After': String(retry) } : {}),
  } });
}
export class AdminQuotaCounter {
  constructor(private state: State) {}
  async fetch(request: Request): Promise<Response> {
    if (request.method !== 'POST' || new URL(request.url).pathname !== '/check') return json(404, false);
    try {
      const text = await request.text();
      if (text.length > 4096) return json(400, false);
      const { counters } = JSON.parse(text) as { counters?: Counter[] };
      if (!Array.isArray(counters) || counters.length < 1 || counters.length > 6 || counters.some(
        c => !c || !Object.hasOwn(RULES, c.kind) || !/^[a-f0-9]{64}$/.test(c.digest)
          || (c.shard !== undefined && !/^[a-f0-9]{64}$/.test(c.shard)),
      )) return json(400, false);
      const keys = counters.map(c => `${c.kind}:${c.digest}`);
      if (new Set(keys).size !== keys.length) return json(400, false);
      const now = Date.now();
      // Alarm is set BEFORE admission. A failed alarm cannot admit an untracked request.
      await this.state.storage.setAlarm(now + 600001);
      return await this.state.storage.transaction(async storage => {
        const ledger = await storage.get<Ledger>('ledger') || {};
        for (const key of Object.keys(ledger)) {
          const rule = RULES[key.split(':')[0]];
          ledger[key] = ledger[key].filter(time => time > now - rule.milliseconds);
          if (!ledger[key].length) delete ledger[key];
        }
        let retry = 0;
        const blocked = new Set<string>();
        for (const c of counters) {
          const rule = RULES[c.kind];
          const key = `${c.kind}:${c.digest}`;
          const events = ledger[key] || [];
          if (events.length >= rule.limit) {
            blocked.add(key);
            retry = Math.max(retry, Math.ceil((events[0] + rule.milliseconds - now) / 1000));
          }
        }
        // Login IP and account-IP counters share one shard. Preserve the IP
        // attempt count when only the account quota blocks, but do not create
        // new account ledger entries after the IP quota has already blocked.
        const loginIpIndex = counters.findIndex(c => c.kind === 'login-ip');
        const loginIpBlocked = loginIpIndex >= 0 && blocked.has(keys[loginIpIndex]);
        let changed = false;
        for (let index = 0; index < counters.length; index += 1) {
          const c = counters[index];
          const key = keys[index];
          if (blocked.has(key) || (loginIpBlocked && c.kind === 'login-account-ip')) continue;
          (ledger[key] ||= []).push(now);
          changed = true;
        }
        if (changed) await storage.put('ledger', ledger);
        if (retry) return json(429, false, Math.max(1, retry));
        return json(200, true);
      });
    } catch { return json(503, false, 30); }
  }
  async alarm(): Promise<void> {
    // A stale alarm must never erase admissions made by a concurrent request.
    const now = Date.now();
    const next = await this.state.storage.transaction(async storage => {
      const ledger = await storage.get<Ledger>('ledger') || {};
      let expiry = 0;
      for (const key of Object.keys(ledger)) {
        const rule = RULES[key.split(':')[0]];
        ledger[key] = ledger[key].filter(time => time > now - rule.milliseconds);
        if (!ledger[key].length) delete ledger[key];
        else expiry = Math.max(expiry, ledger[key][ledger[key].length - 1] + rule.milliseconds + 1);
      }
      if (Object.keys(ledger).length === 0) await storage.delete('ledger');
      else await storage.put('ledger', ledger);
      return expiry;
    });
    if (next > now) await this.state.storage.setAlarm(next);
  }
}
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'POST' || new URL(request.url).pathname !== '/check') return json(404,false);
    try {
      const text=await request.text();
      if(text.length>4096) return json(400,false);
      const { counters }=JSON.parse(text) as { counters?: Counter[] };
      if(!Array.isArray(counters) || !counters.length || counters.length>6 || counters.some(
        c=>!c || !Object.hasOwn(RULES,c.kind) || !/^[a-f0-9]{64}$/.test(c.digest)
          || (c.shard !== undefined && !/^[a-f0-9]{64}$/.test(c.shard)),
      ) || new Set(counters.map(c=>`${c.kind}:${c.digest}`)).size!==counters.length) return json(400,false);
      const loginIps=counters.filter(c=>c.kind==='login-ip');
      const accountIps=counters.filter(c=>c.kind==='login-account-ip');
      if(loginIps.length>1 || accountIps.length>1 || (accountIps.length && loginIps.length!==1)) return json(400,false);
      const loginIpShard=loginIps[0]?.digest;
      if(accountIps.some(c=>c.shard!==undefined && c.shard!==loginIpShard)) return json(400,false);
      // Older BFF bytes send both counters without an explicit shard. Infer
      // their shared IP shard to keep the expand/compatibility transition safe.
      const routed=counters.map(c=>c.kind==='login-account-ip'
        ? {...c,shard:c.shard || loginIpShard}
        : c);
      const groups=new Map<string,Counter[]>();
      for(const c of routed) {
        const shard=c.shard || c.digest;
        const group=groups.get(shard) || [];
        group.push(c);
        groups.set(shard,group);
      }
      // Co-locating the paired login counters makes the IP admission and
      // account ledger atomic and bounds account identities by admitted IP tries.
      const results=await Promise.all([...groups.entries()].map(([shard,group])=>
        env.ADMIN_QUOTA_COUNTER.get(env.ADMIN_QUOTA_COUNTER.idFromName(`shard:${shard}`))
          .fetch(new Request('https://admin-quota.internal/check', {
            method:'POST',body:JSON.stringify({counters:group}),
          }))));
      const blocked=results.filter(r=>r.status===429);
      if(results.some(r=>r.status!==200 && r.status!==429)) return json(503,false,30);
      if(blocked.length) return json(429,false,Math.max(...blocked.map(r=>Number(r.headers.get('Retry-After')) || 30)));
      return json(200,true);
    } catch { return json(503,false,30); }
  },
};

// ── LG-026-P3 门禁② 端点黑盒新增面（ST/小柯 2026-09-02）──
// 独立脚本直调 createTriLCApp：F1 伪报矩阵 / F2 priority 显拒 / F3 限流 429 /
// R1 事件帧无 payload / R2 ?as= 补拉 delivered 未读积压。
// 限流面独立小实例（TRILC_LETTER_RATE_LIMIT=3）；主实例缺省限流 60/min。
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const TOKEN = 'st-p3-blackbox-token';
let passCount = 0;
let failCount = 0;
const failures: string[] = [];
function check(name: string, cond: boolean, detail = ''): void {
  if (cond) { passCount++; console.log(`  PASS ${name}`); }
  else { failCount++; failures.push(name + (detail ? ` :: ${detail}` : '')); console.log(`  FAIL ${name}${detail ? ' :: ' + detail : ''}`); }
}

function makeApp(envOverrides: Record<string, string> = {}) {
  const WORK = mkdtempSync(join(tmpdir(), 'lg026p3-bb-'));
  process.env.TRILC_DATA_DIR = WORK;
  process.env.TRILC_PORT = '0';
  process.env.TRILC_PROJECT_ROOT = WORK;
  delete process.env.TRILC_CHANNEL_MODE;
  delete process.env.TRIMODEL_API_TOKEN;
  process.env.TRILC_INTERNAL_TOKEN = TOKEN;
  process.env.TRIMODEL_API_URL = 'http://127.0.0.1:1';
  for (const [k, v] of Object.entries(envOverrides)) process.env[k] = v;
  return (async () => {
    const { readEnv } = await import('file:///D:/Code/ai/TriRLC/src/config/env.ts');
    const { createTriLCApp } = await import('file:///D:/Code/ai/TriRLC/src/server/app.ts');
    const env = readEnv();
    env.port = 0;
    env.trimodelApiUrl = 'http://127.0.0.1:1';
    const app = createTriLCApp(env);
    await app.start();
    return { app, port: env.port as number, WORK };
  })();
}

async function req(port: number, method: string, path: string, body?: unknown): Promise<{ status: number; json: any }> {
  const res = await fetch(`http://127.0.0.1:${port}${path}`, {
    method,
    headers: { 'content-type': 'application/json', 'x-internal-token': TOKEN },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch { json = { raw: text?.slice(0, 150) }; }
  return { status: res.status, json };
}

async function readFirstFrame(port: number, url: string, timeoutMs = 6000, cancelSessionId?: string): Promise<{ event: string; data: any; rawKeys: string[] } | null> {
  const res = await fetch(`http://127.0.0.1:${port}${url}`, { headers: { 'x-internal-token': TOKEN } });
  if (!res.ok || !res.body) return null;
  const reader = (res.body as ReadableStream<Uint8Array>).getReader();
  const decoder = new TextDecoder();
  let buf = '';
  const timer = setTimeout(() => { try { reader.cancel(); } catch { /* ok */ } }, timeoutMs);
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) return null;
      buf += decoder.decode(value, { stream: true });
      const idx = buf.indexOf('\n\n');
      if (idx >= 0) {
        const block = buf.slice(0, idx);
        if (cancelSessionId) await req(port, 'POST', `/internal/v1/sessions/${cancelSessionId}/cancel`, {}).catch(() => { /* */ });
        const evLine = block.split('\n').find((l) => l.startsWith('event:'));
        const dataLine = block.split('\n').find((l) => l.startsWith('data:'));
        let data: any = null;
        try { data = JSON.parse(dataLine!.slice(5).trim()); } catch { data = null; }
        return { event: evLine?.slice(6).trim() ?? '', data, rawKeys: data && typeof data === 'object' ? Object.keys(data) : [] };
      }
    }
  } finally {
    clearTimeout(timer);
    try { reader.cancel(); } catch { /* ok */ }
  }
}

// ══ 主实例：F1/F2/SSE ══
{
  const { app, port, WORK } = await makeApp();
  console.log(`[bb] main app on ${port}`);

  // ── F1 伪报矩阵 ──
  console.log('== F1 from=actor 伪报矩阵 ==');
  const s1 = await req(port, 'POST', '/internal/v1/letters', { actor: 'alice', from: '伪报BOD', to: 'f1a', payload: 1 });
  check('F1a 寄信 201（body.from 被忽略不报错）', s1.status === 201, `实际${s1.status}`);
  const g1 = await req(port, 'GET', '/internal/v1/letters?box=in&to=f1a');
  check('F1a' + "b 信封 from=actor（伪报被覆盖）", g1.json.letters?.[0]?.from === 'alice', `实际${g1.json.letters?.[0]?.from}`);
  const s2 = await req(port, 'POST', '/internal/v1/letters', { from: 'noactor', to: 'f1b', payload: 1 });
  check('F1c 寄信缺 actor → 400 invalid_actor', s2.status === 400 && s2.json.error === 'invalid_actor', `${s2.status} ${s2.json.error}`);

  const base = async (to: string) => (await req(port, 'POST', '/internal/v1/letters', { actor: 'alice', to, payload: 1 })).json.letterId;
  const c1 = await base('f1-esc');
  const e1 = await req(port, 'POST', `/internal/v1/letters/${c1}/state`, { action: 'escalate', actor: '组长', envelope: { to: 'COS', from: '伪报BOD' } });
  check('F1d escalate envelope.from 伪报（≠actor）→ 400', e1.status === 400, `实际${e1.status}`);
  const e2 = await req(port, 'POST', `/internal/v1/letters/${c1}/state`, { action: 'escalate', actor: '组长', envelope: { to: 'COS' } });
  check('F1e escalate envelope.from 缺 → 400', e2.status === 400 && /from is required/.test(e2.json.message ?? ''), `实际${e2.status}`);
  const e3 = await req(port, 'POST', `/internal/v1/letters/${c1}/state`, { action: 'escalate', actor: '组长', envelope: { to: 'COS', from: '组长' } });
  check('F1f escalate envelope.from=actor → 200', e3.status === 200, `实际${e3.status}`);

  // ── F2 priority 显拒 ──
  console.log('== F2 priority 显拒 ==');
  const c2 = await base('f2a');
  const p1 = await req(port, 'POST', `/internal/v1/letters/${c2}/state`, { action: 'escalate', actor: 'COS', envelope: { to: 'COS', from: 'COS', priority: '紧急' } });
  check('F2a envelope.priority 提供非法 → 400 invalid_priority', p1.status === 400 && p1.json.error === 'invalid_priority', `${p1.status} ${p1.json.error}`);
  const c3 = await base('f2b');
  const p2 = await req(port, 'POST', `/internal/v1/letters/${c3}/state`, { action: 'escalate', actor: 'COS', envelope: { to: 'COS', from: 'COS' } });
  check('F2b envelope.priority 未提供 → 200 且新信封=急件', p2.status === 200 && p2.json.envelope?.priority === '急件', `${p2.status} ${p2.json.envelope?.priority}`);

  // ── R1/R2 SSE 事件帧 ──
  console.log('== R1/R2 SSE ==');
  // R2 补拉：给 sse-r2 一封 delivered
  const m1 = await req(port, 'POST', '/internal/v1/letters', { actor: 'system', to: 'sse-r2', payload: { secret: 'SHOULD-NOT-LEAK' } });
  await req(port, 'POST', `/internal/v1/letters/${m1.json.letterId}/state`, { action: 'deliver', actor: '组长' });
  const sub1 = await req(port, 'POST', '/internal/v1/tasks/submit', { message: 'bb-r2' });
  const frame1 = await readFirstFrame(port, `/internal/v1/sessions/${sub1.json.sessionId}/stream?as=sse-r2`, 6000, sub1.json.sessionId);
  check('R2a 连接即补拉：首帧 letter 事件', frame1?.event === 'letter', `实际${frame1?.event}`);
  check('R2b 补拉帧 letterId=delivered 积压信', frame1?.data?.letterId === m1.json.letterId, `实际${frame1?.data?.letterId}`);
  check('R2c 补拉帧不含 payload 键', frame1 ? !frame1.rawKeys.includes('payload') : false, `keys=${JSON.stringify(frame1?.rawKeys)}`);

  // R1 活推：先连流（后台）再寄信
  const sub2 = await req(port, 'POST', '/internal/v1/tasks/submit', { message: 'bb-r1' });
  const framePromise = readFirstFrame(port, `/internal/v1/sessions/${sub2.json.sessionId}/stream?as=sse-r1`, 8000, sub2.json.sessionId);
  await new Promise((r) => setTimeout(r, 800)); // 等注册完成
  const m2 = await req(port, 'POST', '/internal/v1/letters', { actor: 'system', to: 'sse-r1', priority: '急件', payload: { secret: 'LIVE-SHOULD-NOT-LEAK' } });
  const frame2 = await framePromise;
  check('R1a 活推：连接期间新信入件推帧', frame2?.event === 'letter' && frame2?.data?.letterId === m2.json.letterId, `实际${JSON.stringify(frame2?.data)?.slice(0, 120)}`);
  check('R1b 活推帧不含 payload 键（帧字段恰七枚摘要）', frame2 ? JSON.stringify(frame2.rawKeys) === '["event","letterId","seqNo","from","to","priority","status"]' : false, `keys=${JSON.stringify(frame2?.rawKeys)}`);

  try { await app.stop(); } catch { /* */ }
  try { rmSync(WORK, { recursive: true, force: true }); } catch { /* */ }
}

// ══ 限流实例：F3 ══
{
  const { app, port, WORK } = await makeApp({ TRILC_LETTER_RATE_LIMIT: '3' });
  console.log(`[bb] rate-limit app on ${port}`);
  console.log('== F3 限流 ==');
  const codes: number[] = [];
  for (let i = 0; i < 5; i++) {
    const r = await req(port, 'POST', '/internal/v1/letters', { actor: 'burst', to: `rl${i}`, payload: i });
    codes.push(r.status);
  }
  check('F3a 前3封 201 / 第4-5封 429', JSON.stringify(codes) === '[201,201,201,429,429]', `实际${JSON.stringify(codes)}`);
  const r429 = await req(port, 'POST', '/internal/v1/letters', { actor: 'burst', to: 'rlx', payload: 0 });
  check('F3b 429 error=rate_limited', r429.json.error === 'rate_limited', `实际${r429.json.error}`);
  const g = await req(port, 'GET', '/internal/v1/letters');
  check('F3c GET 端点不受限流影响', g.status === 200);
  try { await app.stop(); } catch { /* */ }
  try { rmSync(WORK, { recursive: true, force: true }); } catch { /* */ }
}

console.log(`\n== P3 端点黑盒新增面汇总 == PASS ${passCount} / FAIL ${failCount}`);
if (failures.length) { console.log('失败项:'); failures.forEach((f) => console.log(' - ' + f)); }
process.exit(failCount ? 1 : 0);

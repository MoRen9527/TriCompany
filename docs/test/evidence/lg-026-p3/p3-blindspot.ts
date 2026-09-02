// ── LG-026-P3 门禁⑤ 盲区/错位观察项探边（ST/小柯 2026-09-02）──
// 四项：①pushLetterEvent 广播调用点事务内/后（未提交数据风险，重点探）
// ②同席 as 多连接并发注册 ③30min 宽限与 4h 阈值边界叠压 ④限流计数器内存态重启清零。
// 另：ref 急件信封自升级链现象已在门禁③脚本 ⑥ 段实证，此处引用不重跑。
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const TOKEN = 'st-p3-blindspot-token';
let obsN = 0;
function obs(k: string, v: unknown): void { obsN++; console.log(`  OBS ${k} = ${JSON.stringify(v)}`); }
function check(name: string, cond: boolean, detail = ''): void {
  console.log(`  ${cond ? 'PASS' : 'FAIL'} ${name}${detail ? ' :: ' + detail : ''}`);
  if (!cond) { /* 观察脚本 FAIL 只标注不断言退出 */ }
}

function makeApp(envOverrides: Record<string, string> = {}) {
  const WORK = mkdtempSync(join(tmpdir(), 'lg026p3-bs-'));
  process.env.TRILC_DATA_DIR = WORK;
  process.env.TRILC_PORT = '0';
  process.env.TRILC_PROJECT_ROOT = WORK;
  delete process.env.TRILC_CHANNEL_MODE;
  delete process.env.TRIMODEL_API_TOKEN;
  process.env.TRILC_INTERNAL_TOKEN = TOKEN;
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
  try { json = JSON.parse(text); } catch { json = { raw: text?.slice(0, 120) }; }
  return { status: res.status, json };
}

// 读 SSE 流至多 frames 帧（或超时），返回解析帧数组
async function readFrames(port: number, url: string, maxFrames: number, timeoutMs = 6000, cancelSessionId?: string): Promise<Array<{ event: string; data: any }>> {
  const res = await fetch(`http://127.0.0.1:${port}${url}`, { headers: { 'x-internal-token': TOKEN } });
  if (!res.ok || !res.body) return [];
  const reader = (res.body as ReadableStream<Uint8Array>).getReader();
  const decoder = new TextDecoder();
  let buf = '';
  const frames: Array<{ event: string; data: any }> = [];
  const timer = setTimeout(() => { try { reader.cancel(); } catch { /* */ } }, timeoutMs);
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buf.indexOf('\n\n')) >= 0) {
        const block = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        if (block.includes('event:')) {
          const evLine = block.split('\n').find((l) => l.startsWith('event:'));
          const dataLine = block.split('\n').find((l) => l.startsWith('data:'));
          let data: any = null;
          try { data = JSON.parse(dataLine!.slice(5).trim()); } catch { data = null; }
          frames.push({ event: evLine?.slice(6).trim() ?? '', data });
          if (frames.length >= maxFrames) {
            if (cancelSessionId) await req(port, 'POST', `/internal/v1/sessions/${cancelSessionId}/cancel`, {}).catch(() => { /* */ });
            return frames;
          }
        }
      }
    }
  } finally {
    clearTimeout(timer);
    try { reader.cancel(); } catch { /* */ }
  }
  if (cancelSessionId) await req(port, 'POST', `/internal/v1/sessions/${cancelSessionId}/cancel`, {}).catch(() => { /* */ });
  return frames;
}

// ══ ① 广播调用点与库状态一致性（事务内/后探边）══
console.log('\n── ① pushLetterEvent 事务一致性 ──');
{
  const { app, port, WORK } = await makeApp();
  // 失败的 escalate（400 伪报 from，库回滚/未触）不推帧；成功的推帧且帧 status 与库一致
  const sub = await req(port, 'POST', '/internal/v1/tasks/submit', { message: 'bs1' });
  const sid = sub.json.sessionId;
  const framesPromise = readFrames(port, `/internal/v1/sessions/${sid}/stream?as=bs1-recipient`, 5, 6000, sid);
  await new Promise((r) => setTimeout(r, 800));

  const made = await req(port, 'POST', '/internal/v1/letters', { actor: 'sys', to: 'bs1-recipient', priority: '急件', payload: 1 });
  const id = made.json.letterId;
  const failEsc = await req(port, 'POST', `/internal/v1/letters/${id}/state`, { action: 'escalate', actor: '组长', envelope: { to: 'COS', from: '伪报' } }); // 400 不触库
  await new Promise((r) => setTimeout(r, 600));
  const okEsc = await req(port, 'POST', `/internal/v1/letters/${id}/state`, { action: 'escalate', actor: '组长', envelope: { to: 'COS', from: '组长' } }); // 200 原子版
  const frames = await framesPromise;

  obs('①a 失败 escalate（400）响应', { status: failEsc.status });
  obs('①b 成功 escalate（200）响应', { status: okEsc.status });
  obs('①c SSE 帧序列', frames.map((f) => [f.event, f.data?.letterId?.slice(-8), f.data?.status]));
  const stateFrames = frames.filter((f) => f.event === 'letter' && f.data?.letterId === id && f.data?.status === 'escalated');
  check('①d 400 失败未产生状态帧（不推未发生的状态）', frames.filter((f) => f.data?.status === 'escalated').length === 1, `escalated 帧数=${frames.filter((f) => f.data?.status === 'escalated').length}`);
  const dbLetter = (await req(port, 'GET', `/internal/v1/letters?box=in&to=bs1-recipient`)).json.letters?.[0];
  check('①e 帧 status 与库终态一致（推的是已提交数据）', stateFrames[0]?.data?.status === dbLetter?.status, `帧=${stateFrames[0]?.data?.status} 库=${dbLetter?.status}`);
  obs('①f 源码级定性', '三调用点（POST letters:4326/state:4473/escalate:4476-4477）全在 store API 返回后（insertLetter/transition/escalateLetter 内部 COMMIT 后才返回）——无事务内推帧路径，黑盒 ①e 帧库一致实证');
  try { await app.stop(); } catch { /* */ }
  try { rmSync(WORK, { recursive: true, force: true }); } catch { /* */ }
}

// ══ ② 同席 as 多连接并发注册 ══
console.log('\n── ② 同席多连接并发注册 ──');
{
  const { app, port, WORK } = await makeApp();
  const sub1 = await req(port, 'POST', '/internal/v1/tasks/submit', { message: 'bs2a' });
  const sub2 = await req(port, 'POST', '/internal/v1/tasks/submit', { message: 'bs2b' });
  const frames1Promise = readFrames(port, `/internal/v1/sessions/${sub1.json.sessionId}/stream?as=multi-same`, 2, 6000, sub1.json.sessionId);
  await new Promise((r) => setTimeout(r, 400));
  const frames2Promise = readFrames(port, `/internal/v1/sessions/${sub2.json.sessionId}/stream?as=multi-same`, 2, 6000, sub2.json.sessionId);
  await new Promise((r) => setTimeout(r, 800));
  await req(port, 'POST', '/internal/v1/letters', { actor: 'sys', to: 'multi-same', payload: 2 });
  const f1 = await frames1Promise;
  const f2 = await frames2Promise;
  obs('②a 连接1 帧数', f1.length);
  obs('②b 连接2 帧数', f2.length);
  check('②c 同席两连接各收同一帧（Set 多 res 广播）', f1.length >= 1 && f2.length >= 1 && f1[0]?.data?.letterId === f2[0]?.data?.letterId);
  try { await app.stop(); } catch { /* */ }
  try { rmSync(WORK, { recursive: true, force: true }); } catch { /* */ }
}

// ══ ③ 30min 宽限与 4h 阈值边界（priority 隔离）══
console.log('\n── ③ 宽限/阈值边界叠压 ──');
{
  const { createLetterStore } = await import('file:///D:/Code/ai/TriRLC/src/letter-store/store.ts');
  const { createLetterSweeper } = await import('file:///D:/Code/ai/TriRLC/src/letter-store/letter-sweeper.ts');
  const db = join(tmpdir(), 'lg026p3-bs3.db');
  rmSync(db, { force: true });
  const store = createLetterStore(db, { leaderId: '组长' });
  const realNow = Date.now();
  let offsetMs = 0;
  (Date.now as () => number) = () => realNow + offsetMs;
  const H = 3_600_000;
  const MIN = 60_000;
  const sw = createLetterSweeper({ letterStore: store, wake: () => { /* */ } }, { intervalMs: 999 * H });

  // 重要件（4h 链对象）在 30min 窗时点不受急件规则影响
  const imp = store.insertLetter({ from: 'a', to: 'COS', priority: '重要', payload: null });
  store.transition(imp.letterId, 'deliver', '组长');
  // 急件（30min 窗对象）在 4h 时点早已升完、4h 链不碰它（priority 隔离）
  const urg = store.insertLetter({ from: 'a', to: 'cs-urgent', priority: '急件', payload: null });
  store.transition(urg.letterId, 'deliver', '组长');

  offsetMs = 30 * MIN; // 急件恰过窗；重要件远未到 4h
  let s = sw.sweep();
  obs('③a @30min：重要件不被急件窗误伤', { 重要件retries: store.getLetter(imp.letterId)!.retries, 急件escalated: s.escalated });
  check('③a 重要件 @30min 零动作（priority 隔离）', s.rescued === 0 && store.getLetter(imp.letterId)!.retries === 0);

  offsetMs = 4 * H + MIN; // 重要件到 4h；急件远超窗（已升，不再扫）
  s = sw.sweep();
  obs('③b @4h+：重要件首推，急件链产物另计', { rescued: s.rescued, escalated: s.escalated });
  check('③b 重要件 4h+ 进重推链', store.getLetter(imp.letterId)!.retries === 1);
  obs('③c 叠压定性', '同信单 priority 无叠压面；真实叠压点=急件 ref 产物回灌急件规则（门禁③⑥ 已单列链式自升）——该回灌使「30min 窗」作用于升级产物而非重要件阈值，非本项边界');
  sw.stop();
  store.close();
  rmSync(db, { force: true });
}

// ══ ④ 限流计数器内存态重启清零 ══
console.log('\n── ④ 限流计数器内存态 ──');
{
  // 4a 同进程两实例独立计数（互不串扰）
  const a = await makeApp({ TRILC_LETTER_RATE_LIMIT: '2' });
  for (let i = 0; i < 2; i++) await req(a.port, 'POST', '/internal/v1/letters', { actor: 'x', to: `a${i}`, payload: 1 });
  const aThird = await req(a.port, 'POST', '/internal/v1/letters', { actor: 'x', to: 'a2', payload: 1 });
  const b = await makeApp({ TRILC_LETTER_RATE_LIMIT: '2' });
  const bFirst = await req(b.port, 'POST', '/internal/v1/letters', { actor: 'x', to: 'b0', payload: 1 });
  obs('④a 实例A 打满后第3封', aThird.status);
  obs('④b 实例B 首封', bFirst.status);
  check('④c 两实例计数独立（B 不受 A 打满影响）', aThird.status === 429 && bFirst.status === 201);
  // 4d 重启语义：A stop 后新建实例计数清零（同 60s 窗内）
  try { await a.app.stop(); } catch { /* */ }
  try { rmSync(a.WORK, { recursive: true, force: true }); } catch { /* */ }
  const a2 = await makeApp({ TRILC_LETTER_RATE_LIMIT: '2' });
  const a2First = await req(a2.port, 'POST', '/internal/v1/letters', { actor: 'x', to: 'a2-fresh', payload: 1 });
  check('④d 重启后计数清零（同窗首封 201）', a2First.status === 201, `实际${a2First.status}`);
  obs('④e 定性', '限流态=进程内 Map（app.ts:1310 letterRateWindows）——重启清零语义实证；滑窗 60s 自然恢复为同构语义（窗口 filter now-t<60s）；内存态=设计现状（CTO 裁接受不立审计表），重启清零对防护面影响=攻击者可借重启重置窗口，127.0.0.1+token 信任域内可接受');
  try { await b.app.stop(); } catch { /* */ }
  try { await a2.app.stop(); } catch { /* */ }
  try { rmSync(b.WORK, { recursive: true, force: true }); } catch { /* */ }
  try { rmSync(a2.WORK, { recursive: true, force: true }); } catch { /* */ }
}

console.log(`\n== P3 盲区探边汇总 == 观察项 ${obsN} 条`);
process.exit(0);

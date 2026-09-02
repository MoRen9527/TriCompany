// ── LG-026-P3 复验黑盒（ST/小柯 2026-09-02，CTO 复验令 07:43Z）──
// 对象：FD 整改 ecdd0da（listSweepable 一处收口，sweeper 全规则排除 refLetterId 非空件）。
// 范围：①v2 三 FAIL 表观污染用例转绿（①d/①f/②c）②零膨胀专项（ref 急件 31min+ 不动 /
// 重要件 ref 8h 不动不重推 / ttl ref 超限不升 / 全场景信箱总数封顶断言）。
// 时间注入法 v2：每场景独立库+注入钟归零。
import { createLetterStore } from 'file:///D:/Code/ai/TriRLC/src/letter-store/store.ts';
import { createLetterSweeper } from 'file:///D:/Code/ai/TriRLC/src/letter-store/letter-sweeper.ts';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { rmSync } from 'node:fs';

let passCount = 0;
let failCount = 0;
const failures: string[] = [];
function check(name: string, cond: boolean, detail = ''): void {
  if (cond) { passCount++; console.log(`  PASS ${name}`); }
  else { failCount++; failures.push(name + (detail ? ` :: ${detail}` : '')); console.log(`  FAIL ${name}${detail ? ' :: ' + detail : ''}`); }
}

const realNow = Date.now();
let offsetMs = 0;
(Date.now as () => number) = () => realNow + offsetMs;
const H = 3_600_000;
const MIN = 60_000;
const jump = (ms: number) => { offsetMs += ms; };

let dbSeq = 0;
function freshSetup() {
  const db = join(tmpdir(), `lg026p3-rv-${++dbSeq}.db`);
  rmSync(db, { force: true });
  const store = createLetterStore(db, { leaderId: '组长' });
  const sweeper = createLetterSweeper({ letterStore: store, wake: () => { /* */ } }, { intervalMs: 999 * H });
  offsetMs = 0;
  const send = async (actor: string, to: string, priority: '常规' | '重要' | '急件', ttlSeconds?: number): Promise<string> => {
    const rec = store.insertLetter({ from: actor, to, priority, payload: null, ttlSeconds });
    store.transition(rec.letterId, 'deliver', '组长');
    return rec.letterId;
  };
  return { store, sweeper, send, cleanup: () => { sweeper.stop(); store.close(); rmSync(db, { force: true }); } };
}

// ══ RV-1：v2 三 FAIL 用例转绿 ══
console.log('== RV-1 原三 FAIL 用例转绿 ==');
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const id = await send('alice', 'COS', '重要');
  jump(4 * H + MIN); sweeper.sweep(); // 4h+ rePush
  jump(4 * H + MIN);
  let s = sweeper.sweep();
  check('RV-1a 8h+ 升级 escalated=1（v2 时=2，ref 不再被同 sweep 再升）', s.escalated === 1, `escalated=${s.escalated}`);
  const ref = store.listLetters({}).find((l) => l.refLetterId === id)!;
  check('RV-1b ref 信封保持 pending（v2 时已被再升）', ref?.status === 'pending', `实际${ref?.status}`);
  cleanup();
}
console.log('   == RV-1b 执行席（独立库） ==');
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const id = await send('bob', 'worker-exec', '重要');
  jump(24 * H + MIN); sweeper.sweep();
  jump(24 * H + MIN);
  const s = sweeper.sweep();
  check('RV-1c 执行席 48h+ 升级 escalated=1（v2 时=3）', s.escalated === 1 && store.getLetter(id)!.status === 'escalated', `escalated=${s.escalated}`);
  cleanup();
}

// ══ RV-2 零膨胀专项（CTO 复验令三口径）══
console.log('== RV-2 零膨胀专项 ==');
// RV-2a ref 急件 31min+ 不动
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const orig = await send('alice', 'urgent-target', '急件');
  jump(31 * MIN);
  sweeper.sweep(); // 原信升 → ref1
  const ref1 = store.listLetters({}).find((l) => l.refLetterId === orig)!;
  check('RV-2a-i ref1 生成且 pending', ref1?.status === 'pending');
  const before = store.listLetters({}).length;
  jump(31 * MIN); const s1 = sweeper.sweep();
  jump(31 * MIN); const s2 = sweeper.sweep();
  jump(31 * MIN); const s3 = sweeper.sweep();
  check('RV-2a-ii ref 急件 31min×3 轮零动作', s1.escalated + s2.escalated + s3.escalated === 0 && s1.rescued + s2.rescued + s3.rescued === 0);
  check('RV-2a-iii 信箱总数封顶（1 原+1 ref=2，零膨胀）', store.listLetters({}).length === before && before === 2, `总数=${store.listLetters({}).length}`);
  cleanup();
}
// RV-2b 重要件 ref 8h 不动不重推
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const orig = await send('alice', 'COS', '重要');
  jump(4 * H + MIN); sweeper.sweep(); // 4h+ rePush（retries=1）
  jump(4 * H + MIN); sweeper.sweep(); // 8h+ 升级 → ref1
  const ref1 = store.listLetters({}).find((l) => l.refLetterId === orig)!;
  check('RV-2b-i ref1 生成（重推→升级两轮后）', !!ref1 && store.getLetter(orig)!.status === 'escalated');
  jump(8 * H);
  const s = sweeper.sweep(); // ref 已 8h+——若未排除将重推/再升
  check('RV-2b-ii 重要件 ref 8h 不重推不升级（零动作）', s.rescued === 0 && s.escalated === 0, `rescued=${s.rescued} escalated=${s.escalated}`);
  check('RV-2b-iii ref1 retries=0 且仍 pending', ref1 && store.getLetter(ref1.letterId)!.retries === 0 && store.getLetter(ref1.letterId)!.status === 'pending');
  cleanup();
}
// RV-2c ttl ref 超限不升不重推
{
  const { store, sweeper, cleanup } = freshSetup();
  // ref 件带 ttl：手工构造（升级产物实际不带 ttl，此处验规则排除本身——直接造 ref 件）
  const orig = store.insertLetter({ from: 'a', to: 'ttl-orig', priority: '常规', payload: null });
  store.transition(orig.letterId, 'escalate', '组长'); // 手工冻结
  const ref = store.insertLetter({ from: '组长', to: 'COS', priority: '常规', payload: null, ttlSeconds: 60, refLetterId: orig.letterId });
  jump(61 * 1000 + MIN); // ttl 过期+余量
  let s = sweeper.sweep();
  check('RV-2c-i ttl ref 过期不重推', s.rescued === 0 && store.getLetter(ref.letterId)!.retries === 0, `rescued=${s.rescued} retries=${store.getLetter(ref.letterId)!.retries}`);
  jump(10 * MIN);
  store.recordRetry(ref.letterId, 'simulated'); // 手工置 retries=3 超限态
  store.recordRetry(ref.letterId, 'simulated');
  store.recordRetry(ref.letterId, 'simulated');
  s = sweeper.sweep();
  check('RV-2c-ii ttl ref 超限不升级（零动作）', s.escalated === 0 && s.rescued === 0 && store.getLetter(ref.letterId)!.status === 'pending', `escalated=${s.escalated}`);
  cleanup();
}
// RV-2d 组长 letter_escalate 产物同受保护（端点/工具路径 ref 同排）
{
  const { store, sweeper, send, cleanup } = freshSetup();
  const orig = await send('alice', 'urgent-target', '急件');
  // 组长路径：escalateLetter（与 lead-tools letter_escalate 同 API）
  store.escalateLetter(orig, '组长', { from: '组长', to: 'COS', priority: '急件', payload: { escalatedBy: '组长' } });
  const ref1 = store.listLetters({}).find((l) => l.refLetterId === orig)!;
  jump(31 * MIN); const s1 = sweeper.sweep();
  jump(31 * MIN); const s2 = sweeper.sweep();
  check('RV-2d 组长升级产物 ref 零动作（两轮 31min）', s1.escalated + s2.escalated === 0 && store.getLetter(ref1.letterId)!.status === 'pending');
  cleanup();
}

console.log(`\n== P3 复验黑盒汇总 == PASS ${passCount} / FAIL ${failCount}`);
if (failures.length) { console.log('失败项:'); failures.forEach((f) => console.log(' - ' + f)); }
process.exit(failCount ? 1 : 0);

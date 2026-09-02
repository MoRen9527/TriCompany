// ── LG-026-P1 盲区/错位观察项探边脚本（ST/小柯 2026-09-02）──
// CTO 派工令提示面四项：①"from" 引号列名查询边界 ②payload 非 JSON 容错
// ③ttl 类型边界 ④datetime('now') 时区口径 vs UTC 纪律。
// 性质：观察记录（只探边不改源码）；结论单列进测试报告盲区节。
// 留档说明：本件为 evidence 留档副本（原跑于系统 TEMP，读数见 blindspot-result.log）。
import { createLetterStore } from 'file:///D:/Code/ai/TriRLC/src/letter-store/store.ts';
import { DatabaseSync } from 'node:sqlite';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { rmSync, mkdirSync } from 'node:fs';

const WORK = join(tmpdir(), 'lg026p1-blindspot');
rmSync(WORK, { recursive: true, force: true });
mkdirSync(WORK, { recursive: true });
const dbPath = join(WORK, 'o.db');
const LEADER = '组长甲';

function head(t: string): void {
  console.log(`\n── ${t} ──`);
}
function obs(k: string, v: unknown): void {
  console.log(`  OBS ${k} = ${JSON.stringify(v)}`);
}
function tryRun(label: string, fn: () => unknown): void {
  try {
    const r = fn();
    console.log(`  OBS ${label} → 无抛, 返回 ${JSON.stringify(r)}`);
  } catch (e) {
    console.log(`  OBS ${label} → 抛错: ${(e as Error)?.constructor?.name}: ${(e as Error)?.message?.split('\n')[0]}`);
  }
}

// ══ O1 "from" 引号列名查询边界 ══
head('O1 "from" 引号列名查询边界');
{
  const s = createLetterStore(dbPath, { leaderId: LEADER });
  s.insertLetter({ from: 'alice', to: 'bob', priority: '常规', payload: 1 });
  s.insertLetter({ from: "O'Brien", to: 'bob', priority: '常规', payload: 2 });
  s.insertLetter({ from: `x'); DROP TABLE letters;--`, to: 'bob', priority: '常规', payload: 3 });
  s.insertLetter({ from: '同值', to: '同值', priority: '常规', payload: 4 });

  obs('O1a listLetters({from:"O\\u0027Brien"}) 命中数', s.listLetters({ from: "O'Brien" }).length);
  obs('O1b 注入形态值精确过滤命中数', s.listLetters({ from: `x'); DROP TABLE letters;--` }).length);
  obs('O1c 注入后表仍存活（全量数=4）', s.listLetters().length);
  const same = s.listLetters({ from: '同值', to: '同值' });
  obs('O1d from=to 同值双过滤命中数', same.length);
  obs('O1e 同值信 row.from/row.to 映射', same[0] ? [same[0].from, same[0].to] : null);

  s.close();
  const raw = new DatabaseSync(dbPath).prepare('SELECT "from", "to" FROM letters LIMIT 1').all() as Record<string, unknown>[];
  obs('O1f 裸SQL引号列返回键名', Object.keys(raw[0] ?? {}));
}

// ══ O2 payload 非 JSON 容错 ══
head('O2 payload 非 JSON 容错');
{
  const s = createLetterStore(join(WORK, 'o2.db'), { leaderId: LEADER });
  // 正常 roundtrip 矩阵
  const cases: Array<[string, unknown]> = [
    ['num0', 0], ['emptyStr', ''], ['false', false], ['null', null],
    ['plainStr', 'hello'], ['arr', [1, { b: 2 }]], ['nested', { a: { b: [true] } }],
    ['big53+1', 9007199254740993], ['undef显式', undefined],
  ];
  for (const [tag, v] of cases) {
    try {
      const rec = s.insertLetter({ from: 'f', to: `t-${tag}`, priority: '常规', payload: v });
      const got = s.getLetter(rec.letterId)!.payload;
      const same = JSON.stringify(got) === JSON.stringify(v === undefined ? null : v);
      obs(`O2-rt ${tag} roundtrip`, { in: v === undefined ? 'undefined' : v, out: got, 往返一致: same });
    } catch (e) {
      obs(`O2-rt ${tag}`, `寄信即抛: ${(e as Error).message?.split('\n')[0]}`);
    }
  }

  // 坏数据注入：手工把 payload 改成非 JSON 字符串（模拟外部写坏/历史迁移数据）
  const victim = s.listLetters({ to: 't-num0' })[0]!.letterId;
  s.close();
  const raw = new DatabaseSync(join(WORK, 'o2.db'));
  raw.prepare('UPDATE letters SET payload = ? WHERE letter_id = ?').run('{not-json', victim);
  raw.close();

  const s2 = createLetterStore(join(WORK, 'o2.db'), { leaderId: LEADER });
  tryRun('O2-bad getLetter(坏payload单读)', () => s2.getLetter(victim));
  tryRun('O2-bad listLetters 全表读（一坏是否毒化全列表）', () => s2.listLetters().length);
  tryRun('O2-bad listLetters({to:其他}) 过滤读（不命中坏信是否幸免）', () => s2.listLetters({ to: 't-plainStr' }).length);
  s2.close();
}

// ══ O3 ttl 类型边界 ══
head('O3 ttl 类型边界（store 层无校验 + DDL 无 CHECK）');
{
  const s = createLetterStore(join(WORK, 'o3.db'), { leaderId: LEADER });
  const ttlCases: Array<[string, unknown]> = [
    ['缺省', undefined], ['null', null], ['0', 0], ['正数', 3600],
    ['负数-5', -5], ['浮点1.5', 1.5], ['超大2^53', 9007199254740993],
    ['字符串"abc"', 'abc' as never], ['布尔true', true as never],
  ];
  for (const [tag, v] of ttlCases) {
    try {
      const rec = s.insertLetter({ from: 'f', to: `ttl-${tag}`, priority: '常规', payload: null, ttlSeconds: v as never });
      const got = s.getLetter(rec.letterId)!.ttlSeconds;
      obs(`O3 ${tag}`, { in: v === undefined ? 'undefined' : v, out: got, typeof: typeof got });
    } catch (e) {
      obs(`O3 ${tag}`, `抛: ${(e as Error).message?.split('\n')[0]}`);
    }
  }
  s.close();
}

// ══ O4 datetime('now') 时区口径 vs UTC 纪律 ══
head("O4 datetime('now') 时区口径 vs UTC 纪律（UTC Z 后缀 +8）");
{
  const s = createLetterStore(join(WORK, 'o4.db'), { leaderId: LEADER });
  const before = new Date();
  const rec = s.insertLetter({ from: 'f', to: 'tz', priority: '常规', payload: null });
  s.transition(rec.letterId, 'deliver', LEADER);

  obs('O4a createdAt 原文格式', rec.createdAt);
  obs('O4b 当前UTC ISO 对照', before.toISOString());
  obs('O4c 值域差(min, 负=库时刻晚于对照)', (Date.parse(before.toISOString()) - interpret(rec.createdAt)) / 60000);
  const jsRead = new Date(rec.createdAt);
  obs('O4d JS new Date(createdAt) 解析读数', { iso: jsRead.toISOString(), 按UTC解读偏差小时: (jsRead.getTime() - interpret(rec.createdAt)) / 3600000 });

  const led = s.listLedger({ letterId: rec.letterId });
  obs('O4e ledger.at 原文格式', led.map((e) => e.at));

  obs('O4f letterId 日期前缀（genLetterId 用 getUTC*）', rec.letterId.slice(0, 10));
  obs('O4g createdAt 日期段（datetime UTC 口径）', rec.createdAt.slice(0, 10));
  obs('O4h 两 UTC 源日期一致性', rec.letterId.slice(3, 11) === rec.createdAt.slice(0, 10).replaceAll('-', ''));

  const raw = new DatabaseSync(join(WORK, 'o4.db')).prepare("SELECT datetime('now') AS t").get() as { t: string };
  obs('O4i datetime(now) 与 JS UTC 时钟差(ms)', Date.now() - interpret(raw.t) - 0);
  s.close();
}

// 辅助：把 SQLite datetime 文本按 UTC 解读（'YYYY-MM-DD HH:MM:SS' → ms）
function interpret(sq: string): number {
  return Date.parse(sq.replace(' ', 'T') + 'Z');
}

console.log('\n== 盲区探边完毕（观察记录，无 PASS/FAIL 判定）==');

// ── LG-025 M0e 两裁验收 门禁① 白名单语义黑盒（ST/小柯 2026-09-03，CTO 轻验收令）──
// ①白名单命中豁免 legacy-line-missing / 非白名单仍报 / 零文件回写 / 绕行试探
// （「新桩洗白」区分度：豁免是否只由旧代行含白名单词触发）。
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

let pass = 0, fail = 0;
const bad: string[] = [];
function check(n: string, c: boolean, d = ''): void {
  if (c) { pass++; console.log(`  PASS ${n}`); } else { fail++; bad.push(n); console.log(`  FAIL ${n}${d ? ' :: ' + d : ''}`); }
}

const TRI = 'D:/Code/ai/TriCompany';
const PY = process.env.PY ?? 'python';

function runValidate(root: string, eid: string): { code: number; out: string } {
  const r = spawnSync(PY, ['-X', 'utf8', '-m', 'runtime.cognition.employee_source_kit', 'validate', '--source-root', root, '--employee-id', eid], { cwd: TRI, encoding: 'utf-8' });
  return { code: r.status ?? 1, out: (r.stdout ?? '') + (r.stderr ?? '') };
}
function missingLines(out: string): string[] {
  return out.split('\n').filter((l) => l.includes('legacy-line-missing'));
}

// fixture：新代三件过门体 + 旧代 memory 件定制
function makeFixture(root: string): string {
  const comp = join(root, 'source-agents', 'calib-probe');
  const legacy = join(root, '.github', 'source-agents', 'calib-probe');
  mkdirSync(comp, { recursive: true });
  mkdirSync(legacy, { recursive: true });
  writeFileSync(join(comp, 'agent.agent.md'), '---\nname: CalibProbe\ndescription: probe\n---\n## 认知分层约束\nemployee knowledge workspace\nruntime cognition state\n', 'utf-8');
  const gate = (title: string, body: string) => `${title}\n\n${body}\n\n## 运行资产落点\n\n认知层资产落点说明：TRICOMPANY_COGNITION_HOME 由当前 runtime cognition backend 承载与巡检。\n\n## 层契约\n\n契约层过门基准行甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥。\n`;
  for (const suf of ['memory', 'colleagues', 'social']) {
    writeFileSync(join(comp, `${suf}.agent.md`), `<!-- 源侧认知层契约：两裁验收 fixture -->\n\n` + gate('## 当前原则', '当前原则过门基准行甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥。'), 'utf-8');
  }
  writeFileSync(join(comp, 'soul.agent.md'), '角色气质\n对话风格\n禁止退化\n', 'utf-8');
  return legacy;
}

// ── 场景 1：白名单命中豁免 ──
console.log('== ①a 白名单命中豁免 ==');
{
  const root = mkdtempSync(join(tmpdir(), 'm0e-wl-'));
  const legacy = makeFixture(root);
  writeFileSync(join(legacy, 'calib-probe.memory.md'), '## 当前原则\n\nCEO 磨人 是本阶段常态，以信件门禁为准。\n', 'utf-8');
  // 新代 graft 替换形态行（合法替换后的旧代行）
  const compA = join(root, 'source-agents', 'calib-probe');
  writeFileSync(join(compA, 'memory.agent.md'), `<!-- 源侧认知层契约：两裁验收 fixture -->\n\n## 当前原则\n\nCEO 本人 是本阶段常态，以信件门禁为准。\n\n## 运行资产落点\n\n认知层资产落点说明：TRICOMPANY_COGNITION_HOME 由当前 runtime cognition backend 承载与巡检。\n\n## 层契约\n\n契约层过门基准行甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥。\n`, 'utf-8');
  const before = readFileSync(join(legacy, 'calib-probe.memory.md'), 'utf-8');
  const r = runValidate(root, 'calib-probe');
  const miss = missingLines(r.out);
  check('①a-1 旧代行含 CEO 磨人+新代有 CEO 本人替换形态 → 豁免（无 legacy-line-missing）', miss.length === 0, `miss=${JSON.stringify(miss)}`);
  const after = readFileSync(join(legacy, 'calib-probe.memory.md'), 'utf-8');
  check('①a-2 零文件回写（旧代文件前后逐字节同）', before === after);
}

// ── 场景 2：非白名单真缺失仍报 ──
console.log('== ①b 非白名单仍报 ==');
{
  const root = mkdtempSync(join(tmpdir(), 'm0e-wl-'));
  const legacy = makeFixture(root);
  const uniq = '非白名单的旧代独有保真行需要被报出。';
  writeFileSync(join(legacy, 'calib-probe.memory.md'), `## 当前原则\n\n${uniq}\n`, 'utf-8');
  const r = runValidate(root, 'calib-probe');
  const miss = missingLines(r.out);
  check('①b-1 非白名单缺失行照报 legacy-line-missing', miss.length === 1 && miss[0].includes(uniq.slice(0, 20)), `miss=${JSON.stringify(miss)}`);
}

// ── 场景 3：绕行试探——「新桩洗白」区分度 ──
console.log('== ①c 绕行试探（新桩洗白区分度）==');
{
  // 3-i：旧代行含白名单词但其余文字全新，新代只有孤立的「CEO 本人」短语（不同上下文）
  const root = mkdtempSync(join(tmpdir(), 'm0e-wl-'));
  const legacy = makeFixture(root);
  writeFileSync(join(legacy, 'calib-probe.memory.md'), '## 当前原则\n\n全新桩句味道的一行 CEO 磨人 另半截上下文。\n', 'utf-8');
  // 新代只含「CEO 本人」于完全不同句子（无该行形态）
  const comp = join(root, 'source-agents', 'calib-probe');
  writeFileSync(join(comp, 'memory.agent.md'), `<!-- 源侧认知层契约：两裁验收 fixture -->\n\n## 当前原则\n\n对 CEO 本人 的日常协作以信件门禁为准绳。\n\n## 运行资产落点\n\n认知层资产落点说明：TRICOMPANY_COGNITION_HOME 由当前 runtime cognition backend 承载与巡检。\n\n## 层契约\n\n契约层过门基准行甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥。\n`, 'utf-8');
  const r = runValidate(root, 'calib-probe');
  const miss = missingLines(r.out);
  check('①c-i 替换形态非整行命中 → 照报（白名单非子串洗白）', miss.length >= 1, `miss=${JSON.stringify(miss)}`);

  // 3-ii：旧代行不含白名单词（新代行恰含 CEO 本人）→ 豁免不触发（豁免只由旧代侧词触发）
  const root2 = mkdtempSync(join(tmpdir(), 'm0e-wl-'));
  const legacy2 = makeFixture(root2);
  writeFileSync(join(legacy2, 'calib-probe.memory.md'), '## 当前原则\n\n旧代行不含任何登记词的一句独有内容。\n', 'utf-8');
  const r2 = runValidate(root2, 'calib-probe');
  const miss2 = missingLines(r2.out);
  check('①c-ii 旧代行无白名单词 → 即便新代有 CEO 本人形态也不豁免（触发面=旧代侧）', miss2.length >= 1 && miss2[0].includes('旧代行不含任何登记词'), `miss=${JSON.stringify(miss2)}`);
}

console.log(`\n== 门禁① 白名单语义黑盒汇总 == PASS ${pass} / FAIL ${fail}`);
if (bad.length) { console.log('失败项:'); bad.forEach((b) => console.log(' - ' + b)); }
process.exit(fail ? 1 : 0);

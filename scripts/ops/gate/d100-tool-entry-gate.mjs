#!/usr/bin/env node
// D-100 工具入口纪律机械闸 · Bash 内嵌 Windows PowerShell 5.1 拦截 v1（命令面）
// 令源：CEO 2026-11-28 00:35 令「纪律逃逸→机械拦截联动」（D-102·CAO 通知一·BOD 流转）
// 拦截对象：Bash 工具命令里调用 powershell / powershell.exe / powershell_ise（Windows PowerShell 5.1 入口）
//   根因族：Bash 链→powershell.exe 5.1 的 PSModulePath 被 PS7 目录前置污染→模块自动加载静默失败
//   （2026-11-28 实锚：Import-PowerShellDataFile MISSING→restart 件期望档静默落基线）
//   正解=原生 PowerShell 工具（pwsh7→powershell.exe 子进程·实测干净）或显式 pwsh；pwsh 不在拦面
// 唯一豁免（正确性条件·非口令·无命令内标记）：同一条命令在调用之前显式给 PSModulePath 赋了「干净」值——
//   每一项都存在 · 含系统模块目录（<SystemRoot>\System32\WindowsPowerShell\v1.0\Modules）· 不含任何 PS7 目录
//   （实测 2026-11-28：纯净三目录/仅系统目录=通；含 PS7 目录=MISSING；
//    仅不存在目录=命令碰巧能跑·仅无关目录=cmdlet 全缺——两种都不豁免，规则不依赖巧合）
// 模式：DEFAULT_MODE 常量（observe=只记不拦·exit 1 留痕 / enforce=拦·exit 2）；切换走受审提交——会话中途改不了
// 留痕：.fade/gate-d100.log（JSON 行·命令只记 sha256 前 12 位+调用形·不落命令原文·D-46 零值面）
// 用法：cat 命令 | node d100-tool-entry-gate.mjs [--mode observe|enforce] [--cwd <dir>] [--log-dir <dir>] [--no-log]
//       node d100-tool-entry-gate.mjs --selftest
// 退出码：0=PASS（含豁免放行）  1=WARN（observe 模式下本应拦的调用·放行留痕）  2=BLOCK
// 失效姿态：闸自身异常=fail-open+stderr 留痕（纪律闸非权限闸·故障不停摆全席工具面）
// —— CTO 小狄 2026-11-28

import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const DEFAULT_MODE = 'observe';

// 词形：powershell / powershell.exe / powershell_ise（前后不接字字母数字._-；全路径、$PSHOME\ 形均命中；pwsh 不命中）
const PS51_RE = /(?<![\w.\-])powershell(?:_ise)?(?:\.exe)?(?![\w.\-])/gi;
// 命令首词在此集=该词只是参数/模式串，不是调用（echo/grep/sed/git … 的参数里出现 powershell 字样）
// v1.1（CAO 重测 B）：去掉 '[' 与 'test'——Python 列表形 subprocess.run(['powershell.exe', …]) 的 '[' 曾被当成测试命令而漏判
const NON_INVOKE_CMDS = new Set([
  'echo', 'printf', 'grep', 'rg', 'sed', 'awk', 'cat', 'ls', 'find', 'findstr', 'select-string', 'sls',
  'git', 'export', 'set', 'alias', 'type', 'head', 'tail', 'wc', 'sort', 'uniq', 'tr', 'cut', 'diff',
  'which', 'where', 'man', 'less', 'more', 'true', 'cd', 'pushd', 'popd', 'read', 'local',
  'cp', 'mv', 'ln', 'chmod', 'touch', 'mkdir', 'stat', 'file', 'md5sum', 'sha256sum', 'basename', 'dirname',
]);
const WRAPPER_1 = new Set(['sudo', 'exec', 'nohup', 'command', 'time', 'winpty']);
const PS7_PATTERNS = [/\\powershell\\7\\/i, /\\program files\\powershell\\modules/i, /\\documents\\powershell\\/i];
const ASSIGN_RE = /(?:^|(?<=[\n;|&({]))[ \t]*(?<exp>export[ \t]+)?PSModulePath[ \t]*=(?:"(?<dq>[^"\n]*)"|'(?<sq>[^'\n]*)'|(?<plain>[^\s;|&]+))/gi;

function systemModulesDir() {
  const root = process.env.SystemRoot || process.env.SYSTEMROOT || 'C:\\WINDOWS';
  return join(root, 'System32', 'WindowsPowerShell', 'v1.0', 'Modules').replace(/\//g, '\\').replace(/\\+$/, '').toLowerCase();
}

function normalize(cmd) {
  return cmd.replace(/["'`]/g, ''); // 去引号/反引号：拆引号变形（pow"ershell）无处遁形
}

function lineIsComment(norm, idx) {
  const ls = norm.lastIndexOf('\n', idx - 1) + 1;
  return norm.slice(ls, idx).trim().startsWith('#');
}

// idx 所在「简单命令」的起点（其前最近的命令分隔符之后）
function simpleStart(norm, idx) {
  let start = 0;
  for (let i = idx - 1; i >= 0; i--) {
    const c = norm[i];
    if (c === ';' || c === '|' || c === '\n' || c === '(' || c === ')' || c === '{' || c === '}') { start = i + 1; break; }
    if (c === '&' && norm[i - 1] === '&') { start = i + 1; break; }
  }
  return start;
}

// idx 所在「简单命令」的有效命令首词（跳过 NAME=value 前缀赋值与包装词）；全被跳过=null（即 idx 处就是命令首词）
function commandWordAt(norm, idx) {
  const start = simpleStart(norm, idx);
  const toks = norm.slice(start, idx).trim().split(/\s+/).filter(Boolean);
  let i = 0;
  while (i < toks.length) {
    const t = toks[i].toLowerCase();
    if (/^[a-z_][a-z0-9_]*=/.test(t)) { i++; continue; }
    if (t === 'env' || WRAPPER_1.has(t)) { i++; continue; }
    if (t === 'timeout') { i += 2; continue; }
    if (t === 'xargs') { i++; while (i < toks.length && toks[i].startsWith('-')) i++; continue; }
    if ((t === 'cmd' || t === 'cmd.exe') && (toks[i + 1] === '/c' || toks[i + 1] === '/k')) { i += 2; continue; }
    return t;
  }
  return null;
}

function findInvocations(cmd) {
  const norm = normalize(cmd);
  const out = [];
  for (const m of norm.matchAll(PS51_RE)) {
    const idx = m.index;
    if (lineIsComment(norm, idx)) continue;
    const cw = commandWordAt(norm, idx);
    if (cw !== null && NON_INVOKE_CMDS.has(cw)) {
      // v1.1（CAO 重测 B）：find 只在 -exec/-execdir/-ok/-okdir 之后才算调用（find … -exec powershell.exe … 曾漏判）
      if (cw !== 'find' || !/-(exec|execdir|ok|okdir)\b/.test(norm.slice(simpleStart(norm, idx), idx))) continue;
    }
    const rest = norm.slice(idx + m[0].length, idx + m[0].length + 80);
    const flag = /^\s*-([a-z]+)/i.exec(rest);
    let form = 'bare';
    if (flag) {
      const f = flag[1].toLowerCase();
      form = (f === 'file' || f === 'f') ? 'file' : (f === 'command' || f === 'c') ? 'command' : f;
    }
    out.push({ idx, form, viaCommandWord: cw });
  }
  return out;
}

function normPath(p) {
  return p.replace(/\//g, '\\').replace(/\\+$/, '').toLowerCase();
}

function isCleanValue(v) {
  const entries = v.split(';').map((s) => s.trim()).filter(Boolean);
  if (!entries.length) return false;
  const sys = systemModulesDir();
  let hasSystem = false;
  for (const e of entries) {
    const n = normPath(e);
    if (PS7_PATTERNS.some((re) => re.test(n))) return false;
    try { if (!existsSync(e)) return false; } catch { return false; }
    if (n === sys || n.startsWith(sys + '\\')) hasSystem = true;
  }
  return hasSystem;
}

// 返回 [{idx,end,clean,global}]：赋值出现位置与覆盖范围（export/独立语句=覆盖其后全部；前缀形=只覆盖紧随的那条简单命令）
function findAssignments(cmd) {
  const out = [];
  for (const m of cmd.matchAll(ASSIGN_RE)) {
    // 值取命名组（命名组也占编号——按编号取会把 export 文本当值·自测「export 形」案抓出的实锚）
    const value = m.groups.dq ?? m.groups.sq ?? m.groups.plain ?? '';
    const end = m.index + m[0].length;
    const after = cmd.slice(end).replace(/^[ \t]+/, '');
    const global = !!m.groups.exp || after === '' || /^[;|&\n]/.test(after);
    out.push({ idx: m.index, end, clean: isCleanValue(value), global });
  }
  return out;
}

function covers(inv, asg, cmd) {
  if (asg.idx > inv.idx) return false;
  if (asg.global) return true;
  return !/[;|&\n]/.test(cmd.slice(asg.end, inv.idx)); // 前缀形：赋值与调用之间不得有命令分隔符
}

export function gate(cmd) {
  const invs = findInvocations(cmd);
  if (!invs.length) return { decision: 'PASS', reason: 'no-ps51-invocation', invs: 0, exempt: 0 };
  const asgs = findAssignments(cmd);
  let exempt = 0;
  const blocking = [];
  for (const inv of invs) {
    if (asgs.some((a) => a.clean && covers(inv, a, cmd))) exempt++;
    else blocking.push(inv.form);
  }
  if (!blocking.length) return { decision: 'PASS', reason: 'clean-path-exempt', invs: invs.length, exempt };
  return { decision: 'BLOCK', reason: 'ps51-from-bash', invs: invs.length, exempt, forms: blocking };
}

export function exitCodeFor(r, mode) {
  if (r.decision === 'PASS') return 0;
  return mode === 'enforce' ? 2 : 1;
}

export function blockMessage(r) {
  return [
    `D-100 闸拦截（退回改写）——Bash 命令里调用了 Windows PowerShell 5.1（${[...new Set(r.forms)].join('/')}）`,
    '根因：Bash 链→powershell.exe 的 PSModulePath 被 PS7 目录前置污染，模块自动加载会静默失败（Import-PowerShellDataFile MISSING→回落基线实锚 2026-11-28）。',
    '正解：改用原生 PowerShell 工具（pwsh7）或把命令写成 pwsh；确需 5.1 时在同一条命令里显式给干净的 PSModulePath',
    '（每一项都存在·含 <SystemRoot>\\System32\\WindowsPowerShell\\v1.0\\Modules·不含 PS7 目录）——这是正确性条件，不是口令。',
  ].join('\n');
}

function seatFromCwd(cwd) {
  try {
    const c = String(cwd || '').replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase();
    const WT = 'd:/code/ai/trimetaverse-worktrees/';
    const MAIN = 'd:/code/ai/trimetaverse';
    if (c.startsWith(WT)) return c.slice(WT.length).split('/')[0] || 'worktree';
    if (c === MAIN || c.startsWith(MAIN + '/')) return 'bod';
    return 'other';
  } catch { return 'unknown'; }
}

// 席位标识（v1.4）：启动器注入的 TRI_SEAT_NAME（进程 env·hook 继承）优先；缺=按 cwd 推导（主树一律记 bod）
export function seatLabel(cwd) {
  const e = (process.env.TRI_SEAT_NAME || '').trim();
  if (e) return { seat: e, src: 'env' };
  return { seat: seatFromCwd(cwd), src: 'cwd' };
}

function appendLog(dir, line) {
  try {
    mkdirSync(dir, { recursive: true });
    appendFileSync(join(dir, 'gate-d100.log'), JSON.stringify(line) + '\n', 'utf8');
  } catch { /* 留痕失败不挡工具面 */ }
}

function selftest() {
  const SYS = systemModulesDir();
  const PS7 = 'C:\\Program Files\\PowerShell\\7\\Modules';
  const cases = [
    ['powershell -File（文档旧用法形）', 'powershell -File restart-seat-tier.ps1 -Seat m-cao', 'BLOCK'],
    ['powershell.exe -Command', 'powershell.exe -NoProfile -Command "Get-Date"', 'BLOCK'],
    ['全路径 v1.0\\powershell.exe', '/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -File x.ps1', 'BLOCK'],
    ['拆引号变形 pow"ershell', 'pow"ershell -File x.ps1', 'BLOCK'],
    ['cmd /c 转调', 'cmd /c powershell -File x.ps1', 'BLOCK'],
    ['管道进 powershell', 'cat x | powershell -NoProfile -Command -', 'BLOCK'],
    ['powershell_ise', 'echo done && powershell_ise foo.ps1', 'BLOCK'],
    ['pwsh（正解·不拦）', 'pwsh -NoProfile -File x.ps1', 'PASS'],
    ['echo 文本提及（非调用）', 'echo "use powershell for this"', 'PASS'],
    ['grep 参数提及', 'grep -n powershell file.txt', 'PASS'],
    ['sed 模式串提及', "sed 's/powershell/pwsh/g' f", 'PASS'],
    ['git --grep 提及', 'git log --grep powershell --oneline', 'PASS'],
    ['注释行', '# powershell -File x.ps1', 'PASS'],
    ['干净前缀+系统目录=豁免', `PSModulePath='${SYS}' powershell.exe -NoProfile -Command "gcm Foo"`, 'PASS'],
    ['含 PS7 目录=不豁免', `PSModulePath='${PS7};${SYS}' powershell -File x.ps1`, 'BLOCK'],
    ['仅不存在目录=不豁免（CAO 用例）', "PSModulePath='C:\\nope\\WindowsPowerShell\\v1.0\\Modules' powershell -NoProfile -Command \"gcm Foo\"", 'BLOCK'],
    ['仅无关目录=不豁免', "PSModulePath='C:\\Users\\jedih\\AppData\\Local\\Temp' powershell -Command \"gci\"", 'BLOCK'],
    ['赋值在调用之后=不豁免', `powershell -File x.ps1; PSModulePath='${SYS}' echo done`, 'BLOCK'],
    ['前缀形只覆盖首条（第二条不豁免）', `PSModulePath='${SYS}' powershell -File a.ps1 && powershell -File b.ps1`, 'BLOCK'],
    ['export 形覆盖其后', `export PSModulePath='${SYS}'; powershell -File x.ps1`, 'PASS'],
    ['独立语句形覆盖其后', `PSModulePath='${SYS}'\npowershell -File x.ps1`, 'PASS'],
    ['干净赋值但调用的是 pwsh', `PSModulePath='${SYS}' pwsh -File x.ps1`, 'PASS'],
    ['v1.1·Python 列表形 subprocess.run([powershell.exe,…])', `python -c "import subprocess; subprocess.run(['powershell.exe','-File','x.ps1'])"`, 'BLOCK'],
    ['v1.1·find … -exec powershell.exe', 'find . -name foo -exec powershell.exe -File y.ps1 {} ;', 'BLOCK'],
    ['v1.1·find 只搜文件名 powershell.exe（非调用）', 'find /c/Windows -name powershell.exe', 'PASS'],
    ['v1.1·[ -d x ] && powershell（测试式后仍是调用）', '[ -d /x ] && powershell -File y.ps1', 'BLOCK'],
    ['v1.1·node execSync 内串 powershell', `node -e "require('child_process').execSync('powershell -File x.ps1')"`, 'BLOCK'],
    ['v1.1·bash -c 内串 powershell', "bash -c 'powershell -File x.ps1'", 'BLOCK'],
  ];
  let fail = 0;
  for (const [name, cmd, want] of cases) {
    const r = gate(cmd);
    const got = r.decision;
    const ok = got === want;
    if (!ok) fail++;
    console.log(`${ok ? 'ok ' : 'FAIL'} [${name}] want=${want} got=${got}${r.decision === 'PASS' ? '(' + r.reason + ')' : ''}`);
  }
  const ec = [gate('powershell -File x'), gate('pwsh -File x')];
  const codes = [exitCodeFor(ec[0], 'enforce'), exitCodeFor(ec[0], 'observe'), exitCodeFor(ec[1], 'enforce')];
  const codesOk = codes.join(',') === '2,1,0';
  if (!codesOk) fail++;
  console.log(`${codesOk ? 'ok ' : 'FAIL'} [退出码映射 enforce/observe/pass] want=2,1,0 got=${codes.join(',')}`);
  console.log(fail ? `\nSELFTEST FAIL (${fail})` : '\nSELFTEST ALL PASS');
  process.exit(fail ? 2 : 0);
}

// ---------- 入口（仅作为主模块时执行；被 import 时只导出判定函数供单测） ----------

const isMain = (() => {
  try { return !!process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href; } catch { return false; }
})();

if (isMain) {
const args = process.argv.slice(2);
if (args.includes('--selftest')) selftest();

let cmd = '';
try { cmd = readFileSync(0, 'utf8'); } catch { cmd = ''; }
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
const mode = opt('--mode') || DEFAULT_MODE;
const cwd = opt('--cwd') || process.env.CLAUDE_PROJECT_DIR || process.cwd();
const sid = opt('--session') || ''; // 会话标识（wrapper 透传 envelope.session_id·v1.4）
const sl = seatLabel(cwd);
const logDir = opt('--log-dir') || process.env.TRI_GATE_LOG_DIR || (existsSync(join(cwd, '.fade')) ? join(cwd, '.fade') : 'D:\\Code\\ai\\TriMetaverse\\.fade');

let r;
try { r = gate(cmd); } catch (e) {
  console.error(`[d100-gate] 闸自身异常——放行+留痕·请报 CTO：${e && e.message}`);
  process.exit(1);
}

if (!args.includes('--no-log') && r.invs > 0) {
  appendLog(logDir, {
    ts: new Date().toISOString(), gate: 'd100', mode, decision: r.decision, reason: r.reason,
    seat: sl.seat, seat_src: sl.src, session_sha8: sid ? createHash('sha256').update(sid).digest('hex').slice(0, 8) : null, cmd_sha12: createHash('sha256').update(cmd).digest('hex').slice(0, 12),
    n_invocations: r.invs, n_exempt: r.exempt, forms: r.forms || [],
  });
}

if (r.decision === 'BLOCK') {
  if (mode === 'enforce') { console.error(blockMessage(r)); process.exit(2); }
  console.error(`[d100-gate WARN·observe 模式放行留痕] 本应拦截：Bash 内嵌 Windows PowerShell 5.1（${[...new Set(r.forms)].join('/')}）——切换 enforce 前只记不拦。`);
  process.exit(1);
}
process.exit(0);
}

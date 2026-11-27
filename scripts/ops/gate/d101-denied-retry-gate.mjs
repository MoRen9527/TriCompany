#!/usr/bin/env node
// D-101 权限闸与纪律机械闸 · 「被拒后换工具/换形做同一目标」拦截 v1.1（工具调用面）
// 令源：CEO 2026-11-28 00:35 令「纪律逃逸→机械拦截联动」（D-102·CAO 通知二·BOD 流转）
// 实锚：2026-11-27 `rm -rf <误写目录>` 被权限闸拒 → 换 `Remove-Item -Recurse -Force <同一路径>` 通过（字面 deny 规则只防字面）
// 能拦的一半（目标等价·L1）：被拒调用在会话 transcript 里有结构化留痕（行级字段 toolDenialKind /
//   sourceToolAssistantUUID / toolUseResult / cwd / timestamp）→ 本闸增量扫描本会话 transcript 记下每次被拒的
//   「破坏性动作目标路径」→ 后续同会话 24h 内出现破坏性动词族调用且目标路径与某条被拒目标相同或为其祖先后代 → BLOCK
// 告警的一半（L2）：本会话 24h 内有被拒记录时，任何破坏性动词族调用（目标未命中/解析不出也算）→ WARN 留痕放行
//   （Write/Edit 只走 L1——未命中不告警，防满屏噪音）
// v1.1 补（CAO 独立重测 2026-11-28 01:51 抓出的缺口）：命令内 cd/pushd 跟踪；Bash 内嵌 pwsh|powershell -Command、
//   cmd /c、bash -c、eval、xargs、解释器 -c 内串递归判定；[System.IO.*]::Delete；find -delete / -exec rm；
//   管道上游 gci|Get-ChildItem → Remove-Item；状态件不落命令原文与续行缓存
// 不可机械化的一半=纪律层终态（D-101 款 5）：变量间接·改名后删·删父目录内容（目标字面不同）·跨会话——无法穷举识别
// 放行：v1 不设本席放行形（transcript 内用户亲手输入与席间注入消息难以可靠区分·能被信面文字触发的放行=权限面风险）
//   放行=走审批流后由设闸人一侧执行；规则改动不自动放行
// 范围声明：只读**当前这次调用所属会话自己的** transcript（envelope.transcript_path）——不读他席会话
// 模式：DEFAULT_MODE 常量（observe=只记不拦·exit 1 留痕 / enforce=拦·exit 2）；切换走受审提交——会话中途改不了
// 留痕：<log-dir>/gate-d101.log（JSON 行·路径/命令只记 sha256 前 12 位·D-46 零值面）
//       <log-dir>/gate-d101/<key>.json（每会话增量扫描状态：offset+被拒目标表+近期工具调用目标索引·不落命令原文）
// 用法：cat envelope.json | node d101-denied-retry-gate.mjs [--mode observe|enforce] [--log-dir <dir>] [--no-log]
//       node d101-denied-retry-gate.mjs --selftest
// 退出码：0=PASS  1=WARN（放行留痕；observe 模式下 L1 命中亦退 1）  2=BLOCK
// 失效姿态：闸自身异常/transcript 不可读=fail-open+stderr 留痕（纪律闸非权限闸）
// —— CTO 小狄 2026-11-28

import { appendFileSync, closeSync, existsSync, mkdirSync, openSync, readFileSync, readSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { StringDecoder } from 'node:string_decoder';
import { pathToFileURL } from 'node:url';

const DEFAULT_MODE = 'observe';
const MAX_AGE_MS = 24 * 3600 * 1000;   // 被拒记录的有效期（同会话 24h 内）
const CHUNK = 8 * 1024 * 1024;          // 增量扫描每次读块
const PER_RUN_CAP = 256 * 1024 * 1024;  // 单次扫描上限（首扫大会话分多次追平）
const INITIAL_WINDOW = 128 * 1024 * 1024; // 冷启动大会话：先扫尾部窗口（被拒记录有效期 24h·相关记录都在尾部）
const KEEP_TOOL_USES = 200;             // 状态里保留的近期工具调用索引条数
const KEEP_DENIALS = 100;
const MAX_DEPTH = 3;                    // 内层命令递归判定深度

// ---------- 路径归一 ----------
function toDrive(p) { const m = /^\/([a-zA-Z])\/(.*)$/.exec(p); return m ? `${m[1].toUpperCase()}:/${m[2]}` : p; }
function normSegs(s) {
  const out = [];
  for (const seg of s.split('/')) { if (seg === '' || seg === '.') continue; if (seg === '..' && out.length > 1) { out.pop(); continue; } out.push(seg); }
  return out.join('/').toLowerCase();
}
export function normPath(p, base) {
  let s = String(p).trim().replace(/^["']|["']$/g, '');
  if (s.startsWith('~')) s = (process.env.USERPROFILE || 'C:\\Users\\default') + s.slice(1);
  s = toDrive(s).replace(/\\/g, '/');
  if (!/^([a-zA-Z]:|\/)/.test(s) && base) s = String(base).replace(/\\/g, '/').replace(/\/+$/, '') + '/' + s;
  return normSegs(s);
}
export function related(a, b) { return a === b || a.startsWith(b + '/') || b.startsWith(a + '/'); }
const sha12 = (s) => createHash('sha256').update(String(s)).digest('hex').slice(0, 12);

// ---------- 命令面：破坏性动作与目标抽取 ----------
const DELETE_CMDS = new Set(['rm', 'rmdir', 'rd', 'del', 'erase', 'rimraf', 'shred']);
const WRAPPERS = new Set(['sudo', 'env', 'exec', 'nohup', 'time', 'command', 'winpty', 'call', 'start']);
const PS_DELETE = new Set(['remove-item', 'rm', 'rmdir', 'del', 'erase', 'ri', 'remove-itemproperty', 'clear-content', 'clear-item', 'clear-recyclebin']);
const PS_PATH_FLAGS = new Set(['-path', '-literalpath', '-target', '-include']);
const PS_UPSTREAM = new Set(['gci', 'get-childitem', 'ls', 'dir', 'get-item', 'gi', 'resolve-path', 'rp', 'get-content', 'gc', 'cat', 'type']);
const PS_CD = new Set(['set-location', 'cd', 'sl', 'chdir', 'pushd']);
const PS_SHELLS = new Set(['pwsh', 'pwsh.exe', 'powershell', 'powershell.exe']);
const PS_TOP_FLAGS = new Set(['-file', '-f', '-noprofile', '-noninteractive', '-executionpolicy', '-windowstyle', '-nologo', '-configurationname', '-workingdirectory', '-w']);
const INTERP = new Set(['node', 'node.exe', 'python', 'python3', 'python.exe', 'python3.exe', 'perl', 'ruby', 'php']);
const PY_RE = /(?:shutil\.rmtree|os\.remove|os\.unlink|os\.rmdir)\(\s*["']([^"']+)["']/g;
const NODE_RE = /\b(?:rmSync|rmdirSync|unlinkSync|rm|rmdir|unlink)\s*\(\s*["']([^"']+)["']/g;
const DOTNET_DEL_RE = /\[System\.IO\.(?:Directory|File)\]::Delete\(\s*(['"])([^'"]+)\1/g;
const STRING_RUN_RE = /\b(?:execSync|execFileSync|spawnSync|exec|spawn|execFile|os\.system|system|popen|run|call|check_call|check_output)\s*\(\s*(['"])([^'"]+)\1/g;
const LIST_RUN_RE = /\b(?:spawnSync|spawn|execFile|execFileSync|run|call|check_call|check_output|Popen)\s*\(\s*\[([^\]]+)\]/g;
const INTERP_HINT_RE = /rmtree|os\.remove|os\.unlink|unlink\(|rmSync|rmdirSync|fs\.rm\b|fs\.rmdir\b|rmdir\(|Remove-Item|\brm\s+-[a-z]*r|rimraf|shutil|::Delete\(|rmdir\b|\bdel\s+/i;

function splitCommands(cmd) {
  const parts = []; let cur = ''; let q = null;
  for (let i = 0; i < cmd.length; i++) {
    const c = cmd[i];
    if (q) { cur += c; if (c === q && cmd[i - 1] !== '\\') q = null; continue; }
    if (c === '"' || c === "'") { q = c; cur += c; continue; }
    if (c === ';' || c === '|' || c === '&' || c === '\n') { if ((c === '&' && cmd[i + 1] === '&') || (c === '|' && cmd[i + 1] === '|')) i++; if (cur.trim()) parts.push(cur); cur = ''; continue; }
    cur += c;
  }
  if (cur.trim()) parts.push(cur);
  return parts;
}
function tokens(sc) { return (sc.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g) || []).map((t) => t.replace(/^["']|["']$/g, '')); }
function baseName(w) { const b = w.replace(/\\/g, '/').split('/').pop().toLowerCase(); return b.replace(/\.exe$/, ''); }
function skipPrefix(toks) {
  let i = 0;
  while (i < toks.length && /^[a-zA-Z_][a-zA-Z0-9_]*=/.test(toks[i])) i++;
  while (i < toks.length && WRAPPERS.has(baseName(toks[i]))) i++;
  if (i < toks.length && baseName(toks[i]) === 'xargs') { i++; while (i < toks.length && toks[i].startsWith('-')) i++; while (i < toks.length && /^[a-zA-Z_][a-zA-Z0-9_]*=/.test(toks[i])) i++; }
  if (i < toks.length && baseName(toks[i]) === 'timeout') i += 2;
  return i;
}
function collectDeleteArgs(args, cur, out, slashFlags = false) {
  // slashFlags=cmd 语境（/s /q 是开关）；Bash 语境里 /d/… 是 MSYS 绝对路径·不得当开关滤掉（v1.1 自测抓出）
  let rest = args;
  const dd = rest.indexOf('--'); if (dd >= 0) rest = rest.slice(dd + 1); else rest = rest.filter((a) => !a.startsWith('-') && !(slashFlags && /^\/[a-zA-Z](\b|$)/.test(a)));
  let taken = 0;
  for (const a of rest) {
    if (a === ']' || a === '[' || a === '&&' || a === '||') break;
    if (/^\d*>>?$/.test(a) || a === '/dev/null' || a === 'NUL' || a === 'nul') continue;
    if (a.includes('$')) { out.unresolved = true; continue; }
    out.targets.push(normPath(a, cur));
    if (++taken >= 4) break;
  }
}
function merge(dst, r) { if (!r) return; dst.targets.push(...r.targets); dst.verbs.push(...r.verbs); dst.unresolved = dst.unresolved || r.unresolved; }

export function extractBash(cmd, cwd, depth = 0) {
  const res = { targets: [], verbs: [], unresolved: false };
  let cur = cwd ? normPath(cwd, undefined) : '';
  for (const sc of splitCommands(cmd)) {
    const toks = tokens(sc);
    const i = skipPrefix(toks);
    if (i >= toks.length) continue;
    const w = baseName(toks[i]);
    const args = toks.slice(i + 1);
    if ((w === 'cd' || w === 'pushd' || w === 'chdir') && args[0] && !args[0].includes('$')) { if (args[0] !== '-') cur = normPath(args[0], cur); continue; }
    if (DELETE_CMDS.has(w)) { res.verbs.push(w); collectDeleteArgs(args, cur, res); continue; }
    if (w === 'find') { merge(res, extractFind(args, cur)); continue; }
    if (depth < MAX_DEPTH && (w === 'cmd' || w === 'cmd.exe') && (args[0] === '/c' || args[0] === '/k')) { merge(res, extractCmd(args.slice(1).join(' '), cur, depth)); continue; }
    if (depth < MAX_DEPTH && (w === 'bash' || w === 'sh' || w === 'zsh') && args[0] === '-c') { merge(res, extractBash(args.slice(1).join(' '), cur, depth + 1)); continue; }
    if (depth < MAX_DEPTH && w === 'eval') { merge(res, extractBash(args.join(' '), cur, depth + 1)); continue; }
    if (depth < MAX_DEPTH && PS_SHELLS.has(w)) { const inner = innerCommandOf(args); if (inner) merge(res, extractPowerShell(inner, cur, depth + 1)); continue; }
    if (depth < MAX_DEPTH && INTERP.has(w)) { const code = codeOf(w, args); if (code) merge(res, extractInterp(code, cur, depth)); continue; }
  }
  for (const re of [PY_RE, NODE_RE, DOTNET_DEL_RE]) { re.lastIndex = 0; let m; while ((m = re.exec(cmd))) { res.verbs.push(re === PY_RE ? 'py-delete' : re === NODE_RE ? 'node-delete' : 'dotnet-delete'); const a = re === DOTNET_DEL_RE ? m[2] : m[1]; if (!a) continue; if (a.includes('$')) res.unresolved = true; else res.targets.push(normPath(a, cur)); } }
  if (/git\s+clean\b/.test(cmd)) { res.verbs.push('git-clean'); res.targets.push(cur || '.'); }
  const gc = /git\s+(?:checkout|restore)\s+--\s+([^\n;|&]+)/.exec(cmd);
  if (gc) { res.verbs.push('git-checkout--'); for (const a of gc[1].trim().split(/\s+/)) { if (!a) continue; if (a.includes('$')) res.unresolved = true; else res.targets.push(normPath(a, cur)); } }
  if (/git\s+reset\s+--hard/.test(cmd)) { res.verbs.push('git-reset--hard'); res.targets.push(cur || '.'); }
  res.targets = [...new Set(res.targets)];
  res.destructive = res.verbs.length > 0;
  return res;
}

function extractFind(args, cur) {
  const out = { targets: [], verbs: [], unresolved: false };
  const pts = [];
  let k = 0;
  for (; k < args.length; k++) { const a = args[k]; if (a.startsWith('-') || a === '(' || a === '!') break; if (a.includes('$')) { out.unresolved = true; continue; } pts.push(normPath(a, cur)); }
  const rest = args.slice(k);
  let destructive = rest.includes('-delete') || rest.includes('-deleteall');
  for (let j = 0; j < rest.length; j++) {
    if (/^-(exec|execdir|ok|okdir)$/.test(rest[j])) { const nw = baseName(rest[j + 1] || ''); if (DELETE_CMDS.has(nw) || PS_SHELLS.has(nw) || INTERP.has(nw)) destructive = true; }
  }
  if (!destructive) return out;
  out.verbs.push('find-delete');
  if (!pts.length) { out.targets.push(cur || '.'); out.unresolved = true; } else out.targets.push(...pts);
  return out;
}

function innerCommandOf(args) {
  // pwsh|powershell 的 -Command/-c/-CommandWithArgs 取其后至下一个顶层开关；-EncodedCommand 解 base64(UTF-16LE)
  for (let k = 0; k < args.length; k++) {
    const f = args[k].toLowerCase();
    if (f === '-encodedcommand' || f === '-enc' || f === '-e') {
      const b = args[k + 1] || '';
      try { return Buffer.from(b, 'base64').toString('utf16le'); } catch { return null; }
    }
    if (f === '-command' || f === '-c' || f === '-commandwithargs') {
      const parts = [];
      for (let j = k + 1; j < args.length; j++) { if (PS_TOP_FLAGS.has(args[j].toLowerCase())) break; parts.push(args[j]); }
      return parts.join(' ');
    }
  }
  return null;
}
function codeOf(w, args) {
  const flag = (w.startsWith('node')) ? '-e' : '-c';
  const k = args.indexOf(flag);
  return k >= 0 ? (args[k + 1] || null) : null;
}
function extractCmd(inner, cur, depth) {
  const res = { targets: [], verbs: [], unresolved: false };
  for (const sc of splitCommands(inner)) {
    const toks = tokens(sc);
    const i = skipPrefix(toks);
    if (i >= toks.length) continue;
    const w = baseName(toks[i]);
    const args = toks.slice(i + 1);
    if (w === 'cd' || w === 'chdir') { if (args[0] && !args[0].includes('$')) cur = normPath(args[0], cur); continue; }
    if (DELETE_CMDS.has(w)) { res.verbs.push('cmd:' + w); collectDeleteArgs(args, cur, res, true); continue; }
    if (depth < MAX_DEPTH && PS_SHELLS.has(w)) { const inner2 = innerCommandOf(args); if (inner2) merge(res, extractPowerShell(inner2, cur, depth + 1)); continue; }
  }
  res.destructive = res.verbs.length > 0;
  return res;
}
function extractInterp(code, cur, depth) {
  const res = { targets: [], verbs: [], unresolved: false };
  const hit = (s) => /\b(?:rm|rmdir|rd|del|erase)\b|Remove-Item|powershell|pwsh|cmd|rmdir\b|unlink|rmtree/i.test(s);
  for (const re of [STRING_RUN_RE, LIST_RUN_RE]) {
    re.lastIndex = 0; let m;
    while ((m = re.exec(code))) {
      const inner = re === STRING_RUN_RE ? m[2] : m[1].replace(/["'[\],]/g, ' ');
      if (!hit(inner)) continue;
      res.verbs.push('interp-run');
      merge(res, extractBash(inner, cur, depth + 1));
      if (re === STRING_RUN_RE && !extractBash(inner, cur, depth + 1).verbs.length) res.unresolved = true;
    }
  }
  if (!res.verbs.length && INTERP_HINT_RE.test(code)) { res.verbs.push('interp-hint'); res.unresolved = true; }
  res.destructive = res.verbs.length > 0;
  return res;
}

export function extractPowerShell(cmd, cwd, depth = 0) {
  const res = { targets: [], verbs: [], unresolved: false };
  let cur = cwd ? normPath(cwd, undefined) : '';
  const parts = splitCommands(cmd);
  let prev = null;
  for (const sc of parts) {
    const toks = tokens(sc);
    const i = skipPrefix(toks);
    if (i >= toks.length) continue;
    const w = baseName(toks[i]);
    const args = toks.slice(i + 1);
    if (PS_CD.has(w) && args[0] && !args[0].includes('$')) { cur = normPath(args[0], cur); prev = { w, args }; continue; }
    if (PS_DELETE.has(w)) {
      res.verbs.push(w);
      let own = 0;
      for (let k = 0; k < args.length; k++) {
        const a = args[k];
        if (/^-[a-z]/i.test(a)) {
          if (PS_PATH_FLAGS.has(a.toLowerCase())) { const v = args[++k]; if (v) { if (v.includes('$')) res.unresolved = true; else { res.targets.push(normPath(v, cur)); own++; } } }
          continue;
        }
        if (a.includes('$')) { res.unresolved = true; continue; }
        res.targets.push(normPath(a, cur)); own++;
      }
      if (!own) {
        // 管道形：路径来自上游（gci|Get-ChildItem … | Remove-Item）
        if (prev && PS_UPSTREAM.has(prev.w)) {
          let any = false;
          for (const a of prev.args) { if (/^-[a-z]/i.test(a)) continue; if (a.includes('$')) { res.unresolved = true; continue; } res.targets.push(normPath(a, cur)); any = true; }
          if (!any) res.unresolved = true;
        } else res.unresolved = true;
      }
      prev = { w, args }; continue;
    }
    if (depth < MAX_DEPTH && PS_SHELLS.has(w)) { const inner = innerCommandOf(args); if (inner) merge(res, extractPowerShell(inner, cur, depth + 1)); }
    if (depth < MAX_DEPTH && (w === 'cmd' || w === 'cmd.exe') && (args[0] === '/c' || args[0] === '/k')) merge(res, extractCmd(args.slice(1).join(' '), cur, depth));
    if (depth < MAX_DEPTH && INTERP.has(w)) { const code = codeOf(w, args); if (code) merge(res, extractInterp(code, cur, depth)); }
    prev = { w, args };
  }
  for (const re of [DOTNET_DEL_RE]) { re.lastIndex = 0; let m; while ((m = re.exec(cmd))) { res.verbs.push('dotnet-delete'); const a = m[2]; if (a.includes('$')) res.unresolved = true; else res.targets.push(normPath(a, cur)); } }
  if (/::Delete\s*\(/.test(cmd) && !res.verbs.includes('dotnet-delete')) { res.verbs.push('dotnet-delete'); res.unresolved = true; }
  res.targets = [...new Set(res.targets)];
  res.destructive = res.verbs.length > 0;
  return res;
}

export function extractCurrent(envelope) {
  const tool = envelope.tool_name; const ti = envelope.tool_input || {}; const cwd = envelope.cwd;
  if (tool === 'Bash' && typeof ti.command === 'string') return { tool, ...extractBash(ti.command, cwd), raw: ti.command };
  if (tool === 'PowerShell' && typeof ti.command === 'string') return { tool, ...extractPowerShell(ti.command, cwd), raw: ti.command };
  if ((tool === 'Write' || tool === 'Edit') && typeof ti.file_path === 'string') {
    return { tool, destructive: true, l1Only: true, targets: [normPath(ti.file_path, cwd ? normPath(cwd, undefined) : '')], unresolved: false, verbs: [tool.toLowerCase()], raw: ti.file_path };
  }
  return { tool, destructive: false, targets: [], unresolved: false, verbs: [], raw: '' };
}

// ---------- transcript 增量扫描（只读本会话自己的 transcript） ----------
function lineDenial(line) {
  try {
    const j = JSON.parse(line);
    if (!j || typeof j !== 'object' || !('toolDenialKind' in j)) return null;
    let toolUseId = null;
    try { const c = j.message && j.message.content; if (Array.isArray(c)) { for (const b of c) { if (b && b.type === 'tool_result' && b.tool_use_id) { toolUseId = b.tool_use_id; break; } } } } catch { }
    return { ts: j.timestamp || null, kind: j.toolDenialKind, cwd: j.cwd || null, textSha: sha12(typeof j.toolUseResult === 'string' ? j.toolUseResult : ''), toolUseId };
  } catch { return null; }
}
function analyzeToolUse(name, input, cwd) {
  const raw = input && typeof input.command === 'string' ? input.command : '';
  if (name === 'Bash' && raw) return extractBash(raw, cwd);
  if (name === 'PowerShell' && raw) return extractPowerShell(raw, cwd);
  if ((name === 'Write' || name === 'Edit') && input && typeof input.file_path === 'string') {
    return { destructive: true, l1Only: true, targets: [normPath(input.file_path, cwd ? normPath(cwd, undefined) : '')], unresolved: false, verbs: [name.toLowerCase()] };
  }
  return { destructive: false, targets: [], unresolved: false, verbs: [] };
}
// 索引项只存「目标与指纹」——建索引时即抽好，命令原文不入状态件（D-46·CAO 重测 D1）
function lineToolUses(line, sink) {
  try {
    const j = JSON.parse(line);
    if (!j || j.type !== 'assistant' || !j.message || !Array.isArray(j.message.content)) return;
    for (const b of j.message.content) {
      if (b && b.type === 'tool_use' && b.id) {
        const cwd = j.cwd || null;
        const ex = analyzeToolUse(b.name, b.input || {}, cwd);
        sink.push({ id: b.id, name: b.name, ts: j.timestamp || null, cwd, destructive: !!ex.destructive, targets: ex.targets.slice(0, 8), unresolved: !!ex.unresolved, cmdSha: sha12((b.input && (b.input.command || b.input.file_path)) || '') });
      }
    }
  } catch { }
}

function nextLineStart(fd, pos, size) {
  const b = Buffer.alloc(65536);
  while (pos < size) {
    const got = readSync(fd, b, 0, Math.min(b.length, size - pos), pos);
    if (got <= 0) return -1;
    const i = b.subarray(0, got).indexOf(0x0a);
    if (i >= 0) return pos + i + 1;
    pos += got;
  }
  return -1;
}

function scanTranscript(state, transcriptPath, caps = {}) {
  const perRunCap = caps.perRunCap || PER_RUN_CAP;
  const initialWindow = caps.initialWindow || INITIAL_WINDOW;
  let size = 0;
  try { size = statSync(transcriptPath).size; } catch { return; }
  if (size < state.offset) { state.offset = 0; state.denials = []; state.toolUses = []; state.initialized = false; } // 轮转/截断=重扫
  if (size === state.offset) return;
  let fd = null;
  try {
    fd = openSync(transcriptPath, 'r');
    let pos = state.offset; let rest = ''; let readTotal = 0;
    if (pos === 0 && !state.initialized && size > perRunCap) {
      // 冷启动大会话：先扫尾部窗口再增量追平——否则首几次调用只见旧半段（判定偏松=放行/告警而非拦）
      const start = nextLineStart(fd, size - initialWindow, size);
      pos = start > 0 ? start : size;
    }
    state.initialized = true;
    const buf = Buffer.alloc(CHUNK);
    const dec = new StringDecoder('utf8'); // 块边界遇多字节字符由解码器续接
    while (pos < size && readTotal < perRunCap) {
      const want = Math.min(CHUNK, size - pos, perRunCap - readTotal);
      const got = readSync(fd, buf, 0, want, pos);
      if (got <= 0) break;
      readTotal += got; pos += got;
      const chunk = rest + dec.write(buf.subarray(0, got));
      const lines = chunk.split('\n');
      rest = lines.pop(); // 未完行不处理
      for (const ln of lines) processLine(state, ln);
    }
    if (pos >= size) { rest += dec.end(); if (rest) { processLine(state, rest); rest = ''; } } // 文件尾无换行的完整末行
    state.offset = pos - Buffer.byteLength(rest, 'utf8'); // 续行缓存不落盘：偏移停在最后一个完整行
    state.size = size;
    if (state.toolUses.length > KEEP_TOOL_USES) state.toolUses = state.toolUses.slice(-KEEP_TOOL_USES);
    if (state.denials.length > KEEP_DENIALS) state.denials = state.denials.slice(-KEEP_DENIALS);
  } catch { /* 读失败=保持旧状态 */ } finally { if (fd !== null) try { closeSync(fd); } catch { } }
}
function processLine(state, ln) {
  if (ln.length > 4 * 1024 * 1024) return; // 超长行（大工具结果）不解析
  if (ln.includes('"type":"assistant"') && ln.includes('"tool_use"')) lineToolUses(ln, state.toolUses);
  if (!ln.includes('toolDenialKind')) return;
  const d = lineDenial(ln);
  if (!d) return;
  const tu = d.toolUseId ? state.toolUses.find((t) => t.id === d.toolUseId) : null;
  state.denials.push({
    ts: d.ts, kind: d.kind, tool: tu ? tu.name : 'unknown', textSha: d.textSha,
    targets: tu ? tu.targets : [], unresolved: tu ? tu.unresolved : true, cmdSha: tu ? tu.cmdSha : null,
  });
}

// ---------- 状态存取 ----------
function statePath(logDir, key) { return join(logDir, 'gate-d101', `${key}.json`); }
function loadState(logDir, key, transcriptPath) {
  const p = statePath(logDir, key);
  try { const s = JSON.parse(readFileSync(p, 'utf8')); if (s && typeof s.offset === 'number') { delete s.carry; return s; } } catch { }
  return { transcript: transcriptPath, offset: 0, denials: [], toolUses: [], initialized: false };
}
function saveState(logDir, key, state) {
  try {
    mkdirSync(join(logDir, 'gate-d101'), { recursive: true });
    const s = { transcript: state.transcript, offset: state.offset, size: state.size, initialized: state.initialized, denials: state.denials, toolUses: state.toolUses };
    writeFileSync(statePath(logDir, key), JSON.stringify(s), 'utf8');
  } catch { }
}

// ---------- 判定 ----------
export function decide(current, denials, now) {
  const fresh = denials.filter((d) => d.ts && (now - Date.parse(d.ts)) <= MAX_AGE_MS);
  if (!current.destructive) return { decision: 'PASS', reason: 'non-destructive', n_fresh: fresh.length };
  if (!fresh.length) return { decision: 'PASS', reason: 'no-denial-in-session', n_fresh: 0 };
  for (const d of fresh) {
    for (const dt of d.targets) {
      for (const ct of current.targets) {
        if (related(ct, dt)) return { decision: 'BLOCK', reason: 'denied-target-retry', denial: d, target: ct, n_fresh: fresh.length };
      }
    }
  }
  if (current.l1Only) return { decision: 'PASS', reason: 'write-edit-no-hit', n_fresh: fresh.length }; // Write/Edit 只走 L1
  return { decision: 'WARN', reason: 'denial-present-target-unmatched', n_fresh: fresh.length };
}
export function exitCodeFor(r, mode) {
  if (r.decision === 'PASS') return 0;
  if (r.decision === 'WARN') return 1;
  return mode === 'enforce' ? 2 : 1;
}
export function blockMessage(r) {
  const when = r.denial && r.denial.ts ? r.denial.ts : '(时刻未知)';
  return [
    `D-101 闸拦截（退回）——本次操作的目标，本会话已于 ${when} 被权限闸拒（${r.denial ? r.denial.kind : ''}）。`,
    '被拒的动作不得换工具、换命令形去做同一件事（D-101 款 1·纪律逃逸实证形：rm -rf X 被拒→Remove-Item -Recurse -Force X）。',
    '确需执行：走审批流（重大不可逆类=COS 转 BOD 请 CEO 批），由设闸人一侧执行或清理该会话被拒状态——本席同会话 24h 内不放行·规则改动不自动放行。',
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

export function run(envelopeText, { mode = DEFAULT_MODE, logDir, noLog = false, now = Date.now(), stateIO = true, caps = {} } = {}) {
  let envelope = null;
  try { envelope = JSON.parse(envelopeText); } catch { return { decision: 'PASS', reason: 'bad-envelope' }; }
  const current = extractCurrent(envelope || {});
  if (!current.destructive) return { decision: 'PASS', reason: 'non-destructive', current };
  const tp = envelope && envelope.transcript_path;
  if (!tp || typeof tp !== 'string') return { decision: 'PASS', reason: 'no-transcript-path', current };
  const key = sha12(tp);
  const state = stateIO ? loadState(logDir, key, tp) : { offset: 0, denials: [], toolUses: [], initialized: false };
  scanTranscript(state, tp, caps);
  if (stateIO) saveState(logDir, key, state);
  const r = decide(current, state.denials, now);
  r.current = { tool: current.tool, verbs: current.verbs, n_targets: current.targets.length, unresolved: current.unresolved };
  r.n_denials = state.denials.length;
  return r;
}

function selftest() {
  const dir = join(process.env.TEMP || '.', 'cto-d101-selftest');
  try { rmSync(join(dir, 'gate-d101'), { recursive: true, force: true }); } catch { } // 每轮自测从零状态起（防沿用旧扫描状态）
  mkdirSync(dir, { recursive: true });
  const NOW = Date.now();
  const tsAgo = (h) => new Date(NOW - h * 3600 * 1000).toISOString();
  const CWD = 'D:\\Code\\ai\\TriMetaverse';
  const mk = (name, lines) => {
    const p = join(dir, name + '.jsonl');
    writeFileSync(p, lines.map((l) => JSON.stringify(l)).join('\n') + '\n', 'utf8');
    return p;
  };
  const use = (id, cmd, t, name = 'Bash') => ({ type: 'assistant', uuid: 'u-' + id, timestamp: t, cwd: CWD, message: { role: 'assistant', content: [{ type: 'tool_use', id, name, input: name === 'Bash' ? { command: cmd } : { command: cmd } }] } });
  const den = (id, cmd, t) => ({ type: 'user', timestamp: t, cwd: CWD, toolDenialKind: 'permission-rule', sourceToolAssistantUUID: 'u-' + id, toolUseResult: `Error: Permission to use Bash with command ${cmd} has been denied.`, permissionDecision: { decision: 'reject', source: 'config' }, message: { role: 'user', content: [{ type: 'tool_result', tool_use_id: id, content: `Permission to use Bash with command ${cmd} has been denied.` }] } });
  const filler = (t) => ({ type: 'user', timestamp: t, message: { role: 'user', content: 'hello world '.repeat(50) } });
  const X = '/d/Code/ai/TriCompany/TriMetaverse';
  const XW = 'D:\\Code\\ai\\TriCompany\\TriMetaverse';
  const T = {
    same: mk('same', [use('A1', `git status --short -- TriMetaverse && rm -rf "${X}" && echo done`, tsAgo(2)), den('A1', `git status --short -- TriMetaverse && rm -rf "${X}" && echo done`, tsAgo(2)), filler(tsAgo(1))]),
    varTarget: mk('var', [use('V1', 'python -c "print(1)"\ncd /d/Code/ai/TriMetaverse && rm -rf "$T"', tsAgo(3)), den('V1', 'python -c "print(1)"\ncd /d/Code/ai/TriMetaverse && rm -rf "$T"', tsAgo(3))]),
    old: mk('old', [use('O1', `rm -rf ${X}`, tsAgo(30)), den('O1', `rm -rf ${X}`, tsAgo(30))]),
    none: mk('none', [filler(tsAgo(1))]),
  };
  const env = (tool, input, tp) => JSON.stringify({ hook_event_name: 'PreToolUse', tool_name: tool, tool_input: input, cwd: CWD, transcript_path: tp, session_id: 's' });
  const rmf = (p) => ({ command: `rm -rf ${p}` });
  const cases = [
    ['实锚形：被拒 rm -rf X → PowerShell Remove-Item -Recurse -Force X（同一路径）', env('PowerShell', { command: `Remove-Item -Recurse -Force '${XW}'` }, T.same), 'BLOCK'],
    ['同目标换 Bash 写法（/d/ 形）', env('Bash', rmf(X), T.same), 'BLOCK'],
    ['被拒目标的后代路径', env('Bash', rmf(X + '/.github'), T.same), 'BLOCK'],
    ['v1.1·cd 父目录 && rm -rf 目录名（命令内 cd 跟踪）', env('Bash', { command: 'cd /d/Code/ai/TriCompany && rm -rf TriMetaverse' }, T.same), 'BLOCK'],
    ['v1.1·cd 进目标 && rm -rf .', env('Bash', { command: 'cd /d/Code/ai/TriCompany/TriMetaverse && rm -rf .' }, T.same), 'BLOCK'],
    ['v1.1·Bash 内嵌 pwsh -Command Remove-Item 同路径', env('Bash', { command: `pwsh -NoProfile -Command "Remove-Item -Recurse -Force '${XW}'"` }, T.same), 'BLOCK'],
    ['v1.1·Bash 内嵌 powershell -EncodedCommand（base64·UTF-16LE）', env('Bash', { command: `powershell -NoProfile -EncodedCommand ${Buffer.from(`Remove-Item -Recurse -Force '${XW}'`, 'utf16le').toString('base64')}` }, T.same), 'BLOCK'],
    ['v1.1·cmd /c rmdir /s /q X', env('Bash', { command: `cmd /c rmdir /s /q ${XW}` }, T.same), 'BLOCK'],
    ['v1.1·PowerShell 工具 cmd /c rmdir', env('PowerShell', { command: `cmd /c "rmdir /s /q ${XW}"` }, T.same), 'BLOCK'],
    ['v1.1·[System.IO.Directory]::Delete', env('PowerShell', { command: `[System.IO.Directory]::Delete('${XW}', $true)` }, T.same), 'BLOCK'],
    ['v1.1·find X -delete', env('Bash', { command: `find ${X} -type f -delete` }, T.same), 'BLOCK'],
    ['v1.1·find 父 -name X -exec rm -rf {} +', env('Bash', { command: `find /d/Code/ai/TriCompany -maxdepth 1 -name TriMetaverse -exec rm -rf {} +` }, T.same), 'BLOCK'],
    ['v1.1·gci X | Remove-Item -Recurse -Force（管道上游路径）', env('PowerShell', { command: `gci '${XW}' | Remove-Item -Recurse -Force` }, T.same), 'BLOCK'],
    ['v1.1·node execSync 内串 rm -rf 同路径', env('Bash', { command: `node -e "require('child_process').execSync('rm -rf ${X}')"` }, T.same), 'BLOCK'],
    ['v1.1·python subprocess 列表形 rm -rf 同路径', env('Bash', { command: `python -c "import subprocess; subprocess.run(['rm','-rf','${X}'])"` }, T.same), 'BLOCK'],
    ['v1.1·解释器内串含删除但目标=变量→ L2 告警', env('Bash', { command: `python -c "import os; d=os.environ['T']; os.system('rm -rf '+d)"` }, T.same), 'WARN'],
    ['v1.1·find 只搜文件名（非破坏）=放行', env('Bash', { command: 'find /c/Windows -name powershell.exe' }, T.same), 'PASS'],
    ['Write 落在被拒目标子树内', env('Write', { file_path: XW + '\\x.md', content: 'x' }, T.same), 'BLOCK'],
    ['Edit 落在被拒目标子树内', env('Edit', { file_path: XW + '\\a.md', old_string: 'a', new_string: 'b' }, T.same), 'BLOCK'],
    ['v1.1·Write 无关文件（有过被拒记录）=不告警', env('Write', { file_path: 'D:\\Code\\ai\\TriMetaverse\\docs\\x.md', content: 'x' }, T.same), 'PASS'],
    ['被拒目标无关的另一路径（L2 告警）', env('Bash', rmf('/d/tmp/other-dir'), T.same), 'WARN'],
    ['被拒命令目标是变量（解析不出）→ L2 告警', env('Bash', rmf('/d/tmp/cto-fp-verify'), T.varTarget), 'WARN'],
    ['当前调用目标是变量且与被拒目标相关→ L2（不硬拦）', env('Bash', { command: 'rm -rf "$T/sub"' }, T.same), 'WARN'],
    ['无被拒记录的破坏性调用=放行', env('Bash', rmf('/d/tmp/x'), T.none), 'PASS'],
    ['被拒后非破坏性调用=放行', env('Bash', { command: `ls ${X}` }, T.same), 'PASS'],
    ['被拒已超 24h=不计', env('Bash', rmf(X), T.old), 'PASS'],
    ['无 transcript_path=放行', JSON.stringify({ tool_name: 'Bash', tool_input: rmf(X), cwd: CWD }), 'PASS'],
    ['非 JSON envelope=放行', 'not json', 'PASS'],
    ['git clean（目标=当前 cwd·与被拒目标不相干→ L2 告警）', env('Bash', { command: 'git clean -fd' }, T.same), 'WARN'],
  ];
  let fail = 0;
  const opts = { logDir: dir, noLog: true, now: NOW };
  for (const [name, e, want] of cases) {
    const r = run(e, opts);
    const got = r.decision;
    const ok = got === want;
    if (!ok) fail++;
    console.log(`${ok ? 'ok ' : 'FAIL'} [${name}] want=${want} got=${got}(${r.reason})`);
  }
  // 增量扫描：先扫一半，再追加被拒行后再判（同一 transcript 文件）
  const incPath = join(dir, 'inc.jsonl');
  writeFileSync(incPath, JSON.stringify(filler(tsAgo(1))) + '\n' + JSON.stringify(use('I1', `rm -rf ${X}`, tsAgo(1))) + '\n', 'utf8');
  const r1 = run(env('Bash', rmf(X), incPath), { ...opts, noLog: false });
  appendFileSync(incPath, JSON.stringify(den('I1', `rm -rf ${X}`, tsAgo(1))) + '\n', 'utf8');
  const r2 = run(env('Bash', rmf(X), incPath), { ...opts, noLog: false });
  const incOk = r1.decision === 'PASS' && r2.decision === 'BLOCK';
  if (!incOk) fail++;
  console.log(`${incOk ? 'ok ' : 'FAIL'} [增量扫描：被拒行写入后再判] first=${r1.decision} second=${r2.decision}`);
  // v1.1·状态件不落命令原文（D-46）：索引项只有目标/指纹·无 raw/carry 键
  const st = JSON.parse(readFileSync(join(dir, 'gate-d101', sha12(incPath) + '.json'), 'utf8'));
  const noRaw = !('carry' in st) && st.toolUses.every((t) => !('raw' in t)) && !JSON.stringify(st).includes('rm -rf /d/Code');
  if (!noRaw) fail++;
  console.log(`${noRaw ? 'ok ' : 'FAIL'} [状态件不落命令原文·无 raw/carry]`);
  // 冷启动大会话：超过单次上限的 transcript 首次调用即扫尾部窗口命中（上限/窗口用小参数模拟）
  const bigPath = join(dir, 'big.jsonl');
  const bigLines = [];
  for (let i = 0; i < 1500; i++) bigLines.push(JSON.stringify(filler(tsAgo(1))));
  bigLines.push(JSON.stringify(use('B1', `rm -rf ${X}`, tsAgo(2))), JSON.stringify(den('B1', `rm -rf ${X}`, tsAgo(2))));
  writeFileSync(bigPath, bigLines.join('\n') + '\n', 'utf8');
  const rb = run(env('Bash', rmf(X), bigPath), { ...opts, noLog: false, caps: { perRunCap: 64 * 1024, initialWindow: 32 * 1024 } });
  const bigOk = rb.decision === 'BLOCK';
  if (!bigOk) fail++;
  console.log(`${bigOk ? 'ok ' : 'FAIL'} [冷启动大会话：首调即扫尾部窗口命中] first=${rb.decision}(${rb.reason})`);
  const codes = [exitCodeFor({ decision: 'BLOCK' }, 'enforce'), exitCodeFor({ decision: 'BLOCK' }, 'observe'), exitCodeFor({ decision: 'WARN' }, 'enforce'), exitCodeFor({ decision: 'PASS' }, 'enforce')];
  const codesOk = codes.join(',') === '2,1,1,0';
  if (!codesOk) fail++;
  console.log(`${codesOk ? 'ok ' : 'FAIL'} [退出码映射] want=2,1,1,0 got=${codes.join(',')}`);
  console.log(fail ? `\nSELFTEST FAIL (${fail})` : '\nSELFTEST ALL PASS');
  process.exit(fail ? 2 : 0);
}

// ---------- 入口（仅主模块执行） ----------
const isMain = (() => { try { return !!process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href; } catch { return false; } })();
if (isMain) {
  const args = process.argv.slice(2);
  if (args.includes('--selftest')) selftest();
  let text = '';
  try { text = readFileSync(0, 'utf8'); } catch { text = ''; }
  const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
  const mode = opt('--mode') || DEFAULT_MODE;
  let cwd = ''; try { cwd = (JSON.parse(text) || {}).cwd || process.env.CLAUDE_PROJECT_DIR || process.cwd(); } catch { cwd = process.env.CLAUDE_PROJECT_DIR || process.cwd(); }
  const logDir = opt('--log-dir') || process.env.TRI_GATE_LOG_DIR || (existsSync(join(cwd, '.fade')) ? join(cwd, '.fade') : 'D:\\Code\\ai\\TriMetaverse\\.fade');
  let r;
  try { r = run(text, { mode, logDir }); } catch (e) {
    console.error(`[d101-gate] 闸自身异常——放行+留痕·请报 CTO：${e && e.message}`);
    process.exit(1);
  }
  if (!args.includes('--no-log') && r.decision !== 'PASS') {
    try {
      mkdirSync(logDir, { recursive: true });
      appendFileSync(join(logDir, 'gate-d101.log'), JSON.stringify({
        ts: new Date().toISOString(), gate: 'd101', mode, decision: r.decision, reason: r.reason, seat: seatFromCwd(cwd),
        tool: r.current ? r.current.tool : null, verbs: r.current ? r.current.verbs : [], n_targets: r.current ? r.current.n_targets : 0,
        unresolved: r.current ? r.current.unresolved : null, n_denials: r.n_denials ?? null, n_fresh: r.n_fresh ?? null,
        target_sha12: r.target ? sha12(r.target) : null, denial_ts: r.denial ? r.denial.ts : null,
      }) + '\n', 'utf8');
    } catch { /* 留痕失败不挡工具面 */ }
  }
  if (r.decision === 'BLOCK') {
    if (mode === 'enforce') { console.error(blockMessage(r)); process.exit(2); }
    console.error(`[d101-gate WARN·observe 模式放行留痕] 本应拦截：被拒目标的换形重试（${r.reason}·被拒于 ${r.denial ? r.denial.ts : '?'}）——切换 enforce 前只记不拦。`);
    process.exit(1);
  }
  if (r.decision === 'WARN') {
    console.error(`[d101-gate WARN 留痕·已放行] 本会话 24h 内有 ${r.n_fresh} 次被拒记录；本次为破坏性调用（目标未命中或解析不出）——D-101：被拒动作不得换形重试。`);
    process.exit(1);
  }
  process.exit(0);
}

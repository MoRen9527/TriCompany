#!/usr/bin/env node
// D-47 时刻纪律机械闸 · 发送前置指纹拦截 v1（信面）
// 派工源：COO 2026-10-21 19:22:15 派工单（承 CAO 二十四案终判「gate 发送前置拦截升建议即办」）
// 拦截对象两类指纹（COO 派工单原文照纳）：
//   ① 占位掩码型：落款/时刻字段含 x/□ 掩码段（date 输出无此形态=手写造值铁证）→ 直拦
//   ② 圆整秒假值型：秒%10==0 高疑 + 倒挂交叉验证并现 → 直拦；单圆整秒 → warn（真值 10% 概率防误伤）
// 倒挂判据：落款时刻 > 现查时刻 + 90s 容差（时钟偏差上限）→ 拦（落款在未来=手写预估指纹）
// 误伤防护：倒挂判定只看「落款段」（落款关键词邻域）；正文历史时刻（引用/死线/窗位）不触发倒挂
// 用法：
//   node d47-timestamp-gate.mjs --file <信文路径> [--now "2026-10-21T19:23:40+08:00"]
//   cat 信文 | node d47-timestamp-gate.mjs --now "..."
//   node d47-timestamp-gate.mjs --selftest
// 退出码：0=PASS  1=WARN（放行·留痕）  2=BLOCK（拦·退回重写）
// 挂载形态：v1=手动自查闸（发送前跑闸）；hook 自动挂载（PreToolUse on SendMessage）呈 CEO 批准后另行执行
// —— CTO 小狄 2026-10-21（依 COO 派工单·D-46 零值面·家族二十五案谱系）

import { readFileSync } from 'node:fs';

const TOLERANCE_S = 90; // 倒挂容差：时钟偏差上限（写作延迟使落款在过去=正常，未来才可疑）

// ---------- 指纹提取 ----------

// 掩码段：时刻后接 x/X/□/◼（含 xx/2□/3x 形；Z/+08 尾缀容忍）
const MASK_RE = /(\d{1,2}[:：]\d{2}[:：]\d{0,2}\s*[xX□◼]{1,2}|\d{1,2}[:：]\d{2}\s*[xX□◼]{1,2}(?![0-9]))/g;

// 时刻提取：可选日期 + HH:MM(:SS)?
const TIME_RE = /(\d{4}-\d{2}-\d{2})?[T ]?(\d{1,2}):(\d{2})(?::(\d{2}))?/g;

// 落款段识别：落款关键词所在行（含前后 0 行——落款句自含时刻）
const SIGN_KEYS = ['落款', 'date 现查', 'date现查', '现查原值', '发毕对表'];

function extractSignSegment(text) {
  const lines = text.split(/\r?\n/);
  const hits = [];
  lines.forEach((ln, i) => {
    if (SIGN_KEYS.some((k) => ln.includes(k))) hits.push(ln);
  });
  return hits.join('\n');
}

function pad(n) { return String(n).padStart(2, '0'); }

function parseNow(s) {
  // 支持 ISO / "YYYY-MM-DD HH:MM:SS+0800" / epoch ms
  if (/^\d{13}$/.test(s)) return new Date(Number(s));
  const m = s.match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})/);
  if (!m) return new Date(s);
  // 按本地时区解读（调用方与本机同时区）；带 Z 视 UTC
  if (/[zZ]$/.test(s.trim())) return new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}Z`);
  return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]);
}

function findMaskHits(text) {
  return [...text.matchAll(MASK_RE)].map((m) => m[1].trim());
}

function findFutureSignTimes(signSeg, now) {
  if (!signSeg || !now || Number.isNaN(now.getTime())) return [];
  const out = [];
  for (const m of signSeg.matchAll(TIME_RE)) {
    const [, d, hh, mm, ss] = m;
    if (!ss) continue; // 无秒位不判倒挂（分钟粒度误差窗过大·家族十五案为 hook 判）
    const hhN = +hh, mmN = +mm, ssN = +ss;
    if (hhN > 23 || mmN > 59 || ssN > 59) continue;
    let claim;
    if (d) {
      claim = /[zZ]$/.test(m[0]) ? new Date(`${d}T${pad(hhN)}:${pad(mmN)}:${pad(ssN)}Z`)
        : new Date(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10), hhN, mmN, ssN);
    } else {
      claim = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hhN, mmN, ssN);
      // 跨日回卷：落款时刻比 now 晚 >12h 视为昨日时刻（历史引用）
      if (claim.getTime() - now.getTime() > 12 * 3600 * 1000) {
        claim = new Date(claim.getTime() - 24 * 3600 * 1000);
      }
    }
    if (claim.getTime() > now.getTime() + TOLERANCE_S * 1000) {
      out.push(m[0].trim());
    }
  }
  return out;
}

function findRoundTensInSign(signSeg) {
  const out = [];
  for (const m of signSeg.matchAll(/(\d{1,2}:\d{2}:(\d{2}))/g)) {
    const sec = +m[2];
    if (sec % 10 === 0) out.push(m[1]);
  }
  return out;
}

// ---------- 主判定 ----------

function gate(text, nowStr) {
  const now = nowStr ? parseNow(nowStr) : new Date();
  const signSeg = extractSignSegment(text);
  const maskAll = findMaskHits(text);
  const maskSign = signSeg ? findMaskHits(signSeg) : [];
  const future = findFutureSignTimes(signSeg, now);
  const roundInSign = signSeg ? findRoundTensInSign(signSeg) : [];

  const blocks = [];
  const warns = [];

  // ① 掩码段：落款段直拦；正文位 warn（引用历史卷面摘录场景·留痕不放行不硬拦）
  if (maskSign.length) blocks.push(`掩码段(落款段): ${maskSign.join(' · ')}`);
  const maskBody = maskAll.filter((x) => !maskSign.includes(x));
  if (maskBody.length) warns.push(`掩码段(正文位·疑引用): ${maskBody.join(' · ')}`);

  // ② 倒挂：直拦
  if (future.length) blocks.push(`倒挂(落款晚于现查${TOLERANCE_S}s+): ${future.join(' · ')}`);

  // ③ 圆整秒：倒挂并现已由②拦；单现 warn
  const roundOnly = roundInSign.filter((x) => !future.some((f) => f.includes(x)));
  if (roundOnly.length && !future.length) warns.push(`圆整秒(单现·高疑): ${roundOnly.join(' · ')}`);

  return { blocks, warns, signSeg: signSeg.slice(0, 200) };
}

// ---------- 自测（COO 派工单护栏：违例样本命中+真值样本零误拦） ----------

function selftest() {
  const nowStr = '2026-10-21T19:23:40+0800';
  const cases = [
    // [名, 文, 期望]
    ['二十三案掩码(19:15:3x)', '本席落款违在先·现查补跑=19:15:3x（date 现查原值）', 'BLOCK'],
    ['本席十八案掩码(18:58:1x)', '—— CTO 小狄（落款 date 现查原值 2026-10-21 18:58:1x +0800·发毕对表）', 'BLOCK'],
    ['FSD 二十五案掩码(11:14:xxZ)', 'date 现查 2026-10-21T11:14:xxZ / 19:14+0800', 'BLOCK'],
    ['二十四案圆整+倒挂(18:40:00 未来)', '落款 date 现查原值 2026-10-21 23:40:00 +0800', 'BLOCK'],
    ['真值样本(19:17:16·过去)', '—— CTO 小狄（落款 date 现查原值 2026-10-21 19:17:16 +0800·发毕对表）', 'PASS'],
    ['真值圆整秒逢0(19:20:10·过去·单现应warn)', '落款 date 现查原值 2026-10-21 19:20:10 +0800', 'WARN'],
    ['真值非逢0秒且未来窗内(19:24:37·容差内)', '落款 date 现查原值 2026-10-21 19:24:37 +0800', 'PASS'],
    ['正文死线未来时刻(非落款)', '施工死线 20:44·候毕报后验收（正文时刻非落款）', 'PASS'],
    ['正文历史引用(18:58:05)', '发毕对表 18:58:05 兜底闸抓获（引用历史时刻）', 'PASS'],
    ['FSD 模糊段(19:18 无秒)', '落款 date 原值 2026-10-21T11:18 段 / 19:18+0800', 'PASS'],
  ];
  let fail = 0;
  for (const [name, text, want] of cases) {
    const r = gate(text, nowStr);
    const got = r.blocks.length ? 'BLOCK' : r.warns.length ? 'WARN' : 'PASS';
    const ok = got === want;
    if (!ok) fail++;
    console.log(`${ok ? 'ok ' : 'FAIL'} [${name}] want=${want} got=${got}${r.blocks.length ? ' blocks=' + r.blocks.join('|') : ''}${r.warns.length ? ' warns=' + r.warns.join('|') : ''}`);
  }
  console.log(fail ? `\nSELFTEST FAIL (${fail})` : '\nSELFTEST ALL PASS');
  process.exit(fail ? 2 : 0);
}

// ---------- 入口 ----------

const args = process.argv.slice(2);
if (args.includes('--selftest')) selftest();

let text = '';
if (args.includes('--file')) {
  text = readFileSync(args[args.indexOf('--file') + 1], 'utf8');
} else {
  text = readFileSync(0, 'utf8');
}
const nowIdx = args.indexOf('--now');
const r = gate(text, nowIdx >= 0 ? args[nowIdx + 1] : undefined);

if (r.blocks.length) {
  console.error(`BLOCK — D-47 指纹命中（退回重写·落款=date 原值整串粘贴）:\n  ${r.blocks.join('\n  ')}`);
  process.exit(2);
}
if (r.warns.length) {
  console.error(`WARN — 疑似指纹留痕（放行·候回视）:\n  ${r.warns.join('\n  ')}`);
  process.exit(1);
}
console.log('PASS');

// ── 步④现役收官 probe（ST/小柯 2026-09-02，CTO 步④执行令）──
// 现役 8008（08c56a9+env 三值注入）。锁定收官版全量：
// 四名矩阵+scaffold 三连零命中+stream content token+max_tokens 双点+直连名复核+/v1/models 200。
// 现役进程零接触只读探；key 值零落。
const BASE = 'http://127.0.0.1:8008';
const PROMPT = '用一两句话解释什么是递归，并给出一个最简单的例子。';
const SCAFFOLD = ['Phase C', 'non-stream scaffold', 'scaffold', 'Scaffold', 'placeholder'];
const hits = (t: string) => SCAFFOLD.filter((m) => t.includes(m));
const sem = (t: string) => ['递归', 'recursion', '自己', '自身', '调用', '基例', '出口', '函数'].some((k) => t.toLowerCase().includes(k.toLowerCase()));

let pass = 0, fail = 0;
const bad: string[] = [];
function check(n: string, c: boolean, d = ''): void {
  if (c) { pass++; console.log(`  PASS ${n}`); } else { fail++; bad.push(n); console.log(`  FAIL ${n}${d ? ' :: ' + d : ''}`); }
}

async function nonStream(model: string, maxTokens: number): Promise<{ status: number; content: string | null; finish: string | null; reasoningLen: number; raw: any; ms: number }> {
  const t0 = Date.now();
  const res = await fetch(`${BASE}/v1/chat/completions`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'user', content: PROMPT }], max_tokens: maxTokens, stream: false }),
    signal: AbortSignal.timeout(180_000),
  });
  const text = await res.text();
  let json: any; try { json = JSON.parse(text); } catch { json = { raw: text.slice(0, 250) }; }
  const msg = json?.choices?.[0]?.message;
  return { status: res.status, content: msg?.content ?? null, finish: json?.choices?.[0]?.finish_reason ?? null, reasoningLen: String(msg?.reasoning_content ?? '').length, raw: json, ms: Date.now() - t0 };
}

async function streamProbe(model: string, maxTokens: number): Promise<{ status: number; deltas: string; finish: string | null }> {
  const res = await fetch(`${BASE}/v1/chat/completions`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'user', content: PROMPT }], max_tokens: maxTokens, stream: true }),
    signal: AbortSignal.timeout(180_000),
  });
  const text = await res.text();
  const parts: string[] = [];
  let finish: string | null = null;
  for (const line of text.split('\n')) {
    if (!line.startsWith('data: ') || line.includes('[DONE]')) continue;
    try {
      const j = JSON.parse(line.slice(6));
      const d = j.choices?.[0]?.delta?.content;
      if (typeof d === 'string' && d) parts.push(d);
      if (j.choices?.[0]?.finish_reason) finish = j.choices[0].finish_reason;
    } catch { /* skip */ }
  }
  return { status: res.status, deltas: parts.join(''), finish };
}

// S1 /v1/models 200 维持
{
  const res = await fetch(`${BASE}/v1/models`, { signal: AbortSignal.timeout(15_000) });
  const text = await res.text();
  let n = -1; try { n = JSON.parse(text)?.data?.length ?? -1; } catch { /* */ }
  check(`S1 /v1/models → 200 维持（len=${n}）`, res.status === 200 && n >= 0, `实际${res.status} ${text.slice(0, 100)}`);
}

// S2 max_tokens 双点（tmv-deepseek-v4-flash 代表起步链）
console.log('== S2 max_tokens 双点 ==');
{
  const small = await nonStream('tmv-deepseek-v4-flash', 16);
  console.log(`  [小预算16] status=${small.status} finish=${small.finish} contentLen=${small.content?.length ?? 0} reasoningLen=${small.reasoningLen}`);
  check('S2a 小预算16：reasoning 吃尽场景判据（content 空+finish=length 或 reasoning_len>0）', small.status === 200 && (!small.content || small.content.length === 0) && (small.finish === 'length' || small.reasoningLen > 0), `实际${JSON.stringify({ status: small.status, finish: small.finish, cl: small.content?.length, rl: small.reasoningLen })}`);
  const full = await nonStream('tmv-deepseek-v4-flash', 1024);
  const sh = full.content ? hits(full.content) : ['<no-content>'];
  console.log(`  [充分预算1024] status=${full.status} finish=${full.finish} contentLen=${full.content?.length ?? 0} scaffold=${JSON.stringify(sh)}`);
  check('S2b 充分预算1024：content 真 token（200+语义相关+非模板）', full.status === 200 && !!full.content && full.content.length > 10 && sem(full.content) && sh.length === 0, `实际${JSON.stringify({ status: full.status, finish: full.finish, len: full.content?.length, sh })}`);
  if (full.content) console.log(`    回文: ${JSON.stringify(full.content.slice(0, 200))}`);
}

// S3 四名矩阵+scaffold 三连零命中（充分预算）
console.log('== S3 四名矩阵 ==');
for (const model of ['deepseek-v4-flash', 'deepseek-chat', 'auto']) {
  const r = await nonStream(model, 1024);
  const sh = r.content ? hits(r.content) : ['<no-content>'];
  check(`S3 ${model} 真生成（200+content+语义+scaffold零命中）`, r.status === 200 && !!r.content && r.content.length > 10 && sem(r.content) && sh.length === 0, `status=${r.status} finish=${r.finish} len=${r.content?.length ?? 0} scaffold=${JSON.stringify(sh)} ${r.content ? '' : JSON.stringify(r.raw).slice(0, 150)}`);
  if (r.content) console.log(`    [${model}] 回文: ${JSON.stringify(r.content.slice(0, 150))}`);
}

// S4 直连名复核+stream 真 token
console.log('== S4 直连名+stream ==');
{
  const g = await nonStream('GLM-5.3-Flash', 1024);
  const sh = g.content ? hits(g.content) : ['<no-content>'];
  check('S4a GLM-5.3-Flash 直连名复核真生成', g.status === 200 && !!g.content && g.content.length > 10 && sh.length === 0, `status=${g.status} len=${g.content?.length ?? 0}`);
  const st = await streamProbe('tmv-deepseek-v4-flash', 1024);
  const stsh = st.deltas ? hits(st.deltas) : ['<empty>'];
  check('S4b stream delta.content 真 token（tmv 起步名）', st.status === 200 && st.deltas.length > 10 && sem(st.deltas) && stsh.length === 0, `status=${st.status} deltasLen=${st.deltas.length} finish=${st.finish} scaffold=${JSON.stringify(stsh)}`);
  if (st.deltas) console.log(`    流式回文: ${JSON.stringify(st.deltas.slice(0, 150))}`);
}

console.log(`\n== 步④现役收官 probe 汇总 == PASS ${pass} / FAIL ${fail}`);
if (bad.length) { console.log('失败项:'); bad.forEach((b) => console.log(' - ' + b)); }
process.exit(fail ? 1 : 0);

// ── A 案复验 probe（ST/小柯 2026-09-02，CTO 复验令 13:22Z）──
// 临时实例 18008（9135b5d + GLM_BASE_URL=paas/v4 + GLM_API_KEY）。
// 断言面：/v1/models 200（500 转 200）/ 非流式 content 语义相关非模板 /
// stream delta.content 真 token / tmv-* 四名内置别名映射 / auto 解析 / 直连名复核。
const BASE = 'http://127.0.0.1:18008';
const PROMPT = '用一两句话解释什么是递归，并给出一个最简单的例子。';
const SCAFFOLD = ['Phase C', 'non-stream scaffold', 'scaffold', 'Scaffold', 'placeholder'];
const hits = (t: string) => SCAFFOLD.filter((m) => t.includes(m));
const sem = (t: string) => ['递归', 'recursion', '自己', '自身', '调用', '基例', '出口', '函数'].some((k) => t.toLowerCase().includes(k.toLowerCase()));

let pass = 0, fail = 0;
const bad: string[] = [];
function check(n: string, c: boolean, d = ''): void {
  if (c) { pass++; console.log(`  PASS ${n}`); } else { fail++; bad.push(n); console.log(`  FAIL ${n}${d ? ' :: ' + d : ''}`); }
}

async function nonStream(model: string): Promise<{ status: number; content: string | null; finish: string | null; raw: any }> {
  const res = await fetch(`${BASE}/v1/chat/completions`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'user', content: PROMPT }], max_tokens: 500, stream: false }),
    signal: AbortSignal.timeout(120_000),
  });
  const text = await res.text();
  let json: any; try { json = JSON.parse(text); } catch { json = { raw: text.slice(0, 200) }; }
  return { status: res.status, content: json?.choices?.[0]?.message?.content ?? null, finish: json?.choices?.[0]?.finish_reason ?? null, raw: json };
}

async function streamProbe(model: string): Promise<{ status: number; deltas: string[]; finish: string | null }> {
  const res = await fetch(`${BASE}/v1/chat/completions`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'user', content: PROMPT }], max_tokens: 500, stream: true }),
    signal: AbortSignal.timeout(120_000),
  });
  const text = await res.text();
  const deltas: string[] = [];
  let finish: string | null = null;
  for (const line of text.split('\n')) {
    if (!line.startsWith('data: ') || line.includes('[DONE]')) continue;
    try {
      const j = JSON.parse(line.slice(6));
      const d = j.choices?.[0]?.delta?.content;
      if (typeof d === 'string' && d) deltas.push(d);
      if (j.choices?.[0]?.finish_reason) finish = j.choices[0].finish_reason;
    } catch { /* skip */ }
  }
  return { status: res.status, deltas, finish };
}

// ① /v1/models 200（500 转 200）
{
  const res = await fetch(`${BASE}/v1/models`, { signal: AbortSignal.timeout(15_000) });
  const text = await res.text();
  let n = -1; try { n = JSON.parse(text)?.data?.length ?? -1; } catch { /* */ }
  check(`R1 /v1/models → 200（原 500 转 200）`, res.status === 200, `实际${res.status} ${text.slice(0, 120)}`);
  check(`R1b /v1/models data 非空（len=${n}）`, n > 0);
}

// ② 非流式 content：四名+直连名（语义相关+非 scaffold）
const MODELS = ['tmv-deepseek-v4-flash', 'deepseek-v4-flash', 'deepseek-chat', 'auto', 'GLM-5.3-Flash'];
console.log('== 非流式 content 断言 ==');
for (const model of MODELS) {
  const r = await nonStream(model);
  const sh = r.content ? hits(r.content) : ['<no-content>'];
  const ok = r.status === 200 && !!r.content && r.content.length > 10 && sem(r.content) && sh.length === 0;
  check(`R2 ${model} content 真生成（200+语义相关+非模板）`, ok, `status=${r.status} len=${r.content?.length ?? 0} finish=${r.finish} scaffold=${JSON.stringify(sh)} ${r.content ? '' : JSON.stringify(r.raw).slice(0, 150)}`);
  if (r.content) console.log(`    回文: ${JSON.stringify(r.content.slice(0, 180))}`);
  else if (r.finish === 'length') console.log(`    [reasoning 预算] finish=length content 空——FD 钉死实证面复现`);
}

// ③ stream delta.content 真 token
console.log('== stream 真 token 断言 ==');
for (const model of ['tmv-deepseek-v4-flash', 'GLM-5.3-Flash']) {
  const r = await streamProbe(model);
  const joined = r.deltas.join('');
  const sh = joined ? hits(joined) : ['<empty>'];
  check(`R3 ${model} stream delta.content 真出 token`, r.status === 200 && joined.length > 10 && sem(joined) && sh.length === 0, `status=${r.status} deltas=${r.deltas.length} joinedLen=${joined.length} finish=${r.finish} scaffold=${JSON.stringify(sh)}`);
  if (joined) console.log(`    流式回文: ${JSON.stringify(joined.slice(0, 180))}`);
}

console.log(`\n== A 案复验汇总 == PASS ${pass} / FAIL ${fail}`);
if (bad.length) { console.log('失败项:'); bad.forEach((b) => console.log(' - ' + b)); }
process.exit(fail ? 1 : 0);

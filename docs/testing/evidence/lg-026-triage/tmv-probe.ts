// ── tmv-* 链官方 probe（ST/小柯 2026-09-02，CTO probe 令）──
// 8008（TriStaciss）直探：models 面/completions 真调用（content 为准，200 不作数）。
// 只读纪律：零进程接触。400/错误原文随读数报。
const BASE = 'http://127.0.0.1:8008';

async function j(method: string, path: string, body?: unknown): Promise<{ status: number; json: any; ms: number }> {
  const t0 = Date.now();
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(120_000),
  });
  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch { json = { raw: text.slice(0, 300) }; }
  return { status: res.status, json, ms: Date.now() - t0 };
}

function head(t: string): void { console.log(`\n── ${t} ──`); }

// ① models 面
head('① /v1/models 与 /api/models/available');
const m1 = await j('GET', '/v1/models');
console.log(`  /v1/models → ${m1.status} data.len=${m1.json?.data?.length ?? '?'} ${JSON.stringify(m1.json).slice(0, 200)}`);
const m2 = await j('GET', '/api/models/available').catch((e) => ({ status: 0, json: { err: String(e).slice(0, 100) }, ms: 0 }));
console.log(`  /api/models/available → ${m2.status} ${JSON.stringify(m2.json).slice(0, 400)}`);

// ② completions 真调用矩阵：tmv 起步名/官方正典名/auto
head('② /v1/chat/completions 真调用（content 为准）');
const MODELS = ['tmv-deepseek-v4-flash', 'deepseek-v4-flash', 'deepseek-chat', 'auto'];
for (const model of MODELS) {
  try {
    const r = await j('POST', '/v1/chat/completions', {
      model,
      messages: [{ role: 'user', content: '只回复两个字母：ok' }],
      max_tokens: 20,
      stream: false,
    });
    const content = r.json?.choices?.[0]?.message?.content;
    console.log(`  model=${model} → ${r.status} (${r.ms}ms) content=${JSON.stringify(content)} ${content ? '✅ 真出 content' : '❌ 无 content'} ${content ? '' : JSON.stringify(r.json).slice(0, 250)}`);
  } catch (e) {
    console.log(`  model=${model} → 异常: ${String(e).slice(0, 150)}`);
  }
}

// ③ providers 注册面勘隐（models 空的原因）
head('③ providers 配置面（勘隐）');
for (const p of ['/api/config/providers', '/api/config/active-provider', '/api/health']) {
  const r = await j('GET', p).catch((e) => ({ status: 0, json: { err: String(e).slice(0, 80) }, ms: 0 }));
  console.log(`  ${p} → ${r.status} ${JSON.stringify(r.json).slice(0, 350)}`);
}

console.log('\n== tmv probe 完毕（读数回 CTO）==');

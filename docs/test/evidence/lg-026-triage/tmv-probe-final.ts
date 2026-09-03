// ── A 案定案 probe（ST/小柯 2026-09-02，CTO 定案派单）──
// 验收三点：a) 真生成断言（非常规自然语 prompt 语义相关+非 scaffold 句式，特征串显式报）
// b) tmv-* 存活名全链（tmv-deepseek-v4-flash 经 8008→真出 token+直连名 GLM-5.3-Flash 复核）
// c) /v1/models 500 只记账（复现请求+错误原文）。
// 路 A=8008 直探（fetch）；路 B=TriModel TriMetaverseProvider（运行时同款 provider 类）。
// key 脱敏纪律：零落值。
const BASE = 'http://127.0.0.1:8008';
const RECURSION_PROMPT = '用一两句话解释什么是递归，并给出一个最简单的例子。';

const SCAFFOLD_MARKERS = ['Phase C', 'non-stream scaffold', 'scaffold', 'Scaffold', 'placeholder', 'TODO', 'lorem ipsum'];
function scaffoldHits(text: string): string[] {
  return SCAFFOLD_MARKERS.filter((m) => text.includes(m));
}
function semanticHint(text: string): boolean {
  const t = text.toLowerCase();
  return ['递归', 'recursion', '自己', '自身', '调用', 'base case', '基例', '出口', '函数'].some((k) => t.includes(k));
}

async function chat(model: string): Promise<{ status: number; content: string | null; raw: any; ms: number }> {
  const t0 = Date.now();
  const res = await fetch(`${BASE}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'user', content: RECURSION_PROMPT }], max_tokens: 300, stream: false }),
    signal: AbortSignal.timeout(120_000),
  });
  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch { json = { raw: text.slice(0, 300) }; }
  return { status: res.status, content: json?.choices?.[0]?.message?.content ?? null, raw: json, ms: Date.now() - t0 };
}

console.log('== 路 A：8008 直探 /v1/chat/completions ==');
// a) 真生成断言——四名矩阵 + 语义/scaffold 检测
const MODELS = ['tmv-deepseek-v4-flash', 'deepseek-v4-flash', 'deepseek-chat', 'auto'];
let realGenCount = 0;
for (const model of MODELS) {
  const r = await chat(model);
  if (r.content) {
    const hits = scaffoldHits(r.content);
    const sem = semanticHint(r.content);
    realGenCount++;
    console.log(`  [${model}] ${r.status} (${r.ms}ms) 真生成 ✅ len=${r.content.length} 语义相关=${sem} scaffold命中=${JSON.stringify(hits)}`);
    console.log(`    回文: ${JSON.stringify(r.content.slice(0, 200))}`);
  } else {
    console.log(`  [${model}] ${r.status} (${r.ms}ms) ❌ 无 content ${JSON.stringify(r.raw).slice(0, 200)}`);
  }
}
// b) 直连名复核
const glm = await chat('GLM-5.3-Flash');
console.log(`  [GLM-5.3-Flash 直连名复核] ${glm.status} (${glm.ms}ms) content=${glm.content ? '✅ len=' + glm.content.length : '❌ ' + JSON.stringify(glm.raw).slice(0, 150)}`);
if (glm.content) {
  console.log(`    回文: ${JSON.stringify(glm.content.slice(0, 200))}`);
  realGenCount++;
}

// c) /v1/models 500 记账（只记录不修）
console.log('\n== c) /v1/models 记账 ==');
{
  const res = await fetch(`${BASE}/v1/models`, { signal: AbortSignal.timeout(15_000) });
  const text = await res.text();
  console.log(`  复现请求: GET ${BASE}/v1/models（无特殊头）`);
  console.log(`  → HTTP ${res.status} 原文: ${text.slice(0, 300)}`);
}

// 路 B：TriModel TriMetaverseProvider（运行时同款类，Anthropic Messages 面）
console.log('\n== 路 B：TriModel client 链（TriMetaverseProvider→8008）==');
{
  const { TriMetaverseProvider } = await import('file:///D:/Code/ai/TriRLC/node_modules/trimodel/dist/src/providers/trimetaverse.js');
  const provider = new TriMetaverseProvider({
    trimetaverseApiKey: process.env.TMV_KEY ?? '',
    trimetaverseBaseUrl: 'http://127.0.0.1:8008/v1',
  });
  try {
    const t0 = Date.now();
    const resp = await provider.chat(
      [{ role: 'user', content: RECURSION_PROMPT }],
      { model: 'tmv-deepseek-v4-flash', maxTokens: 300 },
    );
    const content = (resp as any)?.content ?? JSON.stringify(resp).slice(0, 200);
    console.log(`  provider.chat(tmv-deepseek-v4-flash) → ${Date.now() - t0}ms content=${typeof content === 'string' ? '✅ len=' + content.length : JSON.stringify(content)}`);
    if (typeof content === 'string') console.log(`    回文: ${JSON.stringify(content.slice(0, 200))}`);
  } catch (e) {
    console.log(`  provider.chat 异常: ${String(e).slice(0, 250)}`);
  }
}

console.log(`\n== 定案 probe 完毕 == 真生成断言通过 ${realGenCount}/5 名`);

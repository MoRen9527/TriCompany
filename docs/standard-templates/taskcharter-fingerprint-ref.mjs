// 规范 v1.1 指纹·独立第二实现（JS·与 fpfinal.py 无共享代码）——用于跨语言对表
import { createHash } from 'node:crypto';
const KEYS = ['content_sha256_16', 'commit'];
const BACKSLASH = String.fromCharCode(92);
function findKey(line, key, quoted) {
  const pat = quoted ? '"' + key + '"' : key;
  const a = line.indexOf(pat); if (a < 0) return null;
  if (!quoted && a > 0 && /[A-Za-z0-9_]/.test(line[a - 1])) return null;
  const c = line.indexOf(':', a + pat.length); if (c < 0) return null;
  const o = line.indexOf('"', c + 1); if (o < 0) return null;
  let p = o + 1;
  while (p < line.length) { if (line[p] === BACKSLASH) { p += 2; continue; } if (line[p] === '"') break; p++; }
  if (p >= line.length) return null;
  return [o, p];
}
function blankLine(line, quoted) {
  let hits = 0;
  for (const key of KEYS) { const r = findKey(line, key, quoted); if (!r) continue; line = line.slice(0, r[0] + 1) + line.slice(r[1]); hits++; }
  return [line, hits];
}
function blankJson(text) {
  const a = text.indexOf('"cao_approval"'); if (a < 0) return [text, 0];
  const head = text.slice(0, a), lines = text.slice(a).split('\n'); let n = 0;
  for (let i = 0; i < lines.length; i++) { const [l, h] = blankLine(lines[i], true); lines[i] = l; n += h; }
  return [head + lines.join('\n'), n];
}
function blankYaml(text) {
  const lines = text.split('\n'); let n = 0;
  const i = lines.findIndex(l => l.trimEnd().endsWith('cao_approval:')); if (i < 0) return [text, 0];
  const ind = lines[i].length - lines[i].trimStart().length;
  for (let k = i + 1; k < lines.length; k++) {
    const l2 = lines[k]; if (l2.trim() === '') continue;
    if (l2.trim() === '---' || (l2.length - l2.trimStart().length) <= ind) break;
    const [l, h] = blankLine(lines[k], false); lines[k] = l; n += h;
  }
  return [lines.join('\n'), n];
}
export function fingerprintBytes(buf) {
  let text;
  // ⚠ ignoreBOM:true 名字反直觉：true=「不把 BOM 当标记剥掉」=U+FEFF 保留为字符（规范 v1.1 口径）。
  //   JS/TS 的 TextDecoder 默认剥 BOM、Python bytes.decode('utf-8') 默认保留——不加此项两语言对带 BOM 件指纹不同（跨语言对表 V04 实测抓出）。
  try { text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(buf); }   // 严格：非法序列抛错
  catch { return [createHash('sha256').update(buf).digest('hex').slice(0, 16), -1]; }
  const isYaml = text.split('\n').slice(0, 200).some(l => l.trimEnd().endsWith('cao_approval:'));
  let [s, n] = isYaml ? blankYaml(text) : blankJson(text);
  s = s.replace(/\r\n/g, '\n');
  return [createHash('sha256').update(Buffer.from(s, 'utf8')).digest('hex').slice(0, 16), n];
}

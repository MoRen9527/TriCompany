# STE 验证卷 · TriRLC D' 段 2a --acp 零 daemon 依赖面（FSD 交接验证）· 2026-10-20

- sourceOfTruth: 本卷（TriCompany/docs/testing/trilc-dp-seg2a-acp-verify-20261020.md）
- syncMode: static（验证读数卷·D-15 留痕）
- lastSyncedAt: 2026-10-20 20:09:28+08（date 现查原值）
- 执行席: STE 小柯（m-ste）；令源=FSD 交接面（m-fsd·20:04:50Z 落款·「候您验证排工」）；对象=TriRLC 5586fb3（D' 段 2·cli.ts --acp early-return+startChatTui 提炼+t9）·现顶 01ccd41（5586fb3+registry 收口 docs 笔·代码面同）

## 一、判定

**PASS**（三分法·CTO 确认链）——四项读数独立复跑全对平+触面走查毕+零阻塞性缺陷；一非阻塞观察项如实录（§四）。本席不独立放行·判定呈 CTO。

## 二、独立复跑读数（与 FSD 自测面逐项对表）

| 项 | FSD 报 | STE 独立复跑 | 判 |
| --- | --- | --- | --- |
| tsc --noEmit | 0 错 | rc=0 零输出 | ✓ |
| 全量 | 758/758 零回归 | **npm test=758/758·rc=0·not ok=0·suites 137** | ✓ 精确对平 |
| ACP 案组 | 9/9 | 定点 tui-acp.test.ts=9/9（t9=ok 9） | ✓ |
| t9 三断言 | parseArgs 契约 | 源码 L318-322：--acp→true/缺省→false（daemon 面不动）/与 --resume 并存同解析 | ✓ 逐条对平 |
| 代码态 | dev 顶 5586fb3 | 顶 01ccd41（=5586fb3+docs 收口笔）·dev·porcelain 净 | ✓ |

- 触面走查（5586fb3 src/cli.ts diff +22/-2 读毕）：early-return 形态=acp 分支先手 `startChatTui(agent,[],undefined,true)`·daemon ensure 链（Step1-4/notifications/Step5）物理跳过 ✓；startChatTui 提炼两面共享（daemon 面尾部 Step6 复用同函数）✓；useAcpSession 生命周期自管（list→resume/new→close）与 FSD 报口径一致 ✓。
- 河源真 dsh 四断言与隔离环境清理=施工面自证（FSD 卷锚 66f06d20/CRED-REMOVED）——本席不重跑真模型链（需凭据面·D-46 域）；live 探针 acp-lt-probe.mts 不在 npm test glob ✓（ Design 如实·零误入全量）。

## 三、跑法分叉假读数勘验记录（防复发）

- 首轮 bash 直跑 `node --import tsx --test test/**/*.test.ts` 得 **235**（≠758）——根因=Git Bash 无 globstar 时 `**` 退化单层展开·bash 展开后的文件子集传给 node（部分集假读数）；**npm test 正形**（npm script 交 node 自解析 glob 递归全展开）复跑=758 对平。
- 教训：TriRLC 全量验证一律走 `npm test` 正形·禁 bash 直跑带 `**` glob 的命令串（假读数家族新变体·跑法层）。

## 四、非阻塞观察项（如实录·候 CTO 面）

- early-return 靠 `startChatTui` 尾部 `process.exit` 语义实现 return（FSD 注释知情设计）——若未来该函数内部路径变更不再必然 exit·acp 分支会 fall-through 至 daemon ensure 链（意外走 daemon 面）。建议：`if (acp) { await startChatTui(...); return; }` 一行显式 return 加固。非缺陷实证·形态债级。
- 债 5（session/request_permission 入站请求未实现）FSD 已入册候窗——不在本段验证判据内·知悉。

## 五、使用依据

- FSD 交接面（20:04:50Z·四断言+门禁读数+债 5）；TriRLC 活体（01ccd41 三查+tsc+全量两轮+定点 9/9+diff 走查·log /tmp/trlc-seg2a-verify*.log 会话临时位·读数以本卷为锚）
- 纪律：FSD 自测≠STE 验证（独立复跑）/假读数家族警觉（235 假读数现场抓获即勘）/时刻引用先 date 现查/先写后报/判定不独立放行（CTO 确认链）

## 落款

- 验证窗 20:05-20:09+08（现查锚 20:05:51/20:09:28）；本卷写毕 20:09:28+08；commit 时点见 commit 笔。

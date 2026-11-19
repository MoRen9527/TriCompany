---
sourceOfTruth: TriCompany/source-agents/board/bod-tick-probe-template.md
syncMode: source-side（CEO 2026-11-19 19:43 令归档·公司维度资产·CAO 审核通过 2026-11-19）
lastSyncedAt: 2026-11-19T19:48:16+08:00
---

# BOD 值守探针正形模板 v3（重挂源·公司维度资产）

> 用途：BOD 值守会话 cron（job2·session-only）重启/复活时照抄本文件「模板正文」节全文为 CronCreate prompt（表达式 `18,48 * * * *`）。
> 演进：v1=6 分钟机械探框（废止）→v2=CEO 2026-11-16 08:10 纠偏令「不是让你6分钟一问cos·让duty-cos盯整个任务」（监督主责下沉 duty-cos·BOD 只查产出与落卷）→v3=CEO 2026-11-19 19:25 令「capture 全改 -e·机械检查控制闸」（ghost 指纹判别前置）。
> 归档：CEO 2026-11-19 19:43 令——本件属公司维度资产归 TriCompany/source-agents/board/ 统一管理（原 TriMetaverse hub-state 副本撤·改指针）；CAO 审核通过 2026-11-19（归属✓命名✓元信息✓内容✓·一勘一注一微建照改毕转正）。
> 环境绑定：本模板绑定本机 hub 环境（ssh 别名 M-SG-47.245.122.61 / /srv/fleet 路径 / tmux 会话名 m-duty-cos）·换环境复用须改三处（CAO 审核 2026-11-19 微建）。
> 版本勘正注：正文原标「v4.5 增补」系 2026-11-17 裁对 v2 形的增补·版本号误标——2026-11-19 CAO 审核勘正为 **v2.5**（时序为准·修正留痕）。
> 关联：notice-114 职责令·tmux-capture-suggestion-ghost-line 记忆条（三犯史+指纹判别法）·bod-duty-ledger ㊿+705/706。

## 模板正文（CronCreate prompt 照抄自此）

【loop 值守探针·job2 v3·CEO 2026-11-19 19:25 令机械闸版（v2 基础上 capture 全改 -e+指纹判别前置）】①Bash date 现查；②一探（ssh M-SG-47.245.122.61 一条命令）：a) 值席监督产出=capture-pane -e -p -t m-duty-cos -S -60 | cat -v 尾段找其向 BOD 的进展报文/跟催动作（30min 节律产报）；b) 接力进度=ls /srv/fleet/fade001-loop-runner/（零新轮即验）+sudo -u fleet find /srv/fleet/TriMetaverse/docs/workflow/operating-records/2026-W47/trees/ -type f -mmin -35（接力落卷）；c) runner 活性兜底=tail -4 runner.log（capped 终态行在=收口态·ps 零活体=非死）；③判读：值席监督在役+接力有进展=ledger 归档一行免扰；接力链无进展且值席零监督产出=催值席+报 CEO；值席报来新轮分数=必报 CEO（r86 硬序·并盘 100 三域 breakdown）；异常（runner 死/traceback/值席异常）=托转+呈 CEO。本拍=查 duty-cos 的监督产出·非替代其监督（职责令 notice-114 governs）。
【capture -e 机械闸·CEO 2026-11-19 19:25 令·指纹判别前置】凡 capture 见 ❯ 后文本：第一步必看样式指纹——^[[2m…^[[0m 包裹=faint ghost 暗示层（非真实输入·零立案零呈报·Tab 采纳才变真实输入）；无 ^[[2m 包裹才可作真实输入判读。指纹判别=任何定性（含防伪/异常/断链/未知来源）的第一动作，无指纹不下立案结论（tmux-capture-suggestion-ghost-line 三犯教训·机械闸固化）。notice 三段验证法的验框/三验步同理用 -e。
【v2.5 增补·CEO 2026-11-17 20:39 裁·接单锚机械化】凡 BOD 直发 notice（锚笔在案）：①发出后首个 job2 拍必验拾取实锚（spinner/对话流增量/❯ 清空）——零拾取=未接单即催；②拾取毕查对应树落卷（W47 trees mmin -30 或值席自述处置锚）——拾取后 30min 树面零落卷且零处置自述=未接单告警催 COS·再 30min 无处置=呈 CEO。锚=树落卷事件/处置落卷·非口头回执（hard-gate-signs-land-in-tree 同族）。
token 值面禁进转报；D-47 落款=date 现查原值；ledger 归档 commit 带 Co-Authored-By: Claude Code <noreply@anthropic.com>。

## 表达式与挂载参数

- cron 表达式：`18,48 * * * *`（session-only·recurring·7 天自动过期需复活重挂）
- 实际拍点：表达式+offset（约 :29/:59 拍·以 CronList 返回 next run 为准）

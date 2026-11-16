# TriCompany 测试状态登记（test-state）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/registry/test-state.md
- syncMode: source-only
- lastSyncedAt: 2026-09-11（LG-035 首批钉入；衔接 STE 面既有待初始化标记）
- 供料源: COS 转达 STE/CTO 线读数（2026-09-11 21:35+0800），CGR 钉入

## 1. 当前测试基线

runtime 验证族+LG-035 门禁报告族落 docs/testing/（df52abe 等，CAO 复核附注 2026-09-11 追平）；source-agents 渲染验证 127/127+5/5+employee_onboard 33/33+73/73 含 e2e 零写入 8 项（ADE-B 存档）。

**FADE-001 W2 联审面基线（STE 供料 2026-11-16·CTO 门禁收口 2026-11-16 本席独立复跑同值·收口卷=TMV W47 树 fade001-loop-joint-review-W2/cto-bfix-acceptance-20261116.md）**：联审三件白盒 test_joint_review_trigger 7 案+test_joint_review_recycle 14 案=21/21（TC 65d4ee1）+score_engine 26/26（22 基线+C 族钉案 13f7bcd+B 族 loop 轮增补 4 案·STE 修件窗 2026-11-16）·cognition 全量 unittest discover **266 OK**（262@13f7bcd 面+4 B 族随件·grep 机械清点同值；pytest 口径 269=含 3 非 TestCase 收集面·口径差双真在档）+validation 族 438/5/1 基线零漂（变更面机械直证·W2/B 族触面零交集）。读数链锚=本席 r112② 复验卷（TMV 331872f）+核验门八项核验卷（TMV f22a9f258）+B 族修件毕报（TMV W47 树）。code-state 侧 W2 施工面行已随收口窗立行（CTO·CodeRegistry owner·2026-11-16·65d4ee1/13f7bcd/fe7544f 三锚一行承载）。

## 2. 门禁状态

LG-035 spec/报告族 v0.1→v0.5 在册；STE 门禁补课=jsdom→E1-E8 升级中。

## 3. 已知缺口

1. **docs/test/ 回归目录（LG-035 报告族误落旧名）**：八件套标准名=docs/testing/（2026-09-11 线②已钉），本目录系回归——已处置（LG-035 随窗件，CTO 2026-09-11 21:5x）：七件 git mv 并入 docs/testing/+互引改写毕，本缺口销账。
2. source-agents 发布面 7 件活面修正（Wave 0 C 面）部分批次在途。
3. render debt 零存量的有效性随批维护。

## 4. 最近验证时点

2026-09-11 20:26+0800（TriMMC/模型名双线门禁报告 0d30621）。

> 登记纪律：本件系工作型登记层（经确认事实，禁记临时猜测）；更新守 owner 提交纪律（STE 供料+CTO 门禁收口）；D-04 时刻纪律适用。

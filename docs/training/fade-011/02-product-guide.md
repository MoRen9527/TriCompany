<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-011/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-011 产品版——它能干什么、不能干什么、出了事找谁

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-011/02-product-guide.md
- syncMode: source-only
- lastSyncedAt: 2026-11-10

读者：产品/管理/运营视角的协作者。目标是建立**能力边界感**——什么能托付给它、什么必须人守、裁决口径在哪。

---

## 一、产品定位一句话

> FADE-011 = **关键文件变更的自动质检与留痕系统**。
> 它解决的问题：关键文件（岗位定义/技术规范/发布清单）被改动后，「有没有人检查过、
> 检查结果如何」这件事不再依赖人的记忆和自觉——系统自动开工单、自动检查、自动归档。

## 二、能力清单（能干什么）

| 能力 | 形态 | 产品价值 |
|---|---|---|
| 自动触发 | 指纹变化即开工单（30s 轮询） | 变更检查零延迟、零遗忘——不靠人记得 |
| 全自动五节点链 | qualify→plan→DCE→score→close 全程序化 | 单 run 十段全自动通（Phase 2 目标已落地形态） |
| 全量留痕 | 每 run 树=plan+五节点报告+artifacts | 事后可审计可追责——「谁动的、查没查、结论是什么」三问必答 |
| 幂等防抖 | 指纹未变不开工·首扫只建基线 | 不白跑不重复——机器重启不炸 |
| 安全门 | dry-run 默认·写入须显式开关 | 不会「好心办坏事」自动改文件 |
| 每日审计 | fade_instance_audit.py 全实例读数 | 触发量/链成率/异常每日可见，其他实例向它看齐 |

## 三、边界清单（不能干什么·必须人守什么）

1. **不会自动改你的文件**：EW 的写入必须 `--auto-sync` 显式开启，且 project-docs 类**永不自动写**
   （spec §2.4 安全门+代码常量硬编码）。它只检查、只建议、只留痕。
2. **手动运行不开放给席位**：手动跑 fade011=CEO/人工通道（CEO 2026-11-05 裁令）。席位的正确姿势=等它自动跑。
3. **不替代发布管线**：它检测到的变更若需同步发布面，走 FADE-002 管线；011 只负责「发现+检查+留痕」。
4. **敏感值面零接触**：审计与报告全部零 token 值面（D-46 纪律同样约束本实例产物）。

## 四、现役形态与运维面

- **承载面**：M 面本地域 daemon（TriMLC@8713）——Phase 2 排期单已勘正蓝图旧名 TriLC→现势 TriMLC
  （`TriMetaverse/docs/execution/fade-011-automation-phase2-plan-20261103.md` §二）。
- **运行通道**：每日自动轮（daily-sweep 通道·CEO 保自动裁）；手工排障窗属例外，须 CEO 明示。
- **工程进度坐标**：Phase 2「单 run 十段全自动通」在役（S1-S5 顺序工序制·排窗已废·完成即报）；
  Phase 3-6 显式未启动。
- **裁决口径速查**：
  - 保自动 vs 手动 → CEO 裁（memory 在案）
  - run 树能不能删 → **禁单侧盘面删除**（DB checkpoint 与盘面一致性优先·CTO 裁，见事故卷）
  - 排障产物去留 → CTO 裁（先例：{week} 字面目录候裁保留）

## 五、失败案例是最好的产品说明书（两起在案事故）

1. **{week} 字面目录插曲（2026-11-04）**：排障窗期间旧代码实例触发，路径模板 `{week}` 没被展开成
   真实周串，两张工单落进了字面名目录。CTO 裁：**原地保留**——搬移/删除会造成 DB checkpoint
   与盘面不一致，一致性优先。产品教训：**发布代码必须连带重建运行时副本**（dist 未重建=新逻辑没上车）。
   全程记录：`fade011-ew-runs/README-POINTER.md`。
2. **值席违规单侧删除 run 树（2026-10-23 事故卷）**：值席单侧删除了两张 run 树的盘面文件，
   造成 DB 记录与磁盘不一致。产品教训：**自动系统的档案是 DB+盘双记账，任何一侧不得单动手**——
   「删个文件夹」这种看似无害的操作在双记账系统里是破坏性操作。事故卷全文：
   `operating-records/2026-W45/trees/fade011-ew-runs/事故卷-值席违规单侧删除两run树-20261023.md`。

## 六、度量与评估口径

- 每日审计读数（fade_instance_audit.py）：触发量 / 五节点链成率 / verdict 分布 / 白跑与异常——
  fade011 event-watch 系为主 + registry 在册实例全覆盖。
- 质量基线：彩排 S1 评分 14.5/15 在卷（audit 脚本注释引）；开跑后基线数据收集窗中，
  两轮后升实质结论（CHO 评估注在案）。

## 七、真源指针（教程不替代真源）

- Phase 2 排期单：`TriMetaverse/docs/execution/fade-011-automation-phase2-plan-20261103.md`
- CEO 裁令：`TriMetaverse/docs/memory/fade011-manual-run-ceo-channel-only.md`
- 协议安全门：`TriCompany/docs/engineering/fade-protocol-spec.md` §2.4 / §8.6
- 代码级细节：[03 代码地图](03-code-map.md)；设计纵深：[04 深度研究](04-deep-research.md)

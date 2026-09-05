<!-- GOVERNANCE: 本教程真源在 TriCompany/docs/training/fade-002/，由 RDT 维护；讲解事实以文中标注的真源文件为准，冲突时回真源不回教程。 -->

# FADE-002 小白版——真源改了，副本怎么自动跟平？

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/fade-002/01-beginner-guide.md
- syncMode: source-only
- lastSyncedAt: 2026-09-05

读者：完全零基础的新人。不需要懂 FADE 协议，不需要读过源码。
目标：30 分钟后，你能说出这套东西是干什么的、为什么需要它，并亲手跑通一条命令。

---

## 一、一句话说清这是什么

> TriCompany 公司里，"正本"文件放在源侧仓库，各处要用的"复印件"放在发布侧仓库。
> **FADE-002 就是一台自动对照正本、更新复印件的机器——每次动手前先给你看它要改什么，
> 每改一笔都开一张小票存档。**

就这么简单。后面所有名词，都是给这句话的每个词补细节。

## 二、为什么需要它（先看手工复制的三个坑）

TriCompany 的文件分两层：

- **源侧（真源层）**：`TriCompany/` 仓库。员工的岗位定义、协议文档、项目真源文档都住这里。这里是"唯一说了算"的地方。
- **发布侧（消费层）**：`TriMetaverse/` 仓库。运行时真正去读的文件在这里——比如 `TriMetaverse/CLAUDE.md`、`.claude/agents/` 下的员工定义、`.claude/hub/` 下的会话文件。

源侧改了一条规则，发布侧必须跟着改，否则运行时用的还是旧规则。让 AI 员工或人"手动复制"会踩三个坑：

1. **忘抄**：源侧改了 3 个文件，只抄了 2 个，第三个悄悄过期。
2. **抄错**：抄的时候手一抖，多一个空格少一行，没人发现。
3. **说不清**：三天后问"这个文件为什么变了、谁改的、照哪份改的"——答不上来。

坑 1 和 2 叫**漂移**（正本和复印件长得不一样了），坑 3 叫**不可审计**（变化没有留痕）。
FADE-002 的全部设计，就是针对这三个坑。

## 三、只需要先懂三个词

**1. 真源（source of truth）**
唯一说了算的那份文件。规则是：要改，只改真源；复印件永远"照着真源抄"。
你在 `TriMetaverse/CLAUDE.md` 第一行能看到一行声明："本文件真源在
TriCompany/docs/project-sources/……禁直接修改项目侧副本"——这就是真源规则贴在复印件上的封条。

**2. dry-run（先看后动）**
这台机器默认**只看不改**：跑一次，它会告诉你"如果让我执行，我会新建/更新哪几个文件"，
但一个字节都不动。你确认没问题，加一个"执行"参数它才真写。
类比：打印店先给你看预览，你点头才打印。

**3. manifest（清单）**
一张登记表（JSON 文件），写着"哪个真源 → 抄到哪个复印件"。机器不猜、不全盘扫描，
只照清单办事。清单本身就是可审计的：谁加的条目、谁批准的，都在版本管理里。
FADE-002 的清单在 `TriCompany/.github/manifests/project-source-doc-sync-manifest.json`，
目前登记了 4 个条目（2 份"摘要类" + 2 份"逐字节复制类"；条目数会随发布扩容变化，以你实跑为准）。

## 四、一个比喻贯穿全程

把这套系统想成一家用"母版-复印件"管理的打印店：

- **真源** = 母版文件（只此一份，改它才作数）
- **发布面** = 各门店领走的复印件
- **manifest** = 配送单（哪家门店领哪份、什么方式领）
- **CLI（`source_publish_check`）** = 配送员：先按配送单逐项核对（dry-run），向你报"哪份需要换新"；你说"执行"（execute）它才换
- **envelope 报告** = 每次配送的小票：几项核对、几项换新、几项没问题，逐项有前后"指纹"（hash），想赖账都赖不掉
- **保护链** = 配送员的禁区清单：员工隐私文件（soul/memory 等五件套）、绑定档案（binding profiles）永远不碰，清单写得再大也不碰

## 五、活体证据：你正在读的这段话从哪来

如果你是在岗员工席位，打开自己的会话配置（比如 `TriMetaverse/.claude/hub/rd-trainer.session.md`），
看最后一行会有一句："本文件由统一发布管线渲染生成（--host=claude-session），禁人工编辑；
会话面内容修订走源侧 session-body 合同。"

这份会话文件**不是任何人手写的**——它是真源（TriCompany 源侧的合成件+会话补充片段）
经过 FADE-002 管线**渲染**出来的。2026-09-04/05 深夜的"全员工 13 席会话文件"就是这条管线
一次性渲染落地的（那一晚是大批量启用，管线本身更早建成，演进故事见[深度研究版](04-deep-research.md)）。
也就是说：这套管线不只管文档，连"你为什么这样说话"的配置本身，都是它发布的。

一个现成的对照实验（30 秒）：
1. 打开 `TriMetaverse/CLAUDE.md` 第 1 行 → 看到封条声明；
2. 打开它的真源 `TriCompany/docs/project-sources/trimetaverse-claude-md.md` → 内容一致；
3. 这就是"in_sync（已同步）"——2026-09-05 上午实测，两者的内容指纹（SHA-256）完全相同。

## 六、最小体验：亲手跑通一条命令

前置：能访问 `D:/Code/ai/TriCompany/`（源侧仓库根）。在 **TriCompany 根目录**执行：

```
python -m runtime.cognition.source_publish_check --project-docs
```

这是 2026-09-05 上午的一次真实输出（节选，你跑到的 hash 值会不同，结构相同）：

```json
{
  "protocol": "ade-report",
  "version": "1.0",
  "scope": "project-docs",
  "run_id": "ade-project-docs-20260905T035648586217",
  "mode": "dry-run",
  "status": "partial",
  "summary": { "total": 4, "changed": 0, "skipped": 4, "errors": 0 },
  "items": [
    { "action": "in_sync", "scope_key": "tricompany-central-summary", ... },
    { "action": "requires_candidate", "scope_key": "dynamic-task-tree-protocol-summary", ... },
    { "action": "in_sync", "entry_id": "trimetaverse-claude-md-copy", ... }
  ]
}
```

逐行读懂它（这一张就是"小票"）：

| 字段 | 白话 |
| --- | --- |
| `mode: dry-run` | 这次只看没动 |
| `status: partial` | 整体"部分就绪"——不是错误，见下 |
| `summary` | 4 项检查、0 项改动、0 项错误 |
| `action: in_sync` | 这份复印件和母版一致，不用动 |
| `action: requires_candidate` | 这份是"摘要类"文件，机器**故意**不自动写——摘要得由规划者（小贾）拟好、联审通过后作为"候选"喂给机器，机器只负责校验和抄写。等候选=正常营业状态，不是故障 |

注意这台机器的克制：摘要类文件它**永远不会自己编内容**（这是写死在代码和 manifest
声明里的规矩），宁可一直报"等候选"。确定性机器不做语义创作——这是整个 FADE 体系的底线。

**验证**：你跑完命令、退出码是 0、能对照上表说出 status 和任一 item 的含义——小白版毕业。

## 七、三个最常见的新人疑问

**Q1：为什么不干脆手动复制，还能少维护一套机器？**
手动复制踩第二节那三个坑。这台机器每次跑都留小票（envelope），每张小票有改前/改后
指纹，三分钟后审计、三个月后审计都一样答得上来。维护机器的成本，远低于事后查"谁改的"的成本。

**Q2：status 出现 partial / fail 我该慌吗？**
- `pass`：全绿。
- `partial`：有项在"等人工"（最典型=摘要类等候选）。常态，不是事故。
- `fail`：有 `error`。这时才需要看 item 里的 error 字段，按错误码回真源排查。

**Q3：我赶时间，直接改发布侧的文件行不行？**
不行，而且会被"双重惩罚"：① 下次管线发布时你的改动被真源版本**静默覆盖**；
② 这次改动没有小票，审计链上等于没发生过。正确路径永远是：改真源 → 走管线发布。
（在岗员工席另有纪律条 D-07/D-16 把这件事立成了硬规矩。）

## 八、带走的三句话心智模型

1. **真源只有一个，复印件全部照单（manifest）核平**。
2. **机器默认只看不改（dry-run），动手要显式授权（execute），每动必留小票（envelope）**。
3. **确定性的事交机器（复制、校验、记账），语义的事交人（拟摘要、做裁决）**。

## 九、往下读哪

- 想知道"一次完整发布要经过哪些角色和步骤"→ [产品版 02-product-guide.md](02-product-guide.md)
- 想接手代码 → 先产品版，再 [代码版 03-code-map.md](03-code-map.md)
- 想知道这套设计为什么长这样、失败过几次、怎么防再犯 → [深度研究版 04-deep-research.md](04-deep-research.md)

## 使用依据

- 命令与输出：2026-09-05T03:56Z 在 TriCompany 根实跑 `--project-docs` 取得（本文第六节为原样节选）
- 真源封条：`TriCompany/docs/project-sources/trimetaverse-claude-md.md` L1（其发布副本 `TriMetaverse/CLAUDE.md` L1 同文，字节一致为当日 dry-run in_sync 实证）
- 派生标记：`TriMetaverse/.claude/hub/` 各 `.session.md` 尾注（标记常量定义于 `source_publish_check.py` L160-162）
- manifest 四条目："published-summary/published-copy 分域"见 `TriCompany/.github/manifests/project-source-doc-sync-manifest.json`
- requires_candidate 语义（CLI 永不合成摘要）：manifest notes 第 3 条 + `source_publish_check.py` L1745-1747 docstring

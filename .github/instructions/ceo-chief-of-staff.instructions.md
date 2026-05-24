---
description: "适用场景：修改 TriCompany 总助、source-agents/ceo-chief-of-staff 五件套、开始会议.prompt.md、结束会议.prompt.md 时使用。约束总助源侧套件和会议入口的维护边界。"
name: TriCompany CEOChiefOfStaff Maintenance Rules
applyTo: ".github/source-agents/ceo-chief-of-staff/ceo-chief-of-staff.agent.md, .github/source-agents/ceo-chief-of-staff/ceo-chief-of-staff.soul.md, .github/source-agents/ceo-chief-of-staff/ceo-chief-of-staff.memory.md, .github/source-agents/ceo-chief-of-staff/ceo-chief-of-staff.colleagues.md, .github/source-agents/ceo-chief-of-staff/ceo-chief-of-staff.social.md, .github/prompts/开始会议.prompt.md, .github/prompts/结束会议.prompt.md"
---
# TriCompany 总助套件维护规则

本说明只约束 TriCompany 中总助套件的维护方式，不替代 agent 本体的运行时行为。

## 文件分工

- ceo-chief-of-staff.agent.md：总助源侧 agent 草案；只有发布到 `TriMetaverse/.github/agents` 后才作为 live agent discovery 入口。
- ceo-chief-of-staff.soul.md：人格、气质和对话质感。
- ceo-chief-of-staff.memory.md：memory 层源侧契约、当前原则、写入边界和运行资产落点。
- ceo-chief-of-staff.colleagues.md：colleagues 层源侧契约、当前原则、写入边界和运行资产落点。
- ceo-chief-of-staff.social.md：social 层源侧契约、当前原则、写入边界和运行资产落点。
- 开始会议 / 结束会议 prompt：会议专用入口。

## 维护边界

- 不要把运行时行为全部拆散到多个文件里；真正生效的职责边界仍保留在 agent 本体。
- 不要在 agent 本体里重新引入“你的记忆文件位于哪里”这类显式底层文件感知。
- 如果修改的是人格和口吻，优先改 soul。
- 如果修改的是 memory / colleagues / social 的层契约、边界或运行资产落点，优先改对应文件。
- 如果修改的是具体阶段任务、人物档案、工作关系、称呼偏好、闲聊互动、事项记录或 workflow 写回摘录，优先落到 support employee workspace 或 runtime cognition state，不写入 TriCompany 源码侧 `.memory.md` / `.colleagues.md` / `.social.md`。
- 如果修改的是会议入口动作，优先改 prompt，而不是把命令细节塞回 agent 本体。

## 对齐要求

- TriCompany 当前属于研发仓，同时承载试运行宿主资产；涉及 Hermes 正式宿主化的内容要明确标为待验证。
- 当前阶段总助源侧套件属于 `TriCompany/.github/source-agents/ceo-chief-of-staff/`，不得放回 `TriCompany/.github/agents/` 造成源码侧 agent discovery；修改时要注意同时检查产品真源和技术真源是否需要同步更新。
- 任何会影响产品真源或技术真源的耐久变化，都要评估是否同步给 TriCompanyProductRegistry 或 TriCompanyCodeRegistry。
- 总助要保持真实总助质感，不能退化成系统提示器或文件操作员。
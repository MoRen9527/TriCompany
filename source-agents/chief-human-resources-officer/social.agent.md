# Social Layer Contract

## 社交层契约

- **工作名**：小源（CEO 正式命名，2026-08-01）
- **社交定位**：作为公司组织制度的守护者，在日常协作中保持专业、公正的社交形象。对员工 onboarding 持欢迎态度，对职责交接持严谨态度。
- **社交连续性**：当前阶段由 employee knowledge workspace 承载实时社交状态，源侧仅定义结构契约。

## 当前原则
## 当前原则

- 源码侧只保留社交档案的通用规则和边界，不写具体非正式称呼、互动偏好或轻社交流水。
- CHO 员工实例的具体社交连续性写入 support employee workspace 或 runtime cognition state。
- 工作事实、岗位判断和正式交接记录优先放在 colleagues、memory、workflow 或 registry，不与 social 层混写。
- 说话气质和组织表达风格优先由 `soul` 定义。

## 运行资产落点
## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-human-resources-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend
- 员工实例资产：runtime cognition 私域下 `chief-human-resources-officer/` 员工实例目录（阶段记忆、关系与社交连续性的落点）

## 层契约
## 层契约

- social 层用于承载当前 CHO 员工实例的轻社交连续性、非正式称呼、互动偏好和闲聊层面的待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 如果某条社交偏好变成稳定协作要求，应经复核后晋升到 colleagues、workflow 或正式组织文档。

- 认知层契约正身：源侧认知层契约（source-agents 真源）；运行态不入身份层。

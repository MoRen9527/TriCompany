# FSD 工作协作档案

本文件是 TriCompany 源侧认知层契约，只定义 FSD colleagues 层的用途、写入边界和运行资产落点；不记录具体人物档案或工作事项记录。

## 当前原则

- 源码侧只保留工作协作档案的通用规则和边界，不写具体人物关系、称呼偏好或事项流水。
- FSD 员工实例的具体协作关系和事项记录写入 support employee workspace 或 runtime cognition state。
- 正式编码职责、技术方案执行和输入来源进入 `.agent.md`、engineering docs 或 workflow。
- FSD 向 CTO 小狄报告，由 CTO 分配编码任务并审查工作质量。
- 与 STE 小柯形成编码-测试流水线：小全产出代码 → 小柯验证 → CTO 审查两人工作质量。
- 其他岗位尚未正式上岗时，只在运行资产中记录待同步入口，不把待同步状态写成源码事实。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/full-stack-developer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- colleagues 层用于承载当前 FSD 员工实例在编码工作层面的关系、协作偏好、事项记录和待确认信息。
- 这些内容默认是 current-host consumption data，不属于源码侧岗位定义。
- 可复用的编码协作协议应晋升到 role workspace、workflow 或 `.agent.md`。

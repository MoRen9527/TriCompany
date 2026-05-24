# ChiefAdministrativeOfficer 协作关系契约

本文件是 TriCompany 源侧认知层契约，只定义 ChiefAdministrativeOfficer colleagues 层的用途、写入边界和运行资产落点；不记录具体人物动态或运行同步摘录。

## 当前原则

- CAO 与 CEOChiefOfStaff 协同秘书处日常机制、会议闭环和公司级任务回填。
- CAO 与 ChiefHumanResourcesOfficer 分清行政治理和人力交接治理边界。
- CAO 与 CompanyGovernanceRegistry 协同治理资料事实登记和发布纪律。
- CAO 不替代 CPO / CTO / registry 做产品、技术或业务事实判断。

## 运行资产落点

- 宿主绑定说明：`TriCompany/.github/binding-profiles/chief-administrative-officer.json`
- runtime cognition 私域：`TRICOMPANY_COGNITION_HOME` 或当前 runtime cognition backend

## 层契约

- colleagues 层用于描述 CAO 与其他岗位的稳定协作边界。
- 具体协作事件、会议记录和动作项默认进入 support employee workspace、operating records 或 runtime cognition state。
- 稳定的职责边界变更应回写 workflow 或 CompanyGovernanceRegistry。

# Project Onboarding For Beginners

版本：V0.1
日期：2026-04-29
状态：首版小白导读

## 1. 这个项目在做什么

TriMetaverse 是一个由多个模块组成的三元宇宙项目。

当前最重要的理解方式是：项目不是只有一个应用，而是一组模块、流程、赛博公司岗位、宿主入口和运行系统逐步组合起来。

## 2. TriCompany 是什么

TriCompany 是赛博公司的研发仓。

它不是中央战略仓，也不是 TriMC 服务器正式版。它负责把赛博公司的产品文档、技术设计、岗位、记忆系统、教程、registry 和当前阶段 Copilot-host 资产先研发清楚。

## 3. 当前几个关键层

- TriCompany：模块源侧真源，负责定义赛博公司、岗位、流程和实现。
- TriCompany-copilot-host-assets：当前 Copilot-host 支撑包，负责承接当前宿主消费的发布副本、证据和对象载荷。
- TriMetaverse/.github：当前 live Copilot-host 入口。
- TriMetaverse/docs：中央架构、边界、协议和经营记录层。

## 4. 为什么要区分源侧和宿主侧

源侧回答“公司本来是什么、员工是谁、流程怎么定义、机制如何实现”。

宿主侧回答“当前这个运行环境实际要读哪些对象、写哪些审计、展示哪些快照”。

如果只在宿主侧创建员工和流程，换宿主时就要重新招聘员工、重建流程。正确做法是先在 TriCompany 源侧定义完整赛博公司，再发布到不同宿主。

## 5. role 和 employee knowledge workspace

role knowledge workspace 是岗位知识空间，保存岗位职责、流程、判断框架和可继承知识。

employee knowledge workspace 是员工实例知识空间，保存具体员工的私域记忆、当前任务、协作记录和阶段性经验。

一个员工执行任务时，应该同时读取自己的 employee 空间、岗位 role 空间、公司共享空间和审计空间。

## 6. RAndDTrainer 是什么

RAndDTrainer 是赛博公司的技术研发培训师，当前使用 `rd-trainer` 作为 employeeId、源侧文件名和 support object id；`project-trainer` 只作为历史兼容 alias。

它负责把项目中已经确认的模块、代码、流程、产品功能和新设计，整理成渐进式技术教程。当前先由总助同步输入；已上岗 CPO、CTO 也可以分别同步产品功能、技术架构和工程流程内容。

RAndDTrainer 的输出帮助技术研发新人读懂项目并接手代码，但不替代原始真源。

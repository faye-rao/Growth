# CLAUDE.md — frontend（运营控制台 · 计划中，尚未实现）

> 现状：**前端尚未实现**，本目录目前只有本记忆文件。后端是 7 个 REST 服务 + API 网关。
> 同级目录(backend `src/`)的 CLAUDE.md **不会**自动加载到此 → 前端约定都写在这里。

## 目标
为后端做一个**运营控制台**，复刻 MoEngage 的：圈人规则编辑器、三步活动向导、Flow 画布、报表。

## 技术选型（推荐）
- **React 18 + TypeScript + Vite**
- **Ant Design**（数据密集后台 + 内置 RTL）
- **react-querybuilder**（嵌套规则构造器 ↔ M2 JSON DSL，**必须双向映射**：构造器输出可转 DSL，DSL 可回显）
- **React Flow**（M3 Flow 节点：延时/分支/A·B/等待事件/webhook）
- **ECharts**（M4 漏斗/跨产品漏斗）
- **TanStack Query** + Zustand（服务态/本地态）
- **React Hook Form + Zod**（payload/规则校验）
- **react-i18next + RTL**（en/ar/hi/tl）
- **openapi-typescript**（从网关 `/openapi.json` 生成类型化 client）
- 测试：Vitest + Testing Library + **Playwright(E2E)**

## 硬需求
- **阿语 RTL 必须 day-1 纳入**（Botim 核心市场，后补成本高）。
- **规则构造器 ↔ M2 DSL 双向映射**是 Audience 页核心难点。
- 鉴权走网关 `MOE-APPKEY`/token；多语言文案对接 M6/M5 payload。

## 页面 ↔ 服务
Campaign(M3+M1,最高优先：列表+三步向导+Flow画布+频控+发送状态) · Audience(M2:规则构造器+NL2SQL+实时人数+模板+列表) · Analytics(M4+M9:漏斗+跨产品+归因+报表+洞察) · Personalization(M5:列表+向导+payload编辑器+发布+fetch测试) · Content(M6:多语种生成+行内合规+预览编辑) · Experiment(M7:5%切流+对照报告) · Data(M8:身份查询+DQC+抑制名单)

## 后端前置（前端依赖，需后端先补）
导出 OpenAPI + CORS + 登录换 token 端点 + 列表/保存/CRUD 端点 + 实时通道(人数预估/发送进度)。

## 落地顺序与工作量
详见交接清单/工作报告与对话中的前端计划：阶段0脚手架→阶段1底座(含RTL)→阶段2按优先级(Campaign+Audience先)→阶段3横切→阶段4测试部署。MVP 子集 ~6–7 周；全量 ~2.5–3 个月（前端 ~114 人日 + 后端前置 ~15 人日）。

---

## 当前实现状态（2026-06-05）

**已搭建并验证**（脚手架 + 基础底座 + 2 屏 MVP）：
- 脚手架：Vite + React18 + TS + AntD5 + React Router + TanStack Query + Zustand；`vite.config.ts` 用 dev proxy `/api → :8000`(网关)；`tsc --noEmit` 干净；`vite build` 成功。
- 基础底座：`src/layout/AppLayout.tsx`(7 服务左导航)、`src/i18n.ts`(en/ar + **RTL**，`<html dir>`+ConfigProvider direction 同步)、`src/api/client.ts`(带 MOE-APPKEY 的 fetch 封装 + 各服务 typed helper)、`src/api/types.ts`(M2 DSL 类型)、`src/store.ts`。
- **Audience 屏**(`src/features/audience/`)：`dsl.ts`(react-querybuilder ↔ M2 DSL **双向映射**，事件节点经 `__rawNode` 哨兵无损往返) + `AudiencePage.tsx`(NL2SQL 输入→回填构造器+置信度/待审标签、可视化规则构造器、防抖实时人数预估、模板列表、DSL 预览、Compile SQL)。
- **Campaign 屏**(`src/features/campaign/`)：活动列表 + **三步向导**(选人→A/B/N 变体→排期目标)→ `campaignApi.run` → RunResult 摘要；含 `VariantsTable`/`wizardTypes`。

**测试**：单测 **28 通过**(dsl 20 + Audience 4 + Campaign 4)；**联合集成 11 通过**(打真实网关，见 `INTEGRATION-TEST-REPORT.md`)。总 **39 通过**。

**未建（占位路由 + 后续）**：Analytics(M4+M9) / Personalization(M5) / Content(M6) / Experiment(M7) / Data(M8) 仅占位页；约 79 人日（见 `../docs/Frontend-Plan.md`）。

**已知限制**：`dsl.ts` 数字字符串强转(country="971"→数字)需按字段 inputType 改进；i18n 仅 en/ar(hi/tl 待补)；`campaignApi.run` 返回 `any`(未生成 OpenAPI 类型)；无 Playwright E2E。

**后端前置（生产化）**：导出 OpenAPI、CORS、登录换 token、列表/CRUD 端点、实时通道(人数/进度)。

# 前端工作计划 — Botim Growth 运营控制台

> 目标：为已有的 7 个后端服务 + API 网关做一个**运营控制台**，复刻 MoEngage 的圈人规则编辑器、三步活动向导、Flow 画布、报表。
> 英文版见 `Frontend-Plan-EN.md`。当前实现状态见 `../frontend/CLAUDE.md` 底部与 `../frontend/INTEGRATION-TEST-REPORT.md`。

## 1. 技术选型
| 维度 | 选型 | 理由 |
|---|---|---|
| 框架 | React 18 + TypeScript + Vite | 与竞品形态一致、生态成熟 |
| UI 库 | Ant Design 5 | 数据密集后台 + 内置 RTL |
| 规则构造器 | react-querybuilder | 嵌套规则 ↔ M2 JSON DSL 双向映射 |
| 编排画布 | React Flow | M3 Flow 节点（延时/分支/A·B/等待事件/webhook） |
| 图表 | ECharts | M4 漏斗/跨产品漏斗 |
| 服务态/本地态 | TanStack Query + Zustand | REST 拉取缓存 + 本地状态 |
| 表单校验 | React Hook Form + Zod | payload/规则校验 |
| 国际化 | react-i18next + RTL | en/ar/hi/tl，阿语 RTL |
| API 客户端 | openapi-typescript（从网关 /openapi.json 生成） | 类型安全、契约对齐 |
| 测试 | Vitest + Testing Library + Playwright | 组件 + E2E |

## 2. 后端前置（前端依赖）
1. 各服务 FastAPI 导出 `/openapi.json`，网关聚合。
2. CORS（浏览器跨域）；开发期用 Vite dev proxy 规避。
3. 登录换 token 端点（现仅 MOE-APPKEY 头校验）。
4. 列表/保存/CRUD 端点（分群保存、活动列表、experience CRUD）。
5. 实时通道（人数预估、发送进度，轮询或 WebSocket）。

## 3. 页面 ↔ 服务映射
| 页面 | 服务 | 关键组件 |
|---|---|---|
| Campaign（最高优先） | campaign(M3+M1) | 活动列表 + 三步向导(选人→内容A/B/N→排期目标) + Flow 画布 + 频控设置 + 发送状态 |
| Audience | audience(M2) | 可视化规则构造器 + NL2SQL 输入 + 实时人数预估 + 模板库 + 分群列表/保存 |
| Analytics | analytics(M4+M9) | 漏斗图 + 跨产品漏斗 + 归因 + 报表 + 自动洞察流 |
| Personalization | personalization(M5) | experience 列表 + 三步向导 + payload 编辑器 + 发布开关 + fetch 测试器 |
| Content | content(M6) | 多语种文案生成 + 行内合规提示 + 预览/编辑 + 绑定活动变体 |
| Experiment | experiment(M7) | Shadow 配置(5%切流) + 对照报告(显著性/非劣结论) |
| Data | data-platform(M8) | 身份查询 + DQC 看板 + 抑制名单（偏内部运维） |

## 4. 落地步骤（4 阶段）
- **阶段 0 · 脚手架（~5 人日）**：Vite+TS+AntD、ESLint/Prettier、环境配置、从 OpenAPI 生成 client、Vite dev proxy。
- **阶段 1 · 基础底座（~12 人日）**：设计系统/主题、布局(左导航对应 7 服务)、登录鉴权、i18n+RTL、统一加载/错误/空状态、路由。
- **阶段 2 · 各模块页面（~79 人日）**：按优先级 Campaign(18) + Audience(15) + Analytics(14) + Personalization(12) + Content(8) + Experiment(6) + Data(6)。
- **阶段 3 · 横切（~8 人日）**：RTL 全量、可访问性、RBAC、审计。
- **阶段 4 · 测试与交付（~10 人日）**：组件测试(Vitest)、E2E(Playwright)、Storybook、CI、构建/部署(Docker+网关反代)。

## 5. 工作量与节奏
- 前端 ≈ **114 人日** + 后端前置 ≈ 15 人日 = **~130 人日**。
- 2–3 人前端团队：完整 ~2.5–3 个月；MVP 子集（Campaign+Audience+Content+基础 Analytics）~6–7 周。

## 6. 落地顺序
后端先导出 OpenAPI+登录+CORS → 阶段0/1 底座(含 RTL) → **先 Campaign 三步向导 + Audience 规则构造器** → Content → Analytics → 再 Personalization/Experiment/Data → E2E + 部署。

## 7. 关键风险
- **阿语 RTL** 必须 day-1 纳入（核心市场，后补成本高）。
- 后端契约缺口（列表/保存/CRUD、登录、实时通道）需先补，否则前端阻塞。
- 分析页数字须与后端/旧系统对账，运营才信任。
- **规则构造器 ↔ M2 DSL 双向映射**是 Audience 页核心难点（输出可转 DSL、DSL 可回显）。

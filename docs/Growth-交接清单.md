# Growth 平台 · 工作交接清单（Handover）

> 交接日期：**2026-06-05（刷新）** ｜ 仓库：`https://github.com/faye-rao/Growth`（默认分支 main）
> 本地：`C:\Faye\Growth\botim-growth-m2-cohort`（代码，含 `frontend/`）＋ `C:\Faye\Growth\*.md`（分析文档）
> 配套：`Growth-实现对比报告.md`/`Growth-Implementation-Audit.md`（逐特性实现度）、`ARCHITECTURE.md`（架构）、`Frontend-Plan.md`（前端计划）、`TEST-REPORT.md`、`PRODUCT-CONTEXT.md`、`Growth特性清单-M*-1.md`/`Growth技术方案-*.md`（需求/选型）、`Growth-requirement-prompt.md`
> 各级 `CLAUDE.md`（仓库根 / src 子目录 / frontend）为 AI 会话自动加载的项目记忆，含约定/命令/现状。

---

## A. 项目背景（30 秒）
为 Botim（迪拜，UAE 上线，目标用户 ≈ 250 万）自研一套**用户增长平台**，替换竞品 MoEngage。范围与优先级来自访谈 survey（`用增问题survey-updated v3.xlsx`）。
现状：**后端 9 模块 M1–M9** 建成可运行可测 MVP，按功能独立性拆 **7 服务 + 1 API 网关**；**前端运营控制台 7 屏 MVP** 已建并与后端联合集成跑通；CI 接入。

---

## B. 已完成的工作

### B1. 后端（仓库根 `src/`）
- **9 业务模块**（Python，零核心依赖）：`cohort_engine`(M2)、`messaging`(M1)、`orchestration`(M3)、`analytics`(M4)、`personalization`(M5)、`copywriting`(M6)、`shadow`(M7)、`data_foundation`(M8)、`behavioral`(M9)
- **共享契约** `growth_common`（DeliveryRecord 触达日志、MessagingGateway 协议、确定性分桶 stable_fraction）
- **7 服务**（`src/services/`，各自独立 FastAPI app）+ **API 网关** `src/api_gateway.py`（前缀路由 + MOE-APPKEY 鉴权401 + 令牌桶限流429 + /health）
- **端到端**：`examples/e2e_demo.py` + `tests/test_integration_e2e.py`
- **后端测试：269 通过**（17 文件）；覆盖率 ~90%

### B2. 前端（`frontend/`，本次新增）★
- **技术栈**：React 18 + TS + Vite + Ant Design 5 + React Router + TanStack Query + i18n(**en/ar + RTL**)；dev proxy `/api→:8000`。
- **基础底座**：7 服务左导航布局、`LoginGate`(MOE-APPKEY+角色)、`ErrorBoundary`、类型化 API client、M2 DSL 类型。
- **全部 7 屏**（均 MVP 深度，带测试）：
  - Audience(M2)：规则构造器↔M2 DSL **双向映射** + NL2SQL + 实时人数预估 + 模板 + Compile SQL
  - Campaign(M3+M1)：列表 + 三步向导(选人→A/B/N→排期) + **React Flow 编排画布** + 频控 + RunResult
  - Analytics(M4+M9)：ECharts 漏斗 + 跨产品 + 归因 + 报表 + 自动洞察
  - Personalization(M5)：experience 注册/发布 + 多语言 payload 编辑器 + fetch 测试器
  - Content(M6)：多语种文案生成 + 行内合规(阿语 RTL) + 合规检查 + 选优
  - Experiment(M7)：5% 切流 + 对照报告(判定/显著性/CI)
  - Data(M8)：DQC 看板 + 身份解析 + 抑制检查 + ingest
- **前端测试**：单测 **51**(9 文件) + **联合集成 21**(打真实网关，全 7 服务) = **72 通过**；E2E(Playwright) 1/2（1 真实浏览器用例通过；1 受 chromium 冷启动超时，非代码问题）。详见 `../frontend/INTEGRATION-TEST-REPORT.md`。
- **可运行验证**：已用真实浏览器跑通并截图（登录门 / Audience / Campaign）。

### B3. 差异化亮点（相对 MoEngage）
跨产品漏斗(M4) · 三方案圈人引擎(M2，含 250 万级 RoaringBitmap) · NL2SQL 圈人(M2) · 跨活动频控去重(M3) · Shadow 非劣门禁(M7) · 多语种 AI 文案+合规(M6) · 自建 RFM/churn/engagement(M9)。

### B4. CI 与文档
- **CI**：`.github/workflows/ci.yml`（push/PR，py3.10/3.11/3.12 跑 pytest + 覆盖率），**结果发布到 Actions run Summary + JUnit/coverage 工件**。
- **文档（仓库 `docs/`）**：需求清单(中英)、技术方案(中英)、综合分析、`ARCHITECTURE.md`、**实现对比报告(中英)**、**测试报告 `TEST-REPORT.md`**、**前端计划 `Frontend-Plan.md`(中英)**、**产品级上下文 `PRODUCT-CONTEXT.md`**、工作报告(中英)、本交接清单(中英)。
- **CLAUDE.md 记忆**：仓库根 + `src/cohort_engine/` + `src/services/` + `frontend/`（含工作项状态清单）；`CLAUDE.local.md` 本地特例(gitignore)。

### B5. 完整度快照
- 后端功能（对 survey 特性清单）：均值 **~62%**（M1~60/M2~65/M3~50/M4~80/M5~60/M6~65/M7~55/M8~65/M9~60），核心链路+差异化已落地，AI 主线/生产基础设施待建（详见对比报告）。
- 前端：计划 4 阶段全部走通，**7 屏 MVP 深度**（详见 `frontend/CLAUDE.md` 末尾"工作项状态清单"）。

---

## C. 后续要完成的工作清单

### C0. 🔴 立即可做
- [ ] **验证 CI 绿**：仓库 Actions 页看三档 Python 跑测 + 覆盖率工件（我方 `gh` 未登录，无法代读）。
- [ ] **本地起服务自测**：后端 `pip install -e ".[dev]" && pytest`(269)；前端 `cd frontend && npm install && npm test`(51) + 起 `uvicorn api_gateway:app` 后 `npm run test:integration`(21) / `npm run dev` 看界面（登录用 `demo-appkey`）。

### C1. 🟥 P0 后端前置（解锁前端脱离 mock 直连生产 + 上线最大鸿沟）
- [ ] **导出 OpenAPI + CORS + 登录换 token 端点 + 列表/保存/CRUD 端点 + 实时通道**（前端 5 项硬依赖，现 dev 靠 Vite proxy + MOE-APPKEY 头）。
- [ ] **持久化与真实数据接入**：footprint 事件接入(Kafka/批)、宽表落 OLAP(数据组定)、触达/转化日志落库（现内存契约）。
- [ ] **M2 编译 SQL 接真实 OLAP** + 大人群跑批调度。
- [ ] **M5 千人千面热路径**：预计算人群+Redis 点查+缓存降级；补排期+时区(Asia/Dubai)、active/ended 态、转化目标。
- [ ] **M1 发送管道**：Kafka 削峰、对接 Botim 真实限速接口、日志落库。
- [ ] **统一时区 Asia/Dubai**（M3/M5 现 naive datetime）；**鉴权/多租户/RBAC 强制/审计**。

### C2. 🟧 P1 功能补全（按模块）
- [ ] **M3↔M6 打通**：M6 文案注入 M3 A/B/N 变体；A/B/N 显著性胜出回接(检验在 M7)；Flow 定义落库到活动。
- [ ] **M1 In-App**：活动位/页面配置、页级频控、SDK 自渲染下发。
- [ ] **M7 Shadow**：MoEngage 触达流水接入(需厂商)、复用 M4 归因口径、可配观测周期+序贯检验、CUPED。
- [ ] **M4**：跨产品漏斗 SQL 化、对账差异告警、ROI。
- [ ] **M8**：Kafka 订阅喂抑制层、DQC 漂移检测、Mapping 准确率、标签字典。
- [ ] **M9**：与 Growth 对齐"真有人看报表"清单并复现(证数字对得上)、报告导出、维度异常归因。

### C3. 🟨 P2 AI 增量主线（survey 定位"增量靠 AI"，现多为桩）
- [ ] 真 LLM 接入：M6 文案(`CopyProvider` 协议已留)、M2 NL2SQL(模板→RAG+LLM，保留兜底)。
- [ ] M3 AI 编排（自然语言→人群+文案+排期+Flow）；M2 智能分群(Lookalike/倾向/AI建议/算法优化)；M1 送达优化(可达性预测/STO/Next-Best-Channel)；M6 效果学习；M9 叙事 BI + NL 问数。

### C4. 🟩 前端收尾 + 工程化上线
- [ ] **前端**：`dsl.ts` 数字串强转按字段类型改进、hi/tl 文案补全、RBAC 按路由/按钮强制、a11y、E2E 扩覆盖+CI 稳定化、ESLint/Prettier、Storybook、API 类型改用 openapi-typescript 自动生成。
- [ ] **前端纳入 CI**：加 frontend job 跑 tsc + vitest + build。
- [ ] **容器化/部署**：各服务 + 前端 Dockerfile/compose、K8s、网关反代；可观测性（日志/指标/追踪/告警）；安全审查（PII、限流、UAE Fintech 合规）。

---

## D. 关键依赖与阻塞（需对外协调）
| 责任方 | 待提供 | 卡住的工作 |
|---|---|---|
| **数据组(马老板)** | OLAP 选型、ER图/库表、ID-Mapping+覆盖率、清洗 T+1、脱敏样本、历史取数 SQL 分布 | C1 全部、M2/M8、NL2SQL |
| **Growth(迪拜,Radhika)** | Top Cohort 定义、真看报表清单、Flow 节点类型、频次政策、Shadow 场景与验收 | M2/M3/M4/M7/M9 定型 |
| **裴青** | 事件 schema、数据样本、安排迪拜跟跑 | M8 接入、整体动工 |
| **MoEngage 厂商** | 触达流水接入方式/延迟、隐藏 Webhook/Connector | M7 Shadow 对照 |

> ⚠️ 多数仍"待问/待确认"——**开工前优先关闭这些访谈**。估算在数据/答案到位前为 ±30% 区间。

---

## E. 上手指引（新同事）
**后端**
1. `git clone https://github.com/faye-rao/Growth && cd Growth`
2. `python -m pip install -e ".[dev]"` → `pytest`（应 269 通过）
3. 读 `docs/PRODUCT-CONTEXT.md`(背景) → `ARCHITECTURE.md`(7服务+网关) → `README.md`
4. `PYTHONPATH=src uvicorn api_gateway:app --port 8000` → 看 `/health`、`python examples/e2e_demo.py`

**前端**
5. `cd frontend && npm install` → `npm test`(51) → `npm run dev`（:5173，登录 `demo-appkey`）；后端起着时 `npm run test:integration`(21)
6. 读 `frontend/CLAUDE.md`（约定+状态清单）、`frontend/INTEGRATION-TEST-REPORT.md`

**认领任务**：对照 `docs/Growth-实现对比报告.md`（每模块"已做/缺口"）+ 本清单 C 区。

## F. 风险提示
- **MVP ≠ 生产**：后端内存态/无真实数据源/无真 LLM，前端 7 屏为 MVP 深度——勿直接对真实流量。
- **数字可信**：替换 MoEngage 前提是"数字对得上"，M4/M9 报表须与旧系统双跑对账。
- **口径未统一**：转化/活跃/留存无全公司定义，归因须先对齐口径。
- **Shadow 双发**：上真实 Shadow 前 M7 去重中间层须接两套真实通道。
- **前端生产化阻塞**：依赖 C1 的后端前置（OpenAPI/CORS/登录/CRUD/实时通道）未补前，前端只能 dev proxy + MOE-APPKEY 头。

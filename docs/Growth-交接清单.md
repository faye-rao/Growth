# Growth 平台 · 工作交接清单（Handover）

> 交接日期：2026-06-04 ｜ 仓库：`https://github.com/faye-rao/Growth`（默认分支 main）
> 本地：`C:\Faye\Growth\botim-growth-m2-cohort`（代码）＋ `C:\Faye\Growth\*.md`（分析文档）
> 配套：`Growth-实现对比报告.md`（逐特性实现度）、`ARCHITECTURE.md`（架构）、`Growth特性清单-M*-1.md`（需求）、`Growth技术方案-*.md`（选型）、`Growth-requirement-prompt.md`（需求 prompt 记录）

---

## A. 项目背景（30 秒）
为 Botim（迪拜，UAE 上线，目标用户 ≈ 250 万）自研一套**用户增长平台**，替换竞品 MoEngage。范围与优先级来自访谈 survey（`用增问题survey-updated v3.xlsx`）。已把 9 个模块 M1–M9 全部建成**可运行、可测试的 MVP**，按功能独立性拆成 7 个服务 + 1 个 API 网关，接入 CI。

---

## B. 已完成的工作

### B1. 代码与测试（仓库 faye-rao/Growth）
- **9 个业务模块**（`src/`，Python，零核心依赖）：
  - `cohort_engine`(M2)、`messaging`(M1)、`orchestration`(M3)、`analytics`(M4)、`personalization`(M5)、`copywriting`(M6)、`shadow`(M7)、`data_foundation`(M8)、`behavioral`(M9)
- **共享契约** `growth_common`（DeliveryRecord 触达日志 schema、MessagingGateway 协议、确定性分桶 stable_fraction）
- **7 服务**（`src/services/`，各自独立 FastAPI app，可独立部署）：data-platform / audience / personalization / campaign / content / analytics / experiment
- **API 网关** `src/api_gateway.py`：前缀路由 + MOE-APPKEY 鉴权(401) + 每-key 令牌桶限流(429) + /health
- **端到端**：`examples/e2e_demo.py`（圈人→编排→触达→千人千面→Shadow→漏斗）+ `tests/test_integration_e2e.py`
- **测试：269 全部通过**（17 个测试文件，覆盖每模块 + 服务/网关 + e2e）
- **CI**：`.github/workflows/ci.yml`，push/PR 触发，py3.10/3.11/3.12 跑 pytest
- **Git 历史**：分模块语义化提交（feat(M1)…feat(M9)、feat(common)、feat(services)、ci、docs、test(e2e)）

### B2. 已落地的差异化亮点（相对 MoEngage）
- **跨产品漏斗**（M4，MoEngage 答不了）：Call→Wallet→Remittance，服务渗透率 7.5%→15% KPI
- **三方案圈人引擎**（M2）：解释执行 + 编译 SQL + RoaringBitmap（250 万级秒级交并差）
- **NL2SQL 自然语言圈人**（M2，确定性模板版，破"很难用"）
- **跨活动频控/去重**（M3，MoEngage/Botim 现状空白）
- **Shadow 非劣验证门禁**（M7，CI 置信区间 + 去重防双发）
- **多语种 AI 文案 + 合规初筛**（M6，en/ar/hi/tl，免责声明随截断保留）
- **自建 RFM/churn/engagement**（M9，替代 MoEngage 内部指标避免断供）

### B3. 文档（`C:\Faye\Growth\`）
- 需求：`Growth特性清单-M1-1.md`…`M9-1.md` + `Growth特性清单-总览索引.md`（中）/ `Growth-Feature-List-M1.md`…`M9.md`（英）
- 技术方案：`Growth技术方案-M1-M3/M4-M6/M7-M9.md`（中）+ `Growth-Tech-Solutions-*.md`（英）
- 综合分析：`Botim增长平台_基于Survey的重新分析.md`、`MoEngage特性清单_按菜单维度.md`、`MoEngage视频特性拆解_前端后端数据.md`
- 架构：`ARCHITECTURE.md`（仓库内）
- 本次：`Growth-实现对比报告.md`、`Growth-交接清单.md`、`Growth-requirement-prompt.md`

### B4. 完整度快照（详见对比报告）
M1~60% · M2~65% · M3~50% · M4~80% · M5~60% · M6~65% · M7~55% · M8~65% · M9~60% ｜ **平均 ~62%**（功能清单覆盖；基础设施脚手架已全建）

---

## C. 后续要完成的工作清单

### C0. 🔴 立即可做（交接当天）
- [ ] **验证 CI 绿**：登录后看仓库 Actions 页三档 Python 跑测结果（我方 `gh` 未登录，无法读取）
- [ ] **本地起服务自测**：`pip install -e ".[dev]" && pytest`；`uvicorn api_gateway:app` 后过一遍网关路由
- [ ] 把 `Growth-requirement-prompt.md` 等分析文档（已脱敏）按需纳入仓库 docs/

### C1. 🟥 P0 生产基础设施（MVP→可上线的最大鸿沟）
- [ ] **持久化与真实数据接入**：footprint 事件接入（Kafka/批）、宽表落 OLAP（数据组定 ClickHouse/Doris/StarRocks）、触达/转化日志落库（M8 现为内存契约）
- [ ] **M2 编译 SQL 接真实 OLAP**：`sql_compiler` 已产 SQL，需接引擎执行 + 大人群跑批调度（A5/A8）
- [ ] **M5 千人千面热路径**：预计算人群+Redis 点查+缓存降级（现为请求时实时命中，QPS/延迟不达标）；补 **鉴权(AppKey)**、**排期+时区(Asia/Dubai)**、active/ended 发布态、转化目标
- [ ] **M1 发送管道**：Kafka 削峰队列承载百万级、对接 Botim 开放平台真实限速接口、触达日志落库
- [ ] **统一时区 Asia/Dubai**：M3/M5 当前是 naive datetime，排期/静默/归因须统一 UAE 口径
- [ ] **鉴权与多租户**：网关有 MOE-APPKEY，但模块级鉴权、token 体系、审计待补

### C2. 🟧 P1 功能补全（按模块）
- [ ] **M3 编排**（缺口最大）：活动状态机(草稿/发布/运行/暂停/结束)、Flow 节点(延时/分支/等待事件/webhook)、活动级模板一键复用、静默时段、A/B/N 显著性胜出回接(检验代码已在 M7)、前端编排 UI
- [ ] **M3↔M6 打通**：把 M6 生成文案注入 M3 的 A/B/N 变体（现未打通）
- [ ] **M1 In-App**：活动位/页面位置配置模型、页级频控(首次/每页首次/每天首次)、SDK 自渲染下发协议
- [ ] **M7 Shadow**：MoEngage 触达流水接入(D 组，需厂商配合)、复用 M4 归因口径(C4)、可配观测周期+序贯检验早停、CUPED 方差削减
- [ ] **M4**：跨产品漏斗 SQL 化、对账差异告警阈值、ROI 指标
- [ ] **M8**：Kafka 轻量订阅喂抑制层、DQC 数据漂移检测、Mapping 准确率核对、标签字典/覆盖率
- [ ] **M9**：与 Growth 对齐"真有人看的 5–10 张报表"清单并复现(证数字对得上)、报告导出(PDF/可视化)、按维度异常归因

### C3. 🟨 P2 AI 增量主线（survey 定位"增量靠 AI"，目前几乎全是桩）
- [ ] **真 LLM 接入**：M6 文案（`CopyProvider` 协议已留，换真 LLM provider）、M2 NL2SQL（模板→RAG+schema-linking+LLM，保留模板兜底）
- [ ] **M3 AI 编排**（survey 点名最大亮点）：自然语言→人群+文案+排期+Flow 端到端
- [ ] **M2 智能分群**：Lookalike 相似扩展、流失/转化倾向打分、AI 分群建议、分群效果算法优化（C 系列 4 项全空白）
- [ ] **M1 送达优化**：可达性预测打分排序、最佳发送时间 STO、Next-Best-Channel
- [ ] **M6 效果学习**：文案↔效果建库、高转化风格学习、真 bandit/在线学习
- [ ] **M9 叙事 BI**：生成式洞察、NL 问数(text-to-SQL)

### C4. 🟩 工程化与上线
- [ ] 容器化（Dockerfile/compose）、各服务独立部署与 K8s/编排
- [ ] 可观测性（结构化日志、指标、链路追踪、告警）
- [ ] OpenAPI 契约 + 契约测试、负载/压测（尤其 M5 fetch 热路径、M2 250 万人群跑批）
- [ ] 安全审查（鉴权、PII、限流、合规——UAE Fintech）

---

## D. 关键依赖与阻塞（需对外协调）
| 责任方 | 待提供（决定能否推进） | 卡住的工作 |
|---|---|---|
| **数据组(马老板)** | OLAP 选型拍板、ER图/库表、ID-Mapping 表+覆盖率、清洗 T+1、脱敏样本、历史取数 SQL 分布(评估 NL2SQL) | C1 全部、M2/M8、NL2SQL |
| **Growth(迪拜,Radhika)** | Top Cohort 定义、真有人看的报表清单、Flow 节点类型/复杂度、频次政策、Shadow 场景与验收标准 | M2/M3/M4/M7/M9 功能定型 |
| **裴青** | 事件 schema、数据样本、安排迪拜跟跑 | M8 接入、整体动工 |
| **MoEngage 厂商** | 触达流水接入方式/延迟(D23)、隐藏 Webhook/Connector | M7 Shadow 对照 |

> ⚠️ 这些多数仍是 survey 里"待问/待确认"状态——**开工前优先关闭这些访谈**（Plan W1–W2）。估算与方案在数据/答案到位前为 ±30% 区间。

---

## E. 上手指引（新同事 5 步）
1. `git clone https://github.com/faye-rao/Growth && cd Growth`
2. `python -m pip install -e ".[dev]"` → `pytest`（应 269 通过）
3. 读 `ARCHITECTURE.md`（7 服务+网关全貌）→ `README.md`（M2 细节+各模块概览）
4. 跑 `python examples/e2e_demo.py` 看端到端链路；`uvicorn api_gateway:app` + `/health` 看服务路由
5. 按模块读 `src/<pkg>/` + 对应 `tests/test_<pkg>.py`；对照 `Growth-实现对比报告.md` 看每模块"已做/缺口"，挑 C 区任务认领

## F. 风险提示
- **过度信任 MVP**：当前是算法/契约 MVP，**非生产系统**——无持久化、无真实数据源、无真 LLM；勿直接对真实流量。
- **数字可信**：替换 MoEngage 的前提是"数字对得上"（survey 强调），M4/M9 报表需与旧系统双跑对账后才能让运营信任。
- **口径未统一**：转化/活跃/留存全公司无统一定义(D29)，归因须先对齐口径再开发，否则返工。
- **Shadow 双发**：上真实 Shadow 前，M7 去重中间层必须接入两套真实发送通道，否则对照失真。

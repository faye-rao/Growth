# Growth 平台 · 特性清单/技术方案 vs 代码实现 对比报告

> 审计对象：仓库 `faye-rao/Growth`（本地 `botim-growth-m2-cohort`），逐文件读码核对。
> 基线：`Growth特性清单-M1-1…M9-1.md` + `Growth技术方案-M1-M3/M4-M6/M7-M9.md`。
> 生成日期：2026-06-04。测试现状：**269 通过**，CI(py3.10–3.12) 已接入。
> 状态图例：`✅ 已实现` / `🟡 部分实现` / `⬜ 未实现`。完整度为按重要度加权的诚实估计。

---

## 0. 总览

| 模块 | 服务 | 完整度 | 一句话状态 |
|---|---|---:|---|
| **M1 触达执行** | campaign | ~60% | 薄编排网关(opt-out→可达性→限速→多渠道兜底)+用户级日志跑通；In-App活动位/页级频控空白、Kafka削峰与可达性AI未建 |
| **M2 圈人** | audience | ~65% | 规则引擎A1–A4 + 解释/编译SQL/Bitmap三方案俱全 + 确定性NL2SQL + 模板库；C系列AI(4项)、资产管理D1/D3、近实时A8缺失 |
| **M3 编排** | campaign | ~50% | A/B/N确定性分流+跨活动频控去重+M2/M1衔接硬核；状态机/Flow节点/活动模板/时区静默/AI编排/UI大面积缺失 |
| **M4 漏斗追踪** | analytics | ~80% | 单活动漏斗+跨产品漏斗(差异化)+对照报告核心完整且有测试；缺SQL化、对账告警、真AI归因、OLAP预计算 |
| **M5 千人千面** | personalization | ~60% | fetch+M2命中+多变体+多语言+发布门控+控制组主链路扎实；排期/时区/转化目标/鉴权/缓存降级/AI推荐/前端向导缺失 |
| **M6 AI文案** | content | ~65% | 多语种生成+多版本喂M3+合规初筛+epsilon-greedy选优可用；生成为确定性模板非真LLM，风格学习/文案存储缺失 |
| **M7 Shadow** | experiment | ~55% | 命门核心(切流+去重+CI非劣对照)扎实；MoEngage流水接入(D组)、观测周期调度、M4口径复用缺失 |
| **M8 数据底座** | data-platform | ~65% | 消费+补缺+服务化主体跑通且直供M2/M4；实时整组缺失(Kafka)，宽表为内存契约非OLAP落库，DQC无漂移检测 |
| **M9 行为分析** | analytics | ~60% | 6张报表+内部指标补齐(RFM/churn/engagement)+M4复用扎实；AI主线弱(异常归因/NL2SQL缺)，导出仅JSON |
| **平均** | | **~62%** | 9 模块均为可演示、测试覆盖良好的 MVP；核心链路+差异化亮点已落地，AI 主线与生产基础设施待建 |

**一句话结论**：survey 圈定的 **9 个模块全部建成可运行 MVP**，每个模块的"核心可演示链路 + 差异化亮点"真实落地并配 TDD 测试（269 通过）；共性简化是 **内存态 + 确定性离线算法替代真实基础设施**（无 OLAP/Kafka/Redis/真 LLM/持久化），以及 **AI 主线、前端 UI、鉴权、排期时区、SLA** 普遍待建——与文档"6 周 MVP、AI 作为增量并行不阻塞"的定位一致。

---

## 1. M1 触达执行（~60%）
**技术方案符合度**：落地"方案 C 复用收口接口 + 薄编排层"，`Gateway` 即薄编排收口点；Kafka 削峰、可达性 AI/STO 未建。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A1 Push 适配 / A2 SMS 适配 / A3 无Email | ✅ | `adapters.py:PushAdapter/SmsAdapter`；Channel 枚举无 Email |
| A4 百万级承载 | 🟡 | `gateway.send_batch` 仅同步循环，无 Kafka 队列 |
| A5 多渠道兜底 | ✅ | `gateway._deliver_with_fallback`（push→sms→in_app） |
| B1 In-App 自渲染 | 🟡 | `InAppAdapter` 仅后端投递桩，无 SDK 下发 |
| B2 页面活动位 / B3 页级频控 / B4 活动位框架 | ⬜ | 完全空白 |
| C1 接口限速 / C2 统一频控接入点 | 🟡 | `rate_limiter.py` 单机令牌桶；非对接 Botim 限速接口 |
| D1 Opt-out 名单 / D2 发送前过滤 | ✅ | `gateway` opt_out set + SUPPRESSED_OPTOUT |
| E1 触达日志 / E2 日志服务化 | 🟡 | `DeliveryRecord` 落地但仅内存 `self.log`，无持久化 |
| F1 无效用户过滤 | ✅ | `gateway._unreachable_reason`（卸载/无token/30天不活跃） |
| **F2 可达性预测/STO** | 🟡 | **仅规则过滤，无打分排序/AI预测/STO** |

## 2. M2 圈人（~65%）
**技术方案符合度**：三候选方案**全部落地**——解释执行(`evaluator`)、编译SQL(`sql_compiler`)、RoaringBitmap(`bitmap_engine`)；NL2SQL 走"模板/槽位"，未上 LLM/微调。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A1 嵌套AND/OR/NOT / A2 时间窗 / A3 频次属性算子 / A4 排除 | ✅ | `models/parser/evaluator` 全支持 |
| A5 批量求值刷新 | 🟡 | 内存求值有，无调度刷新管线 |
| A6 可视化构造+人数预估 | 🟡 | `estimate_size`/bitmap 基数有；UI 无 |
| A7 兼容MoEngage语法层 | 🟡 | 自有 JSON DSL，非 MoEngage 原生语法/迁移适配器 |
| A8 近实时分群 | ⬜ | 无 |
| B1 NL2SQL / B2 可预览编辑 / B3 置信兜底 / B4 模板优先 | ✅/🟡 | `nl2sql.py` 确定性模板(非LLM)+confidence+模板优先 |
| **C1 Lookalike / C2 倾向分群 / C3 AI建议 / C4 算法优化** | ⬜ | **四项全无** |
| D1 保存复用 / D3 版本管理 | ⬜ | 无持久化/版本化 |
| D2 模板库 | ✅ | `templates.py` 5 个高频模板 |
| D4 名单导出 | 🟡 | API 返回 customer_ids，无导出格式 |
| E1 多源接入 / E2 ID打通 / E3 已转化抑制 | ✅/🟡 | 主体在 M8（id_mapping/suppression） |
| F1 双路径 / F2 人群API | ✅/🟡 | 推送路径通；人群快照 API 有 |

## 3. M3 编排（~50%）
**技术方案符合度**：落地"方案 B 规则+批量调度"轻量主干(`CampaignRunner`)；无 Flink CEP、无 Temporal 状态机、bandit/AI 编排未启动。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A1 内容配置下发 | ✅ | `models.Campaign/Variant` + `runner` |
| A2 推送时间条件 / A3 触发vs批量 | 🟡 | `Schedule`/`is_triggered` 有；触发用户靠外部传入，无事件流 |
| **A4 状态机 / A5 Flow节点** | ⬜ | 草稿/发布/运行状态机、延时/分支/等待事件/webhook **全无** |
| B1 A/B/N组 / B2 自动分流 | ✅ | `models.variants` + `allocator.allocate`(stable_fraction) |
| B3 显著性胜出 | 🟡 | 检验在 M7，**未回接 M3 变体胜出** |
| C1 排期 | 🟡 | 字段有，无定时调度器 |
| **C2 统一时区Asia/Dubai** | ⬜ | 全 naive datetime |
| D1 活动模板 / D2 一键复用 | 🟡/⬜ | 仅人群模板，无活动级模板 |
| E1 每日上限 / E2 跨活动去重 | ✅ | `frequency.FrequencyCapper` |
| **E3 静默时段** | ⬜ | 无 |
| **F1 自然语言编排 / F2 可预览 / F3 AI文案接入** | ⬜/🟡 | **GPT替代编排最大亮点未建**；M6 文案未注入编排 |
| G1 前端UI | ⬜ | 仅 REST API |
| G2 人群输入 / G3 触达执行 | ✅ | 衔接 M2/M1 真实调用 |

## 4. M4 漏斗追踪（~80%，最完整）
**技术方案符合度**：方案 A 内存退化版(`compute_funnel` 有序贪婪匹配)，未接 OLAP windowFunnel/预计算；归因 first/last touch 可配窗口，未做 Shapley/Markov。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A2 查看→点击→转化漏斗 / A3 口径(CTR/CVR) | ✅ | `funnel.compute_funnel`/`FunnelResult` |
| A4 节点级流失 / A5 口径固化 | 🟡 | drop_off 数据 ready，无可视化/可配口径表 |
| B1 归因窗口 / B2 可配窗口 | ✅ | `attribution.attribute(window_hours)` |
| B3 归因语义服务化 | 🟡 | 库函数可复用，M7 耦合较松 |
| **C1 跨产品漏斗 / C2 渗透率链路** | ✅ | `cross_product.cross_product_funnel` + 测试 ← **核心差异化已落地** |
| C3 cross-sell漏斗 | 🟡 | 引擎通用支持，无专门样例 |
| C4 跨产品漏斗SQL化 | ⬜ | 纯内存，无 SQL 下推 |
| D1 活动效果报告 / D2 对照报告 | ✅ | `behavioral.campaign_performance` + `shadow.compare` |
| D3 对账可信 | 🟡 | 有双跑对比，无差异告警阈值 |
| D4 自动归因洞察 | 🟡 | z-score 异常检测，非真 AI 归因 |
| E2 轻看板 | 🟡 | API 出数，无 UI（符合"不做重看板"） |
| F1 日志消费 / F2 ID依赖 | ✅ | 消费 DeliveryRecord + id_mapping |

## 5. M5 千人千面（~60%）
**技术方案符合度**：方案 A 请求时实时命中(跑 M2 引擎+确定性分流)，未做方案 C 预计算KV+Redis点查+缓存降级；in-memory store。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A1 对等fetch / A3 identifiers / A4 payload返回 | ✅ | `service.fetch`/`resolve_customer_id` |
| A2 鉴权(AppKey) | ⬜ | service 层无鉴权（网关层有 MOE-APPKEY） |
| A5 多端代码片段 | ⬜ | 无 |
| A6 脱钩 / A7 实时SLA | ✅/🟡 | 纯自研；单次缓存，无超时降级SLA |
| B1 命中(复用M2) / B2 分配 / B3 分流 / B4 自有规则 | ✅ | `service` 调 CohortEngine + 权重分流 |
| **B5 AI个性化推荐** | ⬜ | 无召回/排序/画像 |
| C1 KV / C2 payload结构 / C3 多语言 | ✅ | `models.payload_for(locale)` + 测试 |
| C4 KV schema约定 | 🟡 | 基本校验，无显式 schema 契约 |
| D1 客户端自渲染 | ✅ | 只返 payload |
| D2 缓存降级 / D3 SDK规范 | ⬜ | 无 |
| E1 发布态状态机 / E2 未发布门控 | 🟡/✅ | draft/published/paused；**缺 active(时间窗)/ended** |
| **E3 排期+时区 / E4 转化目标** | ⬜ | Experience 无 start/end/tz/goal 字段 |
| F1/F2/F3 三步向导UI | 🟡/⬜ | 后端承载，无前端 |
| (亮点) 控制组 hold-out | ✅ | `control_pct` 已实现 |

## 6. M6 AI文案（~65%）
**技术方案符合度**：未采纳"方案 A Prompt 工程"真实形态，实现 `TemplateProvider`(确定性离线)，保留 `CopyProvider` 协议供真 LLM 后插；未做 RAG/微调；bandit 仅确定性 epsilon-greedy。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A1 多语种生成(en/ar/hi/tl) | ✅ | `provider.TemplateProvider`（**确定性模板非LLM**） |
| A2 本地化适配 | 🟡 | 原生多语模板，无模型本地化/RTL处理 |
| A3 多版本喂M3 | ✅ | `generator.generate(n)` + `to_orchestration_variants` |
| A4 可预览编辑 | 🟡 | 结果透明，无编辑UI |
| B1 文案-效果join | 🟡 | 按variant聚合CVR，非文本↔效果建库 |
| **B2 高转化风格学习 / B3 多语种建模** | ⬜ | 无 RAG/微调/学习 |
| B4 效果回流选优 | 🟡 | `feedback.epsilon_greedy` 选 arm，非生成模型学习 |
| C1 合规初筛 | ✅ | `compliance.check`(禁词/喊话/长度/免责声明+自动修复) |
| C2 Growth自审 | 🟡 | 输出 violations 供人工，无审批流 |
| D1 文案-活动绑定 | ✅ | `to_orchestration_variants` |
| D2 多语言存储版本 | ⬜ | 无持久化/版本 |

## 7. M7 Shadow（~55%）
**技术方案符合度**：方案 A 在线分流对照核心(确定性切流+去重+并行A/B)，统计用 CI 非劣检验；CUPED/序贯检验早停未做，方案 B 离线回放未建。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A1 样本源接入 / A2 切分策略 | ✅ | `splitter.split`/`assign_arm`(shadow_pct可配) |
| A3 5%切流(复用M2) | 🟡 | 用 stable_fraction 哈希，**未真正接 M2 圈人结果** |
| A4 并行对照 | ✅ | `dedup.reconcile` + `report.compare` |
| A5 测试专属通道 | ⬜ | 无 |
| **B1 去重中间层防双发** | ✅ | `dedup.DedupLedger.allow`/`reconcile` ← **硬需求已落地** |
| B2 跨系统触达账本 | 🟡 | 内存 set，无持久化/MoEngage侧写入 |
| C1 A/B对照报告 / C2 显著性 | 🟡/✅ | `compare`/`two_proportion_ztest` + CI 非劣；仅转化率未分层clicked |
| C3 即时ready报告 / C5 可配观测周期 | 🟡/⬜ | 纯函数即算，无调度/早停 |
| C4 归因复用M4 | ⬜ | 未 import analytics |
| **D1 MoEngage流水接入 / D2 口径对齐** | ⬜ | **整组缺失**，control 臂靠合成数据 |

## 8. M8 数据底座（~65%）
**技术方案符合度**：方案 A 接现成OLAP+消费宽表+确定性ID匹配；方案 B 自建实时数仓(Kafka+Flink)、概率/图匹配、AI-DQC 未建；连"轻量 Kafka 订阅喂抑制层"也未落地。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A1 footprint接入 / A2 双源 | 🟡 | `ingestion.ingest` 处理管道，输入内存dict，无真实连接器 |
| A3 事件schema字典 | ✅ | `ingestion._validate` + Schema |
| A4 激活备份 | 🟡 | `build_dataset` 喂下游通；代码层同 A1 |
| **A5 Kafka事件流** | ⬜ | 无流订阅 |
| B1 Mapping消费 / B2 跨线ID打通(无email) | ✅ | `id_mapping`(customer_id>phone>device, union-find) |
| B3 覆盖率/准确率 | 🟡 | coverage 有，无准确率核对 |
| C1 触达宽表 / C2 转化宽表 | 🟡 | DeliveryRecord 字段齐，无落库持久化 |
| C3 触达日志我方补齐 | ✅ | M1 产出 + M8 消费 |
| D1 圈人宽表 / D2 漏斗宽表 | ✅ | `warehouse.build_dataset` 直供 M2/M4(测试证) |
| D3 标签字典对接 | 🟡 | labels join，无字典/覆盖率 |
| E1 延迟监控 / E3 轻DQC | 🟡 | `dqc.run_dqc`(空值/重复/新鲜度/行数)；**无漂移检测** |
| E2 事件流可用性 | ⬜ | 无流 |
| F1 已转化抑制 | ✅ | `suppression.SuppressionList`(内存set+增量add) |
| F2 服务化 / F3 替换无中断 | ✅ | `services/data_platform.py` + 架构无回写 |

## 9. M9 行为分析（~60%）
**技术方案符合度**：方案 A 轻 BI 直查(纯函数报表)+复用 M4；未建指标层/语义层；叙事BI/NL问数/异常归因仅落最浅"自动洞察"。

| Feature | 状态 | 证据 / 缺口 |
|---|---|---|
| A1 5–10张报表复现 | 🟡 | `reports.py` 6 张(active/new_vs_returning/event_volume/campaign_perf/funnel/retention)；非"真有人看清单"，无法证数字对得上 |
| A2 报表盘点 | ⬜ | 调研项无代码 |
| A3 活动后复盘 | ✅ | `campaign_performance` + `auto_insights` |
| A4 报告导出 | 🟡 | API JSON，无文件/PDF |
| A5 克制划界 | ✅ | 仅6报表+洞察+指标，不做全量BI |
| B1 自动洞察 | 🟡 | `auto_insights`(z-score+模板叙事，非LLM) |
| **B2 异常归因 / B3 NL2SQL问数** | ⬜ | 无按维度归因；M9 未接 nl2sql |
| C1 内部指标补齐(RFM/churn/engagement) | 🟡 | `metrics.py` 已自研补齐；"消费方排查"调研未做 |
| D1 底层数据接入 / D2 复用M4归因 | ✅ | 消费 M8 dataset；`conversion_funnel_report` 薄包 M4 |

---

## 10. 平台基础设施（特性清单之外，均已建）
| 项 | 状态 | 证据 |
|---|---|---|
| 共享契约 growth_common | ✅ | DeliveryRecord/MessagingGateway协议/stable_fraction |
| 7 服务拆分（按功能独立性） | ✅ | `src/services/`（data/audience/personalize/campaign/content/analytics/experiment） |
| API 网关（路由/鉴权/限流/健康） | ✅ | `src/api_gateway.py`（MOE-APPKEY→401，令牌桶→429） |
| 端到端集成 demo + 测试 | ✅ | `examples/e2e_demo.py` + `tests/test_integration_e2e.py`(9) |
| CI（GitHub Actions, py3.10–3.12） | ✅ | `.github/workflows/ci.yml` |
| 架构总览文档 | ✅ | `ARCHITECTURE.md` |

---

## 11. 共性简化（影响"生产就绪"判断）
1. **全内存态、无持久化/真实数据连接器**：footprint/Kafka/MoEngage/OLAP 均为入参 dict 或合成 DeliveryRecord。
2. **确定性离线算法替代真实基础设施**：M4 无 OLAP、M5 无 Redis 预计算、M6 无真 LLM。
3. **统计为正态近似**（`two_proportion_ztest` 用 `math.erf`），无精确/贝叶斯/序贯。
4. **"AI"多为统计法/模板**：NL2SQL=模板槽位、自动洞察=z-score、文案=确定性模板——AI 主线（Lookalike/倾向/真 LLM/AI 编排）几乎都停在桩或空白。
5. **普遍缺位**：前端 UI、鉴权(模块级)、排期/时区(Asia/Dubai)、SLA 降级、数据漂移监控、持久化存储。

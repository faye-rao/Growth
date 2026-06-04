# Growth Platform · Feature List / Tech Solution vs Code Implementation Audit Report

> Audit target: repository `faye-rao/Growth` (local `botim-growth-m2-cohort`), file-by-file code reading and verification.
> Baseline: `Growth特性清单-M1-1…M9-1.md` + `Growth技术方案-M1-M3/M4-M6/M7-M9.md`.
> Generation date: 2026-06-04. Test status: **269 passing**, CI (py3.10–3.12) integrated.
> Status legend: `✅ Implemented` / `🟡 Partial` / `⬜ Not implemented`. Completeness is an honest estimate weighted by importance.

---

## 0. Overview

| Module | Service | Completeness | One-line state |
|---|---|---:|---|
| **M1 Messaging Execution** | campaign | ~60% | Thin orchestration gateway (opt-out→reachability→rate limiting→multi-channel fallback) + user-level logging running end-to-end; In-App activity slots/page-level frequency capping blank, Kafka peak shaving and reachability AI not built |
| **M2 Cohort Segmentation** | audience | ~65% | Rule engine A1–A4 + interpret/compiled SQL/Bitmap all three approaches complete + deterministic NL2SQL + template library; C-series AI (4 items), asset management D1/D3, near-real-time A8 missing |
| **M3 Orchestration** | campaign | ~50% | A/B/N deterministic split + cross-campaign frequency capping/dedup + M2/M1 integration solid; state machine/Flow nodes/campaign templates/timezone quiet hours/AI orchestration/UI largely missing |
| **M4 Funnel Tracking** | analytics | ~80% | Single-campaign funnel + cross-product funnel (differentiated) + comparison report core complete and tested; missing SQL implementation, reconciliation alerting, true AI attribution, OLAP precomputation |
| **M5 Personalization** | personalization | ~60% | fetch + M2 hit + multi-variant + multi-language + release gating + control group main chain solid; scheduling/timezone/conversion goals/auth/cache degradation/AI recommendation/frontend wizard missing |
| **M6 AI Copywriting** | content | ~65% | Multi-language generation + multi-version feeding M3 + compliance pre-screening + epsilon-greedy selection usable; generation is deterministic template not true LLM, style learning/copy storage missing |
| **M7 Shadow** | experiment | ~55% | Critical core (split + dedup + CI non-inferiority comparison) solid; MoEngage data pipeline integration (D group), observation period scheduling, M4 metric reuse missing |
| **M8 Data Foundation** | data-platform | ~65% | Consumption + gap-filling + servicification main body running and directly supplying M2/M4; real-time entire group missing (Kafka), wide tables are in-memory contracts not OLAP persisted to storage, DQC has no drift detection |
| **M9 Behavioral Analytics** | analytics | ~60% | 6 reports + internal metrics completed (RFM/churn/engagement) + M4 reuse solid; AI main line weak (anomaly attribution/NL2SQL missing), export JSON only |
| **Average** | | **~62%** | All 9 modules are demonstrable MVPs with good test coverage; core chains + differentiated highlights landed, AI main line and production infrastructure pending |

**One-line conclusion**: The **9 modules** scoped by the survey are **all built into runnable MVPs**, each module's "core demonstrable chain + differentiated highlight" genuinely landed and equipped with TDD tests (269 passing); common simplifications are **in-memory + deterministic offline algorithms replacing real infrastructure** (no OLAP/Kafka/Redis/true LLM/persistence), as well as **AI main line, frontend UI, auth, scheduling/timezone, SLA** generally pending — consistent with the documentation's positioning of "6-week MVP, AI as an incremental parallel that doesn't block."

---

## 1. M1 Messaging Execution (~60%)
**Tech-solution adherence**: Landed "Approach C reuse the consolidation interface + thin orchestration layer", with `Gateway` being the thin orchestration consolidation point; Kafka peak shaving, reachability AI/STO not built.

| Feature | Status | Evidence / Gap |
|---|---|---|
| A1 Push adapter / A2 SMS adapter / A3 No Email | ✅ | `adapters.py:PushAdapter/SmsAdapter`; Channel enum has no Email |
| A4 Million-scale capacity | 🟡 | `gateway.send_batch` is only a synchronous loop, no Kafka queue |
| A5 Multi-channel fallback | ✅ | `gateway._deliver_with_fallback` (push→sms→in_app) |
| B1 In-App self-rendering | 🟡 | `InAppAdapter` is only a backend delivery stub, no SDK delivery |
| B2 Page activity slots / B3 Page-level frequency capping / B4 Activity slot framework | ⬜ | Completely blank |
| C1 Interface rate limiting / C2 Unified frequency capping access point | 🟡 | `rate_limiter.py` single-machine token bucket; not integrated with Botim rate-limiting interface |
| D1 Opt-out list / D2 Pre-send filtering | ✅ | `gateway` opt_out set + SUPPRESSED_OPTOUT |
| E1 Messaging logs / E2 Logging servicification | 🟡 | `DeliveryRecord` landed but only in-memory `self.log`, no persistence |
| F1 Invalid user filtering | ✅ | `gateway._unreachable_reason` (uninstalled/no token/30-day inactive) |
| **F2 Reachability prediction/STO** | 🟡 | **Only rule filtering, no scoring/ranking/AI prediction/STO** |

## 2. M2 Cohort Segmentation (~65%)
**Tech-solution adherence**: All three candidate approaches **fully landed** — interpreted execution (`evaluator`), compiled SQL (`sql_compiler`), RoaringBitmap (`bitmap_engine`); NL2SQL uses "template/slot", no LLM/fine-tuning adopted.

| Feature | Status | Evidence / Gap |
|---|---|---|
| A1 Nested AND/OR/NOT / A2 Time window / A3 Frequency-attribute operators / A4 Exclusion | ✅ | `models/parser/evaluator` fully support |
| A5 Batch evaluation refresh | 🟡 | In-memory evaluation present, no scheduled refresh pipeline |
| A6 Visual construction + audience size estimation | 🟡 | `estimate_size`/bitmap cardinality present; no UI |
| A7 MoEngage syntax-layer compatibility | 🟡 | Own JSON DSL, not MoEngage native syntax/migration adapter |
| A8 Near-real-time segmentation | ⬜ | None |
| B1 NL2SQL / B2 Previewable & editable / B3 Confidence fallback / B4 Template-first | ✅/🟡 | `nl2sql.py` deterministic template (not LLM) + confidence + template-first |
| **C1 Lookalike / C2 Propensity segmentation / C3 AI suggestions / C4 Algorithm optimization** | ⬜ | **All four absent** |
| D1 Save & reuse / D3 Version management | ⬜ | No persistence/versioning |
| D2 Template library | ✅ | `templates.py` 5 high-frequency templates |
| D4 List export | 🟡 | API returns customer_ids, no export format |
| E1 Multi-source integration / E2 ID unification / E3 Converted-user suppression | ✅/🟡 | Main body in M8 (id_mapping/suppression) |
| F1 Dual path / F2 Audience API | ✅/🟡 | Push path works; audience snapshot API present |

## 3. M3 Orchestration (~50%)
**Tech-solution adherence**: Landed "Approach B rules + batch scheduling" lightweight backbone (`CampaignRunner`); no Flink CEP, no Temporal state machine, bandit/AI orchestration not started.

| Feature | Status | Evidence / Gap |
|---|---|---|
| A1 Content config delivery | ✅ | `models.Campaign/Variant` + `runner` |
| A2 Push time conditions / A3 Triggered vs batch | 🟡 | `Schedule`/`is_triggered` present; triggered users rely on external input, no event stream |
| **A4 State machine / A5 Flow nodes** | ⬜ | Draft/published/running state machine, delay/branch/wait-event/webhook **all absent** |
| B1 A/B/N groups / B2 Automatic split | ✅ | `models.variants` + `allocator.allocate` (stable_fraction) |
| B3 Significance-based winner | 🟡 | Test is in M7, **not connected back to M3 variant winner selection** |
| C1 Scheduling | 🟡 | Fields present, no scheduled scheduler |
| **C2 Unified timezone Asia/Dubai** | ⬜ | All naive datetime |
| D1 Campaign templates / D2 One-click reuse | 🟡/⬜ | Only audience templates, no campaign-level templates |
| E1 Daily cap / E2 Cross-campaign dedup | ✅ | `frequency.FrequencyCapper` |
| **E3 Quiet hours** | ⬜ | None |
| **F1 Natural-language orchestration / F2 Previewable / F3 AI copywriting integration** | ⬜/🟡 | **GPT-replacing-orchestration, the biggest highlight, not built**; M6 copy not injected into orchestration |
| G1 Frontend UI | ⬜ | REST API only |
| G2 Audience input / G3 Messaging execution | ✅ | Integration with M2/M1 real calls |

## 4. M4 Funnel Tracking (~80%, most complete)
**Tech-solution adherence**: Approach A in-memory degraded version (`compute_funnel` ordered greedy matching), not connected to OLAP windowFunnel/precomputation; attribution first/last touch with configurable window, no Shapley/Markov done.

| Feature | Status | Evidence / Gap |
|---|---|---|
| A2 View→click→conversion funnel / A3 Metrics (CTR/CVR) | ✅ | `funnel.compute_funnel`/`FunnelResult` |
| A4 Node-level drop-off / A5 Metric finalization | 🟡 | drop_off data ready, no visualization/configurable metric table |
| B1 Attribution window / B2 Configurable window | ✅ | `attribution.attribute(window_hours)` |
| B3 Attribution-semantics servicification | 🟡 | Library function reusable, M7 loosely coupled |
| **C1 Cross-product funnel / C2 Penetration-rate chain** | ✅ | `cross_product.cross_product_funnel` + tests ← **core differentiation landed** |
| C3 Cross-sell funnel | 🟡 | Engine supports generically, no dedicated sample |
| C4 Cross-product funnel SQL implementation | ⬜ | Pure in-memory, no SQL pushdown |
| D1 Campaign-effectiveness report / D2 Comparison report | ✅ | `behavioral.campaign_performance` + `shadow.compare` |
| D3 Reconciliation credibility | 🟡 | Dual-run comparison present, no discrepancy alert threshold |
| D4 Automatic attribution insights | 🟡 | z-score anomaly detection, not true AI attribution |
| E2 Lightweight dashboard | 🟡 | API produces data, no UI (consistent with "no heavy dashboard") |
| F1 Log consumption / F2 ID dependency | ✅ | Consumes DeliveryRecord + id_mapping |

## 5. M5 Personalization (~60%)
**Tech-solution adherence**: Approach A request-time real-time hit (runs M2 engine + deterministic split), Approach C precomputed KV + Redis point query + cache degradation not done; in-memory store.

| Feature | Status | Evidence / Gap |
|---|---|---|
| A1 Peer fetch / A3 identifiers / A4 payload return | ✅ | `service.fetch`/`resolve_customer_id` |
| A2 Auth (AppKey) | ⬜ | No auth at service layer (gateway layer has MOE-APPKEY) |
| A5 Multi-platform code snippets | ⬜ | None |
| A6 Decoupling / A7 Real-time SLA | ✅/🟡 | Fully in-house; single-shot cache, no timeout degradation SLA |
| B1 Hit (reuse M2) / B2 Allocation / B3 Split / B4 Own rules | ✅ | `service` calls CohortEngine + weighted split |
| **B5 AI personalized recommendation** | ⬜ | No recall/ranking/profiling |
| C1 KV / C2 payload structure / C3 Multi-language | ✅ | `models.payload_for(locale)` + tests |
| C4 KV schema convention | 🟡 | Basic validation, no explicit schema contract |
| D1 Client-side self-rendering | ✅ | Returns payload only |
| D2 Cache degradation / D3 SDK spec | ⬜ | None |
| E1 Release-state state machine / E2 Unpublished gating | 🟡/✅ | draft/published/paused; **missing active (time window)/ended** |
| **E3 Scheduling + timezone / E4 Conversion goals** | ⬜ | Experience has no start/end/tz/goal fields |
| F1/F2/F3 Three-step wizard UI | 🟡/⬜ | Backend carries it, no frontend |
| (Highlight) Control group hold-out | ✅ | `control_pct` implemented |

## 6. M6 AI Copywriting (~65%)
**Tech-solution adherence**: Did not adopt "Approach A prompt engineering" real form, implemented `TemplateProvider` (deterministic offline), retained `CopyProvider` protocol for later true-LLM insertion; no RAG/fine-tuning; bandit is only deterministic epsilon-greedy.

| Feature | Status | Evidence / Gap |
|---|---|---|
| A1 Multi-language generation (en/ar/hi/tl) | ✅ | `provider.TemplateProvider` (**deterministic template not LLM**) |
| A2 Localization adaptation | 🟡 | Native multi-language templates, no model localization/RTL handling |
| A3 Multi-version feeding M3 | ✅ | `generator.generate(n)` + `to_orchestration_variants` |
| A4 Previewable & editable | 🟡 | Results transparent, no editing UI |
| B1 Copy-effectiveness join | 🟡 | Aggregates CVR by variant, not text↔effectiveness database building |
| **B2 High-conversion style learning / B3 Multi-language modeling** | ⬜ | No RAG/fine-tuning/learning |
| B4 Effectiveness-feedback selection | 🟡 | `feedback.epsilon_greedy` selects arm, not generative-model learning |
| C1 Compliance pre-screening | ✅ | `compliance.check` (banned words/shouting/length/disclaimer + auto-fix) |
| C2 Growth self-review | 🟡 | Outputs violations for manual review, no approval flow |
| D1 Copy-campaign binding | ✅ | `to_orchestration_variants` |
| D2 Multi-language storage versioning | ⬜ | No persistence/versioning |

## 7. M7 Shadow (~55%)
**Tech-solution adherence**: Approach A online-split comparison core (deterministic split + dedup + parallel A/B), statistics use CI non-inferiority test; CUPED/sequential-test early stopping not done, Approach B offline replay not built.

| Feature | Status | Evidence / Gap |
|---|---|---|
| A1 Sample-source integration / A2 Split strategy | ✅ | `splitter.split`/`assign_arm` (shadow_pct configurable) |
| A3 5% split (reuse M2) | 🟡 | Uses stable_fraction hash, **not truly connected to M2 cohort results** |
| A4 Parallel comparison | ✅ | `dedup.reconcile` + `report.compare` |
| A5 Test-dedicated channel | ⬜ | None |
| **B1 Dedup intermediate layer to prevent double-send** | ✅ | `dedup.DedupLedger.allow`/`reconcile` ← **hard requirement landed** |
| B2 Cross-system messaging ledger | 🟡 | In-memory set, no persistence/MoEngage-side writeback |
| C1 A/B comparison report / C2 Significance | 🟡/✅ | `compare`/`two_proportion_ztest` + CI non-inferiority; conversion rate only, not stratified by clicked |
| C3 Instant-ready report / C5 Configurable observation period | 🟡/⬜ | Pure function computes instantly, no scheduling/early stopping |
| C4 Attribution reuse M4 | ⬜ | Does not import analytics |
| **D1 MoEngage data-pipeline integration / D2 Metric alignment** | ⬜ | **Entire group missing**, control arm relies on synthetic data |

## 8. M8 Data Foundation (~65%)
**Tech-solution adherence**: Approach A connect off-the-shelf OLAP + consume wide tables + deterministic ID matching; Approach B self-built real-time data warehouse (Kafka+Flink), probabilistic/graph matching, AI-DQC not built; even "lightweight Kafka subscription feeding the suppression layer" not landed.

| Feature | Status | Evidence / Gap |
|---|---|---|
| A1 footprint integration / A2 Dual source | 🟡 | `ingestion.ingest` processing pipeline, input in-memory dict, no real connector |
| A3 Event schema dictionary | ✅ | `ingestion._validate` + Schema |
| A4 Activation backup | 🟡 | `build_dataset` feeds downstream; same as A1 at code layer |
| **A5 Kafka event stream** | ⬜ | No stream subscription |
| B1 Mapping consumption / B2 Cross-line ID unification (no email) | ✅ | `id_mapping` (customer_id>phone>device, union-find) |
| B3 Coverage/accuracy | 🟡 | coverage present, no accuracy reconciliation |
| C1 Messaging wide table / C2 Conversion wide table | 🟡 | DeliveryRecord fields complete, no persisted-to-storage |
| C3 Messaging logs filled in by us | ✅ | M1 produces + M8 consumes |
| D1 Cohort wide table / D2 Funnel wide table | ✅ | `warehouse.build_dataset` directly supplies M2/M4 (proven by tests) |
| D3 Label-dictionary integration | 🟡 | labels join, no dictionary/coverage |
| E1 Latency monitoring / E3 Lightweight DQC | 🟡 | `dqc.run_dqc` (null/duplicate/freshness/row count); **no drift detection** |
| E2 Event-stream availability | ⬜ | No stream |
| F1 Converted-user suppression | ✅ | `suppression.SuppressionList` (in-memory set + incremental add) |
| F2 Servicification / F3 Replacement without interruption | ✅ | `services/data_platform.py` + architecture has no writeback |

## 9. M9 Behavioral Analytics (~60%)
**Tech-solution adherence**: Approach A lightweight BI direct query (pure-function reports) + reuse M4; no metric layer/semantic layer built; narrative BI/NL querying/anomaly attribution only land the shallowest "automatic insights".

| Feature | Status | Evidence / Gap |
|---|---|---|
| A1 Reproduce 5–10 reports | 🟡 | `reports.py` 6 reports (active/new_vs_returning/event_volume/campaign_perf/funnel/retention); not "a list someone really reviews", cannot prove the numbers reconcile |
| A2 Report inventory | ⬜ | Research item with no code |
| A3 Post-campaign review | ✅ | `campaign_performance` + `auto_insights` |
| A4 Report export | 🟡 | API JSON, no file/PDF |
| A5 Restraint boundary | ✅ | Only 6 reports + insights + metrics, no full BI |
| B1 Automatic insights | 🟡 | `auto_insights` (z-score + template narrative, not LLM) |
| **B2 Anomaly attribution / B3 NL2SQL querying** | ⬜ | No dimension-based attribution; M9 not connected to nl2sql |
| C1 Internal metrics completion (RFM/churn/engagement) | 🟡 | `metrics.py` developed in-house; "consumer-side troubleshooting" research not done |
| D1 Underlying data integration / D2 Reuse M4 attribution | ✅ | Consumes M8 dataset; `conversion_funnel_report` thin wrapper over M4 |

---

## 10. Platform Infrastructure (outside the feature list, all built)
| Item | Status | Evidence |
|---|---|---|
| Shared contract growth_common | ✅ | DeliveryRecord/MessagingGateway protocol/stable_fraction |
| 7-service split (by functional independence) | ✅ | `src/services/` (data/audience/personalize/campaign/content/analytics/experiment) |
| API gateway (routing/auth/rate limiting/health) | ✅ | `src/api_gateway.py` (MOE-APPKEY→401, token bucket→429) |
| End-to-end integration demo + tests | ✅ | `examples/e2e_demo.py` + `tests/test_integration_e2e.py` (9) |
| CI (GitHub Actions, py3.10–3.12) | ✅ | `.github/workflows/ci.yml` |
| Architecture overview doc | ✅ | `ARCHITECTURE.md` |

---

## 11. Common Simplifications (affect "production-ready" judgment)
1. **Fully in-memory, no persistence/real data connectors**: footprint/Kafka/MoEngage/OLAP are all input dicts or synthetic DeliveryRecord.
2. **Deterministic offline algorithms replace real infrastructure**: M4 has no OLAP, M5 has no Redis precomputation, M6 has no true LLM.
3. **Statistics are normal approximation** (`two_proportion_ztest` uses `math.erf`), no exact/Bayesian/sequential.
4. **"AI" is mostly statistical methods/templates**: NL2SQL = template slots, automatic insights = z-score, copywriting = deterministic templates — the AI main line (Lookalike/propensity/true LLM/AI orchestration) almost all stops at stub or blank.
5. **Generally absent**: frontend UI, auth (module-level), scheduling/timezone (Asia/Dubai), SLA degradation, data drift monitoring, persistent storage.

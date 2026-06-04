# Growth Technical Solution Comparison · M1 Messaging Execution / M2 Audience Segmentation / M3 Orchestration

> Technology selection comparison for the three core modules of Botim's in-house growth platform (MoEngage competitor replacement)
> Companion requirements: `Growth特性清单-M1-1.md` / `M2-1.md` / `M3-1.md` / `总览索引.md`
> Cross-cutting constraints: full-volume footprint instrumentation backup already exists; Data Team performs T+1 cleansing, MoEngage side is hourly-level; **no email** (primary keys are customer_id / phone number); **OLAP engine undecided** (Data Team to call the shot); business lines not yet unified, no CDP; ~800 campaigns/year, 2–3 per day, max millions per campaign; **batch-dominant, partially real-time**; Push/SMS go through Botim's own channels (already consolidated, MoEngage has no direct-push right), In-App SDK self-renders; current state has no cross-campaign dedup / no frequency cap; **incremental value comes from AI; first reuse the existing rule engine + compatibility layer for a 6-week MVP**.

---

## 1. M1 Messaging Execution (Push + In-App Pop-up)

### 1.1 Requirements & Constraints Recap
Replicate MoEngage messaging execution: Push/SMS go through Botim's already-consolidated own channels (neither MoEngage nor our side has third-party direct-push rights), In-App pop-ups are self-rendered by the SDK and bypass the backend, and complete the user-level messaging log (a prerequisite for M4 funnel / M7 Shadow). Constraints: max millions per campaign, batch-dominant; interface-side rate limiting + Opt-out list filtering are external dependencies; current state has no frequency capping / dedup (the main body is in M3; M1 only provides the execution-side integration point); no Email, so fallback can only be arranged among Push/SMS/In-App.

### 1.2 Candidate Solutions

**Solution A — Per-channel independent adapters (per-channel direct connection)**
- Approach: write a separate send logic for each of Push, SMS, and In-App; the business side directly calls the corresponding channel interface (FCM/APNs/Botim SMS gateway/SDK delivery), each implementing its own retry, receipts, and rate limiting.
- Applicable Scenarios: early stage with very few channels, small volume, and no unified frequency-capping/fallback needs; quickly enabling a single high-frequency scenario (e.g. wallet-activation Push).

**Solution B — Unified Messaging Gateway (channel-agnostic gateway, recommended foundation)**
- Approach: expose upward a channel-agnostic `send(customer_id, channel_hint, content, policy)` API; an internal adapter layer translates the unified message into each channel's protocol (Botim Push interface / SMS channel / In-App delivery); in the middle, **use Kafka for load smoothing/peak shaving** (after a million-scale campaign is enqueued, it is consumed at a steady rate), uniformly implementing rate-limiting token buckets, exponential-backoff retry, delivery/read-receipt feedback, Opt-out pre-filtering, and the execution-side frequency-capping integration point (C2). Multi-channel fallback degradation (A5) is orchestrated at the gateway: Push unreachable → SMS/In-App.
- Applicable Scenarios: the medium-to-long-term form with multiple channels, million-scale batches, and the need for unified frequency capping/fallback/receipts/reachability filtering — exactly Botim's target state.

**Solution C — Reuse Botim's already-consolidated interfaces + a thin orchestration layer (pragmatic MVP route)**
- Approach: instead of rebuilding a gateway, wrap a thin orchestration layer (queue + rate-limiting integration + Opt-out filtering + logging instrumentation) directly on top of Botim's already-consolidated Push/SMS interfaces; In-App uses the existing SDK delivery protocol. Adapter/fallback/reachability are reserved as hooks, so it can later grow smoothly into Solution B.
- Applicable Scenarios: a 6-week MVP, first using minimal changes to get "wallet-activation Push + messaging log" running, avoiding over-design against Botim's open-platform interface specs that remain unclear (R4).

### 1.3 Pros/Cons Comparison (High / Medium / Low)

| Dimension | A Per-channel direct connection | B Unified Messaging Gateway | C Reuse consolidated interfaces + thin orchestration |
|---|---|---|---|
| Implementation Cost | Low (single channel) / Medium (multi-channel duplication) | High | **Low** |
| Performance/Latency | Medium (no load smoothing, easy to overload) | **High** (Kafka load smoothing, steady-rate consumption of millions) | Medium |
| Scalability (adding channels/capabilities) | **Low** (rewrite per channel added) | **High** (just add an adapter) | Medium (hooks reserved, needs evolution) |
| Operability | Low (logic scattered, hard to observe uniformly) | **High** (unified rate-limiting/retry/receipts/monitoring) | Medium |
| Fit for Botim | Low | Medium (ideal state but interface specs unclear, easy to over-design) | **High** (fits the already-consolidated reality + 6-week window) |

### 1.4 Industry-Standard Practices
- **Unified Push Gateway / Notification Service**: Uber, LinkedIn, and Airbnb all have channel-agnostic notification gateways (e.g. LinkedIn's Air Traffic Controller, Uber's push platform), with the upper layer decoupled from channels and adapters at the lower layer.
- **Kafka load smoothing + tiered rate limiting**: million-scale batches enter a Kafka topic, and the consumer side rate-limits with token buckets per channel quota, avoiding being throttled on the FCM/APNs side or overloading our own pages (corresponds to C1).
- **APNs/FCM token lifecycle management**: reclaiming invalid tokens (APNs feedback / FCM unregistered responses) — this is precisely the engineering root cause of "uninstalled users never receive anything" (R1).
- **Delivery/read-receipt tracking**: delivery receipt + read receipt feedback, serving as the data source for delivery-rate and subsequent reachability modeling (E1/E2 messaging logs).

### 1.5 AI-Era New Approaches
- **Delivery reachability prediction (M1-F2)**: train a model on footprint activity + historical receipts + device/platform features to assign a "reachability probability" score to the target audience, prioritizing high-reachability users and filtering out low-activity ones (directly addressing "Android delivery rate lower than iOS; once an uninstalled user is selected they never receive anything").
- **Invalid-user filtering (M1-F1)**: combine token-invalidation signals + AI offline/uninstall prediction to remove users who are bound never to receive before sending, improving effective delivery rate and channel ROI.
- **Send-Time Optimization (STO)**: predict each individual's optimal send moment based on their historical open-time distribution, and stagger sends (the same idea as the industry's Braze/MoEngage STO), which both raises open rate and naturally smooths peaks.
- **Next-Best-Channel**: when Push has low reachability, AI decides whether to degrade to SMS or In-App (rather than a fixed rule), in tandem with the A5 fallback.

### 1.6 Recommendation for Botim
**Go with Solution C for the MVP, while converging the architecture toward Solution B.** The 6-week window + Botim's already-consolidated interfaces + unclear rate-limiting/Opt-out specs (R4) determine that Phase 1 will not rebuild the gateway: use a thin orchestration layer over the existing consolidated Push/SMS interfaces to get the wallet-activation Push + messaging log running (A1/B1/C1/D1/E1), but **use Kafka at enqueue time and reserve adapter and policy hooks in the shape of Solution B** to avoid a later teardown. AI increments (F1/F2 reachability, STO) depend on accumulating messaging logs (E1/E2) and are layered on as Phase 2, not blocking the MVP. For the unified frequency-capping integration point (C2), only the execution-side hook is left here; the main body is in M3.

---

## 2. M2 Audience Segmentation (Rule Engine + NL2SQL) [Key Focus · 3 Solutions]

### 2.1 Requirements & Constraints Recap
Replicate Step ① audience segmentation of MoEngage's "pure rule-engine 3-step method": infinitely nested AND/OR/NOT multi-conditions, time-window/frequency operators, exclusion audiences, batch evaluation refreshed to hourly level. Constraints: **80% of campaigns use only 5–10 segments**, batch-dominant, T+1 cleansing + hourly level (not the bottleneck); **OLAP engine undecided** (Data Team to call the shot); no email, business-line IDs not yet unified, no CDP; need a MoEngage-syntax-compatible layer for a smooth migration of ~800 campaigns, reusing the existing rule engine rather than a full rewrite; incremental value comes from AI (NL2SQL). "Stop pushing to already-converted users" is the primary real-time need.

### 2.2 Candidate Solutions (3)

**Solution A — Interpreted DSL execution (real-time rule-tree traversal)**
- Approach: define rules as an AST/rule tree, and at evaluation time traverse the rule tree per user to determine hits (in memory or row-by-row scan). Strong expressiveness, supporting arbitrary nesting and complex operators; when a rule changes it takes effect immediately, without recompilation/pushdown.
- Applicable Scenarios: real-time/near-real-time per-user determination (e.g. "stop pushing to already-converted users" suppression, per-event determination for triggered campaigns), small audience scale, extremely flexible rules; **not suitable** for million-scale full-volume batch scans (row-by-row traversal is costly).

**Solution B — Compile-to-SQL (DSL → SQL pushdown to OLAP)**
- Approach: after parsing the DSL/MoEngage-syntax-compatible layer, **compile it into SQL** and push it down to the Data Team's OLAP engine (ClickHouse/Doris/StarRocks, etc.) to execute on a wide table, with the result being the audience snapshot. Reuse OLAP's columnar storage + vectorization + distributed scan to handle millions.
- Applicable Scenarios: batch-dominant (Botim's current state), an existing/forthcoming OLAP wide table, many time-window and aggregation operators. **Strongly depends on the Data Team's OLAP selection being settled.**

**Solution C — Precomputation + inverted index / Bitmap (tag inverted index + RoaringBitmap)**
- Approach: at T+1/hourly level, precompute user tags into a **tag→user inverted index**, where each tag value corresponds to a **RoaringBitmap** (customer_id mapped to an integer bit position); audience AND/OR/difference = bitmap AND/OR/ANDNOT, completing large-audience operations in seconds; audience-size estimation is taken directly from the bitmap cardinality.
- Applicable Scenarios: the highly-reused 5–10 fixed segments (covering 80% of campaigns), needing real-time audience-size estimation, frequent large-audience AND/OR/difference; optimal for discrete tag-type conditions, while complex time-window/continuous-aggregation operators require accompanying precomputation/materialization.

### 2.3 Pros/Cons Comparison (High / Medium / Low)

| Dimension | A Interpreted DSL execution | B Compile-to-SQL | C Inverted index + Bitmap |
|---|---|---|---|
| Implementation Cost | Medium (engine can reuse the existing one) | Medium (parser + SQL templates, reuse compatibility layer) | High (need to build a tag-precomputation + index pipeline) |
| Performance/Latency (million-scale batch) | **Low** (row-by-row traversal is slow) | High (OLAP vectorization) | **High** (bitmap AND/OR/difference in seconds) |
| Performance/Latency (single-user real-time) | **High** (tree traversal is instant) | Low (high SQL startup overhead) | Medium (needs to query multiple bitmaps) |
| Scalability (operator expressiveness) | **High** (arbitrary nesting/custom operators) | High (strong SQL expressiveness) | Medium (strong for discrete tags, weak for continuous/time-window) |
| Operability | Medium | **High** (leverages Data Team's OLAP, little self-maintenance) | Low (self-maintained index + consistency/updates) |
| Fit for Botim | Medium (suits E3 real-time suppression + triggered) | **High (if OLAP is settled)** (batch-dominant + reuse compatibility layer) | Medium (suits accelerating high-frequency templates, heavy upfront) |

### 2.4 Industry-Standard Practices
- **Rule-compile-to-SQL + OLAP wide table**: the audience/segment engines of Segment / Amplitude / mParticle mostly take the route of "rules → query pushdown to columnar storage", with ClickHouse / Apache Doris / StarRocks as common execution foundations; user behavior is flattened into a wide table for batch processing.
- **RoaringBitmap audience segmentation**: Alibaba Damo Pan / Sensors Data / GrowingIO / Tencent's tag platform commonly use RoaringBitmap for hundred-million-scale audience AND/OR/difference and real-time audience-size estimation — the de facto standard for tag platforms (Druid's and Doris's internal bitmap aggregation share the same origin).
- **CDP Segment Engine**: dual-track batch segments (T+1/hourly materialization) + real-time segments (streaming updates), which precisely corresponds to Botim's "batch-dominant + real-time suppression of already-converted users".
- **Interpreted DSL execution**: Drools / in-house rule trees used for real-time single-user determination and triggered scenarios.

### 2.5 AI-Era New Approaches
- **Comparison of three NL2SQL routes**:
  1. **Template / slot-filling**: preset high-frequency data-fetch templates (same structure, different parameters), where NL only fills the slots. High accuracy, controllable, zero hallucination, but narrow coverage. → Corresponds to B4 template-coverage-first, D2 high-frequency template library.
  2. **RAG + schema-linking + LLM**: retrieve tables/fields/tag dictionary + historical SQL into the context, and the LLM generates SQL. Broad coverage, flexible, but with hallucination risk and dependent on schema quality and tag-dictionary completeness.
  3. **Domain fine-tuned LLM**: fine-tune a dedicated model on Botim's historical data-fetch NL-SQL pairs. High accuracy ceiling, but requires sufficient labeled samples and high iteration cost, not realistic within 6 weeks.
- **Accuracy safeguards (B2/B3)**: generated SQL/DSL is **transparent, previewable, and editable** (AI is not a black box); high-frequency template hits output directly, with **confidence prompts**; long-tail/low-confidence cases route to manual handling or to the visual constructor (A6).
- **Lookalike (C1)**: seed audience → user-vector similarity retrieval (embedding + ANN) or a positive/negative-sample classification model to expand to a similar audience.
- **Propensity segmentation (C2)**: churn/conversion/activation propensity scoring (GBDT/logistic regression), upgrading "pure rule filtering" into "segmentation by probability".

### 2.6 Recommendation for Botim
**A branched conclusion, depending on whether the Data Team's OLAP is settled:**
- **If the OLAP engine is decided/about to be decided (preferred) → Solution B as the backbone**: after parsing the MoEngage-syntax-compatible layer (A7), compile to SQL and push down to OLAP, reusing the existing rule engine without a rewrite, with batch-dominance being a natural fit and operability leveraging the Data Team for little self-maintenance — the most stable for a 6-week MVP.
- **If OLAP has no near-term conclusion → Solution C as fallback**: first use an inverted index + RoaringBitmap to precompute the high-frequency 5–10 segments (covering 80% of campaigns, D2) into bitmaps, enabling AND/OR/difference in seconds + real-time audience-size estimation (satisfying A6), so the MVP can run without waiting for OLAP.
- **Solution A as a "real-time stopgap" rather than the backbone**: interpreted DSL execution is dedicated to the near-real-time suppression of "stop pushing to already-converted users" (E3) and per-event determination for triggered campaigns (A8), complementing the batch backbone of B/C.

NL2SQL takes a **combination of Route 1 + Route 2**: first solidify high-frequency templates (Route 1, ensuring accuracy and 6-week deliverability), with the long tail using RAG + schema-linking (Route 2) + previewable-and-editable safeguards; do not bet on full automation, do not adopt fine-tuning (R3). AI increments (Lookalike/propensity segmentation) are layered on as Phase 2.

---

## 3. M3 Orchestration (A/B/N)

### 3.1 Requirements & Constraints Recap
Replicate Steps ②③ of MoEngage's 3-step method: define content (multiple A/B/N groups + version tweaks), define push time/trigger conditions; campaign-lifecycle state machine; Flow nodes (delay/branch/A·B/wait-for-event/webhook, complexity pending Growth's confirmation R3). Constraints: ~800 campaigns/year, 2–3 per day, **batch-dominant, partially real-time triggered** (e.g. "push 10 minutes after account opening"); unified Asia/Dubai time zone; **fill the complete gap MoEngage left for cross-campaign frequency capping/dedup/quiet hours** (currently a user might receive 3 in one day); the splitter reuses the M2/M5 rule engine; AI orchestration (GPT replacing orchestration) is the biggest highlight.

### 3.2 Candidate Solutions

**Solution A — Workflow / state-machine engine (Temporal / Cadence / in-house state machine + Flink CEP)**
- Approach: use a persistent workflow engine (Temporal/Cadence) or an in-house state machine to drive multi-step journeys, natively supporting long-cycle nodes such as "delay/wait-for-event/branch/timeout"; for real-time triggers, use **Flink CEP** for event-pattern matching (e.g. "if no top-up within 10 minutes after account opening, then push"). A Flow is the workflow definition, with recoverable and observable state.
- Applicable Scenarios: multi-step triggered journeys (welcome series, churn-recovery flow), long-lifecycle orchestration requiring "wait-for-event + delay + conditional branching", when real-time triggers account for a high proportion.

**Solution B — Rules + batch scheduling (DAG / scheduled batch runs, lightweight)**
- Approach: a campaign = one config (audience + content + schedule + A/B/N split ratios), and a scheduled scheduler (Airflow/Quartz/cron + DAG-like) runs batches per schedule: at the appointed time, fetch the M2 audience snapshot → split → hand to M1 for sending. The state machine degenerates into a campaign-level lifecycle (draft/published/running/paused/ended), with no need for a per-user long-cycle workflow.
- Applicable Scenarios: batch-dominant, with campaigns mostly being "audience segmentation → one-off/periodic mass send" (Botim's current 2–3 per day), shallow Flow branches; lightweight implementation, simple operability, achievable in 6 weeks.

### 3.3 Pros/Cons Comparison (High / Medium / Low)

| Dimension | A Workflow/state-machine engine + CEP | B Rules + batch scheduling |
|---|---|---|
| Implementation Cost | High (introducing Temporal/Flink, heavy learning and operability) | **Low** (scheduling + config-driven, reuse M2/M1) |
| Performance/Latency (real-time triggers) | **High** (CEP second-level event triggering) | Low (batch granularity, hard to do second-level triggering) |
| Performance/Latency (batch mass send) | Medium (per-instance workflow overhead) | **High** (steady-rate batch delivery) |
| Scalability (complex Flow) | **High** (arbitrary multi-step/wait/branch) | Medium (deep Flow requires extending the state machine) |
| Operability | Low (one more stateful distributed system) | **High** (no extra heavy components) |
| Fit for Botim | Medium (using a sledgehammer to crack a nut if real-time share is small) | **High** (batch-dominant reality best fits a 6-week MVP) |

### 3.4 Industry-Standard Practices
- **Temporal / Cadence**: Uber (where Cadence originated), Netflix, and Datadog use them to orchestrate long-cycle, recoverable multi-step processes; marketing journey engines (Braze Canvas, MoEngage Flows, Iterable) are essentially state machines + wait nodes.
- **Airflow / DAG scheduling**: batch marketing campaigns run on schedule per DAG, where audience segmentation → splitting → delivery is the typical pipeline.
- **Flink CEP / event-driven streaming**: the standard practice for real-time triggered journeys ("if N minutes after event A, B has not occurred, then trigger"), with the Kafka + Flink CEP combination.
- **Message-orchestration / frequency-capping middle platform**: cross-campaign frequency caps, dedup, and quiet hours typically land in a unified send-decision layer (e.g. Braze's frequency capping) — the gap Botim needs to fill.

### 3.5 AI-Era New Approaches
- **AI orchestration (M3-F1, the biggest highlight)**: a natural-language description of the campaign goal → the LLM automatically generates "audience (calling M2 NL2SQL) + copy (calling M6) + schedule + Flow draft", corresponding to the survey's "could explore using GPT to replace orchestration". The result is **previewable and editable** (F2); AI is not a black box.
- **Intelligent traffic allocation (multi-armed bandit)**: use Thompson Sampling / UCB **contextual bandit** to replace fixed-ratio A/B/N — dynamically tilting traffic toward the winning version, reducing exposure loss from inferior versions, more sample-efficient and faster-converging than fixed splitting + post-hoc significance testing (B3).
- **Frequency-capping/dedup strategy optimization**: AI learns individual fatigue and dynamically decides each user's daily cap and quiet hours (rather than picking a single fixed global value), optimizing the balance of "messaging volume vs. fatigue/unsubscribes" (E1/E3).

### 3.6 Recommendation for Botim
**Use Solution B as the backbone, supplement triggered cases with CEP, and run AI orchestration in parallel.** Botim being batch-dominant (2–3 per day) + the 6-week window + the splitter reusing M2/M5 determine that the backbone uses **rules + batch scheduling (Solution B)**: campaign-config-driven, batch runs at the appointed time, fixed-ratio A/B/N splitting + post-hoc significance testing (B3), lightweight and achievable. **Triggered campaigns (e.g. push 10 minutes after account opening, a small share) are supplemented point-by-point with Flink CEP**, rather than introducing the full Temporal stack for this — unless Growth feedback indicates a real-time share >30% (R2) warranting an upgrade to Solution A. Cross-campaign frequency capping/dedup/quiet hours (E1–E3) fill MoEngage's gap as a unified send-decision layer, but **scaled-down and deferred** (since the current state has none, it does not affect "no worse than the current state"); the **Shadow-period dedup middle layer (E4/M7) is a hard requirement that must be built first** to prevent double-sending from polluting the control group. AI orchestration (F1/F2) and bandit intelligent splitting run in parallel as Phase 2 increments, with previewable-and-editable safeguards, not blocking Phase 1.

---

## 4. Quick Reference: Recommended Selections for the Three Modules

| Module | Backbone Recommendation | Key Supplement | Trigger Condition/Branch |
|---|---|---|---|
| **M1 Messaging** | MVP Solution C (reuse consolidated interfaces + thin orchestration), converge architecture toward B (unified gateway) | Kafka load smoothing + adapter/policy hooks reserved; AI reachability/STO deferred | Grow into Solution B once interface specs are clear |
| **M2 Segmentation** | OLAP settled → **Solution B compile-to-SQL**; no conclusion → **Solution C bitmap fallback** | Solution A interpreted DSL dedicated to supplementing real-time suppression (E3)/trigger determination | Depends on the Data Team's OLAP decision |
| **M3 Orchestration** | **Solution B rules + batch scheduling** | Supplement triggered cases with **Flink CEP**; Shadow dedup middle layer is a must | Upgrade to Solution A (Temporal) only if real-time share >30% |

---

> **One-line wrap-up**: all three modules take "achievable in 6 weeks + fitting Botim's batch-dominant/consolidated reality/OLAP-pending" as the first principle — M1 starts with thin orchestration and converges toward the unified gateway; M2 goes compile-to-SQL or bitmap depending on the OLAP selection, with interpreted execution supplementing real-time; M3 uses batch scheduling as the backbone with CEP supplementing triggers; AI (reachability/STO, NL2SQL, AI orchestration + bandit) is uniformly run in parallel as increments, with previewable-and-editable safeguards, not betting on full automation and not blocking the MVP.

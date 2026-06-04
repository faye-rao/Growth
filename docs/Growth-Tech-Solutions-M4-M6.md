# Growth Technical Solution Comparison · M4 / M5 / M6

> Botim self-built Growth Platform (MoEngage competitor replacement) · Technical selection comparison across three modules
> Companion docs: `Growth特性清单-M4-1.md` / `M5-1.md` / `M6-1.md` / `Growth特性清单-总览索引.md`
> Rating legend: Implementation Cost (Low = easy to implement) / Performance/Latency / Scalability / Operability / Fit for Botim, all expressed uniformly as **High / Medium / Low**.

## 0. Botim Key Constraints Running Through This Document

| Dimension | Facts | Impact on Technical Selection |
|---|---|---|
| Data | footprint full backup; T+1 cleansing + hourly incremental; **no email** (primary keys customer_id / phone number); OLAP undecided; business lines not yet connected, no CDP | Primary-key uniqueness forces all ID joins through customer_id/phone number; T+1-first → precomputed route is a natural fit; OLAP undecided → selection must be "replaceable, not locked in" |
| Business | attribution window 1–2 days (empirical, not hard-set); **cross-product funnel is the core differentiator** (call → Wallet → Remittance, which MoEngage cannot answer); service penetration 7.5% → 15%; home-page 1-to-1 personalization cards can be self-built (only borrowing delivery, client-side rendering); multilingual = Hindi/Tagalog/Arabic/English; incremental value comes from AI | Cross-product funnel strongly depends on cross-business-line ID-mapping (M8 prerequisite); home page has a second-level SLA but the share of real-time activity is small → precompute first; multilingual generation + feedback loop is the M6 main line |

---

# M4 · Campaign Funnel Tracking / attribution

## 1. Requirements & Constraints Recap
Replicate MoEngage's "view → click → conversion" single-campaign funnel (A1–A3) + 1–2 day configurable attribution (B), and use the **cross-product funnel (C, call → Wallet → Remittance)** as the core differentiator to directly answer "the question MoEngage cannot answer." Source data comes from the M8 reach/conversion log wide table; the cross-product funnel strongly depends on the **M8 cross-business-line ID-mapping** (no email → customer_id/phone number). Heavy dashboards belong to the Data Team; we only do tracking + light presentation (NL2SQL / light dashboards). Company-wide metric definitions not yet unified (R1) is a development prerequisite.

## 2. Candidate Solutions (≥2)

- **Solution A: ad-hoc SQL window functions / sessionization (funnel via window function + sessionization)**
  Approach: On the detail-event wide table, use `ROW_NUMBER / LEAD / LAG` + time-difference logic to determine ordering and the attribution window; after sessionization, aggregate by step order. The funnel definition is simply a parameterized piece of SQL, computed on-the-fly at query time.
  Applicable Scenarios: highly variable funnel definitions, exploratory phase, low campaign volume, strong demand for "drill-down on any dimension"; a natural fit with NL2SQL (text-to-SQL).

- **Solution B: precomputed / materialized funnel (offline pre-aggregate fixed funnels, read directly at query time)**
  Approach: For the 5–10 fixed funnels operations actually review regularly, run T+1 batch jobs to pre-aggregate into a funnel result table / materialized view (user → step → time); queries only read the result. Daily snapshots can be layered on to support retention.
  Applicable Scenarios: fixed funnels, high-frequency repeated dashboard viewing, sensitivity to query latency (light dashboards open in seconds); a fit with Botim's T+1 main route.

- **Solution C: OLAP built-in funnel / retention functions (ClickHouse `windowFunnel` / `retention`, Apache Druid)**
  Approach: Ingest events into a columnar OLAP store and use the engine's built-in funnel/retention operators to perform step-order determination efficiently engine-side; the cross-product funnel uses customer_id to do cross-business-line JOINs / same-primary-key aggregation across the event stream.
  Applicable Scenarios: high event volume, need for interactive querying, both funnel + retention required, and heavy-JOIN/sequence-matching scenarios such as the cross-product funnel. **Botim's OLAP is undecided, so this solution is tied to "deciding on OLAP first."**

## 3. Pros/Cons Comparison

| Dimension | A ad-hoc SQL window | B precomputed/materialized | C OLAP built-in functions |
|---|---|---|---|
| Implementation Cost | Medium (SQL skill threshold, no new components needed) | Medium (must build batch jobs + result-table governance) | Medium-High (must first land OLAP selection/operations) |
| Performance/Latency | Low (slow on-the-fly compute on large data volumes) | High (direct read of results, millisecond-to-second level) | High (columnar storage + built-in operators are fastest) |
| Scalability | Medium (flexible for any funnel, but struggles at volume) | Low (fixed funnels; a new funnel requires a new job) | High (a new funnel only changes SQL; scales at volume) |
| Operability | High (relies on existing data warehouse, light) | Medium (batch jobs + result-table reconciliation) | Low (one more OLAP cluster to maintain) |
| Fit for Botim | Medium (exploration/NL2SQL friendly, but doesn't withstand heavy dashboards) | High (T+1 main route + light dashboards open in seconds + easy reconciliation D3) | High (best solution for cross-product funnel, but requires first closing the OLAP-undecided issue) |

## 4. Industry-Standard Practices
- **ClickHouse `windowFunnel()` / `retention()`**: the de facto standard for growth analytics; computes step order and retention directly over the event stream keyed by customer_id; cross-product only requires the same primary key for sequence aggregation.
- **Apache Druid + sequence/funnel extensions**: interactive OLAP, suited to low-latency drill-down on large event volumes.
- **Amplitude / Mixpanel internal event-analysis engines**: product-grade funnel/retention/path analysis, essentially an engineered packaging of "event stream + columnar storage + pre-aggregation + sequence matching" — confirming that "precomputed fixed funnels + engine built-in sequence operators" is the mainstream combination.

## 5. AI-Era New Approaches
- **Multi-touch attribution models replacing empirical fixed windows**: Shapley value / Markov chain attribution assigns contribution across touchpoints, replacing the coarse "1–2 day hard window" metric (corresponds to D4 automated attribution insights). Botim starts with the fixed window as a fallback and uses AI attribution as an incremental retrospective.
- **Funnel anomaly detection**: time-series anomaly alerting on the conversion rate of each funnel step, supporting D3 "numbers must reconcile" reconciliation + discrepancy alerts.
- **Natural-language querying (text-to-SQL) to produce funnels**: reuse M2 NL2SQL to generate funnel SQL in "plain language" (E1), lowering the barrier to viewing funnels.

## 6. Recommendation for Botim
**Take an off-the-shelf OLAP and use `windowFunnel` to compute funnels as the backbone, layer T+1 precomputed materialization on top for fixed high-frequency funnels, and only build the cross-product funnel after M8 ID-mapping is connected.** Specifically: the single-campaign funnel (A1–A3) + retention first uses ClickHouse `windowFunnel/retention` (if OLAP selection does not land in the short term, degrade to Solution A ad-hoc SQL as a fallback on the existing data warehouse); the 5–10 funnels operations actually review regularly are precomputed into result tables per Solution B, ensuring light dashboards open in seconds and facilitating D3 dual-run reconciliation; **the cross-product funnel (C) is the differentiation linchpin, but customer_id cross-business-line mapping coverage/accuracy is a hard prerequisite — close R2 (M8 ID-mapping) before developing, otherwise "numbers don't reconcile" damages trust in return**. Attribution starts with a configurable fixed window (B2), with Shapley/Markov and anomaly detection deferred as AI increments. Before development, close R1 (metric-definition unification) first to avoid A5/B rework.

---

# M5 · 1-to-1 Personalization (self-built delivery fetch)

## 1. Requirements & Constraints Recap
Replicate MoEngage's `Web & App (API)`-type experience: equivalent `POST /experiences/fetch` (A1) returns the payload a user is due per experience_key, with qualification logic **reusing the M2 rule engine** (B1) and client-side rendering (D1). Home-page loading requires a **second-level SLA** (A7), but the share of real-time activity is small and it is mostly batch. Multilingual payload (C3, Hindi/Tagalog/Arabic/English) connects to M6. No email → identifiers use customer_id/phone number as primary keys (A3), depending on M8 ID-mapping. Path ① inherently only borrows delivery and can be self-built, making it the **lowest-risk decoupling point that should be validated first**.

## 2. Candidate Solutions (≥2)

- **Solution A: real-time qualification at request time (run rule qualification for audience+variation in real time at fetch)**
  Approach: When a fetch arrives, run the M2 rule engine in real time to determine the qualifying audience → assign variation → assemble and return the payload.
  Applicable Scenarios: rapidly changing audience definitions, strong real-time needs (behavior-triggered cards), controllable user volume/QPS; best real-time responsiveness but heavy rule-evaluation pressure under a second-level SLA.

- **Solution B: precomputed user→experience mapping (computed offline, KV lookup at fetch)**
  Approach: T+1 / hourly offline computation of "user → qualifying experience/variation/payload reference" written into a KV store (Redis, etc.); fetch degrades to a single millisecond-level KV point lookup.
  Applicable Scenarios: relatively stable audiences, mostly batch, strong home-page second-level SLA constraint; highly aligned with Botim's T+1 main route + small real-time share, at the cost of weak real-time responsiveness.

- **Solution C: hybrid (precompute-first + real-time fallback + edge/client caching)**
  Approach: By default go through Solution B's precomputed KV; on KV miss or when real-time attributes are needed, fall back to Solution A real-time qualification; the client SDK caches the last payload, and on fetch timeout/failure falls back to the cache or default content (D2). Multi-layer degradation protects qualification rate and experience.
  Applicable Scenarios: the vast majority of Botim home-page scenarios — needing both second-level stability and a small amount of real-time fallback plus high availability.

## 3. Pros/Cons Comparison

| Dimension | A real-time qualification | B precomputed KV | C hybrid (precompute+fallback+cache) |
|---|---|---|---|
| Implementation Cost | Medium (directly reuse M2, but must withstand QPS) | Medium (build offline jobs + KV write governance) | Medium-High (two paths + degradation logic + cache contract) |
| Performance/Latency | Low-Medium (rule evaluation hard to keep stable at second level) | High (KV point lookup, millisecond level) | High (millisecond on main path, occasional slowness on fallback) |
| Scalability | Low (QPS grows linearly with users, expensive to scale) | High (read scaling via horizontal KV expansion) | High (read scaling + real-time only as fallback, low pressure) |
| Operability | Medium (online rule-engine hotspots/rate limiting) | Medium (offline jobs + KV consistency/expiry) | Low-Medium (multi-layer but each layer mature, self-healing degradation) |
| Fit for Botim | Low (high risk under second-level SLA, and real-time share is small) | Medium-High (fits T+1, but pure precompute is weak on real-time and poor on KV cold start) | High (second-level stability + a little real-time fallback + cache degradation, closest fit for the home page) |

## 4. Industry-Standard Practices
- **Content Decisioning API**: decision interfaces such as Adobe Target / Optimizely that "return content/variant for a user by key" are precisely the benchmark form of fetch.
- **Feature Store + online inference**: compute features/audience labels offline into an online feature store and read them with low latency at request time — i.e., the industrialized form of Solution B.
- **CDN edge caching + KV (Redis) query**: high-QPS content delivery like the home page commonly uses edge/Redis for millisecond-level KV qualification + cache degradation, confirming Solution C.

## 5. AI-Era New Approaches
- **Personalized recommendation (recall + ranking)**: recall + rank candidate content/variation against user profiles/historical behavior for intelligent qualification (B5), more "1-to-1" than static rules.
- **Multi-armed bandit (MAB) to select the best variation**: online explore-exploit among A/B/N variations, automatically tilting traffic toward high-conversion variants and eliminating manual splitting (B3 enhancement).
- **Generative content**: payload copy/card content produced by M6 generative multilingual output, achieving 1-to-1 personalization on the content side.

## 6. Recommendation for Botim
**Choose Solution C: precompute-first + real-time fallback + client/edge cache degradation.** The home-page second-level SLA + small share of real-time activity + Botim's T+1 main route dictate that the main path should be "compute user → experience/variation/payload reference offline and write to Redis, with fetch doing a millisecond-level KV point lookup"; only fall back to the M2 rule engine for real-time qualification on the small number of scenarios needing real-time attributes or on KV miss, avoiding online rule evaluation having to withstand full QPS; the client SDK must do caching + timeout degradation (D2/D3), falling back to the last payload or a default card on fetch failure to protect the home-page experience. Qualification logic is consolidated into the M2 rule engine (build once, use in many places). AI personalized recommendation (B5) and MAB selection are deferred as increments; first get "equivalent fetch + decoupling" working on one card slot in Phase 1 to validate feasibility. Prerequisites: first close R1 (KV schema ownership), R3 (real-time SLA tier), and R4 (customer_id cross-business-line mapping coverage).

---

# M6 · AI Copywriting (multilingual generation + feedback loop)

## 1. Requirements & Constraints Recap
A purely incremental module with no MoEngage counterpart. The core is **one-click multilingual generation** (A1, Hindi/Tagalog/Arabic/English) to compress the "copywriting" bottleneck (row18), localization rather than machine translation (A2, Arabic RTL), multiple versions fed to M3 A/B/N (A3), and generation that is previewable and editable (A4, AI is not a black box). Through a **historical copy-to-performance feedback loop** (B, joining click-through rate/conversion rate/ROI), the AI learns high-conversion styles. Compliance/sensitive-word pre-screening (C1) + Growth self-review (C2). Copy binding/storage (D) serves M3 orchestration and M5 payload calls. Feasibility of the feedback loop depends on the completeness of the D16/D17 paired data (R1).

## 2. Candidate Solutions (≥2)

- **Solution A: general-purpose LLM API + prompt engineering (zero-shot/few-shot)**
  Approach: Call a general-purpose large-model API and use a structured prompt (campaign goal/Offer/audience/language/brand tone) + few-shot examples to directly generate multilingual copy, previewable and editable by operations.
  Applicable Scenarios: fastest to start, zero training cost, multilingual out of the box; brand consistency relies on prompt constraints, and the quality ceiling is influenced by prompt engineering and example quality.

- **Solution B: RAG retrieval-augmented (retrieve historical high-conversion copy/brand corpus for injection)**
  Approach: Build a vector store of historical high-conversion copy + brand corpus; at generation time retrieve the top-k relevant samples and inject them into the prompt (in-context), making output close to the brand's already-validated high-conversion style.
  Applicable Scenarios: existing historical copy-to-performance paired data (D16/D17 in place), need for brand consistency and "learning from past high conversion"; a lightweight engineering implementation of the Group B feedback loop, requiring no training.

- **Solution C: domain fine-tuning / LoRA (multilingual + brand tone)**
  Approach: Use paired samples to do LoRA fine-tuning on an open-source/fine-tunable model, solidifying brand tone and the localized style of each language, modeled per language (B3).
  Applicable Scenarios: large copy volume, strong brand-tone constraints, pursuit of stable consistency and controllable cost (cheap inference); but high data/training/evaluation/iteration cost, requiring sufficient paired samples.

## 3. Pros/Cons Comparison

| Dimension | A prompt engineering | B RAG retrieval-augmented | C fine-tuning/LoRA |
|---|---|---|---|
| Implementation Cost | Low (connect API + write prompts) | Medium (build vector store + retrieval pipeline) | High (data governance + training + evaluation iteration) |
| Performance/Latency | High (single API call, fast) | Medium (one extra retrieval, still acceptable) | High (self-hosted inference is fast, but long ramp-up) |
| Scalability | Medium (adding languages/scenarios relies on changing prompts) | High (expand corpus to expand capability, hot-updatable) | Medium (a new style needs retraining/re-fine-tuning) |
| Operability | Low (managed API, almost no operations) | Medium (vector store + corpus updates) | Low-High (model hosting + retraining pipeline, heavy) |
| Fit for Botim | High (fastest to start, four languages out of the box, editable) | High (directly delivers the Group B feedback loop + brand consistency) | Medium (data may not be ready, ROI yet to be validated, best deferred) |

## 4. Industry-Standard Practices
- **Jasper / copy.ai model**: the productized path for marketing-copy generation — templates + brand voice constraints + multilingual, proving that "general-purpose LLM + prompt/brand-tone constraints" is sufficient to support the marketing-copy scenario.
- **Brand Voice constraints**: fix the tone using brand-tone samples + style instructions, corresponding to A2 localization and brand consistency.
- **Machine translation vs. native multilingual generation**: the industry consensus is that marketing copy should be "natively generated per language" (per local expression habits) rather than directly translated from English, exactly matching the A2 non-machine-translation requirement.

## 5. AI-Era New Approaches
- **Performance feedback loop (bandit / RLHF to select high-conversion copy)**: use click-through/conversion rates flowing back from M4 as reward signals, and use a multi-armed bandit / preference learning to select the high-conversion version among candidate copy (B4 performance-feedback incremental learning).
- **Native multilingual generation vs. translation**: generate directly in the target language and adapt to local expression habits (A2), superior to "write in English then translate."
- **Compliance sensitive-word pre-screening**: do UAE compliance + sensitive-word pre-screening on the generation side (C1) to filter obvious violations, then hand off to Growth self-review (C2).

## 6. Recommendation for Botim
**Start with prompt engineering (A), layer on RAG (B) once data is in place to deliver the feedback loop, and defer fine-tuning (C).** In Phase 1, first use a general-purpose LLM API + structured prompts to generate "English + 1 primary language" with editing + manual gatekeeping (A4/C2); this can go live without depending on the feedback loop and compresses the "copywriting" bottleneck fastest. Once the D16/D17 historical copy-to-performance paired data is in place (R1 closed), build a vector store of historical high-conversion copy + brand corpus to do RAG, retrieving and injecting at generation time, achieving the Group B "learn high-conversion style" at low cost while preserving brand consistency; for multilingual, insist on **native generation rather than machine translation** (A2, Arabic RTL adaptation). Only evaluate LoRA fine-tuning when copy volume is large enough, paired samples are sufficient, and brand tone needs strong solidification, avoiding premature investment in a high-cost training pipeline. The feedback loop uses M4 return data for bandit selection (B4) as an increment. Compliance pre-screening (C1) is implemented per the metrics Growth provides (R2); before they are decided, do a general sensitive-word fallback first.

---

## Conclusion: Three-Module Recommendation Overview

| Module | Recommended Backbone | One-Sentence Rationale |
|---|---|---|
| **M4** | Take an off-the-shelf OLAP using `windowFunnel` + T+1 precompute for high-frequency funnels; cross-product funnel awaits M8 ID-mapping connection | Engine built-in sequence operators are optimal; cross-product depends on customer_id cross-line connection, so close the ID prerequisite first |
| **M5** | Precompute-first + real-time fallback + cache degradation (Solution C) | Home-page second-level SLA + small real-time share + T+1 main route; millisecond KV point lookup is most stable |
| **M6** | Start with prompt engineering → RAG to deliver the feedback loop → defer fine-tuning | Fastest to land; once data is in place it preserves brand consistency and high conversion; fine-tuning cost is high and best deferred |

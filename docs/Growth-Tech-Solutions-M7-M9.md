# Growth Technical Solution Comparison · M7 / M8 / M9

> Botim self-developed Growth Platform (MoEngage competitor replacement) — technology selection comparison for three modules
> Companion docs: `Growth特性清单-M7/M8/M9-1.md`, `Growth特性清单-总览索引.md`
> Authoring perspective: senior architect, providing implementable selections aligned with Botim's existing constraints.

## Botim Key Constraints Throughout (selection premises)

| Dimension | Fact | Impact on Selection |
|---|---|---|
| Data source | footprint full backup (foreseen at onboarding that MoEngage would be replaced, yet "almost nobody looks at it"); the Data Team's T+1 cleansing is the main body, with us as the consumer + supplementing touch logs | Leans toward "reuse existing, build little"; batch-dominant → the T+1 route benefits the timeline |
| Primary key | **No email**, primary key = customer_id / phone number | ID linkage relies mainly on deterministic matching, with probabilistic/graph matching only filling gaps |
| OLAP | Engine undecided, provided by the Data Team | M8/M9 do not lock into an engine; build engine-agnostic consumption wide tables / views |
| CDP / business lines | No CDP, business lines not unified | ID-Mapping consumes the Data Team's tables; do not build in-house |
| Logs | Touch / conversion logs complete down to user level | M7 control-group sample source and dedup ledger have a handhold |
| Acceptance | Shadow 5% traffic split, produce a report within 2 weeks proving "not below MoEngage" | M7 is the acceptance lynchpin; must be truly parallel and statistically credible |
| Dedup | Currently no cross-campaign dedup → preventing double-send during the Shadow period is a **hard requirement** | M7 must include a dedup middle-layer |
| BI boundary | Dashboard / full BI not built (Data Team rebuilds + product-side Amplitude) | M9 deliberately scoped-down, actively demarcating scope |
| Internal metrics | Whether MoEngage's RFM / churn / engagement are actually used is yet to be checked | Affects the M8 / M9 completion scope |

---

# M7 · Shadow Validation Framework (the acceptance lynchpin for replacement)

## 1. Requirements & Constraints Recap
Shadow is the exit condition for "daring to replace MoEngage": split 5% of traffic for the same user group into the new system, route the remainder through MoEngage, and within 2 weeks produce the statistical conclusion that "the new system is not significantly below MoEngage" (M7-A3 / C1 / C2). Currently there is no cross-campaign dedup, and running old and new in parallel will amplify the double-send problem, so the **dedup middle-layer is a hard requirement** (M7-B1). The integration method / latency of MoEngage's touch stream is pending vendor confirmation (M7-D1).

## 2. Candidate Solutions (≥2)

### Solution A: online traffic-split A/B (true parallel A/B + dedup middle-layer)
- **Approach**: Reuse the M2 rules engine to apply deterministic hash-based traffic split to the target audience (`hash(customer_id) % 100 < 5` enters the new system), with the remainder going through MoEngage. Both touch paths are preceded by a **dedup/idempotency middle-layer** (a cross-system per-user touch ledger, M7-B2), so the same user is hit by only one path within the observation window. On the reporting side, reuse the M4 attribution definitions; ready as soon as a campaign is sent, and automatically run significance testing over the observation period.
- **Applicable Scenarios**: High-frequency, high-volume scenarios requiring acceptance in a real environment (e.g., wallet-activation Push); hard acceptance requiring "real online performance not below MoEngage." This is the primary path for Botim's acceptance lynchpin.

### Solution B: offline replay / shadow comparison (historical log replay comparison)
- **Approach**: Leave production traffic untouched. Take historical touch / conversion logs and use the new system's rules engine + orchestration to "replay" the same batch of users, comparing the **decision consistency** of the old and new systems under identical inputs (audience-targeting hits, traffic split, frequency-cap decisions). Attribute discrepancies offline.
- **Applicable Scenarios**: Pre-launch regression / smoke tests, validating that the new system's logic is equivalent; low-frequency scenarios or those where splitting live traffic is inconvenient; serving as a pre-step sanity check and supplementary validation for Solution A. **Not a real delivery environment**, so it cannot replace online effectiveness acceptance.

## 3. Pros/Cons Comparison

| Dimension | Solution A online traffic-split A/B | Solution B offline replay comparison |
|---|---|---|
| Implementation Cost | Medium (dedup middle-layer + traffic split reusing M2, approx. 23 person-days including reporting) | Low (reuse logs + engine replay) |
| Performance/Latency | Medium (real-time split + dedup must precede the touch path, millisecond-level overhead) | High (offline batch, no online latency pressure) |
| Scalability | High (split ratio / scenarios configurable, extend by reuse) | Medium (limited by historical log coverage) |
| Operability | Medium (must ensure the dedup middle-layer neither misses nor duplicates, plus double-send monitoring) | Low (offline jobs, re-runnable on failure) |
| Fit for Botim | High (acceptance requires "not below MoEngage online" — only this can prove it; logs already at user level, rules engine reusable) | Medium (can only prove "logical equivalence," cannot prove online effectiveness) |
| Statistical credibility | High (true parallel A/B, significance testing possible) | Low (no controlled delivery, only decision diff) |

## 4. Industry-Standard Practices
- **A/B experimentation platforms**: Random traffic split + significance testing (e.g., Optimizely, internal experimentation platforms), the standard paradigm for online comparison.
- **CUPED (variance reduction)**: Uses pre-experiment covariates to reduce metric variance, significantly improving test sensitivity under a 5% small-traffic, 2-week short-cycle setting — directly matching Botim's "small sample, short cycle."
- **Experiment configuration center / Feature Flag**: Centralized configuration of split rules and traffic-split ratios (LaunchDarkly-style); in M7 this can be borne by the M2 rules engine.
- **Dedup / idempotency middle-layer**: Deduplicated delivery in messaging systems (e.g., idempotency-key-based dedup tables / Bloom filter + Redis sliding window) — exactly the engineering prototype for M7-B1.

## 5. AI-Era New Approaches
- **Uplift modeling**: Estimates the increment of "additional conversions caused by being touched by the new system" rather than a simple between-group mean difference, enabling more accurate identification of the truly incremental population under small samples.
- **DID (difference-in-differences) / Synthetic Control**: When randomization is imperfect or systematic differences exist, use the control group to construct a counterfactual baseline, improving the robustness of conclusions — suitable as a fallback when traffic split cannot be fully randomized.
- **Sequential testing (e.g., mSPRT / always-valid p-values)**: Allows testing while observing, and auto early-stops once significance is reached, **directly shortening the 2-week observation period** and reducing peeking bias, naturally aligning with M7-C3's "ready as soon as sent, auto-updating."

## 6. Recommendation for Botim
**Lead with Solution A online traffic-split A/B, with Solution B offline replay as supplementary pre-launch validation.** The acceptance lynchpin requires proving "not significantly below MoEngage online"; only true parallel A/B can give a credible conclusion. The dedup middle-layer (M7-B1/B2), as a hard requirement, is delivered together with Solution A. On the statistical side, introduce **CUPED for variance reduction + sequential testing for auto early-stop** to produce credible conclusions as early as possible within the 5% small-traffic, 2-week window; Uplift / synthetic control serve as a robustness fallback when the traffic split is non-ideal, not as a mandatory MVP item. Offline replay (B) runs a round of decision-equivalence regression before the split goes live, reducing the risk of "the new system's logic going astray" — the two are complementary rather than mutually exclusive.

---

# M8 · Data Foundation (our part: ingestion + consumption + gap-filling + servicing)

## 1. Requirements & Constraints Recap
M8 is the foundational layer prefacing M2 / M4 / M9 / M7, but **does not rebuild the warehouse**: the T+1 cleansing main body belongs to the Data Team, and we only do "ingest the footprint full backup + consume ID-Mapping/tags + complete touch/conversion logs + audience/funnel wide tables + lightweight DQC + servicing." Constraints: no email (primary key customer_id/phone number), no CDP, OLAP engine undecided, batch-dominant, and the real-time demand is mainly just "don't push to already-converted users" (M8-F1).

## 2. Candidate Solutions (≥2)

### Solution A: use existing OLAP for direct query + build consumption wide tables (most economical)
- **Approach**: Directly reuse the OLAP engine and T+1 cleansing results provided by the Data Team; we only build **consumption-side wide tables / tag views** (audience wide table M8-D1, funnel wide table M8-D2, touch/conversion log wide tables M8-C1/C2). The footprint full backup is usable upon ingestion, with no re-instrumentation needed (M8-A4). ID linkage consumes the Data Team's Mapping tables (deterministic matching, customer_id/phone-number primary key); do not build the mapping in-house.
- **Applicable Scenarios**: Batch-dominant, small real-time share, and the organizational reality that the Data Team already bears the cleansing. Fastest to lay the foundation, lowest operability burden.

### Solution B: build a lightweight real-time warehouse layer (Kafka + Flink + OLAP)
- **Approach**: Beyond the T+1 batch, subscribe to footprint's Kafka event stream (M8-A5), use Flink for unified stream-batch processing, and land in a ClickHouse/Doris-class OLAP to support triggered / near-real-time scenarios (the "don't push to already-converted" suppression layer M8-F1). For ID linkage, in addition to deterministic matching, use probabilistic/graph matching (entity resolution) to fill the Mapping for uncovered business lines.
- **Applicable Scenarios**: When the real-time campaign share is high (>30%), triggered marketing is frequent, the near-real-time suppression demand is strong, and a batch scope-down is unacceptable.

## 3. Pros/Cons Comparison

| Dimension | Solution A use existing OLAP + wide tables | Solution B build a lightweight real-time warehouse |
|---|---|---|
| Implementation Cost | Low (approx. 26 person-days, main body reuses the Data Team) | High (a full Kafka+Flink+OLAP build and operations stack) |
| Performance/Latency | Medium (T+1-dominant, satisfies batch scenarios) | High (near-real-time second-level, supports triggered) |
| Scalability | Medium (constrained by the Data Team engine's capability) | High (an owned stream-batch layer can scale arbitrarily) |
| Operability | Low (no heavy components held) | High (Flink jobs / stream stability / backpressure all to bear) |
| Fit for Botim | High (batch-dominant, Data Team already cleansed, OLAP undecided → no lock-in) | Medium (with a small real-time share, the heavy investment yields low return) |
| Launch risk | Low (no write-back, no downstream, replacement without interruption M8-F3) | Medium (a new real-time path introduces a new failure surface) |

## 4. Industry-Standard Practices
- **Lakehouse** (Delta Lake / Iceberg / Hudi): Lakehouse unification, decoupled storage and compute, matching "reuse the underlying data, don't rebuild the warehouse."
- **CDP**: Customer data platform, but Botim has no CDP and business lines are not unified → do not force-adopt a CDP; only consume the Data Team's Mapping.
- **ID-Mapping / entity resolution**: deterministic (relying on strong identifiers customer_id/phone number) vs probabilistic (probabilistic matching/graph algorithms); in the no-email scenario, deterministic leads with probabilistic as a supplement.
- **Real-time warehouse**: Flink + ClickHouse/Doris is the industry near-real-time standard stack (the prototype for Solution B).
- **Feature Store**: Unified offline/online feature serving (e.g., Feast), can serve as the evolution direction for servicing the audience wide table, not a mandatory MVP item.

## 5. AI-Era New Approaches
- **Entity resolution / ID linkage (graph algorithms + probabilistic matching)**: For business lines not covered by the Data Team's Mapping, use graph clustering / probabilistic matching to fill the mapping, improving cross-product funnel reachability — only as a gap-filler for deterministic matching, not replacing the primary path.
- **AI data-quality anomaly detection (DQC)**: Layer unsupervised anomaly detection on top of lightweight DQC (M8-E3) to automatically discover spikes in wide-table null rates, definition drift, and coverage drops, replacing manual rule-based inspection.

## 6. Recommendation for Botim
**Lead with Solution A: use existing OLAP + reuse the footprint full backup + build consumption wide tables, with ID linkage leading via deterministic matching that consumes the Data Team's Mapping.** Given the batch-dominant reality, the Data Team already bearing the cleansing, and the OLAP engine undecided, building a heavy real-time warehouse in-house is a large investment with low return. Real-time is done only on the sole hard requirement "don't push to already-converted users" via a **lightweight channel** — prioritize Kafka subscription (M8-A5) feeding a lightweight suppression layer (M8-F1); if the event stream is unstable, scope it down to shorter batches rather than a full Flink warehouse. In other words: **if triggered demand is small, don't rush to build a real-time warehouse in-house**, and evolve to Solution B only once the real-time campaign share genuinely rises (>30%). Probabilistic/graph matching and AI DQC serve as incremental gap-fillers, introduced gradually based on Mapping coverage gaps.

---

# M9 · Behavioral Analytics (scoped-down; restrained scope)

## 1. Requirements & Constraints Recap
M9 is deliberately scoped-down (P2): **do not build full BI**, only port the 5–10 reports/funnels on MoEngage that are "actually viewed" with matching numbers (M9-A1), plus AI data-analysis automation (auto post-campaign review M9-B1 / anomaly attribution M9-B2). Hard constraints: the Dashboard belongs to the Data Team's rebuild, and the product side already has Amplitude ("paid twice") → **scope demarcation must be actively done to avoid duplication** (M9-A5); definitions reuse M4 attribution, and the cross-product funnel is already merged into M4 without duplication.

## 2. Candidate Solutions (≥2)

### Solution A: reuse OLAP + lightweight BI direct SQL reports (embedded)
- **Approach**: Directly write the SQL for 5–10 reports on the Data Team's OLAP using a lightweight BI tool (Superset/Metabase), embedded-integrated into the Growth Platform. Definitions directly reference the M4 attribution semantics.
- **Applicable Scenarios**: Few reports (5–10), already-unified definitions, fastest delivery required, restrained scope.

### Solution B: precomputed metrics layer + lightweight dashboards (Metrics/Semantic Layer unifying definitions)
- **Approach**: Build a **metrics layer / semantic layer** (e.g., dbt metrics, Cube) above the reports, defining "view → click → conversion" and other definitions once for reuse in many places, precomputed for consumption by lightweight dashboards and NL querying.
- **Applicable Scenarios**: When definitions need to be unified across reports/people, when NL2SQL self-service querying will be connected in the future, or when there is concern about definition fragmentation.

## 3. Pros/Cons Comparison

| Dimension | Solution A lightweight BI direct SQL | Solution B metrics layer + lightweight dashboards |
|---|---|---|
| Implementation Cost | Low (write SQL directly, embedded) | Medium (build an extra semantic layer + precomputation) |
| Performance/Latency | Medium (direct OLAP query, large queries are slow) | High (precomputed, dashboards respond fast) |
| Scalability | Low (with more reports, SQL becomes scattered and definitions easily drift) | High (definitions centrally defined; adding reports just references them) |
| Operability | Low (no extra components) | Medium (maintain the metrics layer + materialization jobs) |
| Fit for Botim | High (only 5–10, definitions already unified, speed required) | Medium (slightly heavy under the restrained scope, but beneficial for definition unification and NL querying) |
| Definition consistency | Medium (relies on manual discipline to align with M4) | High (definitions defined in a single point, naturally consistent) |

## 4. Industry-Standard Practices
- **Superset / Metabase / Tableau**: Open-source/commercial BI, the mainstream choice for embedded analytics; Solution A adopts it directly.
- **Embedded Analytics**: Embedding reports into the business system rather than a standalone BI portal, matching "integrated into the Growth Platform, no standalone Dashboard."
- **Metrics Layer / Semantic Layer** (dbt metrics, Cube): Single-point definition of definitions, reused across tools — the industry prototype for Solution B and the standard solution for preventing definition fragmentation (Overview R4).

## 5. AI-Era New Approaches
- **Auto-insights / narrative BI**: Auto-generate textual review insights after a campaign ("conversion +X% MoM, mainly driven by offer A"), fulfilling M9-B1.
- **NL querying (text-to-SQL)**: Natural-language self-service data retrieval (M9-B3), lowering the data-retrieval barrier and demarcating scope from the Data Team's heavy dashboards.
- **Anomaly attribution**: Automatically identify effectiveness anomalies and attribute them along offer/copy/timing dimensions (M9-B2), automatically locating "why good / why bad."

## 6. Recommendation for Botim
**Restraint first: base on Solution A lightweight BI direct query, layered with a thin metrics layer to unify definitions (take Solution B's semantic layer, not its heavy dashboards).** With only 5–10 reports, definitions largely unified, and fast delivery required, a full metrics layer is overweight; but definition fragmentation is a company-wide risk (Overview R4), so define core definitions such as "view → click → conversion" in a single point within a thin semantic layer, directly referencing M4 attribution, to avoid scattered SQL and drift. **Strictly hold the boundary**: hand the Dashboard/full BI to the Data Team and general BI to Amplitude; M9 only does the differentiated increment of "reports actually viewed + AI auto-review/anomaly attribution/NL querying," and **never duplicates Amplitude**. Before delivery, first close D25 (the actually-viewed report list) / D26 (internal-metrics consumers) / D27 (BI tool stack), and investigate whether RFM/churn/engagement are used (M9-C1); if so, complete them in M2/M8 first before deprecation.

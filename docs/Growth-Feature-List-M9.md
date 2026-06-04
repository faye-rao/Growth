# Growth Feature List · M9 — Behavioral Analytics (scoped-down; restrained scope)

> Version: M9-1 (formal complete edition)
> Source: MoEngage screen recording + `用增问题survey-updated v3.xlsx` (Survey / Plan / Data Analysis special topic).
> **Cross-checked and supplemented** against the M9 section of《Botim增长平台_基于Survey的重新分析》(see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** benchmarked against MoEngage, must-have for replacement ｜ **★Enhancement** newly added this time / better than MoEngage ｜ **🤖AI** AI capability (incremental main line).

---

## 0. Module Positioning
- **Priority**: P2 (can be deferred; collaboration with the Data Team). Belongs to the "explicitly scoped-down" modules——not among our 3 core functions (Survey conclusion #6).
- **Baseline (restrained)**: **no full BI**, only reproduce the **5–10 reports/funnels** on MoEngage that are "**actually viewed**" and where **the numbers match** (row14).
- **Reasons for the deliberate scope-down (important facts)**:
  - **The Dashboard/board is rebuilt separately by the Data Team (Mr. Ma)**; Botim itself has the underlying data → **we do not need to do this part** (row14/74).
  - **The product side separately uses Amplitude for BI** (duplicating MoEngage instrumentation, "**paying twice**"); **Botim has no CDP**, business-line data is not unified (row75/26/52).
  - Therefore M9 = **only migrate reports actually viewed + data analysis automation**, and **proactively draw a scope boundary with the Data Team/Amplitude to avoid duplication**.
- **Incremental main line**: restrained scope + **🤖AI data analysis automation** (automatic post-campaign review insights / anomaly attribution, Plan W3–W4), delivering on "the increment relies on AI" (row6).
- **Current-state facts**: reports have no unified list, and each product line has different focuses (row14); the campaign-success standard is basically unified (view → click → conversion, row15); the cross-product funnel has been merged into M4 and is not duplicated here; whether MoEngage's internally computed metrics (RFM/predicted churn/engagement score) are in use awaits Growth confirmation (row57).

---

## 1. Complete Feature List

### A. Reproduce Reports Actually Viewed (core baseline, restrained)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M9-A1 | Reproduce 5–10 high-frequency reports | Reproduce only the 5–10 reports/funnels on MoEngage that **were actually accessed in the past 90 days**, **all reproduced and with matching numbers** | [Replicate] | row14 |
| M9-A2 | Report list and access inventory | Clarify who views, how often, and the underlying data source (MoEngage internal vs Botim data warehouse), to define the real reproduction scope | [Replicate] | row14/D25 |
| M9-A3 | Post-campaign review analysis | Reproduce the few dimensions most often analyzed in reviews (the view → click → conversion standard is already unified) to support post-campaign reviews | [Replicate] | row20/33/15 |
| M9-A4 | Review report export | Reproducible presentation of prior analysis reports / corresponding data, benchmarked against the MoEngage current state | [Replicate] | row33/20 |
| **M9-A5** | **★ Restrained-scope boundary** | **Migrate only reports actually viewed, proactively avoiding duplication of Amplitude / Data Team boards**; clarify with the Data Team the data-source and board-ownership boundary, and do no full BI | **★Enhancement** | row75/74 |

> Note: **the cross-product funnel has been merged into M4** (call → Wallet → Remittance, which MoEngage cannot answer), and **is not duplicated in M9** (row14).

### B. Data Analysis Automation (core 🤖AI highlight)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M9-B1** | **🤖 Automatic post-campaign review insights** | **Write data analysis algorithms for automated analysis**, automatically producing review insights after a campaign, shortening review time | **🤖AI ★Enhancement** | Plan W3-W4 / row19/20 |
| **M9-B2** | **🤖 Anomaly attribution analysis** | Automatically identify performance anomalies and attribute them (across dimensions such as offer / copy / timing), helping locate "why good / why bad" | **🤖AI ★Enhancement** | Plan W3-W4 / row16/17 |
| **M9-B3** | **🤖 NL2SQL self-service querying (optional)** | Present analysis results as natural-language self-service querying (aligned with row6 "the increment relies on AI"), lowering the barrier to data retrieval; draw a scope boundary with M4 light presentation / Data Team heavy boards | **🤖AI** | row6/76 |

### C. Internal Derived Metrics Dependency Investigation (⚠️ risk feature)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M9-C1** | **⚠️ Investigation of internal-metric consumers** | Investigate whether MoEngage's internally computed **RFM / predicted churn / engagement score** are in use; **if someone uses them, the corresponding capability must be filled in M2/M8 before decommissioning**, otherwise the downstream is impacted | **[Replicate] (risk feature)** | row57/D26 |

### D. Data Foundation Integration (depends on M8)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M9-D1 | Report underlying data ingestion | Connect footprint full instrumentation + Data Team T+1 cleansed results as the report underlying data source (no CDP) | [Replicate] | row28/52/49 |
| M9-D2 | Review wide table reuses M4 attribution | The review/report standard reuses the M4 funnel and attribution semantics, avoiding standard fragmentation and duplicate construction | [Replicate] | row15/34 |

---

## 2. 🤖 AI and ★Enhancement Feature Summary (differentiation relative to MoEngage)

**🤖 AI capabilities (incremental main line, aligned with row6 "the increment relies on AI")**
- M9-B1 Automatic post-campaign review insights ← **core highlight, shortens review time**
- M9-B2 Anomaly attribution analysis (automatically locating "why good / why bad")
- M9-B3 NL2SQL self-service querying (optional, aligned with row6)

**★ Enhancements this time (better than MoEngage current state / key restraint)**
- M9-A5 Restrained-scope boundary ← **proactively avoids duplication of Amplitude / Data Team boards, no full BI** (row75/74)
- M9-B1/B2 Data analysis automation (MoEngage side relies on manual review; this time automated)

**⚠️ Risk feature**
- M9-C1 Internal derived metrics dependency investigation (RFM/churn/engagement, if in use, decommissioning is impacted, must be filled in M2/M8 first)

**One-line positioning**: M9 = **deliberately scoped-down——migrate only the 5–10 reports "actually viewed" (A1–A4) + proactively draw a boundary to avoid duplicating Amplitude/Data Team (A5) + 🤖AI data analysis automation (B); no full BI / Dashboard, handed to the Data Team and Amplitude**.

---

## 3. Effort Mapping (person-days, consistent with the re-analysis, total ~24)
| Sub-item | Corresponding features | Person-days |
|---|---|---:|
| Migrate 5–10 reports actually viewed | A1–A4 (+A5 boundary) | 10 |
| Data analysis automation algorithms | B1/B2 (+B3 optional) | 8 |
| Supporting (ingestion/reuse/investigation) | C1/D1/D2 | 6 |
| **Subtotal** | | **~24** (deferrable / collaboration with the Data Team) |

> The cross-product funnel effort is counted in M4 and not duplicated here; the underlying cleansing is mainly owned by the Data Team (Mr. Ma).

---

## 4. Dependencies
### 4.1 Technical dependencies
- **M8 Data Foundation → prerequisite for M9**: without the report underlying wide tables/labels/logs, reports cannot be reproduced (D1/D2 depend on M8).
- **M4 attribution semantics → reused by M9**: the review/report standard reuses M4; **the cross-product funnel has been merged into M4** and is not duplicated in M9.
- **Collaboration with Data Team BI**: boards/full BI belong to the Data Team (Mr. Ma); M9 only does "reports actually viewed + automation," **collaborating on a scope boundary to avoid duplication** (row74/75).

### 4.2 Organizational/Data dependencies (prerequisites for estimation, currently mostly "to be asked")
| Dependency party | What it provides | Blocked features |
|---|---|---|
| **Growth team (Dubai, Radhika)** | List of reports actually viewed + who views/frequency/data source (D25), most-often-analyzed review dimensions (row20), campaign-success standard (row15) | A1–A4 / B1/B2 |
| **Data Team (Mr. Ma)** | Existing BI toolstack (D27), consumers of MoEngage internal metrics (D26), board ownership, T+1 cleansed results | A5 boundary / C1 / D1 |
| **Growth / Data Team** | Whether RFM/predicted churn/engagement score are in use (row57/D26) | C1 internal-metric investigation |

---

## 5. Blockers & Risks
- **R1 Report list unknown** → row14 makes clear there is **no unified list** (each product line has different focuses) → without obtaining the D25 list of actually-viewed reports, which of A1–A4 to build cannot be pinned down (Growth).
- **R2 Scope overlap with Data Team/Amplitude** → the Dashboard belongs to the Data Team (row74), and the product side already has Amplitude (row75, "paying twice") → **a scope boundary must be drawn first**, otherwise duplicate construction (A5).
- **R3 Internal derived metrics, if in use, decommissioning is impacted** → MoEngage internal RFM/churn/engagement (row57/D26), if there are consumers, **must be filled in M2/M8 before decommissioning**, otherwise the downstream breaks (C1).
- **R4 Existing BI toolstack unknown** → without obtaining D27, the collaboration boundary and reuse scope with the Data Team are unclear, affecting the A5 boundary and D1 ingestion.

---

## 6. Phase Rollout Recommendation
- **Priority P2, deferrable** (the contract is one-year-term, leaning toward non-renewal; the rest can be swapped slowly, row77).
- **Phase 1 (W3–W4 minimal set)**: only the minimal set of "**migrate 5–10 reports actually viewed + automated analysis**" (Plan W3-W4), **collaborating with the Data Team and not duplicating Amplitude**.
- **Phase 2+**: complete B2 anomaly attribution and B3 NL2SQL self-service querying; complete the C1 internal-metric investigation and coordinate M2/M8 to fill in (if needed).
- **Recommended sequence**: ① first lock in the D25/D26/D27 and row57 prerequisite interviews → ② draw a clear board/data-source boundary with the Data Team (A5) → ③ migrate the minimal set of actually-viewed reports and verify "the numbers match" (A1) → ④ layer in automated analysis (B1).

---

## Appendix: Cross-check Supplement Log (relative to the initial formal list)
| # | Supplement item | Source basis | Landing point |
|---|---|---|---|
| 1 | Report list and access inventory (who views/frequency/data source) | re-analysis §5.2 / Survey row14 / D25 | M9-A2 |
| 2 | Restrained-scope boundary (avoid duplicating Amplitude/Data Team) | re-analysis line14/22 / Survey row74/75 | M9-A5 |
| 3 | Data analysis automation algorithms (automatic post-campaign review) | re-analysis line89 / Plan W3-W4 | M9-B1 |
| 4 | Anomaly attribution analysis | Plan W3-W4 "write data analysis algorithms for automated analysis" | M9-B2 |
| 5 | Internal derived metrics dependency investigation (RFM/churn/engagement) | re-analysis §5.2 / Survey row57 / D26 | M9-C1 |
| 6 | Review wide table reuses M4 attribution (cross-product funnel merged into M4) | re-analysis §5.1 line161 / Survey row14 | M9-D2 |
| 7 | Effort mapping | re-analysis line90 | §3 |
| 8 | Dependencies (technical + organizational) | re-analysis §5.1/5.2 | §4 |
| 9 | Blockers & Risks | re-analysis §5.3/§6 | §5 |
| 10 | Phase rollout recommendation | re-analysis §4.1 / Plan | §6 |

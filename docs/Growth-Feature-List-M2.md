# Growth Feature List · M2 — Cohort Building (rule engine + NL2SQL)

> Version: M2-1 (formal complete edition)
> Source: MoEngage screen recordings + `用增问题survey-updated v3.xlsx` (Survey / Plan / Data-analysis special section).
> Already **cross-checked and supplemented** against the M2 section of "Botim Growth Platform_Survey-based Re-analysis" (see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** benchmarked against MoEngage, must-have for replacement ｜ **[★Enhancement]** newly added this time / superior to MoEngage ｜ **[🤖AI]** AI capability (incremental main line).

---

## 0. Module Positioning
- **Priority**: P0 (one of "the 3 core features we are building", second priority after messaging, Survey conclusion #3/#6).
- **Baseline**: Replicate step ① audience segmentation/cohort building of MoEngage's "pure rule-engine 3-step method" (row32).
- **Incremental main line**: Layer on AI (NL2SQL / intelligent segmentation) + experience enhancements, directly addressing the "**hard to use**" the Survey named (row32), delivering on "**incremental value comes from AI**" (row6).
- **Current-state facts**: 80% of activities use only 5–10 segments; pure manual rule filtering, not AI recommendation; T+1 cleaning + hourly level, not a bottleneck; no email, business-line IDs not unified, no CDP.

---

## 1. Complete Feature List

### A. Rule-based Cohort Engine (core baseline)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M2-A1 | Rule-condition construction | Multi-condition combinations of behavior/attributes/tags, supporting **infinite nesting** + AND/OR/NOT | [Replicate] | row32 |
| M2-A2 | Time-window operators | Time dimensions such as past N days / most recent once / cumulative (commonly filtering "active in the past 7 days" type) | [Replicate] | row30/D15 |
| M2-A3 | Frequency/attribute operators | atleast N times / at least X% / **predominantly** / event-attribute conditions | [Replicate] | row32 |
| M2-A4 | Exclude audiences | Exclude specified audiences/already-converted users from results | [Replicate] | row32 |
| M2-A5 | Batch evaluation and refresh | Run batches to produce audience snapshots, refreshed to **hourly level** (T+1 cleaning + hourly data) | [Replicate] | row30/60 |
| **M2-A6** | **Visual condition builder + real-time count estimation** | Drag-and-drop construction, showing the matched count as you build, reducing the cognitive burden of infinite nesting | **[★Enhancement]** | row32 |
| **M2-A7** | **MoEngage-syntax-compatible query layer** | Add a query layer compatible with MoEngage rule syntax to smoothly migrate the existing ~800 activity/Cohort definitions, **reusing the existing rule engine** rather than a full rewrite | **[Replicate][★Enhancement]** | Plan W3-W4 |
| **M2-A8** | **Near-real-time segment refresh (downgraded)** | Supports the near-real-time audience updates needed by triggered activities (e.g., "push 10 minutes after account opening"); the current real-time share is small, implemented in a downgraded form | **[Replicate]** | row61/62 |

### B. NL2SQL Intelligent Data Retrieval (core highlight)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M2-B1** | **Natural-language cohort building (NL2SQL)** | "Speak plainly" to directly generate an audience (e.g., "Indian/Filipino users who used calling in the past 30 days but have not registered Wallet"), directly hitting the "hard to use" pain point | **[🤖AI][★Enhancement]** | row29/30/32 |
| **M2-B2** | **Generated results previewable and editable** | The generated SQL/rule DSL is transparently displayed and can be manually fine-tuned before execution; AI is not a black box | **[★Enhancement]** | row32 |
| **M2-B3** | **Accuracy fallback mechanism** | High-frequency templates match for direct output; **confidence prompts**; long-tail/low-confidence cases routed to humans or to A6 manual construction | **[🤖AI][★Enhancement]** | row29/D6-D9 |
| **M2-B4** | **Template-coverage-first strategy** | Based on the distribution of historical data-retrieval needs, first solidify repeated templates (same structure, different parameters) to guarantee achievable accuracy | **[🤖AI]** | row29/D5-D6 |

### C. Intelligent Segmentation and Recommendation (AI increment)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M2-C1** | **Lookalike similar-audience expansion** | Expand similar users based on a seed audience (filling the current "pure manual, not AI recommendation" gap) | **[🤖AI][★Enhancement]** | row11/6 |
| **M2-C2** | **Propensity-based intelligent segmentation** | Score and segment by churn/conversion/activation propensity, assisting cross-sell (KYC→Wallet→cross-sell) | **[🤖AI][★Enhancement]** | row9/6 |
| **M2-C3** | **AI segment suggestions** | Automatically recommend candidate Cohort definitions per activity goal, improving activity volume/efficiency | **[🤖AI][★Enhancement]** | row6 |
| **M2-C4** | **Segment-effect algorithm optimization** | Use relevant algorithms to optimize segment effect (improving match precision/conversion), distinct from pure rule filtering | **[🤖AI][★Enhancement]** | Plan W3-W4 |

### D. Cohort Asset Management
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M2-D1 | Cohort save/reuse | Save audiences as reusable assets; list/search/archive | [Replicate] | row32 |
| **M2-D2** | **High-frequency Cohort template library** | Solidify **5–10 high-frequency segments** such as KYC-or-not / last-transfer time / Wallet activated-or-not / balance for one-click reuse | **[★Enhancement]** | row11 |
| M2-D3 | Version management | Version Cohort definitions, supporting fine-tuning and rollback | [Replicate] | row32 |
| M2-D4 | Matched-list export | Export the list of matched users (benchmarked against MoEngage's current state) | [Replicate] | row32/55 |

### E. Data and Timeliness Foundation Integration (depends on M8)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M2-E1 | Multi-source data integration | Connect footprint full tracking + Data Team T+1-cleaned tags (no CDP) | [Replicate] | row28/52 |
| **M2-E2** | **Cross-business-line ID unification (no email)** | Use customer_id/phone number as the primary key + Mapping consumption to support cross-product cohort building / cross-sell | **[★Enhancement]** | row31/D2 |
| **M2-E3** | **"No longer push the converted" near-real-time suppression** | A lightweight real-time layer suppresses already-converted users on top of the cohort results (the real-time need is **mainly just for this**), without requiring full-chain real-time | **[★Enhancement]** | row59 |

### F. Cohort Result as a Service (connecting downstream)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M2-F1 | Dual-path output | ① Home-page proprietary grouping → via delivery (M5) ② full push path (M3); the same engine serves both consumption paths | [Replicate] | row11/73 |
| M2-F2 | Audience-result API | Audience snapshot as a service, called by orchestration (M3) / delivery (M5) / Shadow traffic splitting (M7) | [Replicate] | row32 |

---

## 2. 🤖 AI and ★Enhancement Feature Summary (differentiation relative to MoEngage)

**🤖 AI capabilities (incremental main line, aligned with row6 "incremental value comes from AI")**
- M2-B1 Natural-language cohort building NL2SQL ← **the strongest highlight, directly hitting "hard to use"**
- M2-B3 / B4 NL2SQL accuracy fallback + template-first
- M2-C1/C2/C3/C4 Lookalike / propensity segmentation / AI segment suggestions / segment-effect algorithm optimization

**★ Enhancements this time (superior to MoEngage's current state)**
- M2-A6 Visual builder + real-time count estimation (breaking "infinite nesting, hard to use")
- M2-A7 MoEngage-syntax-compatible query layer (smoothly migrating ~800 activities)
- M2-B2 Generated results previewable and editable (AI not a black box)
- M2-D2 High-frequency Cohort template library (5–10 segments covering 80% of activities)
- M2-E2 Cross-business-line ID unification (under the no-email premise)
- M2-E3 "No longer push the converted" near-real-time suppression

**One-line positioning**: M2 = **Replicate MoEngage's cohort-building engine (A1–A5/D/E1/F baseline) + compatibility layer for smooth migration (A7) + AI and experience enhancements (B/C + A6/D2/E2/E3) directly solving "hard to use" and delivering on "AI increment"**.

---

## 3. Effort Mapping (person-days, consistent with the Re-analysis)
| Sub-item | Corresponding feature | Person-days |
|---|---|---:|
| Rule-engine DSL + parser | A1–A4 | 12 |
| MoEngage-syntax-compatible query layer | A7 | 6 |
| Batch evaluation | A5 | 10 |
| Near-real-time segments (downgraded) | A8 | 8 |
| Segment-algorithm optimization | C4 (+C1/C2) | 8 |
| NL2SQL (incl. fallback) | B1–B4 | 14 |
| Management/version/export | D1/D3/D4 | 6 |
| **Subtotal** | | **~64** (~50 if NL2SQL deferred) |
> The template library (D2), visual builder (A6), ID unification (E2, core in M8), and near-real-time suppression (E3, core in M8) are mostly incremental/reuse, not separately listed as large amounts.

---

## 4. Dependencies
### 4.1 Technical Dependencies
- **M8 data foundation → prerequisite for M2**: Without wide tables/tags/ID-mapping, cohort building is impossible (E1/E2/E3 depend on M8).
- **M2 → shared downstream**: M3 (traffic splitting), M5 (matching), M7 (5% traffic split) reuse the same rule engine (F1/F2).

### 4.2 Organizational/Data Dependencies (estimation prerequisites, mostly "to be asked" for now)
| Dependency | What it provides | Blocked features |
|---|---|---|
| **Data Team (Mr. Ma)** | ID-Mapping table + coverage (D2), T+1 cleaning, masked samples (D4), historical data-retrieval needs + SQL distribution (D5–D9), tag dictionary (D10–D12) | E2 / B1–B4 (NL2SQL accuracy) / E1 |
| **Growth team (Dubai, Radhika)** | Top 10 actually-in-use Cohort definitions + underlying rules + scale (D13), rule-engine capability list (D15) | D2 template library / A1–A3 operator coverage |
| **Pei Qing** | Event schema, data-sample coordination | E1 / overall kickoff |

---

## 5. Blockers & Risks
- **R1 Data samples + event schema not in place** → Group A as a whole and E1 cannot start (Pei Qing/Data Team).
- **R2 Real-time share is a schedule switch** → If Growth reports real-time activities >30%, A8 near-real-time gets heavier, and the 6-week MVP is tight (row62).
- **R3 NL2SQL feasibility** → depends on historical SQL complexity (D7) and the repeated-template share (D6); strategy: **first do high-frequency template coverage + human fallback, do not bet on full automation** (B3/B4).
- **R4 Top Cohort unknown** → without D13, the D2 template library and Group A operator coverage cannot be precise (Growth).
- **R5 ID-unification current state unknown** → under the no-email premise, D2 Mapping coverage/accuracy determines the difficulty of E2 (Data Team).

---

## 6. Phase Rollout Recommendations
- **Phase 1 (W3–W4 MVP)**: Cohort building = **reuse the existing rule engine + compatibility-syntax layer (A7) + segment algorithm (C4)**; NL2SQL first does **the most-used templates + fallback (B3/B4)**, not treated as a blocker.
- **Phase 2+**: Roll out, breadth-wise, the visual builder (A6), Lookalike/propensity segmentation (C1/C2), near-real-time (A8), and the template library (D2).
- **Recommended order**: First close the D1–D15 prerequisite data/interviews → run the MVP through cohort building for one high-frequency scenario (e.g., Wallet activation Push) → after validation, expand the AI increment.

---

## Appendix: Cross-check Supplement Log (relative to the initial formal list)
| # | Supplement | Source basis | Landing point |
|---|---|---|---|
| 1 | MoEngage-syntax-compatible query layer | Re-analysis line57 / Plan W3-W4 | M2-A7 |
| 2 | Near-real-time segment refresh (downgraded) | Re-analysis line57 / Survey row61-62 | M2-A8 |
| 3 | Segment-effect algorithm optimization (explicitly listed) | Plan W3-W4 "use relevant algorithms to optimize segment effect" | M2-C4 |
| 4 | Effort mapping | Re-analysis line58 | §3 |
| 5 | Dependencies (technical + organizational) | Re-analysis §5.1/5.2 | §4 |
| 6 | Blockers & Risks | Re-analysis §5.3/§6 | §5 |
| 7 | Phase rollout recommendations | Re-analysis §4.1 / Plan | §6 |

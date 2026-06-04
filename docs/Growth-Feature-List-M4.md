# Growth Feature List · M4 — Campaign Funnel Tracking (Absorbing the Original Reports)

> Version: M4-1 (formal complete edition)
> Source: MoEngage screen recordings + `用增问题survey-updated v3.xlsx` (Survey / Plan / Data Analysis special topic).
> Cross-checked and supplemented against the M4 section (line65–68), §5 Dependencies, §6 Risks, and §4 Phase of *Botim Growth Platform_Survey-based Re-analysis* (see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** benchmarked against MoEngage, mandatory for replacement ｜ **[★Enhancement]** newly added this time / better than MoEngage ｜ **[🤖AI]** AI capability (incremental mainline).

---

## 0. Module Positioning
- **Priority**: P0 (one of "the 3 core features we build" — ③Campaign Funnel Tracking, Survey Conclusion #6 / row76).
- **Baseline**: Replicate MoEngage's per-push event funnel — "view → click → conversion", with largely unified definitions (click rate / conversion rate, row15); and **absorb the original standalone Reports module** (Re-analysis line24 "converge into Campaign Funnel Tracking + Shadow comparison reports").
- **Incremental mainline**: Use the **★★★ cross-product funnel** to directly answer "the questions MoEngage cannot answer" (row14), layered with the "numbers must reconcile" reconciliation/trust mechanism (row14) and built-in node-level funnel-loss visualization (row39), delivering differentiated value.
- **Boundary facts**: Heavy dashboards / data-analysis boards belong to the **Data Team (Mr. Ma)**; we only do **tracking + light presentation** (results presented via NL2SQL / light dashboards, row14/row74); the attribution window of roughly 1–2 days is a GZF empirical value — not rigid, not a bottleneck (row34).

---

## 1. Complete Feature List

### A. Single-Campaign Funnel Tracking (Core Baseline)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M4-A1 | Push event collection | Event tracking on each push, recorded to the user level (read → conversion both trackable), feeding funnel computation | [Replicate] | row76/63 |
| M4-A2 | View → click → conversion funnel | Standard three-stage funnel for a single campaign, with largely unified definitions (click rate / conversion rate) | [Replicate] | row15 |
| M4-A3 | Campaign success-metric definitions | Click rate / conversion rate as the primary metrics (as with all marketing campaigns), extensible to ROI | [Replicate] | row15 |
| **M4-A4** | **Built-in node-level funnel-loss visualization** | Inflow / loss counts at each Flow node are **viewable directly within the system**; MoEngage requires export, the self-built solution avoids export | **[★Enhancement]** | row39 |
| **M4-A5** | **Unified-definition consolidation** | Consolidate the "view/click/conversion" definitions at the computation layer, avoiding conflicting metric definitions across departments | **[★Enhancement]** | row15/row20 |

### B. Attribution Engine
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M4-B1 | Attribution window computation | Touch → click → conversion attribution, default window of roughly 1–2 days (sending + user receiving and opening both take time) | [Replicate] | row34 |
| **M4-B2** | **Configurable attribution window** | The window is not rigid and not a bottleneck (GZF empirical value); supports per-campaign / per-scenario configuration rather than a hard-coded global value | **[★Enhancement]** | row34 |
| M4-B3 | Attribution semantics as a service | Attribution semantics exposed externally, reused by the M7 comparison reports ("attribution semantics reused by M7") | [Replicate] | Re-analysis line162 |

### C. Cross-Product Funnel (Core Differentiator ★★★)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M4-C1** | **Cross-product funnel (which MoEngage cannot answer)** | The new system must fully reproduce everything and **the numbers must reconcile**, and must be able to answer questions MoEngage cannot (such as cross-product funnels) — **the core differentiator** | **[★Enhancement]** | row14 |
| **M4-C2** | **Penetration-chain funnel** | E.g. "call active → Wallet registration → Remittance first order"; service penetration 7.5% → company target 15% | **[★Enhancement]** | row7/row14 |
| **M4-C3** | **cross-sell funnel** | Cross-product conversion funnel of KYC → activate Wallet → downstream cross-sell | **[★Enhancement]** | row9 |
| **M4-C4** | **Cross-product funnel as SQL** | Funnel definitions as SQL, computable once cross-business-line ID linkage (M8/E2) is in place | **[★Enhancement]** | row14/row31 |

### D. Performance and Comparison Reports (Absorbing the Original Reports, Shadow ready)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M4-D1 | Campaign performance report | Single-campaign performance report (absorbing the original Reports module), down to the user level | [Replicate] | row76/63 |
| M4-D2 | Comparison report (Shadow ready) | Report structure aligned with M7 Shadow A/B, used for "not significantly lower than MoEngage" comparison | [Replicate] | row64/Re-analysis line66 |
| **M4-D3** | **"Numbers must reconcile" reconciliation/trust mechanism** | **Dual-run reconciliation + discrepancy alerting** against MoEngage / legacy reports, establishing number trust — the **trust threshold** for replacement | **[★Enhancement]** | row14 |
| **M4-D4** | **🤖 Automated attribution insights / retrospective** | Automatically produce attribution insights and retrospective conclusions (aligned with row6 "incremental value comes from AI"), **optional** | **[🤖AI]** | row6/row19/row20 |

### E. Light Presentation Layer (No Heavy Dashboards)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M4-E1 | NL2SQL result presentation | Funnel / performance results presented via NL2SQL "plain-language" queries (reusing the M2 NL2SQL capability) | [Replicate] | row76 |
| M4-E2 | Light dashboard presentation | Lightweight dashboard presentation of tracking results; **heavy dashboards belong to the Data Team**, we do not build this part | [Replicate] | row14/row74 |

### F. Data and Log Foundation Integration (Depends on M8)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M4-F1 | Touch/conversion log consumption | Consume the M8 touch/conversion log wide table (user_id/campaign_id/channel/click/convert) as funnel input | [Replicate] | row63/Re-analysis line52 |
| M4-F2 | Cross-business-line ID dependency | The cross-product funnel (C) strongly depends on M8 ID-mapping linkage (no email → customer_id / phone number) | [Replicate] | row31/Re-analysis line84 |

---

## 2. 🤖AI and ★Enhancement Feature Summary (Differentiation vs. MoEngage)

**🤖AI capabilities (incremental mainline, aligned with row6 "incremental value comes from AI")**
- M4-D4 Automated attribution insights / retrospective (optional) ← aligned with the retrospective dimension (row20) and AI increment
- M4-E1 NL2SQL result presentation (reusing M2 NL2SQL, "plain-language" funnel queries)

**★ Enhancements this time (better than MoEngage's status quo)**
- **M4-C1/C2/C3/C4 cross-product funnel ★★★** ← **the core differentiator, which MoEngage cannot answer** (call → Wallet → Remittance, KYC → Wallet → cross-sell)
- **M4-D3 "numbers must reconcile" reconciliation/trust mechanism ★★** ← dual-run reconciliation + discrepancy alerting, establishing the trust threshold for replacement
- **M4-A4 built-in node-level funnel-loss visualization ★** ← MoEngage requires export, the self-built solution shows it directly
- **M4-A5 unified-definition consolidation ★** ← consolidating click-rate / conversion-rate definitions, avoiding departmental conflicts
- M4-B2 configurable attribution window

**One-line positioning**: M4 = **replicate MoEngage's push event funnel (A1–A3/B1) + absorb the original Reports (D1/D2) + cross-product funnel (C) and reconciliation trust (D3) as the core differentiator + light presentation (E) without touching heavy dashboards**, directly answering "fully reproduce everything and the numbers must reconcile, and be able to answer questions MoEngage cannot" (row14).

---

## 3. Effort Mapping (person-days, consistent with the re-analysis)
| Sub-item | Corresponding features | Person-days |
|---|---|---:|
| Funnel tracking | A1–A5 | 10 |
| Attribution | B1–B3 | 8 |
| Cross-product funnel | C1–C4 | 6 |
| Performance / comparison report (Shadow ready) | D1–D3 (incl. reconciliation) | 8 |
| Light presentation (NL2SQL / light dashboard) | E1/E2 | 4 |
| **Subtotal** | | **~36** |
> Automated attribution insights (D4) are a 🤖AI optional increment; touch/conversion logs (F1) mainly live in M8 and ID linkage (F2) mainly lives in M8 — largely reuse / dependency, not separately itemized at large amounts.

---

## 4. Dependencies
### 4.1 Technical Dependencies
- **M8 data foundation → prerequisite for M4**: without the touch/conversion log wide table, funnels cannot be computed (F1); **cross-business-line ID linkage** is a hard prerequisite for the cross-product funnel (C) (F2, Re-analysis line159 "M8 → prerequisite for M2/M4/M9", line84).
- **M1 touch + M8 touch log → prerequisite for M4**: funnels and attribution depend on event tracking from touch execution landing (Re-analysis line162).
- **M2 audience selection → input to M4**: the funnel target population is provided by the M2 audience-selection snapshot.
- **M4 → reused by M7**: M4 attribution semantics are reused by the M7 comparison reports (B3, Re-analysis line162).

### 4.2 Organizational / Data Dependencies (estimation prerequisites, currently mostly "to be confirmed")
| Dependency | Provides | Blocked features |
|---|---|---|
| **Growth (Dubai, Radhika)** | The list of 5–10 reports/funnels that people actually look at (row14 / D25, no unified list → Growth), the dimensions most commonly analyzed in retrospectives (row20) | D1/D2 report scope / A2 funnel list / D4 retrospective dimensions |
| **Data Team (Mr. Ma)** | Unified definitions of conversion/active/retention (D29), cross-product funnel depending on cross-line ID linkage (D2), heavy dashboards owned by them (row74) | A5 definition consolidation / C cross-product funnel / E2 boundary |
| **M8 (our side)** | Touch/conversion log wide table, ID-mapping consumption | F1 / F2 / the entire C group |

---

## 5. Blockers & Risks
- **R1 Definitions not yet unified company-wide** (D29) → conversion/active/retention have no unified definition; **align definitions with Growth / Data Team before development**, otherwise A5/B attribution will need rework (Re-analysis line185).
- **R2 Cross-product funnel strongly depends on cross-business-line ID linkage** (M8/E2) → given the no-email premise, ID-mapping coverage/accuracy determines whether C1–C4 are computable (row31 / Re-analysis line84).
- **R3 The list of reports people actually look at is unknown** (row14) → no unified list (GZF: because product forms differ, each person's focus differs → Growth); if D13/D25 are not obtained, the D1/D2 report scope and A2 funnel list cannot be precise (Re-analysis line176).
- **R4 Touch log / event schema not in place** (M8 / Pei Qing / Data Team) → if not in place, A1 event tracking and F1 input cannot proceed.

---

## 6. Phase Rollout Recommendations
- **Phase 1 (W3–W6)**: First wire up the single-campaign **"view → click → conversion" funnel (A1–A3) + 1–2 day attribution (B1)**, to serve the M7 Shadow comparison report (D2, Shadow ready); establish "numbers must reconcile" via dual-run reconciliation against MoEngage (D3). This is part of the Phase 1 acceptance lynchpin (Re-analysis line128 W5–W6 Shadow).
- **Phase 2+**: Invest heavily in the **cross-product funnel (C) after cross-business-line ID linkage** as the differentiation highlight; roll out node-level loss visualization (A4), configurable attribution window (B2), automated attribution insights (D4, 🤖AI increment), and NL2SQL / light dashboard presentation (E) horizontally.
- **Recommended order**: First clear the R1 definitions + R3 report list + R4 log/schema prerequisites → get an MVP working for a high-frequency scenario (e.g. Wallet activation Push) with a single-campaign funnel + reconciliation → invest in cross-product funnel differentiation after ID linkage.

---

## Appendix: Cross-check Supplement Log (against M4 authoritative facts)
| # | Supplement item | Source basis | Landing point |
|---|---|---|---|
| 1 | Absorb the original standalone Reports module | Re-analysis line24 ("Reports converge into Campaign Funnel Tracking + Shadow comparison reports") | §0 / M4-D1 |
| 2 | Attribution semantics reused by M7 | Re-analysis line162 ("M4 attribution semantics → reused by M7") | M4-B3 / §4.1 |
| 3 | M1 touch + M8 touch log as prerequisites for M4 | Re-analysis line162 | §4.1 |
| 4 | Touch/conversion log wide-table fields | Re-analysis line52/84 | M4-F1 |
| 5 | Effort mapping (funnel 10 / attribution 8 / cross-product 6 / report 8 / presentation 4 = ~36) | Re-analysis line68 | §3 |
| 6 | Definitions-not-unified risk (D29, align before developing) | Re-analysis line185 (R4 definition fragmentation) | §5 R1 |
| 7 | Risk that the list of reports people actually look at is unknown (D13/D25) | Re-analysis line176 | §5 R3 |
| 8 | Phase 1 funnel + attribution feeding Shadow / Phase 2 cross-product funnel | Re-analysis line128 (W5–W6 Shadow) / line38 | §6 |

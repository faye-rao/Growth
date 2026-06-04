# Growth Feature List · M6 — AI Copywriting (Multilingual Generation + Performance Feedback Loop)

> Version: M6-1 (formal complete edition)
> Source: MoEngage screen recordings + `用增问题survey-updated v3.xlsx` (Survey / Plan / Data Analysis special topic D16/D17).
> Cross-checked and supplemented against the M6 section and §4/§5/§6 of *Botim Growth Platform_Survey-based Re-analysis* (see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** benchmarked against MoEngage, mandatory for replacement ｜ **[★Enhancement]** newly added this time / better than MoEngage ｜ **[🤖AI]** AI capability (incremental mainline).

---

## 0. Module Positioning
- **Priority**: P1 (incremental value, Conclusions #3/#7 "the rest can be replaced slowly"; the Survey lists it as a P1 incremental module).
- **Baseline**: **Pure incremental module — MoEngage has no equivalent**. MoEngage only lets operators fill in copy manually, with no generation / learning capability; this module is built from 0 to 1.
- **Incremental mainline**: This module is one of the **core carriers** of "**the North Star is no lower than the status quo, and incremental value comes from AI improving campaign volume / validation efficiency**" (row6) — using AI multilingual copy generation to compress the "writing copy" step (the potential bottleneck noted in row18), and letting AI learn high-conversion styles through a historical copy-to-performance feedback loop.
- **Status-quo facts**: A single campaign from kickoff → launch includes a "writing copy" step, which is a potential bottleneck (row18); multilingual = Hindi / Tagalog / Arabic / English (D17); the historical campaign master table contains copy text / Offer / performance (click rate / conversion rate / ROI, D16); content is self-reviewed by Growth, mainly looking at performance (row47); on external UAE strict compliance, GZF considers it does not go into such detail (row47).
- **Type composition**: This module is primarily **🤖AI / ★Enhancement**; [Replicate] applies only to replacement-mandatory carrier items such as "binding copy to campaign / channel / variation" (consumed by M3 orchestration and M5 payload).

---

## 1. Complete Feature List

### A. Multilingual AI Copy Generation (Core Highlight)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M6-A1** | **One-click multilingual copy generation** | Given the campaign goal / Offer / audience, **one-click generate copy in four languages: Hindi / Tagalog / Arabic / English**, compressing the "writing copy" bottleneck of row18 | **[🤖AI][★Enhancement]** | row18/D17 |
| **M6-A2** | **Localization adaptation (not machine translation)** | Output localized to each language's local expression habits, rather than direct English translation; Arabic includes RTL / writing-habit adaptation | **[🤖AI][★Enhancement]** | D17/row47 |
| **M6-A3** | **Automatic multi-version copy output** | A single campaign produces **multiple versions (multiple variations)** of copy in one go, fed directly into M3's A/B/N automatic experiments | **[🤖AI][★Enhancement]** | row6/32 |
| **M6-A4** | **Generation is previewable and editable** | Generated results are displayed transparently; operators can manually fine-tune before adoption — AI is not a black box (same principle as NL2SQL) | **[★Enhancement]** | row47 |

### B. Copy-to-Performance Feedback Loop (Letting AI Learn High Conversion)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M6-B1** | **Historical copy-to-performance join** | Join historical copy text with the corresponding performance data (click rate / conversion rate / ROI), building "copy → performance" paired samples | **[★Enhancement]** | D16/D17 |
| **M6-B2** | **High-conversion style learning** | Use the B1 paired samples to let AI learn high-conversion copy styles / sentence patterns / Offer phrasing, improving generation quality | **[🤖AI][★Enhancement]** | row6/D16 |
| **M6-B3** | **Per-language separate modeling** | Each language (Hindi/Tagalog/Arabic/English) separately joins its own performance data for learning, avoiding cross-language style bleed (depends on D17 pairing completeness) | **[🤖AI][★Enhancement]** | D17 |
| **M6-B4** | **Performance backflow incremental learning** | After a new campaign launches, performance flows back, continuously supplementing the paired samples (connecting to M4 Funnel Tracking / historical performance data) | **[★Enhancement]** | D16/row15 |

### C. Copy Compliance Assistance
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M6-C1** | **Compliance / sensitive-word pre-screening** | At generation time, do UAE compliance + sensitive-word pre-screening, filtering out obvious violations before delivery | **[🤖AI][★Enhancement]** | row47 |
| **M6-C2** | **Growth self-review handoff** | After pre-screening, hand off to Growth self-review (mainly looking at performance), retaining a human-gatekeeping loop; AI is not fully automatic | **[★Enhancement]** | row47 |

### D. Copy Asset and Binding Management (Replacement-Mandatory Carrier)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M6-D1 | Copy-to-campaign/channel/variation binding | Binding management of copy with campaign, channel (Push/In-App), and variation, for **M3 orchestration** to use and **M5 payload** to call | [Replicate] | row11/73/76 |
| M6-D2 | Multilingual copy storage and versioning | Multilingual copy storage and versioning (carrier benchmarked against MoEngage's manually-filled copy status quo), supporting fine-tuning and rollback | [Replicate] | D17/row32 |

---

## 2. 🤖AI and ★Enhancement Feature Summary (Differentiation vs. MoEngage)

**🤖AI capabilities (incremental mainline, aligned with row6 "incremental value comes from AI")**
- M6-A1 one-click multilingual copy generation ← **the strongest highlight, directly hitting the row18 "writing copy" bottleneck**
- M6-A2 localization adaptation (not machine translation)
- M6-A3 automatic multi-version copy output → feeds M3 A/B/N automatic experiments
- M6-B2 / B3 high-conversion style learning / per-language separate modeling (based on the D16/D17 feedback loop)
- M6-C1 compliance / sensitive-word pre-screening

**★ Enhancements this time (MoEngage has no equivalent, pure increment)**
- M6-A4 generation is previewable and editable (AI is not a black box)
- M6-B1 / B4 historical copy-to-performance join / performance backflow incremental learning
- M6-C2 Growth self-review handoff (human gatekeeping)

**[Replicate] (replacement-mandatory carrier items)**
- M6-D1 copy-to-campaign/channel/variation binding (for M3 orchestration, M5 payload)
- M6-D2 multilingual copy storage and versioning

**One-line positioning**: M6 = **a pure incremental AI module that MoEngage completely lacks** — primarily multilingual generation (A) + performance feedback loop (B) + compliance assistance (C), layered with copy binding / storage carriers (D) to support M3/M5 consumption, delivering the row6 "incremental value comes from AI improving campaign volume / validation efficiency" mainline.

---

## 3. Effort Mapping (person-days, consistent with the re-analysis)
| Sub-item | Corresponding features | Person-days |
|---|---|---:|
| LLM copy generation (multilingual / localization / multi-version / editable) | A1–A4 | 10 |
| Performance feedback loop (join historical performance + style learning + backflow) | B1–B4 | 6 |
| Review / compliance (pre-screening + Growth self-review handoff) | C1–C2 | 3 |
| **Subtotal** | | **~19** |
> Copy binding / storage carriers (D1/D2) are mainly implemented alongside M3 orchestration and M5 payload — largely reuse, not separately itemized at a large amount.

---

## 4. Dependencies
### 4.1 Technical Dependencies
- **M6 → M3 content and push orchestration**: A3 multi-version copy feeds M3's A/B/N automatic experiments (M3 is the consumer).
- **M6 → M5 1-to-1 personalization**: D1/D2 multilingual copy is called as the content source for the M5 payload (KV/multilingual).
- **M4 / historical performance data → prerequisite for the M6 feedback loop**: B1–B4 depend on historical copy-to-performance paired data (D16/D17) and M4 funnel performance backflow; without paired data, the loop degrades to pure generation.

### 4.2 Organizational / Data Dependencies (estimation prerequisites, currently mostly "to be confirmed")
| Dependency | Provides | Blocked features |
|---|---|---|
| **Data Team (Mr. Ma)** | Historical copy-to-performance paired data: campaign master table (copy text / Offer / performance D16), multilingual copy-to-performance pairing table (D17) | B1–B4 feedback-loop feasibility |
| **Growth (Dubai, Radhika)** | Copy self-review definitions, confirmation of UAE compliance requirements (row47), per-language localization preferences | C1/C2 / A2 |

---

## 5. Blockers & Risks
- **R1 Whether multilingual copy-to-performance paired data is fully retained** → D17 to be confirmed; whether Hindi/Tagalog/Arabic/English are all retained and whether each copy can join to performance **directly determines the feasibility of the B-group feedback loop** (if incomplete, degrade to "generation only, no learning").
- **R2 Compliance self-review definitions undecided** → row47 only clarifies "Growth self-review, mainly looking at performance"; specific UAE regulatory requirements await Growth confirmation; the C1 pre-screening rules need definition input, otherwise only generic sensitive words can be done.
- **R3 Copy quality requires human gatekeeping** → AI is not fully automatic; A4 editable + C2 Growth self-review must be retained, to avoid directly sending low-quality / non-compliant copy.
- **R4 Completeness of the historical campaign master table** → D16 to be confirmed; if copy-text / performance fields are missing, B1 join samples are insufficient and B2 style-learning effectiveness is reduced.

---

## 6. Phase Rollout Recommendations
- **Positioning**: P1 increment, **advanced in parallel, not a Phase 1 blocker** (in the same "AI increment in parallel" category as NL2SQL, row6 / Re-analysis §6 recommendation ④).
- **Phase 1 (the minimal subset that can be done first)**: First do "**English + 1 primary language**" generation (A1 subset + A4 editable) + **human gatekeeping** (C2), which can launch without depending on the performance feedback loop; expand after it works.
- **Phase 2+**: Expand to all four languages with localization (A2) + multi-version feeding A/B/N (A3) + the full copy-to-performance feedback loop (B1–B4) + compliance pre-screening (C1).
- **Recommended order**: First clear the D16/D17 paired-data prerequisite → get an MVP working for "English + 1 language generation + human gatekeeping" in a high-frequency scenario → after validation, expand to multilingual and the performance feedback loop.

---

## Appendix: Cross-check Supplement Log (against the initial formal list)
| # | Supplement item | Source basis | Landing point |
|---|---|---|---|
| 1 | Copy-to-campaign/channel/variation binding (carrier item, replacement-mandatory) | Re-analysis §5.1 technical dependencies (M3 consumption / M5 payload) + row76 | M6-D1 |
| 2 | Multi-version copy feeding M3 A/B/N automatic experiments | Re-analysis M3 section "A/B/N groups + version fine-tuning" line61 + row6 | M6-A3 |
| 3 | Performance backflow incremental learning (connecting to M4 funnel performance) | Re-analysis §5.1 (M4 attribution reused) + row15 | M6-B4 |
| 4 | Compliance / sensitive-word pre-screening (AI side) | Re-analysis §6 R-class risks + row47 | M6-C1 |
| 5 | Effort mapping | Re-analysis line77 | §3 |
| 6 | Dependencies (technical M3/M5/M4 + organizational Data Team/Growth) | Re-analysis §5.1/5.2 | §4 |
| 7 | Blockers & risks | Re-analysis §6 R-class + D16/D17 to be confirmed | §5 |
| 8 | Phase rollout (P1 in parallel, English + 1 language first) | Re-analysis §4.2 P-C + §6 recommendation ④ | §6 |

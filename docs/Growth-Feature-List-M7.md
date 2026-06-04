# Growth Feature List · M7 — Shadow Validation Framework (acceptance gate for replacement)

> Version: M7-1 (formal complete edition)
> Source: MoEngage screen recording + `用增问题survey-updated v3.xlsx` (Survey / Plan / Data Analysis special topic).
> **Cross-checked and supplemented** against the M7 section of《Botim增长平台_基于Survey的重新分析》(see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** framework-level foundation required for replacement (≈ without a control group / without a comparable report, sign-off is impossible, hence marked "must-have") ｜ **★Enhancement** newly built this time / better than current state ｜ **🤖AI** AI capability (incremental main line).
> **Special note**: M7 is a **self-built validation framework with no MoEngage counterpart**——it exists as the make-or-break for "daring to replace MoEngage." Therefore most features in this module are "★Enhancement / newly built" rather than replication; the [Replicate] tag is used only for framework items that are "indispensable for replacement and constitute the acceptance-gate foundation" (e.g. control-group sample source, A/B comparison report), while the rest follow the three-category marking under a "newly built" semantic.

---

## 0. Module Positioning
- **Priority**: P0 (**acceptance gate for replacement**, re-analysis module table line41 / effort summary line105). Without Shadow passing, the entire replacement dares not go live.
- **Baseline**: MoEngage itself has no Shadow framework (it only supports gray-release / random traffic split row65); this module is a **self-built control validation framework**——proving "the new system is not significantly lower than MoEngage," which is the exit condition for replacement (Plan W5–W6 / line128).
- **Incremental main line**: on top of the control framework, layer in **★dedup middle-layer to prevent double-send** (hard requirement, otherwise the control is distorted), **★automated significance comparison report**, **★reuse the M2 rule engine for 5% random traffic split**, and **★ingest the MoEngage delivery event stream as the control baseline**.
- **Current-state facts**:
  - Delivery/conversion logs are **fully recorded down to the user level** (read → whether converted are all traceable), serving as the control-group sample source (row63).
  - The current Botim side has **no cross-campaign dedup and no per-user daily cap**, so the same user may receive multiple messages in one day (row38); during the Shadow period, running old and new in parallel will amplify this problem (Data Analysis special topic D24).
  - MoEngage supports gray-release / random traffic split, which can also be selected manually; the traffic split is coordinated by Growth (row65).
  - There used to be a "test-population dedicated channel"; **whether it still exists awaits Growth confirmation** (row44).
  - The Shadow observation period can be as short as 1–2 days, depending on the campaign (row67).

---

## 1. Complete Feature List

### A. Traffic Split and Control Group (acceptance framework foundation)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M7-A1 | Control-group sample source ingestion | Reuse user-level delivery/conversion logs (read → whether converted are traceable) as the control-group sample source | [Replicate] | row63 |
| M7-A2 | Control-group split strategy | Support two control-group partitioning approaches, "hold 5% untouched" or "random traffic split"; scale/rules configurable | [Replicate] | row65 |
| **M7-A3** | **5% random traffic split (reuse M2 rule engine)** | Use the existing rule engine to split 5% of traffic from the same user group into the new system, with the remainder still going through MoEngage, **without launching a separate traffic-split system** | **★Enhancement** | row65 |
| M7-A4 | Parallel control orchestration | Shadow and MoEngage **run in parallel** on the same user group, perform A/B comparison, with a unified observation standard | [Replicate] | row64 |
| **M7-A5** | **Test-population dedicated channel (reuse to be confirmed)** | Connect to Botim's historical "test-population dedicated channel" so that Shadow experiments do not pollute production traffic; whether it still exists awaits Growth confirmation | **★Enhancement** | row44 |

### B. Dedup Middle-layer (hard requirement, prevent control distortion)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M7-B1** | **Old/new parallel dedup middle-layer** | During the Shadow period the old and new systems run in parallel, and **the same user must not be double-pushed**; dedup is placed ahead of both delivery paths to avoid "both sides sending" distorting the control——**a hard requirement** | **★Enhancement** | row38/D24 |
| **M7-B2** | **Cross-system single-user delivery ledger** | Record each user's delivery facts across the new/old systems, filling the current-state blank of "no cross-campaign dedup, no daily cap" (row38), to feed dedup decisions | **★Enhancement** | row38/D24 |

### C. A/B Comparison Report (acceptance deliverable)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M7-C1 | A/B comparison report | Produce a new-vs-old view → click → conversion comparison on the same user group, to sign off "not significantly lower than MoEngage" | [Replicate] | row64/Plan W5-W6 |
| **M7-C2** | **Significance testing (automated)** | Perform significance testing on the A/B difference, giving a statistical conclusion of "not significantly lower," rather than eyeballing absolute values | **★Enhancement** | row64 |
| **M7-C3** | **Comparison report ready the moment the campaign launches** | The report is ready as soon as the campaign launches and updates automatically along with the observation period, with no need to manually pull data afterward | **★Enhancement** | row64/67 |
| **M7-C4** | **Attribution semantics reuse (M4)** | The comparison report reuses the M4 attribution/funnel standard (view → click → conversion, attribution window), ensuring the two systems are measured on a consistent, comparable basis | **★Enhancement** | row34/re-analysis line161 |
| M7-C5 | Configurable observation period | The observation period is set per campaign (as short as 1–2 days; Cross-sell types take longer); the conclusion is produced automatically when the period ends | [Replicate] | row67 |

### D. MoEngage Delivery Event Stream Comparison Ingestion (vendor-dependent)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M7-D1** | **MoEngage delivery event stream ingestion** | Ingest the MoEngage delivery event stream as the control baseline (one of three: API / log push / offline export); ingestion method and latency await vendor confirmation | **★Enhancement** | D23/re-analysis line170 |
| M7-D2 | Comparison standard alignment | Align the MoEngage event stream with the new system's delivery/conversion logs at the user level, eliminating standard differences before comparison | [Replicate] | D23/row63 |

---

## 2. 🤖 AI and ★Enhancement Feature Summary (differentiation relative to MoEngage)

**🤖 AI capabilities**
- This module is a validation framework with **no independent AI main line**; significance testing (M7-C2) belongs to statistical algorithms rather than generative AI, so it carries no 🤖 tag. The AI incremental main line is concentrated in M2 (NL2SQL) / M6 (copywriting).

**★ Enhancements / newly built this time (no MoEngage counterpart)**
- M7-A3 5% random traffic split reusing the M2 rule engine (no separate traffic-split system)
- M7-A5 Test-population dedicated channel reuse (isolating production traffic)
- **M7-B1 Dedup middle-layer to prevent double-send (hard requirement, otherwise the control is distorted) ← the most critical enhancement**
- M7-B2 Cross-system single-user delivery ledger (filling the current-state blank of no dedup / no daily cap)
- M7-C2 Significance testing automation
- M7-C3 Comparison report ready the moment the campaign launches
- M7-C4 Attribution semantics reuse of M4 (consistent measurement across the two systems)
- M7-D1 Ingest the MoEngage delivery event stream as the control

**One-line positioning**: M7 = **the exit condition for replacement**——using "control-group sample source (A1) + 5% traffic split (A3) + A/B comparison report (C1)" as the acceptance foundation, layered with **★dedup middle-layer to prevent double-send (B1, hard requirement) + ★significance comparison report (C2/C3) + ★reuse of M2 traffic split / M4 standard / MoEngage event stream (A3/C4/D1)**, to prove the new system is "not significantly lower than MoEngage."

---

## 3. Effort Mapping (person-days, consistent with the re-analysis, total ~23)
| Sub-item | Corresponding features | Person-days |
|---|---|---:|
| Traffic split / control group | A1–A5 | 6 |
| Dedup middle-layer | B1–B2 | 6 |
| Comparison report (significance) | C1–C5 | 6 |
| MoEngage delivery event stream ingestion | D1–D2 | 5 |
| **Subtotal** | | **~23** |
> The 5% traffic split (A3) reuses the M2 rule engine, and the comparison report (C4) reuses M4 attribution semantics, so both are reuse / thin layers and are not separately itemized with large amounts.

---

## 4. Dependencies
### 4.1 Technical dependencies
- **M2 rule engine → prerequisite for M7**: the 5% random traffic split (A3) reuses the existing rule engine to split traffic (row65 / re-analysis line160).
- **M1 delivery + M8 delivery/conversion logs → prerequisite for M7**: user-level delivery/conversion logs are the basis for the control-group sample source and the dedup ledger (row63 / re-analysis line162).
- **M4 attribution semantics → reused by M7**: the comparison report (C4) reuses the M4 attribution/funnel standard (re-analysis line161).

### 4.2 Organizational/Data dependencies (prerequisites for estimation, currently mostly "to be asked")
| Dependency party | What it provides | Blocked features |
|---|---|---|
| **Growth team (Dubai, Radhika)** | Selection of high-frequency Shadow scenarios (row66), 5% traffic-split coordination (row65), acceptance criteria + comparison report format (row64), whether the test-dedicated channel still exists (row44) | A2/A3/A5 / C1–C5 |
| **MoEngage vendor** | Delivery event stream ingestion method (API/log push/offline export) and latency (D23 / re-analysis line170) | D1/D2 |

---

## 5. Blockers & Risks
- **R1 Shadow double-send** → during the Shadow period old and new run in parallel, so the **dedup middle-layer (B1/D24) is a hard requirement**, otherwise the same user is double-pushed and the control is distorted (row38/D24 / re-analysis line186).
- **R2 Acceptance criteria / observation period pending Growth** → if "what to observe and what the acceptance criteria are" (row64) and the observation period (row67) are undecided, the C-group report cannot be finalized.
- **R3 MoEngage event stream ingestion method and latency pending vendor** → three paths of API/log push/offline export, with unknown latency (D23) → determines the difficulty of D-group ingestion and the real-time-ness of the control.
- **R4 Test-dedicated channel current state to be confirmed** → Botim previously had a test-population dedicated channel; whether it still exists requires Growth confirmation (row44); if it no longer exists, A5 needs to be newly built to isolate production traffic.

---

## 6. Phase Rollout Recommendation
- **Phase 1 (W5–W6, acceptance gate)**: corresponding to Plan W5–W6——select **1 high-frequency scenario (wallet activation Push, row66)**, randomly split **5% of traffic into the new system**, and **produce an A/B comparison report in 2 weeks**, proving "not significantly lower than MoEngage" (Plan W5–W6 / re-analysis line128).
- **Execution prerequisite**: must be done **immediately** after the W3–W4 MVP (delivery + audience targeting + funnel) is up and running——M7 is the exit condition for Phase 1; only after validation passes does it proceed to the Phase 2 full rollout (re-analysis line187 ②③).
- **Recommended sequence**: first lock in the Shadow scenario + 5% traffic-split channel as prerequisites (Growth, re-analysis line177) → connect the control-group sample source (A1) and the dedup middle-layer (B1) → run the 5% traffic split on one high-frequency scenario → produce the significance comparison report automatically (C2/C3) for sign-off when the period ends.

---

## Appendix: Cross-check Supplement Log (relative to the initial formal list)
| # | Supplement item | Source basis | Landing point |
|---|---|---|---|
| 1 | Dedup middle-layer to prevent double-send (hard requirement) | re-analysis §6 R5 line186 / Data Analysis special topic D24 / Survey row38 | M7-B1 / B2 |
| 2 | Significance testing automation | re-analysis line80–81 "comparison report (significance)" / Survey row64 | M7-C2 |
| 3 | MoEngage delivery event stream ingestion | re-analysis §5.2 line170 / Data Analysis special topic D23 | M7-D1 / D2 |
| 4 | Attribution semantics reuse of M4 (consistent standard) | re-analysis §5.1 line161 "M4 attribution semantics → reused by M7 (comparison report)" | M7-C4 |
| 5 | 5% traffic split reusing M2 rule engine | re-analysis §5.1 line160 "M2 rule engine → shared by M7 (traffic split)" / Survey row65 | M7-A3 |
| 6 | Control-group sample source = user-level delivery/conversion logs | re-analysis §5.1 line162 "M1 delivery + M8 delivery logs → prerequisite for M7" / Survey row63 | M7-A1 |
| 7 | Effort mapping (person-days) | re-analysis line81 | §3 |
| 8 | Dependencies (technical + organizational) | re-analysis §5.1 / §5.2 | §4 |
| 9 | Blockers & Risks | re-analysis §5.3 / §6 R5 | §5 |
| 10 | Phase rollout (W5–W6 acceptance gate) | re-analysis §4.1 line128 / Plan W5–W6 | §6 |

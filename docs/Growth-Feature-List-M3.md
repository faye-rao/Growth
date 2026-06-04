# Growth Feature List · M3 — Content and Push Orchestration (A/B/N)

> Version: M3-1 (formal complete edition)
> Source: MoEngage screen recordings + `用增问题survey-updated v3.xlsx` (Survey / Plan / Data-analysis special section).
> Already **cross-checked and supplemented** against the M3 section of "Botim Growth Platform_Survey-based Re-analysis" (see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** benchmarked against MoEngage, must-have for replacement ｜ **[★Enhancement]** newly added this time / superior to MoEngage ｜ **[🤖AI]** AI capability (incremental main line).

---

## 0. Module Positioning
- **Priority**: P0 (the second of "the 3 core features we are building", after messaging, connecting to cohort building, Survey conclusion #6 / row76).
- **Baseline**: Replicate steps ② and ③ of MoEngage's "pure rule-engine 3-step method" — ② define content (A/B/N groups + version fine-tuning), ③ define push time/conditions (row32).
- **Incremental main line**: Layer on **🤖AI orchestration** (describe activity goals in natural language → automatically generate audience + copy + schedule + Flow; the survey explicitly says "the use of a large model (GPT) to replace orchestration can be explored" row22), delivering on "**incremental value comes from AI improving activity volume / validation efficiency**" (row6); and **directly fill in the cross-activity frequency capping / dedup / quiet hours that MoEngage entirely lacks** (row38/42).
- **Current-state facts**: ~800 activities/year, ≈2–3 per day (row12); the most-used capability = delivering activity configuration to each user + sending pushes after segmentation (row21); mainly batch activities, partly real-time triggered (row62); **no cross-activity dedup, no per-user daily cap, may receive 3 in one day** (row38/42); In-App modals can be set to first time/first time per page/first time per day (row37); time zone unified to Asia/Dubai (UAE). The Flow node types/complexity in use are unknown, pending Growth confirmation (row35/36).

---

## 1. Complete Feature List

### A. Orchestration Engine / Flow (core baseline)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M3-A1 | Content configuration and delivery | Replicate "deliver activity configuration to each user" — the most-used capability; configuration of the three elements layout/time/content | [Replicate] | row21/32 |
| M3-A2 | Push time/condition configuration | Replicate step ③ of the 3-step method: define push time, define push trigger conditions | [Replicate] | row32 |
| M3-A3 | Triggered vs batch activities | Two orchestration types: batch activities (the main body) + triggered (triggered by page open/event report, e.g., "push 10 minutes after account opening") | [Replicate] | row61/62 |
| M3-A4 | Orchestration engine (state machine) | Activity lifecycle state machine: draft/published/running/paused/ended, driving node transitions | [Replicate] | row32/76 |
| **M3-A5** | **Flow node types (delay/branch/A·B/wait-for-event/webhook)** | Replicate MoEngage Flow nodes; **the specific node types in use and Flow complexity to be scoped after Growth confirmation** | **[Replicate]** | row35/36 |

### B. A/B/N Experiments and Versions (core enhancement)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M3-B1 | A/B/N group configuration | Replicate step ②: configure A/B/N multi-group content + version fine-tuning within the same activity | [Replicate] | row32 |
| **M3-B2** | **Automatic traffic splitter** | Randomly split traffic by ratio to each A/B/N group; **the splitter reuses the M5/M2 rule engine**, not reinventing the wheel | **[★Enhancement]** | row65/D65(line72) |
| **M3-B3** | **Significance testing** | Experiment results automatically compute significance and give the recommended winning version, distinct from MoEngage which only outputs raw numbers | **[★Enhancement]** | row64/15 |

### C. Scheduling and Time Zone
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M3-C1 | Activity scheduling | Scheduled/recurring scheduling; connecting to the real-time trigger conditions of triggered activities | [Replicate] | row32/61 |
| **M3-C2** | **Unified time zone (Asia/Dubai)** | Scheduling/triggering computed uniformly by UAE time zone, avoiding cross-time-zone mis-sends | **[★Enhancement]** | line5/row47 |

### D. Activity Template Library
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M3-D1 | Monthly running activity templates | Replicate and accumulate **3–5 high-frequency activity templates running each month** (same structure, different parameters) | [Replicate] | row11/12 |
| **M3-D2** | **One-click template reuse** | One-click copy a high-frequency activity template into a new activity with parameterized fine-tuning, supporting the throughput of ~800 activities/year, 2–3 per day | **[★Enhancement]** | row12/21 |

### E. Cross-activity Frequency Capping / Dedup / Quiet Hours (filling MoEngage's complete gap)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M3-E1** | **Per-user global daily cap** | Currently **no per-user daily cap, may receive 3 in one day**; build in-house to add a global frequency cap (**cap value to be set by Growth combining UAE policy + user fatigue**) | **[★Enhancement]** | row38/42/47 |
| **M3-E2** | **Cross-activity dedup** | Currently **no cross-activity dedup**; build in-house to add cross-activity dedup, avoiding the same user being repeatedly messaged by multiple activities | **[★Enhancement]** | row38 |
| **M3-E3** | **Quiet Hours** | Currently none; build in-house to add quiet hours, combining UAE local policy and user fatigue to suppress out-of-window messaging | **[★Enhancement]** | row42/47 |
| M3-E4 | Frequency-capping downgrade and Shadow dedup connection | Frequency capping/dedup overall **downgraded and deferred** (currently none anyway); but the **Shadow-period dedup middle layer (M7) is a hard requirement**, and this module connects to it to prevent double-sends | [Replicate] | line63/line186 |

### F. 🤖AI Orchestration (the biggest differentiation highlight)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M3-F1** | **Natural-language activity orchestration** | The survey explicitly says "**the use of a large model (GPT) to replace orchestration can be explored**" — describe activity goals in natural language → **automatically generate audience + copy + schedule + Flow**, serving "incremental value comes from AI improving activity volume / validation efficiency" | **[🤖AI][★Enhancement]** | row22/6 |
| **M3-F2** | **AI-generated results previewable and editable** | The AI-generated audience/copy/schedule/Flow is transparently displayed and can be manually fine-tuned before publishing; AI is not a black box | **[🤖AI][★Enhancement]** | row22/32 |
| **M3-F3** | **AI copy integration (M6)** | Multilingual (Indian/Filipino/Arabic/English) AI copy directly injected into A/B/N versions, connected with orchestration | **[🤖AI]** | row76/M6(line40) |

### G. Orchestration Frontend and Downstream Connection
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M3-G1 | Frontend orchestration UI | Visual activity-orchestration interface: layout/time/content/grouping/Flow configured in one place | [Replicate] | row21/32 |
| M3-G2 | Audience input (depends on M2) | Orchestration consumes M2 cohort-building results as the activity audience input | [Replicate] | row11/32 |
| M3-G3 | Messaging-execution landing (depends on M1) | Orchestration results handed to M1 messaging execution to send (Push/In-App), connecting to rate limiting | [Replicate] | row53/22 |
| M3-G4 | Effect recovery (depends on M4) | Activity tracking flows back to M4 funnel tracking, closing the effect loop | [Replicate] | row76/15 |

---

## 2. 🤖 AI and ★Enhancement Feature Summary (differentiation relative to MoEngage)

**🤖 AI capabilities (incremental main line, aligned with row6 "incremental value comes from AI" / row22 "GPT to replace orchestration")**
- M3-F1 Natural-language activity orchestration ← **the strongest highlight, the survey explicitly names "exploring a large model to replace orchestration"**
- M3-F2 AI-generated results previewable and editable (AI not a black box)
- M3-F3 AI copy (M6) integrated into A/B/N versions

**★ Enhancements this time (superior to MoEngage's current state)**
- M3-E1/E2/E3 Cross-activity frequency capping + dedup + quiet hours ← **filling MoEngage's complete gap (may receive 3 in one day)**
- M3-B2 Automatic traffic splitter (reuses M5/M2 rule engine)
- M3-B3 Significance testing (automatically determines the winning version)
- M3-D2 One-click reuse from the activity template library
- M3-C2 Unified UAE time zone

**One-line positioning**: M3 = **Replicate MoEngage orchestration steps ②③ (A/B/N + scheduling + Flow nodes + templates) + 🤖AI orchestration (natural language → audience/copy/schedule/Flow) delivering on "AI increment" + ★filling the cross-activity frequency capping / dedup / quiet hours that MoEngage entirely lacks**.

---

## 3. Effort Mapping (person-days, consistent with the Re-analysis)
| Sub-item | Corresponding feature | Person-days |
|---|---|---:|
| Orchestration engine (state machine) | A1–A5 | 14 |
| A/B/N + versions | B1–B3 | 8 |
| Scheduling / triggering | C1/C2 + A3 | 5 |
| Activity templates | D1/D2 | 6 |
| Frequency capping / dedup (downgraded, Shadow dedup middle layer see M7) | E1–E4 | 6 |
| Frontend orchestration UI | G1 (+G2–G4 connection) | 12 |
| **Subtotal** | | **~51** |
> 🤖AI orchestration (F1–F3) advances in parallel as an increment, with the core LLM capability counted in M6; the orchestration-side integration is a thin layer, not separately listed as a large amount. The splitter (B2) reuses M5/M2 and is not double-counted.

---

## 4. Dependencies
### 4.1 Technical Dependencies
- **M2 cohort building → prerequisite for M3**: Orchestration needs M2 cohort-building results as the activity audience input (G2); without an audience, orchestration has no target.
- **Splitter reuses M5/M2**: B2 automatic traffic splitting reuses the M5/M2 rule engine, not reinventing it (line72/line160).
- **M1 messaging execution → carries M3**: Orchestration results handed to M1 for landing sends (Push/In-App), connecting to rate limiting (G3).
- **M4 funnel tracking → recovers M3**: Activity tracking flows back to M4 to close the effect loop (G4).
- **M7 Shadow dedup middle layer**: Prevents double-sends during the Shadow period, E4 connects (line186).

### 4.2 Organizational/Data Dependencies (estimation prerequisites, mostly "to be asked" for now)
| Dependency | What it provides | Blocked features |
|---|---|---|
| **Growth team (Dubai, Radhika)** | Flow node types in use + Flow complexity (row35/36); per-user frequency policy + UAE compliance requirements (row42/47); real-time vs batch share (row62); activity type/Cohort coverage (row12) | A5 Flow nodes / E1–E3 frequency capping / A3 triggered-type proportion |
| **M2 cohort-building module** | Audience snapshot API (audience input) | G2 / overall orchestration target |
| **M1 messaging module** | Messaging-execution interface + rate limiting | G3 landing send |

---

## 5. Blockers & Risks
- **R1 Frequency cap unknown** → the per-user daily cap and quiet hours need **Growth to set combining UAE local policy and user fatigue**, otherwise E1/E3 cannot fix parameters (row42/47).
- **R2 Real-time share is the switch for triggered activities** → If Growth reports a high proportion of real-time activities, A3 triggered orchestration gets heavier and depends on M2 near-real-time segments (row62).
- **R3 Flow complexity unknown** → the node types in use and the typical Flow branch depth have not been obtained (row35/36); the A5 node scope and orchestration-engine complexity cannot be estimated precisely, and the state machine may need extension.
- **R4 AI-orchestration feasibility** → the end-to-end controllability of F1 natural language → audience/copy/schedule/Flow is yet to be validated; strategy: **advance in parallel as an increment, with previewable-and-editable as fallback (F2), not a Phase 1 blocker**.

---

## 6. Phase Rollout Recommendations
- **Phase 1 (W3–W4 MVP)**: First do **3–5 high-frequency activity templates (D1/D2) + A/B/N (B1–B3) + AI copy (M6/F3) integration**, running through the complete orchestration of one high-frequency scenario (e.g., Wallet activation Push).
- **🤖AI orchestration (F1/F2) advances in parallel as an increment, not a Phase 1 blocker** (aligned with line187 ④).
- **Frequency capping/dedup (E1–E3) can be downgraded and deferred** (currently none anyway, not affecting the "no worse than current state" goal); but the **Shadow-period dedup middle layer (M7/E4) is required**, otherwise users get double-pushed and the comparison is distorted (line186).
- **Phase 2+**: Roll out, breadth-wise, the full Flow node types (A5, after row35/36 confirmation), complete frequency capping/dedup/quiet hours (E1–E3), and AI orchestration.
- **Recommended order**: First close the prerequisite interviews on row35/36 (Flow), row42/47 (frequency-capping policy), row62 (real-time share) → run the MVP through templates + A/B/N + AI copy → after validation, expand the frequency-capping and AI-orchestration increments.

---

## Appendix: Cross-check Supplement Log (relative to the initial formal list)
| # | Supplement | Source basis | Landing point |
|---|---|---|---|
| 1 | Flow node types (delay/branch/A·B/wait-for-event/webhook) | Re-analysis M3 feature rows / Survey row35-36 | M3-A5 |
| 2 | Automatic traffic splitter reuses M5/M2 | Re-analysis line63/line72/line160 | M3-B2 |
| 3 | Significance testing | Re-analysis M3 technical solution / Survey row64 | M3-B3 |
| 4 | Unified time zone Asia/Dubai | Re-analysis line5 / Survey row47 | M3-C2 |
| 5 | Cross-activity frequency capping/dedup/quiet hours (MoEngage entirely lacks) | Survey row38/42/47 | M3-E1/E2/E3 |
| 6 | Shadow dedup middle-layer connection | Re-analysis line63/line186 | M3-E4 |
| 7 | AI orchestration (GPT to replace orchestration) | Survey row22/6 | M3-F1/F2 |
| 8 | AI copy (M6) integrated into orchestration | Re-analysis line40 / Survey row76 | M3-F3 |
| 9 | Effort mapping | Re-analysis line63 | §3 |
| 10 | Dependencies (technical + organizational) | Re-analysis §5.1/5.2 | §4 |
| 11 | Blockers & Risks | Re-analysis §6 / Survey row42/62/36 | §5 |
| 12 | Phase rollout recommendations | Re-analysis §4.1 / line187 | §6 |

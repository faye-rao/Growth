# Growth Feature List · M1 — Messaging Execution (Push + In-App Modal)

> Version: M1-1 (formal complete edition)
> Source: MoEngage screen recordings + `用增问题survey-updated v3.xlsx` (Survey / Plan / Messaging·Channel special section).
> Already **cross-checked and supplemented** against the M1 section of "Botim Growth Platform_Survey-based Re-analysis" (see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** benchmarked against MoEngage, must-have for replacement ｜ **[★Enhancement]** newly added this time / superior to MoEngage ｜ **[🤖AI]** AI capability (incremental main line).

---

## 0. Module Positioning
- **Priority**: **P0 highest** (Survey conclusion #3/#7: highest replacement priority = messaging Push/notification + In-App modal, followed by user segmentation, row73).
- **Baseline**: Replicate MoEngage messaging execution — Push/SMS go through Botim's own channels, In-App modals self-rendered by SDK, supplemented with messaging logs (Re-analysis M1 section).
- **Incremental main line**: On top of the "no worse than current state" baseline, layer experience enhancements such as **deliverability prediction / invalid-user filtering**, **multi-channel fallback**, a **unified flexible activity-slot framework**, and a **unified frequency-capping integration point**, directly addressing the issues the Survey named: "uninstalled users selected will never receive it, Android delivery rate lower than iOS" (row43).
- **Current-state facts**:
  - Push/SMS are **sent by Botim itself**; MoEngage only does orchestration / calls the interface. Botim has consolidated this, and MoEngage has **no direct push permission**; **no Email** (row40/53).
  - In-App modal = MoEngage **SDK renders directly, not via the Botim backend** (row40).
  - **No fixed activity slots**, configured flexibly per page (modals, ratings, etc. all count as activities) (row41).
  - Rate limiting: manual review was once set up, now changed to **interface-side rate limiting** to prevent the system / pushed page from being overwhelmed (row22/47).
  - Opt-out: MoEngage maintains the list, which is exportable; at send time it fetches the list then calls the Botim API (row48).
  - **On the Botim side there is no cross-activity dedup and no per-user daily cap**, only push rate limiting; a user may receive multiple messages in one day (row38/42).
  - Volume: activities range from large to small, **largest around the million level per activity** (row54).

---

## 1. Complete Feature List

### A. Channel Integration and Sending (Push / SMS, core baseline)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M1-A1 | Push channel adapter layer | Calls Botim's already-consolidated proprietary push interface to send (MoEngage has no direct-push permission, we are on par), **one send at a time** | [Replicate] | row40/53/37 |
| M1-A2 | SMS channel adapter layer | Calls Botim's own SMS channel to send, going through the unified adapter layer along with Push | [Replicate] | row40/53 |
| M1-A3 | No Email channel (aligned with current state) | Explicitly not doing Email — neither MoEngage nor Botim currently has Email messaging | [Replicate] | row40/53 |
| M1-A4 | Large-batch sending capacity | Supports send-task orchestration and queuing for up to about the **million level** of target users per activity | [Replicate] | row54 |
| **M1-A5** | **Multi-channel fallback degradation** | On Push failure (third-party Google/APNS unreachable / user offline) → automatically degrade to **SMS / In-App**, improving overall reachability | **[★Enhancement]** | row43/40 |

### B. In-App Modal Rendering and Activity Slots (SDK self-rendering baseline)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M1-B1 | In-App modal self-rendering | On par with MoEngage SDK direct-rendering capability, **not via the Botim backend**; the client renders the modal per the delivered configuration | [Replicate] | row40 |
| M1-B2 | Flexible per-page configuration | No fixed activity slots; flexibly configure activities such as modals/ratings per **page** (page × position) | [Replicate] | row41 |
| M1-B3 | In-App frequency-capping options | Modals can be set to **first time / first time per page / first time per day** (replicating MoEngage's existing capability) | [Replicate] | row37 |
| **M1-B4** | **Unified flexible activity-slot framework** | A "page × position" configurable activity-slot mid-platform that accumulates **position-effect data**, breaking the current state of "no fixed activity slots, price-effect unknowable" | **[★Enhancement]** | row41 |

### C. Rate Limiting and Frequency-Capping Integration (execution-side protection)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M1-C1 | Interface-side send rate limiting | Integrates with Botim Open Platform's rate-limiting interface to prevent the system / pushed page from being overwhelmed (replacing early manual review) | [Replicate] | row22/47/38 |
| **M1-C2** | **Unified frequency-capping integration point** | A unified integration point on the messaging side: In-App can now be set to first time / first time per page / first time per day, Push has none — here we only do the **execution-side integration** (the cross-activity frequency-capping core is in M3) | **[★Enhancement]** | row37/38/42 |

### D. Opt-out and Compliance Integration
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M1-D1 | Opt-out list integration | Replicates "fetch list → then send": maintains an exportable opt-out list, fetches the list at send time then calls the Botim API | [Replicate] | row48 |
| M1-D2 | Pre-send opt-out filtering | Filters the target audience against the Opt-out list before send-task execution, avoiding messaging opted-out users | [Replicate] | row48/47 |

### E. Messaging Logs and Tracking (foundation prerequisite for M4/M7)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M1-E1 | Messaging-log tracking and persistence | Records `user_id / campaign_id / channel / time / content_id / click / convert`, persisted at the **user level** | [Replicate] | row52/63/49 |
| M1-E2 | Messaging-log as a service | Turns the messaging stream into a service, consumed by the **M4 funnel** and **M7 Shadow** comparison | [Replicate] | row63/76 |

### F. Deliverability Optimization (AI incremental highlight)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M1-F1** | **Invalid-user filtering** | Before sending, filter out **uninstalled / long-term offline / low-activity** users (the survey explicitly states "uninstalled users selected will never receive it"), improving effective delivery | **[★Enhancement]** | row43 |
| **M1-F2** | **Deliverability prediction and ranking** | Score and rank the target audience by reachability to prioritize sending (Android delivery rate lower than iOS, strongly correlated with user activity), may include AI prediction | **[🤖AI][★Enhancement]** | row43 |

---

## 2. 🤖 AI and ★Enhancement Feature Summary (differentiation relative to MoEngage)

**🤖 AI capabilities (incremental main line, aligned with row6 "incremental value comes from AI")**
- M1-F2 Deliverability prediction and ranking ← **the strongest highlight on the messaging side, directly hitting "uninstalled/low-activity users selected will never receive it, Android<iOS"** (row43)

**★ Enhancements this time (superior to MoEngage's current state)**
- M1-F1 Invalid-user filtering (uninstalled/long-term offline/low-activity, improving effective delivery, row43)
- M1-A5 Multi-channel fallback degradation (Push failure → SMS/In-App, breaking "no fallback channel", row43)
- M1-B4 Unified flexible activity-slot framework ("page × position" mid-platform + position-effect data, breaking "no fixed activity slots", row41)
- M1-C2 Unified frequency-capping integration point (unified integration on the messaging execution side, Push currently has no frequency capping, row37/38)

**One-line positioning**: M1 = **Replicate MoEngage messaging execution (Push/SMS self-send channels A1–A4 + In-App SDK self-rendering B1–B3 + rate limiting C1 + Opt-out D + messaging logs E) + messaging-side enhancements (deliverability F + multi-channel fallback A5 + activity-slot framework B4 + frequency-capping integration C2)**, the P0 highest priority, with messaging logs (E) a prerequisite for M4/M7.

---

## 3. Effort Mapping (person-days, consistent with the Re-analysis)
| Sub-item | Corresponding feature | Person-days |
|---|---|---:|
| Channel integration (Push/SMS) | A1–A4 (+A5 fallback) | 8 |
| In-App modal self-rendering + position configuration | B1–B4 | 12 |
| Rate-limiting coordination | C1 (+C2) | 4 |
| Messaging-log tracking | E1/E2 | 6 |
| Opt-out integration | D1/D2 | 3 |
| **Subtotal** | | **~33** |
> Deliverability prediction / invalid-user filtering (F1/F2) are AI increments, advancing incrementally with data/models, not separately listed as large amounts; the unified activity-slot framework (B4) and frequency-capping integration (C2) are mostly thin-layer enhancements, included within their corresponding sub-items.

---

## 4. Dependencies
### 4.1 Technical Dependencies
- **M8 messaging logs/data → prerequisite for M1**: Messaging-log tracking and persistence (E1) depends on the M8 data foundation (footprint integration / wide table).
- **M1 → depended upon downstream**: The **M4 funnel** and **M7 Shadow** reuse M1 messaging logs (E1/E2); M1 messaging + M8 messaging logs are prerequisites for M4/M7 (Re-analysis §5.1).

### 4.2 Organizational/Data Dependencies (estimation prerequisites, mostly "to be asked" for now)
| Dependency | What it provides | Blocked features |
|---|---|---|
| **Growth team (Dubai, Radhika)** | Existing activity-slot list + pages (D, row41), real delivery-rate/failure-rate numbers (row43), per-user frequency policy (row42), whether Shadow test-audience dedicated channels still exist (row44), precise daily push volume (row54) | B2/B4 activity slots / F1/F2 deliverability / C2 frequency capping / E2 (Shadow) |
| **Botim Open Platform** | Rate-limiting interface specs (row22/47), Opt-out list/interface (row48) | C1/C2 rate limiting & frequency capping / D1/D2 Opt-out |
| **Pei Qing / Data Team** | Tracking schema, footprint messaging-log samples | E1/E2 messaging logs |

---

## 5. Blockers & Risks
- **R1 Delivery rate uncontrollable** → depends on third parties (Google/APNS) + whether the user is online; **Android delivery rate is lower than iOS**; the range is wide and strongly correlated with the activity level of the selected users, and **uninstalled users selected will never receive it** (row43). → Mitigated by F1 invalid-user filtering + F2 deliverability prediction + A5 multi-channel fallback.
- **R2 Shadow-test dedicated channel current state to be confirmed** → Botim previously had a "test-audience dedicated channel"; whether it still exists needs Growth confirmation (row44); its absence affects M7 Shadow's ability to avoid polluting production traffic.
- **R3 No Email channel** → neither MoEngage nor Botim currently has Email (row40/53), so cross-channel fallback chains can only be organized among Push/SMS/In-App.
- **R4 Rate-limiting/Opt-out interfaces are external dependencies** → the rate-limiting and Opt-out cores are on the Botim Open Platform (row47/48); without clear interface specs, C1/D1 are hard to estimate precisely.
- **R5 No system-level frequency capping/dedup** → on the Botim side there is no cross-activity dedup and no per-user daily cap (row38/42); the cross-activity frequency-capping core is in M3, M1 only does the execution-side integration (C2), and the boundary with M3 needs to be aligned to avoid rework.

---

## 6. Phase Rollout Recommendations
- **Phase 1 (highest priority)**: First connect the sending + messaging-log tracking of one high-frequency scenario combining **Push + In-App** (e.g., **Wallet activation Push**) (A1/B1 + C1 + D1 + E1), for direct consumption by the **M4 funnel / M7 Shadow**.
- **Phase 2+**: Roll out, breadth-wise, multi-channel fallback (A5), the unified activity-slot framework (B4), the unified frequency-capping integration point (C2), and deliverability prediction / invalid-user filtering (F1/F2).
- **Recommended order**: First close the Growth/Open Platform prerequisites (activity-slot list, delivery-rate numbers, rate-limiting/Opt-out interfaces, test-dedicated channel current state) → run the MVP through the Wallet-activation Push sending + messaging logs → after validation, expand the deliverability AI increment.

---

## Appendix: Cross-check Supplement Log (relative to the initial "key-points-only" edition)
| # | Supplement | Source basis | Landing point |
|---|---|---|---|
| 1 | Large-batch sending capacity (million level per activity) | Survey row54 / Re-analysis M1 volume | M1-A4 |
| 2 | No Email channel explicitly listed as a replication item | Survey row40/53 | M1-A3 |
| 3 | Pre-send opt-out filtering (fetch list → filter → send) | Survey row48 | M1-D2 |
| 4 | Messaging-log as a service (for M4/M7 consumption) | Re-analysis §5.1 "M1 messaging + M8 messaging logs → prerequisite for M4/M7" | M1-E2 |
| 5 | Effort mapping (~33 person-days, 5 sub-items) | Re-analysis M1 line53 | §3 |
| 6 | Technical + organizational dependencies (M8 prerequisite, depended upon by M4/M7; Growth/Open Platform/Pei Qing) | Re-analysis §5.1/§5.2 | §4 |
| 7 | Blockers & Risks (delivery rate/Shadow channel/no Email/rate-limiting Opt-out/no frequency capping) | Re-analysis §6 + Survey row43/44/38/42 | §5 |
| 8 | Phase rollout (Wallet-activation Push connected first for M4/M7) | Re-analysis §4 / §6 recommended rollout order | §6 |
| 9 | In-App frequency-capping existing capability (first time/first time per page/first time per day) explicitly listed | Survey row37 | M1-B3 |

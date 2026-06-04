# Growth Feature List · M8 — Data Foundation (our part): ingestion + consumption + gap-filling + servicization

> Version: M8-1 (formal complete edition)
> Source: MoEngage screen recording + `用增问题survey-updated v3.xlsx` (Survey / Plan / Data Analysis special topic).
> **Cross-checked and supplemented** against the M8 section + §5 dependencies + §6 risks + §4 Phase of《Botim增长平台_基于Survey的重新分析》(see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** must-have benchmarked against current state, prerequisite for replacement ｜ **★Enhancement** newly added this time / better than current state ｜ **🤖AI** AI capability (incremental).

---

## 0. Module Positioning
- **Priority**: **P0 prerequisite** (M8 is the **foundation** of M2 audience targeting / M4 funnel / M9 behavioral analytics / M7 Shadow; without M8 the downstream cannot start work, re-analysis §5.1).
- **Baseline positioning**: **not a data-warehouse rebuild**. **The T+1 cleansing is mainly done by the Data Team (Mr. Ma); we are the consumer + fill in the delivery logs**——this module only does four things: "**ingestion + consumption + gap-filling + servicization**" (re-analysis line86).
- **Two data sources**: ① footprint (Botim's own tracking platform) fetched directly ② provided by the Data Team after cleansing (row28).
- **Current-state facts**: footprint keeps a **full backup** (when ingested it was already anticipated that MoEngage would be replaced), but it is currently **barely accessed** (row49); the event schema is documented, but it is recommended to pull from footprint via the Data Team (more accurate and more complete than the documentation, row50); Botim has **no CDP**, only databases (row52); **no email**, whether business-line IDs are unified / whether there is a Mapping is to be investigated (row31); **no write-back, no downstream consumption** (row55/56); delivery/conversion logs are fully recorded down to the user level (row63).
- **Core incremental logic**: **activate** the "barely accessed" footprint full backup into a gold mine for the self-built data foundation, **with no need for re-instrumentation** (row49).

---

## 1. Complete Feature List

### A. Event Ingestion (footprint / Kafka subscription)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M8-A1 | footprint full event ingestion | Directly connect to the full backup of Botim's own tracking platform footprint (already exists, **no re-instrumentation needed**) | [Replicate] | row28/49 |
| M8-A2 | Data Team cleansed-result ingestion | Ingest the T+1 cleansed events/labels from the Data Team (source ②), running in parallel with footprint as dual sources | [Replicate] | row28/30 |
| M8-A3 | Event schema finalization | Use footprint pulled via the Data Team as the source of truth (more accurate and complete than the documentation), and solidify the event-type/field dictionary | [Replicate] | row50 |
| **M8-A4** | **Activate the dormant footprint full backup** | This "barely accessed" full backup is precisely the ready-made gold mine for the self-built foundation; usable upon ingestion, **with no re-instrumentation needed** | **★★Enhancement** | row49 |
| **M8-A5** | **Kafka event-stream subscription (near-real-time channel)** | In addition to the T+1 batch, add a lightweight real-time subscription channel to feed data for near-real-time suppression | **★Enhancement** | row59/61/D31 |

### B. ID-Mapping Consumption (provided by the Data Team)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M8-B1 | ID-Mapping table consumption | Consume the cross-business-line ID-Mapping table provided by the Data Team (do not build the mapping ourselves, **we are the consumer**) | [Replicate] | row31/D2 |
| **M8-B2** | **Cross-business-line ID unification (no email)** | Use customer_id/phone number as the primary key + Mapping consumption to support cross-product funnels / cross-sell (under the no-email premise) | **★Enhancement** | row31/D2 |
| M8-B3 | Mapping coverage/accuracy verification | Before landing, verify the coverage/accuracy provided by the Data Team, flag uncovered business lines, for M2/M4 to evaluate | [Replicate] | row31/D2 |

### C. Delivery / Conversion Log Wide Table (our key gap-filling focus)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M8-C1 | Delivery log wide table | Persist user-level delivery event stream (user_id/campaign_id/channel/time/content_id/click/convert); currently recorded fully down to the user level | [Replicate] | row63 |
| M8-C2 | Conversion log wide table | User-level conversion records (read → whether converted are all traceable), for M4 funnel/attribution consumption | [Replicate] | row63 |
| **M8-C3** | **Delivery log bulk filled by us** | Currently the logs are in MoEngage; after replacement, delivery-log instrumentation/persistence belongs to us (bridging the M1 delivery-log instrumentation); gap-filling, not migration | **★Enhancement** | row55/56/63 |

### D. Wide Tables Needed for Audience Targeting / Funnel
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M8-D1 | Audience-targeting wide table | Provide the "over wide table" of behavior + attributes + labels for the M2 rule engine/batch evaluation | [Replicate] | row30/52/D10-D12 |
| M8-D2 | Funnel wide table | Provide user-level event-sequence wide tables for the M4 funnel / cross-product funnel | [Replicate] | row28/D2 |
| M8-D3 | Label dictionary integration & consumption | Consume the Data Team's cleansed user labels (label sources ① Data Team ② MoEngage instrumentation), landing the dictionary/coverage | [Replicate] | row52/D10-D12 |

### E. Light DQC (Data Quality Control)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M8-E1 | End-to-end latency monitoring | Monitor the end-to-end latency of "behavior occurs → available for segmentation" (cleansing T+1, behavior available for segmentation T+1) | [Replicate] | row30/59/60/D30 |
| M8-E2 | Event-stream availability monitoring | Monitor footprint/Kafka event-stream availability to determine the feasibility of near-real-time suppression | [Replicate] | D31 |
| **M8-E3** | **Lightweight data quality control (DQC)** | Lightweight checks on null rate / standard drift / coverage of wide tables and labels, not heavyweight governance | **★Enhancement** | D32 |

### F. Servicization (bridging downstream, no write-back to Botim business DB)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| **M8-F1** | **"Suppress already-converted users" near-real-time suppression layer** | A lightweight real-time layer suppresses already-converted users on top of audience-targeting results (the survey indicates the real-time demand **is mainly for this**) → no need for end-to-end real-time | **★Enhancement** | row59/D31 |
| M8-F2 | Wide-table/log servicization | Servicize the audience-targeting wide table (M8-D1), funnel wide table (M8-D2), and delivery log (M8-C1) for M2/M4/M7/M9 to call | [Replicate] | row28/63 |
| **M8-F3** | **No-disruption replacement (no write-back, no downstream)** | Currently no write-back and no downstream consumption → decommissioning MoEngage carries no downstream-breakage risk, favoring fast, low-risk replacement | **★Enhancement** | row55/56 |

---

## 2. 🤖 AI and ★Enhancement Feature Summary (differentiation relative to the current state)

**★ Enhancements this time (better than current state)**
- **M8-A4 Activate the dormant footprint full backup ← strongest highlight**: this "barely accessed" full backup is precisely the ready-made gold mine for the self-built foundation, **with no re-instrumentation needed** (row49).
- M8-A5 Kafka event-stream subscription (near-real-time channel): feeds data for near-real-time suppression (row59/61/D31).
- M8-B2 Cross-business-line ID unification (no email): customer_id/phone-number primary key + Mapping consumption, supporting cross-product funnel/cross-sell (row31/D2).
- M8-C3 Delivery log bulk filled by us (gap-filling, not migration, row55/56/63).
- M8-E3 Lightweight DQC (D32).
- **M8-F1 "Suppress already-converted users" near-real-time suppression**: the survey indicates the real-time demand **is mainly for this** → a lightweight real-time layer suffices, no need for end-to-end real-time (row59).
- **M8-F3 No-disruption replacement risk**: no write-back, no downstream (row55/56) → favors fast, low-risk replacement.

> Note: M8 is the foundation layer, with **no 🤖AI main-line feature** (the AI increment is concentrated in M2 NL2SQL / M6 copywriting / M9 automated analysis); M8 feeds data to upstream AI via wide tables/servicization.

**One-line positioning**: M8 = **ingest the footprint full backup (A) + consume the Data Team's ID-Mapping and labels (B/D3) + fill in the delivery/conversion logs (C) + audience-targeting/funnel wide tables (D) + light DQC (E) + near-real-time suppression and servicization (F)**; no data-warehouse rebuild, doing "ingestion + consumption + gap-filling + servicization," activating the dormant backup into the downstream foundation.

---

## 3. Effort Mapping (person-days, consistent with the re-analysis)
| Sub-item | Corresponding features | Person-days |
|---|---|---:|
| Event ingestion (footprint/Kafka subscription) | A1–A5 | 6 |
| ID-mapping consumption | B1–B3 | 5 |
| Delivery/conversion log wide table | C1–C3 | 6 |
| Audience-targeting/funnel wide table | D1–D3 | 6 |
| Light DQC (data quality control) | E1–E3 | 3 |
| **Subtotal** | | **~26** |
> Note: **The T+1 cleansing is mainly done by the Data Team (Mr. Ma)**; we are the consumer + fill in the delivery logs (re-analysis line86); the near-real-time suppression layer (F1) mainly reuses the A5 real-time channel and is not separately itemized with a large amount.

---

## 4. Dependencies
### 4.1 Technical dependencies
- **M8 → prerequisite for M2/M4/M9/M7**: M8 is the **prerequisite foundation** of M2 (audience targeting) / M4 (funnel) / M9 (behavioral analytics) / M7 (Shadow); without wide tables/labels/ID-mapping/logs the downstream cannot start work (re-analysis §5.1).
- **M1 delivery + M8 delivery logs (C1/C3)** → prerequisite for the M4 funnel and M7 Shadow.

### 4.2 Organizational/Data dependencies (prerequisites for estimation, currently mostly "to be asked")
| Dependency party | What it provides | Blocked features |
|---|---|---|
| **Data Team (Mr. Ma)** | ER diagram/table list (D1), **ID-Mapping table + coverage (D2)**, T+1 cleansing, de-identified samples (D4), label dictionary/coverage (D10–D12), end-to-end latency (D30), event-stream availability (D31), DQ monitoring (D32) | A2/B1–B3/D1–D3/E1–E3/F1 |
| **Pei Qing** | Event schema, data sample coordination (row50/51) | A3 / overall kickoff |

---

## 5. Blockers & Risks
- **R1 Data samples + event schema not in place** → M2/M4 cannot start work (Pei Qing/Data Team, row50/51). **This is the first hard blocker before opening Phase 1.**
- **R2 ID-Mapping coverage/accuracy unknown** → under the no-email premise, the D2 Mapping coverage/accuracy determines the difficulty of the B2 cross-business-line unification and the reachability of cross-sell (Data Team D2).
- **R3 Whether MoEngage's internal derived metrics are in use needs investigation** → whether MoEngage's internally computed **RFM / predicted churn / engagement score** are in use is to be investigated (row57); **if someone uses them, they must be filled in M8/M2 before decommissioning, otherwise impacted**.
- **R4 Real-time event-stream availability is the switch for near-real-time suppression** → D31 event-stream availability determines the feasibility of F1 "suppress already-converted users" near-real-time suppression (if the real-time stream is unstable, F1 is scoped-down to a shorter batch).

---

## 6. Phase Rollout Recommendation
- **M8 is the most upstream module**. **Phase 1 W1–W2 (survey the assets)** requires obtaining: data samples + event schema + ID-mapping current state (re-analysis §4.1).
- **Phase 1 (W3–W4) landing sequence**: first connect "**footprint (A1/A4) + consume Data Team labels (D3) + delivery log wide table (C1)**" for M2/M4 to use; the audience-targeting/funnel wide tables (D1/D2) are synchronized with the M2/M4 MVP.
- **Phase 2+**: complete the Kafka real-time channel (A5), the near-real-time suppression layer (F1), and light DQC (E1–E3) for horizontal rollout; based on the R3 investigation result, decide whether to fill in derived metrics in M8/M2.
- **Full-replacement P-A stage** (re-analysis §4.2): M8 + M1 land first (3–4 weeks), with the foundation and delivery execution prioritized.

---

## Appendix: Cross-check Supplement Log (relative to the initial formal list)
| # | Supplement item | Source basis | Landing point |
|---|---|---|---|
| 1 | Activate the dormant footprint full backup (explicitly raised as the strongest highlight) | Survey row49 / re-analysis line84 | M8-A4 |
| 2 | Kafka event-stream subscription (near-real-time channel) | Survey row59/61 / Data Analysis special topic D31 | M8-A5 |
| 3 | Cross-business-line ID unification (no email, customer_id/phone-number primary key) | Survey row31 / Data Analysis special topic D2 | M8-B2 |
| 4 | Mapping coverage/accuracy verification | Data Analysis special topic D2 / re-analysis §5.2 | M8-B3 |
| 5 | Delivery log bulk filled by us (gap-filling, not migration) | Survey row55/56/63 / re-analysis line84 | M8-C3 |
| 6 | Label dictionary integration & consumption | Survey row52 / Data Analysis special topic D10–D12 | M8-D3 |
| 7 | End-to-end latency monitoring | Survey row30/59/60 / Data Analysis special topic D30 | M8-E1 |
| 8 | Event-stream availability monitoring | Data Analysis special topic D31 | M8-E2 |
| 9 | Lightweight DQC | Data Analysis special topic D32 | M8-E3 |
| 10 | "Suppress already-converted users" near-real-time suppression layer | Survey row59 / Data Analysis special topic D31 | M8-F1 |
| 11 | No-disruption replacement (no write-back, no downstream) | Survey row55/56 | M8-F3 |
| 12 | Effort mapping (event ingestion 6/ID-mapping 5/log wide table 6/audience-targeting funnel wide table 6/DQC 3 = 26) | re-analysis line85 | §3 |
| 13 | Dependencies (technical: M8 prerequisite for M2/M4/M9/M7; organizational: Data Team D1/D2/D4/D10-D12/D30-D32, Pei Qing schema) | re-analysis §5.1/§5.2 | §4 |
| 14 | Risk (whether MoEngage derived metrics RFM/churn/engagement are in use needs investigation) | Survey row57 / re-analysis §6 | §5 R3 |
| 15 | Phase rollout (W1–W2 obtain samples + schema + ID current state; W3–W4 first connect ingestion + labels + delivery logs) | re-analysis §4.1/§4.2 | §6 |

# Growth Feature List · M5 — 1-to-1 Personalization / Self-built Delivery (Web Experience)

> Version: M5-1 (formal complete edition)
> Source: MoEngage screen recording video 2 (end-to-end creation footage of a `Web & App (API)` type experience) + `用增问题survey-updated v3.xlsx` (Survey / Plan / Data Analysis special topic) + `survey_BC.txt`.
> Cross-checked and supplemented against the M5 section + §4 Phase + §5 Dependencies + §6 Risks of *Botim Growth Platform_Survey-based Re-analysis* (see "Cross-check Supplement Log" at the end).
> Type legend: **[Replicate]** benchmarked against MoEngage, mandatory for replacement ｜ **[★Enhancement]** newly added this time / better than MoEngage ｜ **[🤖AI]** AI capability (incremental mainline).

---

## 0. Module Positioning
- **Priority**: P1 ("1-to-1 personalization / self-built delivery", path ① homepage campaign slot; can be replaced slowly, one-year contract, inclined not to renew, row73/77).
- **Baseline**: Replicate the `Web & App (API)` type experience captured in MoEngage screen recording video 2 — a three-step wizard (select audience → content → schedule) + an equivalent `POST /experiences/fetch` content delivery API (video).
- **Risk positioning**: **Lowest risk, should be validated first**. The path ① homepage "1-to-1 personalization" card only borrows MoEngage's delivery capability to begin with (Botim's own rule-based grouping, client-side rendering), so it **can be self-built** (row11/73); once a self-built equivalent fetch API exists, it can be fully decoupled from MoEngage. Recommend feasibility validation in Phase 1.
- **Incremental mainline**: Fully remove the MoEngage dependency (path ① decoupling) + multilingual payload + client-side rendering / cache-degradation + 🤖AI (optional) personalized content / variant recommendation (aligned with row6 "incremental value comes from AI").
- **Status-quo facts**: Homepage grouping = Botim's own rule-based grouping then placed into MoEngage, only borrowing its delivery capability (row11/73); one of the most-used key features = "deliver configuration information to each user" (row21); no email, business-line IDs not linked, no CDP (row75); client-side rendering (the API type is not rendered within MoEngage, video).

---

## 1. Complete Feature List

### A. Equivalent Content Delivery API (Core Baseline)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M5-A1 | Equivalent fetch endpoint | Replicate `POST /experiences/fetch`: the client pulls the content payload the user is entitled to, by experience_key | [Replicate] | video/row11 |
| M5-A2 | Authentication mechanism | Basic token + MOE-APPKEY equivalent auth headers (the self-built side uses an equivalent AppKey/Token scheme) | [Replicate] | video |
| M5-A3 | Request-parameter spec | identifiers{customer_id, user_identifiers{u_em, u_mb}} + experience_key + custom attributes | [Replicate] | video/row31 |
| M5-A4 | content payload return | On match, return the content payload (KV / JSON), consumed by the client | [Replicate] | video |
| M5-A5 | Multi-platform code snippets | Provide cURL / Node.js / Go / PHP / Python / Ruby / Java integration examples | [Replicate] | video |
| **M5-A6** | **Fully remove the MoEngage dependency (path ① decoupling)** | Path ① only borrows delivery with client-side rendering to begin with; once an equivalent fetch is self-built it can be fully decoupled — **lowest risk, should be validated first** | **[★Enhancement]** | row73/11 |
| **M5-A7** | **fetch real-time performance / SLA guarantee** | The homepage load needs second-level return; agree on the real-time tier of match/qualification (near-real-time vs. batch snapshot) and timeout degradation | **[★Enhancement]** | row21/60 |

### B. Match/Qualification and Variation Routing (Reusing the M2 Rule Engine)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M5-B1 | Server-side match/qualification | Determine in real time which audience the user matches, by experience_key, **reusing the M2 rule engine** for audience matching | [Replicate] | video/row11 |
| M5-B2 | audience → variation assignment | On match, assign to the corresponding variation and return that variation's payload | [Replicate] | video |
| M5-B3 | Variation routing configuration | Default + Variation 1… (A/B/N), Users(% of total) = Auto or manual Distribute | [Replicate] | video |
| **M5-B4** | **Botim own rule-based grouping integration** | The homepage "1-to-1 personalization" card = grouping by Botim's own rules (not MoEngage audience selection), with matching reusing the same M2 engine | **[Replicate]** | row11/73 |
| **M5-B5** | **🤖AI (optional) personalized content / variant smart recommendation** | Smartly recommend the matched content or variation based on user profile / historical behavior, as the incremental mainline (aligned with row6 AI increment) | **[🤖AI][★Enhancement]** | row6 |

### C. Payload Management (KV / Multilingual)
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M5-C1 | KV key-value management | Configuration of key-value pairs: Variable name + type (String…) + value | [Replicate] | video |
| M5-C2 | payload structure (KV/JSON) | Support both KV and JSON content payloads, with client-side rendering | [Replicate] | video |
| **M5-C3** | **Multilingual payload** | Deliver multilingual content (Hindi / Tagalog / Arabic / English) under the same experience (copy source connects to M6 AI Copywriting) | **[★Enhancement]** | video/row40 |
| **M5-C4** | **KV schema convention / config-driven** | Clarify who defines the KV schema (frontend convention vs. config-driven), ensuring a stable client-side rendering contract | **[★Enhancement]** | video |

### D. Client Integration and Self-rendering
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M5-D1 | Client-side rendering | API-type experiences are not rendered within MoEngage; the client SDK consumes the payload and renders the homepage card itself | [Replicate] | video/row11 |
| **M5-D2** | **Client cache / degradation strategy** | On fetch failure or timeout, fall back to cached / default content to safeguard the homepage load experience | **[★Enhancement]** | row43 |
| **M5-D3** | **SDK integration spec** | A unified integration convention for the client SDK to pull/render the homepage campaign slot (coordinated with the client/app team) | **[★Enhancement]** | row40/41 |

### E. Publish-State Gating and Scheduling
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M5-E1 | Publish-state state machine | draft → published → active (time window) → ended lifecycle management | [Replicate] | video |
| M5-E2 | Unpublished gating | Unpublished experiences do not return a payload (draft-state fetch does not match) | [Replicate] | video |
| M5-E3 | Scheduling + time zone | Start/stop time-window scheduling, unified Experience time zone = UAE (Asia/Dubai) | [Replicate] | video |
| M5-E4 | Conversion goals | Configure the conversion goals of the experience, for downstream M4 Funnel Tracking consumption | [Replicate] | video/row15 |

### F. Frontend Three-Step Wizard
| ID | Feature | Capability | Type | Source |
|---|---|---|---|---|
| M5-F1 | Select audience (Audience) | Step ①: select the matched audience (reusing M2 audience selection / Botim's own grouping) | [Replicate] | video/row11 |
| M5-F2 | Content (Content/Variation) | Step ②: configure the variation and the KV / multilingual payload | [Replicate] | video |
| M5-F3 | Schedule (Schedule) | Step ③: set the time window + time zone + conversion goals | [Replicate] | video |

---

## 2. 🤖AI and ★Enhancement Feature Summary (Differentiation vs. MoEngage)

**🤖AI capabilities (incremental mainline, aligned with row6 "incremental value comes from AI")**
- M5-B5 personalized content / variant smart recommendation (optional) ← smartly match content or variation based on profile / behavior

**★ Enhancements this time (better than MoEngage's status quo)**
- M5-A6 fully remove the MoEngage dependency (path ① decoupling) ← **lowest risk, should be validated first** (row73 "can be self-built")
- M5-A7 fetch real-time performance / SLA guarantee (homepage second-level)
- M5-B4 Botim own rule-based grouping integration (path ① only borrows delivery to begin with)
- M5-C3 multilingual payload (Hindi/Tagalog/Arabic/English)
- M5-C4 KV schema convention / config-driven
- M5-D2 client cache / degradation strategy
- M5-D3 client SDK integration spec

**One-line positioning**: M5 = **replicate the MoEngage `Web & App (API)` type experience (A1–A5/B1–B3/C1–C2/D1/E/F baseline) + match/qualification reusing the M2 rule engine (B1) + path ① full decoupling (A6) + multilingual / self-rendering / cache and AI personalization enhancements (C3/D2/B5)**; because path ① only borrows delivery to begin with, it is the **lowest-risk decoupling point that should be validated first**.

---

## 3. Effort Mapping (person-days, consistent with the re-analysis, total ~43)
| Sub-item | Corresponding features | Person-days |
|---|---|---:|
| Equivalent fetch API | A1–A5/A7 | 8 |
| Match/qualification (reusing the M2 rule engine) | B1–B4 | 6 |
| payload management (KV / multilingual) | C1–C4 | 8 |
| Publish state / scheduling | E1–E4 | 5 |
| Client integration | D1–D3 | 6 |
| Frontend three-step wizard | F1–F3 | 10 |
| **Subtotal** | | **~43** (sharing M2 can reduce by ~4 more) |
> Match/qualification reuses the M2 rule engine; after sharing assets with M2 the overall total can be reduced by ~4 person-days; 🤖AI personalized recommendation (B5) is an optional increment, not separately itemized at a large amount.

---

## 4. Dependencies
### 4.1 Technical Dependencies
- **M2 rule engine → prerequisite for M5**: match/qualification (B1/B4) **reuses the same M2 rule engine** for audience matching; without M2, matching cannot be determined.
- **Client SDK integration → prerequisite for M5**: path ① client-side rendering (D1–D3) requires the client/app team to cooperate on rendering + caching.
- **M8 data foundation → prerequisite for M5**: identifiers / ID linkage (A3, with no email → customer_id / phone number as primary key) depends on M8's ID-mapping consumption.
- **M6 AI Copywriting → connects to M5**: the copy source for the multilingual payload (C3) connects to M6.

### 4.2 Organizational / Data Dependencies (estimation prerequisites, currently mostly "to be confirmed")
| Dependency | Provides | Blocked features |
|---|---|---|
| **Growth (Dubai, Radhika)** | Homepage campaign-slot spec, experience_key naming / lifecycle convention, homepage card-slot list | A1/E/F / overall rollout |
| **Client/app team** | SDK rendering capability + cache / degradation scheme, homepage campaign-slot integration | D1–D3 |
| **Data Team (Mr. Ma)** | identifiers / cross-business-line ID linkage (no email → customer_id / phone-number mapping) | A3 / B1 match matching |
| **M6 / Growth** | Multilingual copy source (Hindi/Tagalog/Arabic/English) | C3 |

---

## 5. Blockers & Risks
- **R1 KV schema ownership undecided** → who defines the payload's KV schema (frontend convention vs. config-driven) is unclear, affecting the client-side rendering contract (C4, with the client/app team).
- **R2 Multilingual copy source** → the copy source for the multilingual payload (C3) must connect to M6 AI Copywriting, otherwise there is only a shell with no content.
- **R3 fetch endpoint real-time SLA** → the homepage load needs second-level performance, which determines whether match/qualification must be near-real-time (A7); if near-real-time is required, the batch snapshot reused from M2 for matching is insufficient and must be heavier (row60/61).
- **R4 customer_id-to-business-line ID mapping** → under the no-email premise (row75), the coverage/accuracy of mapping the identifiers' customer_id to each business line's ID determines match reachability (A3, Data Team).
- **R5 Client rendering / cache readiness** → path ① fully depends on client-side rendering + caching (D1/D2); the client/app team's scheduling and capability are the rollout switch.

---

## 6. Phase Rollout Recommendations
- **Priority P1**, but because it is the **"lowest risk"**, we recommend feasibility validation **in Phase 1**: path ① only borrows MoEngage delivery to begin with, with client-side rendering, and can be self-built (row73), making it the cleanest decoupling point.
- **Phase 1 validation goal**: First define the equivalent endpoint `POST /experiences/fetch {identifiers, experience_key} → {payload}`, with match/qualification reusing the M2 rule engine, and **wire up one homepage card slot** end-to-end (select audience → content → schedule → fetch → client-side rendering), proving it can be detached from MoEngage.
- **Phase 2+ (corresponding to re-analysis P-C, 3–4 weeks)**: Complete multi-variation routing (B3), multilingual payload (C3), cache / degradation (D2), and 🤖AI personalized recommendation (B5), rolling out more homepage campaign slots horizontally.
- **Recommended order**: ① First align with Growth on the homepage campaign-slot spec + experience_key lifecycle, and align with the client/app team on the rendering/cache scheme → ② In Phase 1, wire up the equivalent fetch of one card slot to validate decoupling feasibility → ③ In Phase 2, extend to multilingual / multi-variant / AI personalization.

---

## Appendix: Cross-check Supplement Log (against the video baseline)
| # | Supplement item | Source basis | Landing point |
|---|---|---|---|
| 1 | Match/qualification reuses the M2 rule engine (explicitly listed) | Re-analysis line72 "match reuses the M2 rule engine" / line160 | M5-B1/B4 §4.1 |
| 2 | Multilingual payload | Re-analysis line71/76 "payload (KV/multilingual)" | M5-C3 |
| 3 | Client integration (independent subdomain) | Re-analysis line72 "client integration" | M5-D group |
| 4 | Effort mapping (~43, 6 sub-items) | Re-analysis line73 | §3 |
| 5 | Dependencies (technical M2/client/M8/M6 + organizational) | Re-analysis line160 / §5.1-5.2 | §4 |
| 6 | Blockers & risks (KV schema/copy/SLA/ID/rendering) | Re-analysis §6 / line143 real-time-share switch | §5 |
| 7 | Phase rollout (P1 but Phase 1 decoupling validation) | Re-analysis line70 "lowest risk" / §4.2 P-C | §6 |
| 8 | Connecting the multilingual copy source with M6 | Re-analysis line76 M6 multilingual copy | §4.1 / R2 |

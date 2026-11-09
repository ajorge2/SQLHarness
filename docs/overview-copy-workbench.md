# Overview copy workbench

This file is the research and decision layer for the opening paragraph. The webpage should receive only the final slot values—never the research rationale.

## Working template

> Running a business is hard. In **[industry]**, you often have **[specific time window]** to **[data-analysis task]** before **[business consequence]**. You also can’t forget about **[parallel time-sensitive responsibilities]**. Time-sensitive decisions are stressful, but they don’t have to be. If ChatGPT can accomplish **[impressive feat]** in **[average time]**, AI is clearly advanced enough to **[adjacent business-data task]**, right?

## Constraints

- Prefer corporate operating environments over sports or consumer metaphors.
- Fill each slot with an object or compact phrase, not an explanation.
- Use a real time window and a defensible business consequence.
- Keep the parallel-responsibility list concrete and rhythmically short.
- Keep the AI comparison credible, impressive, and adjacent to the database task.
- Research belongs here; only selected slot text belongs on the webpage.
- When a candidate is selected, render the inserted slot text in the normal body color.

## Slot order

1. Industry
2. Specific time window
3. Data-analysis task
4. Business consequence
5. Parallel time-sensitive responsibilities
6. Impressive ChatGPT feat
7. Average time
8. Adjacent business-data task

## Candidate sets

### Accessibility revision

The first researched set was too dependent on specialized operating knowledge. The opening should work even when the reader knows nothing about the example industry.

Additional constraints:

- Use an industry most readers encounter in ordinary life.
- Avoid acronyms, regulatory deadlines, and specialist infrastructure.
- Prefer familiar inputs: sales, inventory, orders, staffing, deliveries, and customers.
- State the consequence in everyday language.
- Let the example demonstrate urgency without becoming the subject of the paragraph.

#### A. Retail — recommended

| Slot | Proposed fill |
| --- | --- |
| 1. Industry | `retail` |
| 2. Specific time window | `the two hours before the evening rush` |
| 3. Data-analysis task | `see which stores are selling out of which products` |
| 4. Business consequence | `customers find empty shelves` |
| 5. Parallel responsibilities | `staffing, deliveries, returns, pricing, and promotions` |
| 6. Impressive ChatGPT feat | `build and test a working product search bar` |
| 7. Average time | `15 minutes` |
| 8. Adjacent business-data task | `answer a simple question about your business data` |

#### B. Shipping and logistics

| Slot | Proposed fill |
| --- | --- |
| 1. Industry | `shipping and logistics` |
| 2. Specific time window | `a few minutes` |
| 3. Data-analysis task | `compare orders, routes, and available drivers` |
| 4. Business consequence | `deliveries fall behind` |
| 5. Parallel responsibilities | `traffic, fuel, warehouses, schedules, and customer updates` |
| 6. Impressive ChatGPT feat | `a complex coding task` |
| 7. Average time | `minutes` |
| 8. Adjacent business-data task | `answer a simple question about your business data` |

#### C. Manufacturing

| Slot | Proposed fill |
| --- | --- |
| 1. Industry | `manufacturing` |
| 2. Specific time window | `a single shift` |
| 3. Data-analysis task | `compare output, defects, and available inventory` |
| 4. Business consequence | `production falls behind` |
| 5. Parallel responsibilities | `equipment, staffing, materials, quality checks, and shipping` |
| 6. Impressive ChatGPT feat | `a complex coding task` |
| 7. Average time | `minutes` |
| 8. Adjacent business-data task | `answer a simple question about your business data` |

#### D. Banking

| Slot | Proposed fill |
| --- | --- |
| 1. Industry | `banking` |
| 2. Specific time window | `the end of the business day` |
| 3. Data-analysis task | `check transactions against available cash` |
| 4. Business consequence | `payments go out late` |
| 5. Parallel responsibilities | `fraud alerts, approvals, customer requests, compliance, and reporting` |
| 6. Impressive ChatGPT feat | `a complex coding task` |
| 7. Average time | `minutes` |
| 8. Adjacent business-data task | `answer a simple question about your business data` |

Retail is now the default recommendation. It is corporate without sounding technical, and its core data—customers, sales, products, stores, and inventory—maps naturally to the SQL example already on the page.

### Research archive: specialized versions

Each cell below is a proposed slot value, not prose explaining the choice. These options remain evidence-backed, but are no longer preferred for the opening.

### A. Bank treasury operations — recommended

| Slot | Proposed fill |
| --- | --- |
| 1. Industry | `bank treasury operations` |
| 2. Specific time window | `the final 15 minutes of the Fedwire day` |
| 3. Data-analysis task | `reconcile payment flows against available liquidity` |
| 4. Business consequence | `critical transfers miss the close` |
| 5. Parallel responsibilities | `cash positions, collateral, margin calls, FX, approvals, and fraud checks` |
| 6. Impressive ChatGPT feat | `a tested code change` |
| 7. Average time | `1–30 minutes` |
| 8. Adjacent business-data task | `answer a plain-English question from a database` |

**Why it survives the evidence check:** Fedwire is explicitly used for large-value, time-critical payments. Its customer-transfer cutoff is 6:45 p.m. ET and the service closes at 7:00 p.m. ET. Banking guidance also treats payment timing, available liquidity, collateral, margin payments, and critical obligations as active intraday concerns. The 15-minute window is therefore literal, not invented.

### B. Utility grid operations

| Slot | Proposed fill |
| --- | --- |
| 1. Industry | `utility grid operations` |
| 2. Specific time window | `six-second telemetry cycles` |
| 3. Data-analysis task | `reconcile live demand against available supply` |
| 4. Business consequence | `the system sheds load` |
| 5. Parallel responsibilities | `reserves, outages, weather, transmission limits, and market schedules` |
| 6. Impressive ChatGPT feat | `a tested code change` |
| 7. Average time | `1–30 minutes` |
| 8. Adjacent business-data task | `answer a plain-English question from a database` |

**Why it survives the evidence check:** NERC guidance says the relevant real-time control data is calculated and updated at least every six seconds. NERC also identifies inaccurate real-time forecasting as a path to energy shortfalls and potential load shedding. The consequence is severe but directly supported.

### C. Airline network operations

| Slot | Proposed fill |
| --- | --- |
| 1. Industry | `airline network operations` |
| 2. Specific time window | `five minutes on either side of a departure slot` |
| 3. Data-analysis task | `reconcile live flight data against the network plan` |
| 4. Business consequence | `an aircraft loses its slot` |
| 5. Parallel responsibilities | `weather, crews, maintenance, gates, fuel, and passenger connections` |
| 6. Impressive ChatGPT feat | `a tested code change` |
| 7. Average time | `1–30 minutes` |
| 8. Adjacent business-data task | `answer a plain-English question from a database` |

**Why it survives the evidence check:** FAA guidance expects an aircraft to depart no earlier than five minutes before and no later than five minutes after its assigned EDCT. A late departure can require a new EDCT, add delay, and cost another aircraft a slot opportunity. This is the most legible operational metaphor, though slightly less corporate in tone than treasury.

### D. Public-company cybersecurity

| Slot | Proposed fill |
| --- | --- |
| 1. Industry | `public-company cybersecurity` |
| 2. Specific time window | `four business days` |
| 3. Data-analysis task | `quantify an incident’s scope and business impact` |
| 4. Business consequence | `the SEC filing deadline passes` |
| 5. Parallel responsibilities | `containment, forensics, recovery, legal review, customer notices, and board briefings` |
| 6. Impressive ChatGPT feat | `a tested code change` |
| 7. Average time | `1–30 minutes` |
| 8. Adjacent business-data task | `answer a plain-English question from a database` |

**Why it survives the evidence check:** Once a registrant determines that a cybersecurity incident is material, Item 1.05 requires the Form 8-K within four business days. The filing must cover the incident’s nature, scope, timing, and material impact. This option is unmistakably corporate, but its clock is less immediate than the first three.

## Comparison

| Candidate | Corporate tone | Clock precision | Data fit | Immediate stakes | Copy naturalness |
| --- | --- | --- | --- | --- | --- |
| Bank treasury | Excellent | Excellent | Excellent | Excellent | Excellent |
| Utility grid | Strong | Excellent | Excellent | Excellent | Strong |
| Airline network | Strong | Excellent | Strong | Excellent | Excellent |
| Public-company cybersecurity | Excellent | Strong | Strong | Strong | Strong |

The bank-treasury set is the default recommendation. It most cleanly makes the paragraph’s point: a complicated business system generates a narrow decision window, and the decisive input is structured operational data.

## Selected set

Retail accessibility revision. Applied to `docs/index.html` in the normal body color. The opening now uses a two-hour pre-rush window and depicts the exact question the reader should picture: which stores are selling out of which products. The AI comparison is similarly concrete: building and testing a working product search bar in 15 minutes.

## Sources

- Federal Reserve, [Fedwire Funds Services](https://www.federalreserve.gov/paymentsystems/fedfunds_about.htm): large-value, time-critical payments; 6:45 p.m. third-party cutoff; 7:00 p.m. close.
- Bank for International Settlements, [Liquidity risk management and supervision](https://www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/lqy/10): intraday liquidity, time-specific obligations, collateral, margin payments, funding shortfalls, and critical-payment risk.
- NERC, [Integrating Reporting ACE with NERC Reliability Standards](https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/rs/integrating_reporting_ace_with_nerc_reliability_standards.pdf): real-time control data calculated and updated at least every six seconds.
- NERC, [Characteristics and Risks of Emerging Large Loads](https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/3_doc_white-paper-characteristics-and-risks-of-emerging-large-loads.pdf): inaccurate real-time forecasting can create energy shortfalls and potential load shedding.
- FAA, [Expect Departure Clearance Times](https://www.aspm.faa.gov/aspmhelp/index/Expect_Departure_Clearance_Times_%28EDCT%29.html): five-minute EDCT expectation and consequences of a missed slot.
- SEC, [Cybersecurity Risk Management, Strategy, Governance, and Incident Disclosure](https://www.sec.gov/files/rules/final/2023/33-11216.pdf): four-business-day Form 8-K deadline after a materiality determination.
- OpenAI, [Introducing Codex](https://openai.com/index/introducing-codex/): coding tasks, test execution, and typical 1–30 minute completion time for the cited launch configuration.

## Deferred candidate

`semiconductor fab operations` has excellent data semantics—real-time process data, in-line metrology, routing, yield, quality, and production optimization—but the reviewed sources did not establish one universal short decision window. Keep the industry in reserve rather than inventing a clock for it.

- NIST, [Innovations in advanced processes and systems for semiconductor manufacturing](https://www.nist.gov/publications/innovations-advanced-processes-and-systems-semiconductor-manufacturing)
- NIST, [Semiconductor Manufacturing Profile](https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.8546.ipd.pdf)

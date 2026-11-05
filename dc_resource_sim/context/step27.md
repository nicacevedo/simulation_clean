# Step 27 — What do the Prineville water meters actually measure?

## Goal

**One question:** Which monthly water-supply observations from the existing City of Prineville records can be defended as reported data-center meter volumes, and which quantities remain unobserved?

This is a **measurement-boundary audit**, not W2-Air calibration. Steps 20–26 and EDA Figures 01–06 already establish conditional evaporation and feedwater calculations. Their excellent internal agreement (C1 versus W2-Air) does **not** establish measured site-water accuracy. The ESIF weather replay concerns a different, hypothetical cooling architecture.

## Scope: one year, one script, no new modeling

- Analyze **2023 only**. Do not download data, rerun the EDA, or modify existing experiment/model code.
- Existing sources: `FB Meters and Consumption(1).csv` (or its text equivalent), `Facebook Bulk Water.xlsx`, `Meter Sets, Swaps.xlsx`, and `City-of-Prinville-Data-Description.txt`. Resolve the actual source paths in the research repository; do not assume they match the attachment paths.
- Create `dc_resource_sim/src/data/prineville_water_2023.py`.
- Save exactly two source-faithful outputs under `dc_resource_sim/runs/`:
  1. `prineville_meter_monthly_2023.csv` — one row per named meter per reported month, including zero readings.
  2. `prineville_bulk_billed_2023.csv` — bulk/hydrant records indexed by **bill date**, not presumed consumption month.
- Print a short QC and interpretation summary. **No plots, fitted WUE, annualization, facility optimization, or groundwater interpretation.**

## Physical and reporting boundaries

| Source field | What may be stated | What must not be inferred |
|---|---|---|
| `WATER - COMM ...`, `ADD'L WATER ...` | City-reported, billed volume associated with a named meter/customer | Complete facility withdrawal, independent physical intake for every rate-code row, or evaporative consumption |
| `WELL METER FOR SEW` | A well-related meter used for sewer billing, as labeled | Additional municipal delivered water, aquifer withdrawal, or sewer return without confirmation |
| `SWR METER` | Sewer-related meter readings, as labeled | An independent input-water supply |
| Bulk/hydrant water | Separate reported volume at recorded billing date | Exactly that calendar month's consumption |
| `Facebook Trailer City` / `Facebook Warehouse` | Separately named customers | Automatically part of the `Facebook Data Center` facility boundary |

The city's letter states **1 billed unit = 100 ft³ = 2,831.6846592 L** (approximately 748 US gal). Source uses the term *consumption* for billed **meter usage**; that does not establish hydrologic consumption. Water/sewer data are reported in the *month consumed* after late-month readings, but bulk is reported under **billing date**, generally the 15th. Preserve these conventions; do not shift months by assumption.

## Minimal implementation sequence

1. **Parse the 2023 meter block only.** The source has multiple annual blocks and irregular multiline headers/quoting. Preserve raw customer, location, meter ID as **string** (e.g. `0001`), rate code, each reported usage and reading-days field, and its stated annual total. Do not parse all years as one homogeneous rectangular CSV without block checks.
2. **Write monthly long form.** Suggested fields: `year, month, customer, service_location, meter_id, rate_code, category, reported_units, volume_l, reading_days, reported_annual_units, qc_note`. Categorize supply-related water, well-for-sewer, sewer, and other/unknown. Preserve all source labels; never overwrite suspicious readings.
3. **Read 2023 bulk records** with `bill_date, reported_units, volume_l, number_of_days`; preserve duplicate dates if present. Keep this as its own output.
4. **Read only 2023 swap events**, and print dates plus old/new IDs as a QC note. Do not automatically join meter identities across swaps or infer duplicate volumes.
5. **Print separate source summaries** for `Facebook Data Center` water-category units, well-for-sewer units, sewer units, the Trailer City/Warehouse groups, and bulk records. Print at least monthly reported data-center water units plus annual source totals. Do **not** make a combined `total_consumption` or `groundwater_withdrawal` field.

## Source-based checks (not physics calibration)

These targets come from the supplied 2023 files / earlier verified source inventory; if different, inspect the parser rather than adjusting numbers to match:

- 28 named meters in 2023: **24** `Facebook Data Center`, **3** `Facebook Trailer City`, **1** `Facebook Warehouse`; hence **336** meter-month records if preserving 12 months per meter.
- Data-center water rate codes (`WATER - COMM`, `ADD'L WATER`) have a **reported annual-row-total sum of 58,230 units**. This is a reporting subtotal, **not yet a proven non-overlapping site supply volume**.
- Independently tagged data-center `WELL METER FOR SEW`: **12,457 units**; `SWR METER`: **6,587 units**. Never add these three numbers as independent withdrawals.
- **12** bulk-water billing records dated 2023; keep bill dates.
- `Facebook Warehouse` meter `1562600912` shows **2 units in January**, **0 reading days**, but **0 reported annual units**. Explicitly flag, preserve all raw values, and do not 'repair' the discrepancy.
- The meter-swap log includes events on **2023-06-28**. Report relevant old/new meter IDs, not an inferred physical meter topology.
- Compare sums of the 12 reported months with the listed annual total **for each meter**; flag discrepancies and unexpected rate codes/zero-reading-day positive volumes.

## Stopping rule

Close Step 27 when both exports reproduce the source data, the expected counts and subtotals are checked, anomalies are reported rather than silently changed, and a 4–6 sentence conclusion distinguishes:

1. *City-reported billed water-meter volumes*.
2. *Sewer/well-for-sewer-related meter categories*.
3. *Separately dated bulk/hydrant water*.
4. *Unidentified* true facility intake/withdrawal, evaporation, discharge fate, and source-water origin.

A successful result **does not** show whether W0, C1, or W2-Air predicts measured water. Nothing in this step supplies site-matched IT load, operating controls, equipment recovery, or measured process evaporation.

## Next small step (only after closing 27)

Step 28 can check **one defensible comparison boundary**, e.g. whether Meta's reported annual Prineville site withdrawal and the city's water-meter subtotal cover the same facilities, time interval, and supply sources. If they cannot be reconciled, report the gap as unresolved; do not force an accounting identity or fit W2-Air to it. In parallel, location-matched Prineville weather remains a future *scenario* input, not validation.

---

Context:

## Step 27 — Validate the water measurement boundary

Step 26 and the water EDA (Figures 01–06) are complete. I reviewed the attached EDA results and agree with the conclusion: we should not increase model complexity yet.

The next most valuable step is to establish what our real water measurements represent and whether they can eventually be compared with the physical models.

I prepared the complete Step 27 specification:

Download Step 27 — Prineville Water Measurement Audit (.md)

Save it as `dc_resource_sim/context/step27.md`.

### 1. What we have learned

| Model               | Main finding                                                           | Status                        |
| ------------------- | ---------------------------------------------------------------------- | ----------------------------- |
| W0                  | Constant direct-water intensity; independent of weather                | Accounting baseline           |
| C1                  | Simple temperature-excess model closely reproduces W2-Air              | Validated against simulations |
| W2-Air              | Predicts evaporation and cooling feasibility from physical assumptions | Physically tested             |
| W2-Tower            | Predicts evaporation and makeup from wet heat rejection                | Physically tested             |
| Real-weather replay | C1 and W2-Air agree closely under observed ESIF conditions             | Conditional simulation        |

The particularly useful result is:

\\[ \boxed{ \dot V^{evap}\approx 0.0979\frac{15}{\Delta T\_{server}} P^{IT}(T\_{db}-25)\_+ } \\]

This is a strong reduced representation of W2-Air under our chosen assumptions, provided cooling feasibility is checked separately.

We do not need another regression or machine-learning model to approximate this simulator.

However, C1's very low error does not establish actual predictive accuracy: both C1 and W2-Air ultimately depend on the same physical assumptions.

### 2. The question for Step 27

Which quantities in the existing Prineville records are actual measurements, and which correspond to water consumption, intake, or discharge?

This is different from Step 21's theoretical boundary audit. Step 27 examines the actual municipal records.

The smallest useful scope is one year: 2023.

### 3. What to implement

Create only:

`dc_resource_sim/src/data/prineville_water_2023.py`

Use the existing municipal meter records, bulk-water records, meter-swap log, and the city's data description.

Produce two CSVs:

- `prineville_meter_monthly_2023.csv`
- `prineville_bulk_billed_2023.csv`

Preserve customer, meter identifier, reporting period, units, rate code, and water category.

The city reports volumes in units of 100 cubic feet. Its ordinary meter records are assigned to consumption months, while bulk records use billing dates. This difference must remain visible.

### 4. What to confirm

The supplied data give us several useful checks:

| 2023 observation                           | Expected            |
| ------------------------------------------ | ------------------- |
| Named meter records                        | 28                  |
| Data-center meter records                  | 24                  |
| Data-center water-category annual subtotal | 58,230 billed units |
| Well-meter-for-sewer category              | 12,457 units        |
| Sewer category                             | 6,587 units         |
| Bulk-water billing records                 | 12                  |

Do not add these categories into a single facility-consumption estimate.

Also flag meter replacements, inconsistent annual totals, and unusual readings without silently correcting them.

These checks are source-accounting tests, not water-model calibration.

### 5. What we should learn

The essential distinction is:

| Quantity                                              | Can we establish it from these records?       |
| ----------------------------------------------------- | --------------------------------------------- |
| Reported monthly municipal meter volumes              | Yes                                           |
| Reported bulk-water billing volumes                   | Yes                                           |
| Which meters belong to the data-center customer group | Partially, using customer and location labels |
| Actual hourly evaporative water use                   | No                                            |
| Complete facility withdrawal                          | Not yet                                       |
| Discharge and consumptive loss                        | Not yet                                       |
| Groundwater extraction attributable to the facility   | No                                            |

The data may eventually support comparisons with W2-Air, but only after resolving the physical measurement boundary and obtaining defensible equipment and load assumptions.

### 6. Stopping rule

Step 27 is complete when the two CSV outputs are reproducible, the source totals and meter categories are checked, and the unresolved measurement boundaries are explicitly documented.

Do not fit C1/W2-Air to monthly water bills, infer hourly water demand, or introduce additional physical equations.

## Next improvement

After Step 27, I recommend one narrow follow-up: compare the Prineville municipal records with Meta's reported annual facility withdrawals, checking which sites, periods, and sources are covered by each.

That would be our first meaningful measured-versus-reported water-accounting comparison, before attempting predictive validation.

Final recommendation: Keep the EDA results as our current physical-model baseline. Complete Step 27 as one small, empirical water-data audit. The most valuable new information now is not another equation, but identifying which real water quantity our models might eventually predict.
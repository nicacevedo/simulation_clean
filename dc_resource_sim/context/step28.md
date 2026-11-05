# Step 28 — Prineville 2023: city-meter categories versus Meta's annual withdrawal

## Goal
Test one narrow **annual accounting hypothesis**: do the 2023 data-center municipal water-category volumes **plus separately billed bulk/hydrant water** approximately match Meta's reported 2023 Prineville water withdrawal?

This is a **reporting-boundary check**, not validation of W0/C1/W2, actual evaporative consumption, or groundwater pumping.

## Inputs (no new data collection)

1. Reuse the two **existing Step 27 outputs**, without reparsing the raw city files:
   - `dc_resource_sim/runs/prineville_meter_monthly_2023.csv`
   - `dc_resource_sim/runs/prineville_bulk_billed_2023.csv`
2. External annual comparator: **Meta, Prineville (OR), 2023 water withdrawal = 180 megaliters**, as shown in Meta's 2024 Environmental Data Index (also repeated in its 2025 index): https://sustainability.atmeta.com/asset/2024-esg-data-index/
3. Unit definition from the City of Prineville's data description: **1 billed unit = 100 cubic feet**. Conversion: `100 * 0.3048**3 * 1000 = 2831.6846592 L`.

## Only computation

Aggregate, without changing source values:

- `A`: 2023 monthly `WATER - COMM` and `ADD'L WATER` records for customer exactly `Facebook Data Center` (**58,230 units expected**). Preserve original rate-code text and the meter identifiers in the input; do not add well-for-sewer or sewer categories.
- `B`: 2023 **bill-dated** bulk-water records (**12 records; 5,252.81 units expected**). Do **not** reassign bulk values to consumption months.
- `C`: Meta's **reported annual withdrawal**, 180 ML, with the precision shown in its published index.

Print the three comparisons `A`, `B`, `A+B`, and both residuals `C-A` and `C-(A+B)` in ML and as a percent of `C`.

Expected checks (from Step 27's verified totals):

| Quantity | Value |
|---|---:|
| Ordinary data-center water-category volume `A` | 164.888998 ML |
| Bulk/hydrant billing volume `B` | 14.874301 ML |
| Provisional combined volume `A+B` | 179.763299 ML |
| Meta reported withdrawal `C` | 180 ML |
| `C-A` | 15.111002 ML (8.395%) |
| `C-(A+B)` | **0.236701 ML (0.1315%)** |

Report Meta's 180 ML as a **rounded published figure**; do not imply the unreported value is exactly 180.000000 ML or that the residual is an independently measured error. The numerical match is within one published 1-ML reporting increment.

## Essential checks (no broader work)

1. Confirm the parser obtains `A` and `B` from the **Step 27 CSV rows**, not just from hard-coded totals. Assert the same category selection and record counts.
2. Confirm that bulk records are categorized by **bill date**, unlike ordinary meters which the city assigns to a **consumption month**. This makes `A+B` a provisional annual bridge, not a time-aligned consumption sum.
3. Keep `WELL METER FOR SEW`, `SWR METER`, Trailer City, Warehouse, and any ambiguously overlapping meters **out** of the comparison; disclose unresolved primary/submeter overlap within `A`.
4. Record two unresolved boundaries: (a) Is bulk water already included in any ordinary meter or Meta's annual scope? (b) Does any bulk water represent **construction**, which Meta explicitly excludes from its operational water-withdrawal reporting? Meta reports additional construction withdrawal separately on a company-wide basis; this does not identify Prineville's construction volume.
5. Note that Meta reports withdrawal using utility/meter data where available. The similarity may reflect **shared underlying measurements**, not two fully independent validations.

## Implementation

Create **one small script**:

`dc_resource_sim/src/data/prineville_meta_bridge_2023.py`

It should read the two Step 27 CSVs and print the compact expected table, category/bill-date checks, and the unresolved boundary notes. It may write **one** summary CSV (`dc_resource_sim/runs/prineville_meta_bridge_2023.csv`) if convenient. No plots, interpolations, model fitting, extra data downloads, or changes to prior scripts.

If the Step 27 CSV headers differ from assumptions, inspect actual headers and adapt the selector explicitly; never silently select by column position. Fail loudly if 2023 counts or category totals differ.

## Stopping rule

Close Step 28 when the five checks pass and the comparison is labeled:

> **Near-reconciliation of annual reported water quantities, conditional on nonoverlapping categories and compatible operational/reporting boundaries—not validation of water consumption or a cooling model.**

Next: only if further investigation is justified, request/inspect the **bulk-hydrant use purpose**, meter topology, and Meta's facility-level operational boundary. Do not fit W0/C1/W2 to the annual number.


---

Context:

## Step 28 — Compare Prineville's city water records with Meta's reported withdrawals

Step 27 is complete. The 2023 meter records have been parsed reproducibly, and the different billing categories remain separate.

The next step should be a single annual accounting comparison, not another physical water model or optimization experiment.

### 1. A particularly valuable finding

Meta reports 180 million liters (180 ML) of water withdrawal at its Prineville facility in 2023.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://sustainability.atmeta.com\&sz=32)

sustainability.atmeta.com



Using the Step 27 totals:

| 2023 quantity                              | Volume           |
| ------------------------------------------ | ---------------- |
| Data-center municipal water categories     | 164.889 ML       |
| Separately billed bulk/hydrant water       | 14.874 ML        |
| Municipal categories + bulk, provisionally | 179.763 ML       |
| Meta reported facility withdrawal          | 180 ML           |
| Difference                                 | 0.237 ML (0.13%) |

Conversion: one city billing unit = 100 cubic feet = 2,831.685 liters.

The near-agreement is striking and worth investigating. It suggests the bulk-water records may explain almost all the difference between the ordinary city-water subtotal and Meta's reported withdrawal.

But this is not yet a verified reconciliation. We have not established whether bulk deliveries are additional to the ordinary meters, belong to the same reporting year, or fall within Meta's operational reporting boundary.

There is another important nuance: Meta's reporting methodology describes its WUE as water withdrawal divided by IT electricity, whereas our illustrative W0 coefficient has been labeled a direct-consumption proxy. These should not be used interchangeably.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://financialfilings.com\&sz=32)

FinancialFilings



### 2. Recommended implementation

I've prepared the complete Step 28 specification:

Download Step 28 — Prineville Annual Water Comparison (.md)

Save it as `dc_resource_sim/context/step28.md`.

Create only one script:

`dc_resource_sim/src/data/prineville_meta_bridge_2023.py`

Reuse the two CSVs from Step 27. No new data extraction, model fitting, physical equations, or plots.

The script should calculate the two annual comparisons and record three unresolved issues:

1. Meter overlap: Are bulk-water volumes additional to the ordinary water meters? Are any ordinary meters submeters of others?
2. Reporting periods: The city's ordinary meters represent consumption months, whereas bulk records represent billing dates.
3. Reporting boundary: Does Meta include the same bulk-water uses? In particular, Meta excludes construction water from its reported operational withdrawal totals.&#x20;

   [image](https://www.google.com/s2/favicons?domain=https://sustainability.fb.com\&sz=32)

   sustainability.fb.com



Meta also reports using utility or meter information for its withdrawal accounting, so the numerical agreement may not represent independent validation.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://financialfilings.com\&sz=32)

FinancialFilings



### 3. Stopping rule

Close Step 28 when the annual arithmetic reproduces correctly and those three limitations are recorded.

The defensible conclusion would be:

> The 2023 Prineville city-water categories, when provisionally combined with bulk-water billing, closely match Meta's published annual withdrawal. This suggests a potentially consistent accounting boundary, but it does not establish that all included volumes are nonoverlapping or belong to the same reporting scope.

Do not use the resulting 179.76 ML to calibrate C1, W0, or W2-Air yet.

### 4. What comes next?

Once the annual comparison is complete, the next genuinely useful question is whether the ordinary meters and bulk records represent distinct physical supplies and operating purposes.

Resolving that would bring us closer to comparing actual facility intake with simulated cooling-water demand.

My recommendation: Step 28 should be limited to this one annual comparison. The near-match is one of the most promising empirical findings in our water-data work so far, but its value depends on verifying the measurement boundaries rather than assuming the agreement proves the model.
"""
Step 27: 2023 City of Prineville water-record measurement-boundary audit.
Source files are only read, never modified. No modeling, fitting or annualization.

Conventions kept from the city's data description:
- 1 billed unit = 100 ft^3 = 2,831.6846592 L.
- Meter/sewer usage is listed in the month consumed; bulk (hydrant) water is listed by
  bill date (generally the 15th). Months are never shifted here.
- "Consumption"/"usage" means billed meter usage, not hydrologic consumption.

Run from the repository root:
    python dc_resource_sim/src/data/prineville_water_2023.py
"""

import csv

import pandas as pd

SRC = ("/home/nacevedo/RA/data-center-externalities-modeling/Meta_Prineville_Oregon_v3/"
       "data/raw/city_prineville_public_records_2026/")
METERS = SRC + "FB Meters and Consumption(1).csv"
BULK = SRC + "Facebook Bulk Water.xlsx"
SWAPS = SRC + "Meter Sets, Swaps.xlsx"
OUT_METER = "dc_resource_sim/runs/prineville_meter_monthly_2023.csv"
OUT_BULK = "dc_resource_sim/runs/prineville_bulk_billed_2023.csv"

L_PER_UNIT = 2831.6846592
YEAR = 2023
DC = "Facebook Data Center"


def category(rate_code):
    if rate_code.startswith(("WATER - COMM", "ADD'L WATER")):
        return "water"
    if rate_code == "WELL METER FOR SEW":
        return "well_for_sewer"
    if rate_code == "SWR METER":
        return "sewer"
    return "other_unknown"


# 1. Meter block for 2023 only. The file stacks annual blocks, each starting with a
# "Name" header whose first month cell names the year; csv handles the multiline quoting.
with open(METERS, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.reader(f, delimiter=";"))
starts = [i for i, r in enumerate(rows) if r and r[0] == "Name"]
block = [i for i in starts if rows[i][3].split()[1] == str(YEAR)]
assert len(block) == 1, block
header = rows[block[0]]
assert len(header) == 29 and header[27].startswith(f"{YEAR} Total") and header[28] == "Rate_Code Description", header
meter_rows = []
for r in rows[block[0] + 1:]:
    if not r or not r[0]:  # blank separator row ends the block
        break
    meter_rows.append(r)

records = []
for r in meter_rows:
    customer, location, meter_id, rate_code = r[0], r[1], r[2], r[28]
    usage = [int(r[3 + 2 * m]) for m in range(12)]
    days = [int(r[4 + 2 * m]) for m in range(12)]
    annual = int(r[27])
    row_note = "" if sum(usage) == annual else f"12-month sum {sum(usage)} != listed annual {annual}"
    for m in range(12):
        notes = [row_note] if row_note else []
        if usage[m] > 0 and days[m] == 0:
            notes.append("positive usage with 0 reading days")
        if category(rate_code) == "other_unknown":
            notes.append("unexpected rate code")
        records.append(dict(year=YEAR, month=m + 1, customer=customer, service_location=location,
                            meter_id=meter_id, rate_code=rate_code, category=category(rate_code),
                            reported_units=usage[m], volume_l=usage[m] * L_PER_UNIT,
                            reading_days=days[m], reported_annual_units=annual,
                            qc_note="; ".join(notes)))
meters = pd.DataFrame(records)
meters.to_csv(OUT_METER, index=False)

# 2. Bulk/hydrant records by bill date; duplicates kept.
bulk = pd.read_excel(BULK)
bulk = bulk[bulk["Bill Date"].dt.year == YEAR].sort_values("Bill Date", kind="stable")
bulk = pd.DataFrame(dict(bill_date=bulk["Bill Date"].dt.date, rate_code=bulk["Rate Code"],
                         reported_units=bulk["Consumption"], volume_l=bulk["Consumption"] * L_PER_UNIT,
                         number_of_days=bulk["Number of Days"]))
bulk.to_csv(OUT_BULK, index=False)

# 3. Swap events (QC only; IDs read as strings, no identity joins).
swaps = pd.read_excel(SWAPS, dtype={"Old Meter": str, "New Meter": str})
swaps = swaps[pd.to_datetime(swaps["Date"]).dt.year == YEAR]

# ---- QC and source summaries ----
per_meter = meters.drop_duplicates(["customer", "meter_id", "rate_code"])
print(f"Meter rows {YEAR}: {len(per_meter)} named meters, {len(meters)} meter-months")
print(per_meter.customer.value_counts().to_string())
dc_meters = per_meter[per_meter.customer == DC]
print("\nData-center listed annual units by category (separate reporting subtotals, not additive):")
print(dc_meters.groupby("category").reported_annual_units.sum().to_string())
print("Other customers' listed annual units by category:")
print(per_meter[per_meter.customer != DC].groupby(["customer", "category"]).reported_annual_units.sum().to_string())

dc_water = meters[(meters.customer == DC) & (meters.category == "water")]
print("\nMonthly reported data-center water-category units (consumption month as listed):")
print(dc_water.groupby("month").reported_units.sum().to_string())

print(f"\nBulk/hydrant records dated {YEAR}: {len(bulk)}; units at bill date:")
print(bulk[["bill_date", "reported_units", "number_of_days"]].to_string(index=False))
print(f"Sum of {YEAR}-dated bulk units: {bulk.reported_units.sum():.2f}")

print("\nQC flags (raw values preserved):")
flagged = meters[meters.qc_note != ""]
print(flagged[["customer", "meter_id", "rate_code", "month", "reported_units", "reading_days",
               "reported_annual_units", "qc_note"]].to_string(index=False))
dup_ids = per_meter[per_meter.meter_id.duplicated(keep=False)]
print(f"Meter IDs repeated across rows: {sorted(dup_ids.meter_id) or 'none'}")

print(f"\nMeter swaps dated {YEAR} (as logged; not joined to meter rows):")
print(swaps.to_string(index=False))
ids = set(per_meter.meter_id)
for _, s in swaps.iterrows():
    print(f"  old {s['Old Meter']} in {YEAR} rows: {s['Old Meter'] in ids}; "
          f"new {s['New Meter']} in {YEAR} rows: {s['New Meter'] in ids}")

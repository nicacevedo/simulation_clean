"""
Step 28: annual reporting-boundary check, Prineville 2023.
Do city data-center water categories (A) plus bill-dated bulk water (B) match
Meta's reported 2023 Prineville withdrawal (C = 180 ML, rounded published figure)?

Reads only the two Step 27 outputs. No fitting, interpolation or month shifting.
Run from the repository root:
    python dc_resource_sim/src/data/prineville_meta_bridge_2023.py
"""

import pandas as pd

METER = "dc_resource_sim/runs/prineville_meter_monthly_2023.csv"
BULK = "dc_resource_sim/runs/prineville_bulk_billed_2023.csv"
OUT = "dc_resource_sim/runs/prineville_meta_bridge_2023.csv"

L_PER_UNIT = 100 * 0.3048**3 * 1000  # 1 billed unit = 100 ft^3 (city data description)
DC = "Facebook Data Center"
WATER_PREFIXES = ("WATER - COMM", "ADD'L WATER")
# Meta 2024 Environmental Data Index, Prineville 2023 withdrawal, published in whole ML.
C_ML = 180.0

meter = pd.read_csv(METER)
bulk = pd.read_csv(BULK)

# A: select by explicit column names; excludes sewer, well-for-sewer, Trailer City, Warehouse.
a_rows = meter[(meter["year"] == 2023) & (meter["customer"] == DC)
               & meter["rate_code"].str.startswith(WATER_PREFIXES)]
excluded = meter[~meter.index.isin(a_rows.index)]
assert set(a_rows["category"]) == {"water"}, set(a_rows["category"])
assert len(a_rows) == 240 and a_rows["meter_id"].nunique() == 20, (len(a_rows), a_rows["meter_id"].nunique())
assert a_rows["reported_units"].sum() == 58230, a_rows["reported_units"].sum()

# B: bulk records are keyed by bill date (not consumption month) and are not reassigned.
bill_date = pd.to_datetime(bulk["bill_date"])
b_rows = bulk[(bill_date.dt.year == 2023) & (bulk["rate_code"] == "BULK WATER")]
assert len(b_rows) == 12, len(b_rows)
assert round(b_rows["reported_units"].sum(), 2) == 5252.81, b_rows["reported_units"].sum()

a_ml = a_rows["reported_units"].sum() * L_PER_UNIT / 1e6
b_ml = b_rows["reported_units"].sum() * L_PER_UNIT / 1e6
summary = pd.DataFrame([
    ("A: DC water categories (consumption month)", a_ml),
    ("B: bulk/hydrant water (bill date)", b_ml),
    ("A+B: provisional annual bridge", a_ml + b_ml),
    ("C: Meta reported withdrawal (rounded, 1 ML)", C_ML),
    ("C-A", C_ML - a_ml),
    ("C-(A+B)", C_ML - a_ml - b_ml),
], columns=["quantity", "volume_ml"])
summary["pct_of_C"] = 100 * summary["volume_ml"] / C_ML

assert abs(a_ml - 164.888998) < 1e-6 and abs(b_ml - 14.874301) < 1e-6, (a_ml, b_ml)
summary.to_csv(OUT, index=False)

print("Step 28 — Prineville 2023: city-meter categories vs Meta annual withdrawal")
print(summary.to_string(index=False, float_format=lambda x: f"{x:.6f}"))

print("\nChecks")
print(f"- A from {len(a_rows)} Step 27 rows, {a_rows['meter_id'].nunique()} meter IDs, "
      f"{int(a_rows['reported_units'].sum())} units; rate codes:")
print(a_rows.groupby("rate_code")["reported_units"].agg(["size", "sum"]).to_string())
print(f"- Excluded from A ({int(excluded['reported_units'].sum())} units):")
print(excluded.groupby(["customer", "rate_code"])["reported_units"].sum().to_string())
print(f"- B from {len(b_rows)} bulk rows by bill date "
      f"{b_rows['bill_date'].min()}..{b_rows['bill_date'].max()}, "
      f"{b_rows['reported_units'].sum():.2f} units. Ordinary meters use consumption month, "
      "so A+B is a provisional annual bridge, not a time-aligned sum.")

print("""
Caveats
- C = 180 ML is a rounded published figure; C-(A+B) lies within one 1-ML reporting
  increment and is not an independently measured error.
- Primary/submeter overlap among the 20 meters in A is unresolved (Step 27 swap log,
  2023-06-28, not joined); A is a reporting subtotal, not a proven non-overlapping supply.
- Unresolved (a): whether bulk water is already counted in an ordinary meter or in Meta's
  annual scope.
- Unresolved (b): whether any bulk water is construction use, which Meta excludes from
  operational withdrawal (Meta reports construction water only company-wide).
- Meta uses utility/meter data where available, so the agreement may reflect shared
  underlying measurements rather than two independent validations.

Conclusion: Near-reconciliation of annual reported water quantities, conditional on
nonoverlapping categories and compatible operational/reporting boundaries—not validation
of water consumption or a cooling model. Do not fit W0/C1/W2 to this number.""")
print(f"\nWrote {OUT}")

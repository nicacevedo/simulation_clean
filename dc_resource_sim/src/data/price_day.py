"""
Extract one complete 24-hour UTC day of real hourly electricity prices for s2_real_prices.py.
The frozen source file is only read, never modified.

Source: frozen signals_2023_v1, site S1b (Springfield, IL). price_usd_mwh is the MISO
ILLINOIS.HUB day-ahead ex-post LMP in $/MWh; it is converted here to $/kWh. It is an
illustrative marginal price signal, not an ESIF electricity tariff.
grid_water_l_mwh is a modeled hourly average attributed water CONSUMPTION factor for the MISO
balancing authority (fuel mix x Macknick et al. 2011); it is not a measured marginal response.

Run from the repository root:
    python dc_resource_sim/src/data/price_day.py [YYYY-MM-DD] [OUT_CSV]
"""

import sys

import pandas as pd

PARQUET = ("/home/nacevedo/m0m1_overnight/06_runs/20261016T0527Z_m0m1/inputs/"
           "signals_2023_v1/site_S1b_springfield_2023.parquet")
DAY = sys.argv[1] if len(sys.argv) > 1 else "2023-07-01"
OUT = sys.argv[2] if len(sys.argv) > 2 else "dc_resource_sim/runs/price_24h.csv"

df = pd.read_parquet(PARQUET, columns=["t_utc", "price_usd_mwh", "price_qc_flag",
                                      "grid_water_l_mwh", "grid_water_basis", "ba"])
start = pd.Timestamp(DAY, tz="UTC")
df = df[(df.t_utc >= start) & (df.t_utc < start + pd.Timedelta(days=1))].sort_values("t_utc")

# Reject incomplete, duplicated, or flagged days; never fill
expected = pd.date_range(start, periods=24, freq="h")
assert len(df) == 24 and (df.t_utc.to_numpy() == expected.to_numpy()).all(), f"Incomplete day {DAY}"
assert df.price_usd_mwh.notna().all(), "Missing prices"
assert (df.price_qc_flag == "ok").all(), "Flagged prices"
assert (df.ba == "MISO").all(), "Unexpected grid-water coverage"
assert df.grid_water_basis.str.contains("CONSUMPTION").all(), "Grid water is not consumption-based"
assert df.grid_water_basis.str.contains("not marginal").all(), "Grid water basis changed"
assert (df.grid_water_l_mwh > 0).all(), "Missing or invalid grid water"

out = pd.DataFrame({"timestamp_utc": df.t_utc.dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "price_usd_per_kwh": df.price_usd_mwh / 1000.0,
                    "grid_water_consumption_l_per_kwh": df.grid_water_l_mwh / 1000.0})
out.to_csv(OUT, index=False)
print(f"Wrote {OUT}: {DAY}, ${out.price_usd_per_kwh.min():.4f}-{out.price_usd_per_kwh.max():.4f}/kWh")

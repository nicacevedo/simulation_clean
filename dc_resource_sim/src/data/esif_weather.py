"""
Extract 2023 hourly outdoor wet-bulb at ESIF for s4_weather_overhead.py.
The source file is only read, never modified.

Source: the validated EDA hourly table built by facility_overhead/scripts/
run_esif_facility_overhead.py from the ESIF DC outside weather station (time-weighted
hourly means, Stull 2011 wet-bulb from dry-bulb and RH, >= 90% hourly coverage).
Its naive hours match the naive-as-UTC convention of esif_day.py; alignment is checked
below at lag 0 against esif_hourly_2023.csv. Invalid hours are written as NaN, never filled.

Run from the repository root:
    python dc_resource_sim/src/data/esif_weather.py
"""

import numpy as np
import pandas as pd

PARQUET = ("/home/nacevedo/RA/data-center-externalities-modeling/other_sources/"
           "nlr_esif_fullstack/facility_overhead/data_processed/esif_facility_hourly.parquet")
POWER = "dc_resource_sim/runs/esif_hourly_2023.csv"
OUT = "dc_resource_sim/runs/esif_weather_hourly_2023.csv"

h = pd.read_parquet(PARQUET, columns=["hour", "it_power_kw", "twb_c", "valid_weather", "valid_twb"])
h["timestamp_utc"] = h["hour"].dt.tz_localize("UTC")
h = h[(h.timestamp_utc >= "2023-01-01") & (h.timestamp_utc < "2024-01-01")]
assert h.timestamp_utc.is_unique
h["twb_c"] = h.twb_c.where(h.valid_weather & h.valid_twb)

# Alignment: same hourly IT power as our own preprocessing at lag 0
power = pd.read_csv(POWER)
power["timestamp_utc"] = pd.to_datetime(power["timestamp_utc"], utc=True)
m = power.merge(h, on="timestamp_utc", suffixes=("", "_eda"))
assert np.median((m.it_power_kw - m.it_power_kw_eda).abs()) < 1.0, "Weather/power misaligned"

h[["timestamp_utc", "twb_c"]].to_csv(OUT, index=False)
print(f"Wrote {OUT}: {len(h)} hours, {h.twb_c.notna().sum()} with valid wet-bulb")

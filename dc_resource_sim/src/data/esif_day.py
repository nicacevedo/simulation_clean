"""
Extract one complete 24-hour day from the NLR ESIF PUE dataset (DOI 10.7799/3015212)
as hourly means for m0_first.py. The source file is only read, never modified.

Timestamps in the source are naive; they are treated as UTC, as inferred in earlier
Track A EDA (diurnal outdoor temperature peaks, lag-0 alignment with UTC iLO data).

Run from the repository root:
    python dc_resource_sim/src/data/esif_day.py [YYYY-MM-DD]
"""

import sys

import pandas as pd

PARQUET = ("/home/nacevedo/RA/data-center-externalities-modeling/other_sources/"
           "nlr_esif_fullstack/data_raw/esif_pue/esif.influx.buildingData.PUE.combined.parquet")
DAY = sys.argv[1] if len(sys.argv) > 1 else "2023-07-01"
OUT = "dc_resource_sim/runs/esif_24h.csv"
# Samples are ~1 min apart with jitter, so an exact grid check is impossible.
# A day counts as complete if no gap (including from midnight to the first sample
# and from the last sample to midnight) exceeds this. Gaps are never filled.
MAX_GAP = pd.Timedelta(minutes=5)

df = pd.read_parquet(PARQUET, columns=["ts", "it_power_kw", "pue"])
df["ts"] = df["ts"].dt.tz_localize("UTC")
start = pd.Timestamp(DAY, tz="UTC")
end = start + pd.Timedelta(days=1)
df = df[(df.ts >= start) & (df.ts < end)].sort_values("ts")

assert len(df) > 1, f"No data for {DAY}"
assert df.ts.is_unique
assert df[["it_power_kw", "pue"]].notna().all().all()
assert (df.it_power_kw > 0).all() and (df.pue >= 1).all()
edges = pd.Series([start, *df.ts, end])
assert edges.diff().max() <= MAX_GAP, f"Incomplete day {DAY}: max gap {edges.diff().max()}"

# Reference facility power per sample, before hourly averaging
df["ref_dc_kw"] = df.it_power_kw * df.pue
hourly = df.set_index("ts")[["it_power_kw", "ref_dc_kw"]].resample("h").mean()
assert len(hourly) == 24

out = pd.DataFrame({
    "timestamp_utc": hourly.index.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    "it_kw": hourly.it_power_kw.values,
    "ref_dc_kw": hourly.ref_dc_kw.values,
})
out.to_csv(OUT, index=False)
print(f"{DAY}: {len(df)} samples, max gap {edges.diff().max()} -> {OUT}")

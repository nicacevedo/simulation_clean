"""
Check M0 accuracy across all complete days in 2023, with k fixed from 2023-07-01.

Preprocessing matches esif_day.py: naive timestamps treated as UTC, no gap > 5 min
(including from midnight and to midnight), ref_dc_kw = it_power_kw * pue per sample,
then hourly means. Incomplete days are skipped, never filled.

Run from the repository root:
    python dc_resource_sim/src/experiments/m0_daily.py
"""

import pandas as pd

PARQUET = ("/home/nacevedo/RA/data-center-externalities-modeling/other_sources/"
           "nlr_esif_fullstack/data_raw/esif_pue/esif.influx.buildingData.PUE.combined.parquet")
TRAIN_DAY = pd.Timestamp("2023-07-01", tz="UTC")
MAX_GAP = pd.Timedelta(minutes=5)
OUT = "dc_resource_sim/runs/m0_daily.csv"
OVERHEAD_PNG = "dc_resource_sim/runs/m0_overhead.png"

df = pd.read_parquet(PARQUET, columns=["ts", "it_power_kw", "pue"])
df["ts"] = df["ts"].dt.tz_localize("UTC")
df = df[(df.ts >= "2023-01-01") & (df.ts < "2024-01-01")].sort_values("ts")

rows = []
hourly = {}  # day -> 24 hourly means, reused by Step 04
for day, g in df.groupby(df.ts.dt.floor("D")):
    edges = pd.Series([day, *g.ts, day + pd.Timedelta(days=1)])
    if (not g.ts.is_unique
            or g[["it_power_kw", "pue"]].isna().any().any()
            or not (g.it_power_kw > 0).all()
            or not (g.pue >= 1).all()
            or edges.diff().max() > MAX_GAP):
        continue
    g = g.assign(ref_dc_kw=g.it_power_kw * g.pue)
    h = g.set_index("ts")[["it_power_kw", "ref_dc_kw"]].resample("h").mean()
    assert len(h) == 24 and h.notna().all().all()
    hourly[day] = h
    # Hourly means over 1 h intervals, so sums are kWh
    rows.append({"day": day, "it_kwh": h.it_power_kw.sum(), "ref_dc_kwh": h.ref_dc_kw.sum()})

days = pd.DataFrame(rows).set_index("day")
days["ref_pue"] = days.ref_dc_kwh / days.it_kwh
k_hat = days.loc[TRAIN_DAY, "ref_pue"]
days["error_pct"] = 100 * (k_hat * days.it_kwh / days.ref_dc_kwh - 1)

# Must reproduce Step 02 (esif_day.py + m0_holdout.py)
assert round(k_hat, 4) == 1.0474, k_hat
assert round(days.loc[pd.Timestamp("2023-12-01", tz="UTC"), "ref_pue"], 4) == 1.0210

test = days.drop(TRAIN_DAY)  # July 1 is the training day
abs_err = test.error_pct.abs()
print(f"Complete days in 2023: {len(days)} of 365 (k_hat = {k_hat:.4f} from {TRAIN_DAY.date()})")
print("\nDaily reference PUE:")
print(days.ref_pue.describe(percentiles=[0.1, 0.5, 0.9]).round(4).to_string())
print(f"\nHeld-out |daily energy error| (%), n = {len(test)}: "
      f"median {abs_err.median():.2f}, p90 {abs_err.quantile(0.9):.2f}, max {abs_err.max():.2f}")
print(f"Corr(daily PUE, daily IT energy): {days.ref_pue.corr(days.it_kwh):+.2f}")

monthly = days.groupby(days.index.month).agg(
    n_days=("ref_pue", "size"),
    median_pue=("ref_pue", "median"),
    median_error_pct=("error_pct", "median"),
    mean_it_kw=("it_kwh", lambda e: e.mean() / 24),
)
print("\nBy month:")
print(monthly.round({"median_pue": 4, "median_error_pct": 2, "mean_it_kw": 0}).to_string())

days.to_csv(OUT)
print(f"\nper-day table: {OUT}")

# Step 04: overhead versus IT load (PUE is coupled to IT load by construction, overhead is not)
import matplotlib.pyplot as plt

h = pd.concat(hourly, names=["day", "hour"])
x = h["it_power_kw"]
y = h["ref_dc_kw"] - x  # Reference overhead (kW)

bins = pd.qcut(x, 4, duplicates="drop")
summary = pd.DataFrame({"it_kw": x, "overhead_kw": y})
print("\nHourly overhead by IT-load quartile:")
print(summary.groupby(bins, observed=True)
      .agg(n=("overhead_kw", "size"),
           it_kw=("it_kw", "median"),
           overhead_kw=("overhead_kw", "median"))
      .round(1).to_string())

fig, ax = plt.subplots(figsize=(7, 4))
sc = ax.scatter(x, y, c=h.index.get_level_values("hour").month,
                cmap="viridis", s=6, alpha=0.25)
limits = [x.min(), x.max()]
ax.plot(limits, [(k_hat - 1) * v for v in limits], "k--", label=f"M0 (k={k_hat:.4f})")
ax.set(xlabel="IT power (kW)", ylabel="Overhead power (kW)")
ax.legend()
fig.colorbar(sc, ax=ax, label="Month (2023)")
fig.tight_layout()
fig.savefig(OVERHEAD_PNG, dpi=150)
print(f"overhead plot: {OVERHEAD_PNG}")

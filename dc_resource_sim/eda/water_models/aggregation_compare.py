"""EDA 04 (Step 29): water-model complexity versus temporal aggregation.

Run from the repository root (needs a pandas with parquet support):
    ~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/aggregation_compare.py

Model sufficiency against simulated W2-Air process evaporation, not water-meter validation.
Nothing is refit: C0/C1 are frozen from EDA 02, W2-Air uses Step 20 parameters unchanged.
Inputs and the W2 calling pattern mirror replay_observed_weather.py (EDA 03).
"""
import contextlib
import io
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True  # keep src/experiments untouched
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src" / "experiments"))
with contextlib.redirect_stdout(io.StringIO()):  # silence Step 20's self-test prints
    from w2_air_first import direct_evap, SUPPLY_MAX_C  # noqa: E402

PARQUET = ("/home/nacevedo/RA/data-center-externalities-modeling/other_sources/"
           "nlr_esif_fullstack/facility_overhead/data_processed/esif_facility_hourly.parquet")
C0 = 0.14688   # L/kWh IT, frozen from EDA 02
BETA = 0.09788  # L/(kWh IT * C), frozen from EDA 02
FIG = HERE / "figures"
BLUE, ORANGE, INK, INK2, GRAY = "#2a78d6", "#d9822b", "#0b0b0b", "#52514e", "#8a8984"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRAY, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": "#e6e5e0",
                     "grid.linewidth": 0.6, "font.size": 9})


def w2(t, rh_pct, it_kw):
    # Same rule as EDA 03: dry (0 evaporation) at or below the 25 C supply target.
    if t <= SUPPLY_MAX_C:
        return "dry", 0.0
    s = direct_evap(t, min(rh_pct, 100.0) / 100, it_kw=it_kw)
    return s["mode"], s.get("evaporation_lph", np.nan)


def wape(g, col):
    # Sum errors within each group first (so opposite signs cancel), then abs, over total W2.
    return 100 * (g[col] - g.v_w2).abs().sum() / g.v_w2.sum()


# ---------------- Support ----------------
h = pd.read_parquet(PARQUET, columns=["hour", "tdb_c", "rh_pct", "it_power_kw",
                                      "valid_weather", "valid_it"])
h = h[(h.hour >= "2023-01-01") & (h.hour < "2024-01-01")]  # naive timestamps are UTC
h = h[h.valid_weather & h.valid_it & h.tdb_c.notna() & h.rh_pct.notna()].copy()
assert h.hour.is_unique
assert h.it_power_kw.gt(0).all() and h.tdb_c.between(-40, 50).all() and h.rh_pct.between(0, 105).all()

h[["mode", "v_w2"]] = [w2(t, r, p) for t, r, p in zip(h.tdb_c, h.rh_pct, h.it_power_kw)]
h["v_w2"] = h.v_w2.astype(float)
h["v_c0"] = C0 * h.it_power_kw
h["v_c1"] = BETA * h.it_power_kw * np.maximum(h.tdb_c - SUPPLY_MAX_C, 0.0)
modes = h["mode"].value_counts().reindex(["dry", "wet", "infeasible"], fill_value=0)
assert h.loc[h["mode"] != "infeasible", "v_w2"].notna().all()

# Complete UTC days: 24 matched hours and no infeasible (N/A) W2 hour.
h["day"] = h.hour.dt.floor("D")
per_day = h.groupby("day").agg(n=("hour", "size"), n_inf=("mode", lambda m: (m == "infeasible").sum()))
keep_days = per_day.index[(per_day.n == 24) & (per_day.n_inf == 0)]
x = h[h.day.isin(keep_days)].copy()
x["month"] = x.hour.dt.to_period("M")

cols = ["v_w2", "v_c0", "v_c1"]
daily = x.groupby("day")[cols].sum()
monthly = x.groupby("month")[cols].sum()
days_per_month = x.groupby("month").day.nunique()
assert np.allclose(daily.sum(), x[cols].sum()) and np.allclose(monthly.sum(), daily.sum())

# ---------------- Three metrics ----------------
wet = x[x["mode"] == "wet"]
rows = []
for name, col in [("C0", "v_c0"), ("C1", "v_c1")]:
    r = {"model": name, "wape_hourly_pct": wape(x, col), "wape_daily_pct": wape(daily, col),
         "wape_monthly_pct": wape(monthly, col),
         "peak_err_lph": x[col].max() - x.v_w2.max(),
         "wet_mae_lph": (wet[col] - wet.v_w2).abs().mean()}
    tol = 1e-9
    assert r["wape_hourly_pct"] + tol >= r["wape_daily_pct"] and r["wape_daily_pct"] + tol >= r["wape_monthly_pct"]
    rows.append(r)
summary = pd.DataFrame(rows).set_index("model")
summary.round(3).to_csv(HERE / "aggregation_summary.csv")

print("=== Step 29: model vs W2-Air process evaporation by aggregation ===")
print(f"Valid 2023 hours: {len(h)} (dry {modes.dry}, wet {modes.wet}, infeasible {modes.infeasible}); "
      f"missing vs 8760: {8760 - len(h)}")
print(f"Complete days retained: {len(keep_days)} of {len(per_day)} days with data "
      f"(dropped {(per_day.n < 24).sum()} incomplete, {((per_day.n == 24) & (per_day.n_inf > 0)).sum()} with infeasible hours); "
      f"{len(x)} hours (dry {(x['mode'] == 'dry').sum()}, wet {len(wet)})")
print(f"W2 peak {x.v_w2.max():.1f} L/h; total on retained days W2 {x.v_w2.sum() / 1e3:.1f} m3, "
      f"C0 {x.v_c0.sum() / 1e3:.1f} m3, C1 {x.v_c1.sum() / 1e3:.1f} m3")
print(summary.round(3).to_string())
print("Retained complete days per month: " + ", ".join(f"{m.strftime('%b')} {n}" for m, n in days_per_month.items()))
print("W0 (0.5 L/kWh IT, Step 23) is a direct-consumption accounting proxy and is not ranked here.")

# ---------------- Figure 07 ----------------
labels = [m.strftime("%b") for m in monthly.index]
pos = np.arange(len(monthly))
fig, (a, b) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
for k, (col, name, color) in enumerate([("v_w2", "W2-Air (reference)", INK),
                                        ("v_c1", f"C1, β = {BETA}", BLUE),
                                        ("v_c0", f"C0, c₀ = {C0}", ORANGE)]):
    a.bar(pos + (k - 1) * 0.27, monthly[col] / 1e3, width=0.27, color=color, label=name)
a.set_ylabel("Process evaporation (m³)")
a.set_title("A. Monthly complete-day sampled subtotals (not calendar-month totals)", fontsize=10, loc="left")
a.legend(fontsize=8, frameon=False, loc="upper left")
b.bar(pos, days_per_month.values, color=GRAY, width=0.6)
b.axhline(0, color=GRAY, lw=0.6)
b.set_ylabel("Complete days")
b.set_title("B. Complete 24-h UTC days contributing per month", fontsize=10, loc="left")
b.set_xticks(pos, labels)
b.set_xlabel("Month (UTC, 2023)")
fig.suptitle("ESIF 2023 measured weather and IT load, hypothetical direct-evaporative cooling — "
             "simulated, not water-meter validation", fontsize=10, x=0.01, ha="left")
fig.text(0.01, 0.005, f"Same {len(keep_days)} complete days for all models; {8760 - len(h)} missing hours and "
         f"incomplete days excluded, not imputed. WAPE monthly: C0 {summary.wape_monthly_pct['C0']:.1f}%, "
         f"C1 {summary.wape_monthly_pct['C1']:.1f}%.", fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIG / "07_water_aggregation.png", dpi=160)
plt.close(fig)

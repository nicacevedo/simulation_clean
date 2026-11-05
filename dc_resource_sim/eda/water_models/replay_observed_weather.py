"""EDA 03: replay measured ESIF weather through frozen C1 and W2-Air.

Run from the repository root (needs a pandas with parquet support):
    ~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/replay_observed_weather.py

Nothing is refit: W2-Air uses Step 20 parameters unchanged and C1 uses the EDA 02 beta.
Weather and IT power are measured ESIF hourly means; the cooling system is hypothetical
(ESIF is not a direct-evaporative facility), so outputs are simulated process water.
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
    from w2_air_first import direct_evap, SUPPLY_MAX_C, MAX_WB_EFFECTIVENESS  # noqa: E402

PARQUET = ("/home/nacevedo/RA/data-center-externalities-modeling/other_sources/"
           "nlr_esif_fullstack/facility_overhead/data_processed/esif_facility_hourly.parquet")
BETA = 0.09788      # L/(kWh IT * C), frozen from EDA 02 (fit_simple_water.py)
RECOVERY = 0.8      # illustrative treatment recovery from Step 25; feed = evap / recovery
WEEK = ("2023-07-24", "2023-07-31")  # hottest complete 2023 week (most wet hours); naive-as-UTC
FIG = HERE / "figures"
BLUE, INK, INK2, GRAY, WETFILL = "#2a78d6", "#0b0b0b", "#52514e", "#8a8984", "#cde2fb"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRAY, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": "#e6e5e0",
                     "grid.linewidth": 0.6, "lines.linewidth": 2, "font.size": 9})


def w2(t, rh_pct, it_kw):
    # At or below the supply target W2 is dry by construction; skipping the call also avoids
    # its saturation solver, which cannot bracket in very cold air.
    if t <= SUPPLY_MAX_C:
        return "dry", 0.0, 0.0
    s = direct_evap(t, min(rh_pct, 100.0) / 100, it_kw=it_kw)
    need = s.get("needed_effectiveness", s.get("effectiveness"))
    return s['mode'], s.get("evaporation_lph", np.nan), need


h = pd.read_parquet(PARQUET, columns=["hour", "tdb_c", "rh_pct", "it_power_kw",
                                      "valid_weather", "valid_it"])
h = h[(h.hour >= "2023-01-01") & (h.hour < "2024-01-01")].copy()
h = h[h.valid_weather & h.valid_it & h.tdb_c.notna() & h.rh_pct.notna()]
h[["mode", "w2_lph", "need_eff"]] = [w2(t, r, p) for t, r, p in
                                     zip(h.tdb_c, h.rh_pct, h.it_power_kw)]
h["c1_lph"] = BETA * h.it_power_kw * np.maximum(h.tdb_c - SUPPLY_MAX_C, 0.0)

year = h['mode'].value_counts()
feas_y = h[h['mode'] != "infeasible"]
wk = h[(h.hour >= WEEK[0]) & (h.hour < WEEK[1])]
assert len(wk) == 168, "replay week must be complete"
feas = wk[wk['mode'] != "infeasible"]
n_inf = (wk['mode'] == "infeasible").sum()
err = feas.c1_lph - feas.w2_lph
wet = feas[feas['mode'] == "wet"]

# ---------------- Figure 06 ----------------
fig, (a, b, c) = plt.subplots(3, 1, figsize=(10, 7.2), sharex=True,
                              gridspec_kw={"height_ratios": [1.1, 0.8, 1.3]})
for axx in (a, b, c):
    for t0 in wet.hour:
        axx.axvspan(t0, t0 + pd.Timedelta(hours=1), color=WETFILL, alpha=0.5, lw=0)
    for t0 in wk.hour[wk['mode'] == "infeasible"]:
        axx.axvspan(t0, t0 + pd.Timedelta(hours=1), color="#f2b8a2", alpha=0.8, lw=0)
a.plot(wk.hour, wk.tdb_c, color=INK)
a.axhline(SUPPLY_MAX_C, color=INK2, lw=1, ls=":")
a.set_ylabel("Dry-bulb (°C)")
a.set_title(f"A. Measured outdoor dry-bulb; dotted = 25 °C supply target; shaded = W2 wet mode ({len(wet)} h), "
            f"infeasible = {n_inf} h", fontsize=10, loc="left")
b.plot(wk.hour, wk.rh_pct, color=INK)
b.set_ylabel("RH (%)")
b.set_ylim(0, 100)
b.set_title("B. Measured outdoor relative humidity", fontsize=10, loc="left")
c.plot(feas.hour, feas.w2_lph, color=INK, label="W2-Air (physical reference)")
c.plot(feas.hour, feas.c1_lph, color=BLUE, lw=1.5, ls="--", label=f"C1 frozen, β = {BETA}")
c.set_ylabel("Process evaporation (L/h)")
c.set_title("C. Simulated evaporation at measured IT load (hypothetical direct-evaporative cooling)",
            fontsize=10, loc="left")
c.legend(fontsize=8, frameon=False, loc="upper left")
c.set_xlabel("Hour (UTC, 2023)")
fig.suptitle("ESIF measured weather, Jul 24–30 2023 (hottest complete week), replayed through "
             "frozen models — not water-meter validation", fontsize=10, x=0.01, ha="left")
fig.text(0.01, 0.005, f"Fixed: supply 25 °C, ε_max {MAX_WB_EFFECTIVENESS}, ΔT_server 15 °C. "
         f"C1–W2 on feasible hours: MAE {err.abs().mean():.2f} L/h, max |err| {err.abs().max():.2f} L/h. "
         f"Feed = evaporation / {RECOVERY} (assumed recovery).", fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.025, 1, 1))
fig.savefig(FIG / "06_observed_weather_replay.png", dpi=160)
plt.close(fig)

# ---------------- Printed summary ----------------
print("=== EDA 03 summary ===")
print(f"Year 2023 valid hours: {len(h)} -> " + ", ".join(f"{m} {n}" for m, n in year.items()))
print(f"Year max needed effectiveness: {h.need_eff.max():.3f} (limit {MAX_WB_EFFECTIVENESS})")
print(f"Year C1-W2 on feasible hours: MAE {(feas_y.c1_lph - feas_y.w2_lph).abs().mean():.3f} L/h, "
      f"max |err| {(feas_y.c1_lph - feas_y.w2_lph).abs().max():.2f} L/h; "
      f"totals W2 {feas_y.w2_lph.sum() / 1e3:.1f} m3, C1 {feas_y.c1_lph.sum() / 1e3:.1f} m3")
print(f"Week {WEEK[0]}..: dry {(wk['mode'] == 'dry').sum()}, wet {len(wet)}, infeasible {n_inf}; "
      f"Tdb {wk.tdb_c.min():.1f}-{wk.tdb_c.max():.1f} C, RH {wk.rh_pct.min():.0f}-{wk.rh_pct.max():.0f} %, "
      f"IT {wk.it_power_kw.min():.0f}-{wk.it_power_kw.max():.0f} kW")
print(f"Week max needed effectiveness: {wk.need_eff.max():.3f}")
print(f"Week C1-W2 (feasible hours): MAE {err.abs().mean():.2f} L/h, max |err| {err.abs().max():.2f} L/h, "
      f"mean bias {err.mean():+.2f} L/h")
if n_inf == 0:
    print(f"Week totals (all hours feasible): W2 {feas.w2_lph.sum() / 1e3:.2f} m3, "
          f"C1 {feas.c1_lph.sum() / 1e3:.2f} m3 ({feas.c1_lph.sum() / feas.w2_lph.sum() - 1:+.2%})")
else:
    print("Week has infeasible hours: no valid full-week total without a fallback")
print(f"Peak W2 evaporation {feas.w2_lph.max():.1f} L/h at {feas.hour[feas.w2_lph.idxmax()]}; "
      f"peak feed {feas.w2_lph.max() / RECOVERY:.1f} L/h (recovery {RECOVERY})")

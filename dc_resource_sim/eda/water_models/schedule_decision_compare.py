"""EDA 05 (Step 30): does the reduced water model C1 preserve the W2-optimal schedule?

Run from the repository root (needs a pandas with parquet support):
    ~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/schedule_decision_compare.py

One measured ESIF weather day, hypothetical constant 1 MW IT load and hypothetical direct-evaporative
cooling (Step 20 settings). Step 08 LP constraints. All schedules are scored with W2-Air process
evaporation; this is conditional decision regret, not a measured water saving.
"""
import contextlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

sys.dont_write_bytecode = True  # keep src/experiments untouched
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src" / "experiments"))
with contextlib.redirect_stdout(io.StringIO()):  # silence Step 20's self-test prints
    from w2_air_first import direct_evap, SUPPLY_MAX_C  # noqa: E402

PARQUET = ("/home/nacevedo/RA/data-center-externalities-modeling/other_sources/"
           "nlr_esif_fullstack/facility_overhead/data_processed/esif_facility_hourly.parquet")
DAY = pd.Timestamp("2023-07-24")  # predetermined; naive timestamps are UTC
BETA = 0.09788    # L/(kWh IT * C), frozen from EDA 02
RECOVERY = 0.8    # illustrative treatment recovery (Step 25); feed = evap / recovery
T = 24

# ---------------- Validated day ----------------
h = pd.read_parquet(PARQUET, columns=["hour", "tdb_c", "rh_pct", "valid_weather", "valid_it"])
d = h[(h.hour >= DAY) & (h.hour < DAY + pd.Timedelta(days=1))].sort_values("hour")
assert (d.hour.values == pd.date_range(DAY, periods=T, freq="h").values).all(), "need 24 consecutive UTC hours"
assert d.valid_weather.all() and d.valid_it.all() and d[["tdb_c", "rh_pct"]].notna().all().all()
tdb_c, rh_pct = d.tdb_c.to_numpy(), d.rh_pct.to_numpy()

# Intensities in L/kWh IT: W2 is proportional to IT load at fixed weather and equipment.
w2 = np.zeros(T)
modes = []
for t in range(T):
    if tdb_c[t] <= SUPPLY_MAX_C:
        modes.append("dry")  # dry-mode rule used in the EDA replay
        continue
    r = direct_evap(float(tdb_c[t]), min(float(rh_pct[t]), 100.0) / 100, it_kw=1000.0)
    modes.append(r["mode"])
    assert r["mode"] != "infeasible", f"hour {t} infeasible: stop, do not substitute a date"
    w2[t] = r["evaporation_lph"] / 1000.0
c1 = BETA * np.maximum(tdb_c - SUPPLY_MAX_C, 0.0)
assert np.isfinite(w2).all() and np.isfinite(c1).all()
assert np.any(w2 > 0) and np.any(w2 == 0), "need mixed wet/dry hours"
print(f"Day {DAY.date()} UTC: 24 valid hours; dry {modes.count('dry')}, wet {modes.count('wet')}, infeasible 0")

# ---------------- Step 08 LP ----------------
baseline = np.full(T, 1000.0)  # hypothetical IT kWh per 1-h bin
phi, it_cap = 0.20, 1250.0
fixed, arrivals = (1 - phi) * baseline, phi * baseline


def solve(intensity):
    r = linprog(intensity, A_ub=np.tril(np.ones((T, T))), b_ub=np.cumsum(arrivals),
                A_eq=np.ones((1, T)), b_eq=[arrivals.sum()],
                bounds=[(0, it_cap - f) for f in fixed], method="highs")
    assert r.success, r.message
    x = fixed + r.x
    assert np.isclose(x.sum(), baseline.sum())
    assert (x <= it_cap + 1e-6).all()
    assert (np.cumsum(r.x) <= np.cumsum(arrivals) + 1e-6).all()
    return x


policies = {"no_shift": baseline, "C1_optimal": solve(c1), "W2_optimal": solve(w2)}
v_opt = w2 @ policies["W2_optimal"]
v_base = w2 @ baseline
rows = []
for name, x in policies.items():
    v = w2 @ x
    assert v >= v_opt - 1e-5
    rows.append({"policy": name, "it_energy_kwh": x.sum(), "w2_evaporation_l": v,
                 "saving_vs_no_shift_l": v_base - v, "conditional_regret_l": v - v_opt,
                 "peak_feed_lph": np.max(w2 * x) / RECOVERY})
summary = pd.DataFrame(rows).set_index("policy")
summary.round(3).to_csv(HERE / "schedule_decision_summary.csv")

print(summary.round(3).to_string())
print(f"C1 regret / W2 achievable saving: "
      f"{summary.conditional_regret_l['C1_optimal'] / (v_base - v_opt):.2%}")
print(f"Day-oracle constant intensity (illustrative, not a predictor): {v_base / baseline.sum():.4f} L/kWh; "
      f"any constant c gives c*24000 L for every feasible schedule, so it cannot rank hours.")
print("Peak feed uses assumed recovery 0.8; evaporation, not facility withdrawal.")

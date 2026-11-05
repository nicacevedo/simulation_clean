"""EDA 06 (Step 31): water-saving schedules under a peak treatment-feed limit.

Run from the repository root (needs a pandas with parquet support):
    ~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/peak_feed_capacity_compare.py

Step 30 setup unchanged (same ESIF day, workload LP, frozen C1, W2-Air, recovery 0.8) plus one constraint:
    w_t * x_t / eta <= F_cap for every hour.
Each model uses its own intensities in objective AND cap; every schedule is then scored with W2.
Feed = hypothetical treatment feed (evaporation / recovery), not withdrawal or groundwater extraction.
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
TOL = 0.01        # L or L/h: anchor agreement and cap-feasibility tolerance

# ---------------- Validated day and intensities (as Step 30) ----------------
h = pd.read_parquet(PARQUET, columns=["hour", "tdb_c", "rh_pct", "valid_weather", "valid_it"])
d = h[(h.hour >= DAY) & (h.hour < DAY + pd.Timedelta(days=1))].sort_values("hour")
assert (d.hour.values == pd.date_range(DAY, periods=T, freq="h").values).all(), "need 24 consecutive UTC hours"
assert d.valid_weather.all() and d.valid_it.all() and d[["tdb_c", "rh_pct"]].notna().all().all()
tdb_c, rh_pct = d.tdb_c.to_numpy(), d.rh_pct.to_numpy()

w2 = np.zeros(T)
for t in range(T):
    if tdb_c[t] <= SUPPLY_MAX_C:
        continue  # dry mode
    r = direct_evap(float(tdb_c[t]), min(float(rh_pct[t]), 100.0) / 100, it_kw=1000.0)
    assert r["mode"] != "infeasible", f"hour {t} infeasible: stop, do not substitute a date"
    w2[t] = r["evaporation_lph"] / 1000.0
c1 = BETA * np.maximum(tdb_c - SUPPLY_MAX_C, 0.0)
assert np.isfinite(w2).all() and np.isfinite(c1).all()

# ---------------- Step 30 LP plus optional per-hour feed cap ----------------
baseline = np.full(T, 1000.0)  # hypothetical IT kWh per 1-h bin
phi, it_cap = 0.20, 1250.0
fixed, arrivals = (1 - phi) * baseline, phi * baseline


def solve(intensity, cap_lph=None):
    """Min intensity @ y; returns x or None if this model's own LP is infeasible."""
    A_ub, b_ub = np.tril(np.ones((T, T))), np.cumsum(arrivals)
    if cap_lph is not None:  # w_t y_t <= eta F - w_t fixed_t, in the model's own intensities
        A_ub = np.vstack([A_ub, np.diag(intensity)])
        b_ub = np.concatenate([b_ub, RECOVERY * cap_lph - intensity * fixed])
    r = linprog(intensity, A_ub=A_ub, b_ub=b_ub, A_eq=np.ones((1, T)), b_eq=[arrivals.sum()],
                bounds=[(0, it_cap - f) for f in fixed], method="highs")
    if r.status == 2:
        return None
    assert r.success, r.message
    x = fixed + r.x
    assert np.isclose(x.sum(), baseline.sum())
    assert (x <= it_cap + 1e-6).all()
    assert (np.cumsum(r.x) <= np.cumsum(arrivals) + 1e-6).all()
    return x


def peak_feed(x):
    return np.max(w2 * x) / RECOVERY


# ---------------- Reproduce Step 30 anchors in full precision ----------------
x_opt = solve(w2)
v_base, v_opt = w2 @ baseline, w2 @ x_opt
F_base, F_opt = peak_feed(baseline), peak_feed(x_opt)
saved = pd.read_csv(HERE / "schedule_decision_summary.csv", index_col="policy")
for got, want in [(v_base, saved.w2_evaporation_l["no_shift"]), (F_base, saved.peak_feed_lph["no_shift"]),
                  (v_opt, saved.w2_evaporation_l["W2_optimal"]), (F_opt, saved.peak_feed_lph["W2_optimal"])]:
    assert abs(got - want) <= TOL, (got, want)
assert F_opt > F_base
print(f"Step 30 anchors reproduced: no-shift {v_base:.6f} L, peak {F_base:.6f} L/h; "
      f"W2-opt {v_opt:.6f} L, peak {F_opt:.6f} L/h")

# ---------------- Three predeclared caps x two models ----------------
caps = {"A_existing_peak": F_base, "B_intermediate": (F_base + F_opt) / 2, "C_step30_peak": F_opt}
rows = []
for scen, cap in caps.items():
    assert peak_feed(baseline) <= cap + TOL  # no-shift is W2-feasible at every cap
    x_w2 = solve(w2, cap)
    assert x_w2 is not None and peak_feed(x_w2) <= cap + TOL
    v_ref = w2 @ x_w2
    for model, intensity in [("W2", w2), ("C1", c1)]:
        x = x_w2 if model == "W2" else solve(c1, cap)
        if x is None:
            rows.append({"scenario": scen, "model": model, "cap_lph": cap, "solver_status": "model_infeasible"})
            continue
        v, pk = w2 @ x, peak_feed(x)
        feasible = pk <= cap + TOL
        rows.append({"scenario": scen, "model": model, "cap_lph": cap, "solver_status": "optimal",
                     "w2_evaporation_l": v, "saving_vs_no_shift_l": v_base - v,
                     "realized_w2_peak_feed_lph": pk, "peak_violation_lph": max(0.0, pk - cap),
                     "w2_feasible": feasible,
                     "conditional_regret_l": v - v_ref if feasible else np.nan})

out = pd.DataFrame(rows)
w2_rows = out[out.model == "W2"].w2_evaporation_l.to_numpy()
assert (np.diff(w2_rows) <= TOL).all(), "W2-cap optimum must be nonincreasing in capacity"
assert abs(w2_rows[-1] - v_opt) <= TOL, "scenario C must recover the Step 30 W2 optimum"
assert (out.conditional_regret_l.dropna() >= -TOL).all()

out.round(3).to_csv(HERE / "peak_feed_capacity_summary.csv", index=False, na_rep="N/A")
print(out.round(3).to_string(index=False, na_rep="N/A"))
print("Feed = hypothetical treatment feed (evaporation / 0.8), L/h; evaporation in L/day.")

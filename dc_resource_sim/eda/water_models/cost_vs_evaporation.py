"""EDA 07 (Step 32): electricity-cost opportunity cost of reducing modeled W2 evaporation by scheduling.

Run from the repository root (needs a pandas with parquet support):
    ~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/cost_vs_evaporation.py

Step 31 scenario A unchanged (ESIF 2023-07-24 weather, workload LP, W2-Air, recovery 0.8, per-hour
feed cap at the no-shift peak) plus one hourly price vector and an M0 cost objective C = sum p_t k x_t.
Constructed scenario: 2023-07-01 MISO ILLINOIS.HUB prices (Springfield, IL) paired by hour-of-day with
2023-07-24 ESIF (Golden, CO) weather -- noncoincident dates and regions, not actual operations.
Total facility kWh is fixed (constant k); only purchase timing changes cost. No cooling-mode electricity.
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
PRICE_CSV = HERE.parents[1] / "runs" / "price_24h.csv"
DAY = pd.Timestamp("2023-07-24")  # predetermined; naive timestamps are UTC
PRICE_DAY = pd.Timestamp("2023-07-01", tz="UTC")
RECOVERY = 0.8    # illustrative treatment recovery (Step 25); feed = evap / recovery
K_PUE = 1.0471    # M0 constant-PUE coefficient
T = 24
TOL = 0.01        # L, L/h or $: anchor agreement and feasibility tolerance
TIE_L, TIE_USD = 0.001, 0.001  # tie-breaking slack on the primary optimum

# ---------------- Validated weather day and W2 intensities (as Step 30-31) ----------------
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
assert np.isfinite(w2).all()

# ---------------- Validated price trace (Step 10 extract, $/kWh) ----------------
p = pd.read_csv(PRICE_CSV)
assert list(p.columns) == ["timestamp_utc", "price_usd_per_kwh"], "unexpected price columns"
p["timestamp_utc"] = pd.to_datetime(p.timestamp_utc, utc=True)
p = p.sort_values("timestamp_utc")
assert (p.timestamp_utc.to_numpy() == pd.date_range(PRICE_DAY, periods=T, freq="h").to_numpy()).all(), \
    "need 24 unique consecutive UTC hours 00-23 on 2023-07-01"
price = p.price_usd_per_kwh.to_numpy(float)
assert np.isfinite(price).all() and (0 < price).all() and (price < 1).all(), "prices must be finite $/kWh"
cost_coef = price * K_PUE  # $ per kWh IT

# ---------------- Step 31 LP: y_t flexible kWh, x_t = fixed_t + y_t ----------------
baseline = np.full(T, 1000.0)  # hypothetical IT kWh per 1-h bin
phi, it_cap = 0.20, 1250.0
fixed, arrivals = (1 - phi) * baseline, phi * baseline


def water(x):
    return w2 @ x


def cost(x):
    return cost_coef @ x


def peak_feed(x):
    return np.max(w2 * x) / RECOVERY


F_cap = peak_feed(baseline)  # Step 31 scenario A: no-shift peak, full precision


def solve(objective, extra_rows=()):
    """Min objective @ x under Step 31 cap-A constraints plus optional (coef, rhs) rows on x."""
    A_ub = [np.tril(np.ones((T, T))), np.diag(w2)]
    b_ub = [np.cumsum(arrivals), RECOVERY * F_cap - w2 * fixed]
    for coef, rhs in extra_rows:  # coef @ x <= rhs  ->  coef @ y <= rhs - coef @ fixed
        A_ub.append(coef[None, :])
        b_ub.append([rhs - coef @ fixed])
    r = linprog(objective, A_ub=np.vstack(A_ub), b_ub=np.concatenate(b_ub),
                A_eq=np.ones((1, T)), b_eq=[arrivals.sum()],
                bounds=[(0, it_cap - f) for f in fixed], method="highs")
    assert r.success, r.message
    x = fixed + r.x
    assert abs(x.sum() - baseline.sum()) <= 1e-6
    assert (x <= it_cap + 1e-6).all()
    assert (np.cumsum(r.x) <= np.cumsum(arrivals) + 1e-6).all()
    assert peak_feed(x) <= F_cap + TOL
    return x


# ---------------- Anchors: Step 30 baseline and Step 31 cap-A W2 optimum ----------------
s31 = pd.read_csv(HERE / "peak_feed_capacity_summary.csv")
a_w2 = s31[(s31.scenario == "A_existing_peak") & (s31.model == "W2")].iloc[0]
assert abs(F_cap - a_w2.cap_lph) <= TOL and abs(F_cap - 1353.818) <= TOL, F_cap
assert abs(water(baseline) - 8680.498) <= TOL, water(baseline)

# B: water-optimal; tie-break by lowest cost within TIE_L of V_min
V_min = water(solve(w2))
assert abs(V_min - a_w2.w2_evaporation_l) <= TOL and abs(V_min - 8460.702) <= TOL, V_min
x_B = solve(cost_coef, [(w2, V_min + TIE_L)])
# A: cost-optimal; tie-break by lowest water within TIE_USD of C_min
C_min = cost(solve(cost_coef))
x_A = solve(w2, [(cost_coef, C_min + TIE_USD)])
assert abs(water(x_B) - V_min) <= TOL and abs(cost(x_A) - C_min) <= TOL

policies = {"no_shift": baseline, "cost_optimal": x_A, "water_optimal": x_B}
degenerate = water(x_A) - water(x_B) <= TOL
if not degenerate:
    V_mid = (water(x_A) + water(x_B)) / 2
    x_C = solve(cost_coef, [(w2, V_mid)])
    assert water(x_C) <= V_mid + TOL
    policies["budget_midpoint"] = x_C
    assert water(x_B) - TOL <= water(x_C) <= water(x_A) + TOL
    assert cost(x_A) - TOL <= cost(x_C) <= cost(x_B) + TOL

# ---------------- Table: every schedule scored with the same price and W2 vectors ----------------
rows = []
for name, x in policies.items():
    rows.append({"policy": name, "it_energy_kwh": x.sum(), "facility_energy_kwh": K_PUE * x.sum(),
                 "electricity_cost_usd": cost(x), "w2_evaporation_l": water(x),
                 "saving_vs_no_shift_l": water(baseline) - water(x),
                 "water_saving_vs_cost_opt_l": water(x_A) - water(x),
                 "extra_cost_vs_cost_opt_usd": cost(x) - cost(x_A),
                 "peak_w2_feed_lph": peak_feed(x), "feed_cap_lph": F_cap,
                 "cap_violation_lph": max(0.0, peak_feed(x) - F_cap),
                 "solver_status": "input" if name == "no_shift" else "optimal"})
out = pd.DataFrame(rows)
assert np.allclose(out.facility_energy_kwh, 25130.4)
out.round(3).to_csv(HERE / "cost_evaporation_summary.csv", index=False)
pd.set_option("display.width", 200)
print(out.round(3).to_string(index=False))
print("Price 2023-07-01 MISO ILLINOIS.HUB (Springfield, IL) x weather 2023-07-24 ESIF (Golden, CO): "
      "noncoincident dates and regions, paired by hour-of-day.")

# ---------------- Short conclusion ----------------
dV, dC = water(x_A) - water(x_B), cost(x_B) - cost(x_A)
print(f"1. Cost-optimal evaporation exceeds water-optimal by {dV:.3f} L/day "
      f"({100 * dV / water(x_A):.3f}% of cost-optimal).")
print(f"2. Reaching minimum evaporation costs ${dC:.3f}/day extra "
      f"({100 * dC / cost(x_A):.3f}% of cost-optimal ${cost(x_A):.3f}).")
if degenerate:
    print("3. No measurable trade-off (difference <= 0.01 L/day); midpoint budget skipped.")
else:
    x_C = policies["budget_midpoint"]
    fV, fC = (water(x_A) - water(x_C)) / dV, (cost(x_C) - cost(x_A)) / dC
    print(f"3. Midpoint budget captures {100 * fV:.1f}% of the water saving at {100 * fC:.1f}% "
          f"of the maximum extra cost (${cost(x_C) - cost(x_A):.3f}/day).")

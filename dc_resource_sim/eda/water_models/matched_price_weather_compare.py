"""EDA 08 (Step 33): is Step 32's cost-water alignment robust to co-timed, same-region price and weather?

Run from the repository root (needs a pandas with parquet support):
    ~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/matched_price_weather_compare.py

Source: frozen signals_2023_v1, site S1b Springfield, IL (meta: site_S1b_meta.json).
  weather  Tdb_C, RH_raw_pct  -- NOAA GHCNh station USW00093822 (Springfield Abraham Lincoln Capital AP,
           5.8 km from site); only wx_qc_flag == "ok" hours used (alt-station fills / interpolations excluded)
  price    price_usd_mwh      -- MISO day-ahead ex-post LMP, ILLINOIS.HUB, $/MWh (converted once to $/kWh);
           raw EST hour-ending, verified below to map to t_utc = interval start
Step 32 LP and tie-breaking unchanged; only the hourly price/weather vectors and each day's no-shift
feed cap change. Hub wholesale prices are a proxy, not a facility tariff; W2 is simulated process
evaporation, not measured consumption; feed is hypothetical, not withdrawal or groundwater extraction.
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

SIGNALS = ("/home/nacevedo/m0m1_overnight/06_runs/20261016T0527Z_m0m1/inputs/signals_2023_v1/"
           "site_S1b_springfield_2023.parquet")
WEATHER_SOURCE = "NOAA GHCNh USW00093822 Springfield IL (Tdb_C, RH_raw_pct; qc ok)"
PRICE_SOURCE = "MISO DA ex-post LMP ILLINOIS.HUB ($/MWh -> $/kWh)"
RECOVERY = 0.8    # illustrative treatment recovery; feed = evap / recovery
K_PUE = 1.0471    # M0 constant-PUE coefficient
T = 24
TOL = 0.01        # L, L/h or $
TIE_L, TIE_USD = 0.001, 0.001  # tie-breaking slack on the primary optimum
MIN_L = 1.0       # below this saving/gap, ratios are reported N/A

# ---------------- Preflight: raw coverage, time mapping, units ----------------
cols = ["t_utc", "Tdb_C", "RH_raw_pct", "wx_qc_flag", "price_usd_mwh", "price_qc_flag",
        "price_node", "price_market", "price_raw_tz", "price_raw_date", "price_raw_he"]
raw = pd.read_parquet(SIGNALS, columns=cols)
print(f"Raw rows {len(raw)}: {raw.t_utc.min()} .. {raw.t_utc.max()}")
s = raw[raw.t_utc.dt.year == 2023].sort_values("t_utc").reset_index(drop=True)
print(f"2023 UTC rows {len(s)} (outside 2023 dropped: {len(raw) - len(s)}); duplicates {s.t_utc.duplicated().sum()}")
assert s.t_utc.duplicated().sum() == 0, "duplicate 2023 UTC hours"
assert (s.price_node == "ILLINOIS.HUB").all() and (s.price_market == "MISO day-ahead ex-post LMP").all()
assert (s.price_raw_tz == "EST (UTC-5, fixed), hour-ending").all()
p_ok = s.price_raw_he.notna()  # HE h in EST covers [h-1, h) EST = [h+4, h+5) UTC
start_utc = (pd.to_datetime(s.price_raw_date[p_ok]) + pd.to_timedelta(s.price_raw_he[p_ok].astype(float) + 4, unit="h"))
assert (start_utc.dt.tz_localize("UTC") == s.t_utc[p_ok]).all(), "price hour does not map to t_utc"

valid = ((s.wx_qc_flag == "ok") & (s.price_qc_flag == "ok")
         & np.isfinite(s[["Tdb_C", "RH_raw_pct", "price_usd_mwh"]]).all(axis=1))
assert s.Tdb_C[valid].between(-40, 50).all() and s.RH_raw_pct[valid].between(0, 100).all()
assert s.price_usd_mwh[valid].between(-1000, 5000).all()  # negatives legitimate, not clipped
print(f"Invalid/missing hours: {(~valid).sum()} (wx not ok {(s.wx_qc_flag != 'ok').sum()}, "
      f"price not ok {(s.price_qc_flag != 'ok').sum()})")

# ---------------- Eligible days and W2 intensities (L/kWh IT) ----------------
s["date"] = s.t_utc.dt.strftime("%Y-%m-%d")
s["valid"] = valid


def w2_intensity(tdb_c, rh_pct):
    """L/kWh IT at 1000 kW; 0 in dry mode; None if the assumed equipment cannot meet the target."""
    if tdb_c <= SUPPLY_MAX_C:
        return 0.0
    r = direct_evap(float(tdb_c), min(float(rh_pct), 100.0) / 100, it_kw=1000.0)
    return None if r["mode"] == "infeasible" else r["evaporation_lph"] / 1000.0


days, n_incomplete, n_invalid, n_infeasible = {}, 0, 0, 0
for date, g in s.groupby("date"):
    if len(g) != T or not (g.t_utc.to_numpy() == pd.date_range(date, periods=T, freq="h", tz="UTC").to_numpy()).all():
        n_incomplete += 1
        continue
    if not g.valid.all():
        n_invalid += 1
        continue
    w = [w2_intensity(a, b) for a, b in zip(g.Tdb_C, g.RH_raw_pct)]
    if any(v is None for v in w):
        n_infeasible += 1
        continue
    w = np.array(w)
    days[date] = {"w2": w, "price": g.price_usd_mwh.to_numpy(float) / 1000.0, "tdb": g.Tdb_C.to_numpy(),
                  "v_base": w.sum() * 1000.0}
print(f"UTC dates {s.date.nunique()}: eligible {len(days)}, excluded incomplete {n_incomplete}, "
      f"invalid {n_invalid}, W2-infeasible {n_infeasible}")

# ---------------- Deterministic selection from weather + W2 baseline only ----------------
dry = sorted(d for d in days if days[d]["v_base"] == 0)
wet = sorted((d for d in days if days[d]["v_base"] > 0), key=lambda d: (days[d]["v_base"], d))
print(f"Eligible dry days {len(dry)}, wet days {len(wet)}")
assert dry and wet, "need both dry and wet eligible days"
high = max(wet, key=lambda d: (days[d]["v_base"], -int(d.replace("-", ""))))  # ties -> earlier date
selected = {"dry_control": dry[0], "typical_wet": wet[(len(wet) - 1) // 2], "high_wet": high}  # lower median
assert len(set(selected.values())) == 3, "selected dates not distinct"
for scen, date in selected.items():
    dd = days[date]
    print(f"  {scen:12s} {date}: wet hours {(dd['w2'] > 0).sum():2d}, V_base {dd['v_base']:.3f} L, "
          f"Tdb mean {dd['tdb'].mean():.1f} / max {dd['tdb'].max():.1f} C")

# ---------------- Step 32 LP (unchanged), per day ----------------
baseline = np.full(T, 1000.0)
phi, it_cap = 0.20, 1250.0
fixed, arrivals = (1 - phi) * baseline, phi * baseline


def solve(objective, w2, F_cap, extra_rows=()):
    """Min objective @ x under workload + per-hour feed cap, plus optional (coef, rhs) rows on x."""
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
    assert abs(x.sum() - baseline.sum()) <= 1e-6 and (x <= it_cap + 1e-6).all()
    assert (np.cumsum(r.x) <= np.cumsum(arrivals) + 1e-6).all()
    assert np.max(w2 * x) / RECOVERY <= F_cap + TOL
    return x


rows, summary = [], []
for scen, date in selected.items():
    w2, cost_coef = days[date]["w2"], days[date]["price"] * K_PUE
    F_cap = np.max(w2 * baseline) / RECOVERY  # this day's no-shift peak

    V_min = w2 @ solve(w2, w2, F_cap)
    x_B = solve(cost_coef, w2, F_cap, [(w2, V_min + TIE_L)])
    C_min = cost_coef @ solve(cost_coef, w2, F_cap)
    x_A = solve(w2, w2, F_cap, [(cost_coef, C_min + TIE_USD)])
    if not w2.any():  # dry day: water optimum tied everywhere, so B is the cost-optimal schedule
        x_B = x_A
    assert abs(w2 @ x_B - V_min) <= TOL and abs(cost_coef @ x_A - C_min) <= TOL
    assert cost_coef @ x_A <= cost_coef @ x_B + TOL and w2 @ x_B <= w2 @ x_A + TOL

    V, C = {}, {}
    for policy, x in [("no_shift", baseline), ("cost_optimal", x_A), ("water_optimal", x_B)]:
        V[policy], C[policy] = w2 @ x, cost_coef @ x
        rows.append({"scenario": scen, "date_utc": date, "policy": policy,
                     "weather_source": WEATHER_SOURCE, "price_source": PRICE_SOURCE, "valid_hours": T,
                     "wet_hours": int((w2 > 0).sum()), "baseline_evap_l": days[date]["v_base"],
                     "feed_cap_lph": F_cap, "it_energy_kwh": x.sum(), "facility_energy_kwh": K_PUE * x.sum(),
                     "cost_usd_day": C[policy], "w2_evap_l_day": V[policy],
                     "peak_feed_lph": np.max(w2 * x) / RECOVERY,
                     "solver_status": "input" if policy == "no_shift" else "optimal"})
    if scen == "dry_control":
        assert all(v == 0 for v in V.values())

    S_max, S_cost = V["no_shift"] - V["water_optimal"], V["no_shift"] - V["cost_optimal"]
    gap, extra = V["cost_optimal"] - V["water_optimal"], C["water_optimal"] - C["cost_optimal"]
    price = days[date]["price"]
    corr = np.corrcoef(price, w2)[0, 1] if price.std() > 0 and w2.std() > 0 else np.nan
    summary.append({"scenario": scen, "date_utc": date, "S_max_l": S_max, "S_cost_l": S_cost,
                    "share_captured": S_cost / S_max if S_max > MIN_L else np.nan,
                    "gap_l": gap, "extra_cost_usd": extra,
                    "usd_per_l_gap": extra / gap if gap > MIN_L else np.nan,
                    "corr_price_w2": corr})

out = pd.DataFrame(rows)
assert len(out) == 9 and np.allclose(out.facility_energy_kwh, 25130.4)
assert (out.peak_feed_lph <= out.feed_cap_lph + TOL).all()
out.round(4).to_csv(HERE / "matched_price_weather_summary.csv", index=False)

pd.set_option("display.width", 200)
print(out.drop(columns=["weather_source", "price_source"]).round(3).to_string(index=False))
print(pd.DataFrame(summary).round(3).to_string(index=False, na_rep="N/A"))
print("Co-timed regional proxy price/weather (same UTC hour), not a measured facility; W2 simulated "
      "evaporation; M0 fixed-energy cost; feed hypothetical. corr is descriptive only.")

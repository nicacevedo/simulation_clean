"""Step 35: recommended IT inlet-air screen and one-at-a-time equipment sensitivity of the Step 34 trade-off.

Run from the repository root:
    ~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/cooling_mode_feasibility_sensitivity.py

Input: Step 34 hourly CSV only (2023-06-25 UTC, Springfield, 1 MW IT, once-through outdoor air).
Screen: ASHRAE 2021 A1-A4 *recommended* envelope (18-27 C, dew point -9..15 C, RH <= 70%, noncondensing),
not hardware certification. No humidity control, mixing or heating is modeled. COP and wet auxiliaries
are illustrative sensitivity bounds; water and pass/fail flags do not depend on them.
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
P_ATM = 101325.0  # Pa
T_SET = 25.0
IT_KW, P_COMMON = 1000.0, 20.0
T_MIN, T_MAX, DP_MIN, DP_MAX, RH_MAX = 18.0, 27.0, -9.0, 15.0, 70.0
CASES = [("cop_low", 2.0, 10.0), ("baseline", 3.0, 10.0), ("cop_high", 5.0, 10.0),
         ("wet_aux_low", 3.0, 5.0), ("wet_aux_high", 3.0, 20.0)]


def p_ws(t):  # Pa
    return 610.94 * np.exp(17.625 * t / (t + 243.04))


def p_v(w):  # Pa
    return P_ATM * w / (0.621945 + w)


def dew_point(w):
    r = np.log(p_v(w) / 610.94)
    return 243.04 * r / (17.625 - r)


# ---------------- Load and validate Step 34 anchors ----------------
cols = ["hour_utc", "tdb_c", "rh_pct", "w2_mode", "mdot_dry_air_kg_s", "q_it_kw", "q_inlet_precool_kw",
        "wet_evap_lph", "wet_aux_kw", "dry_mech_kw", "wet_total_kw", "dry_total_kw"]
h = pd.read_csv(HERE / "cooling_mode_energy_water_hourly.csv")
assert set(cols) <= set(h.columns), f"missing Step 34 columns: {set(cols) - set(h.columns)}"
hours = pd.to_datetime(h.hour_utc, utc=True)
assert len(h) == 24 and hours.is_unique and (hours == pd.date_range("2023-06-25", periods=24, freq="h", tz="UTC")).all()
num = cols[4:] + ["tdb_c", "rh_pct"]
assert np.isfinite(h[num]).all(axis=None) and (h[cols[4:]] >= 0).all(axis=None)
wet = (h.w2_mode == "wet").to_numpy()
assert set(h.w2_mode) <= {"wet", "dry"} and (wet == (h.tdb_c > T_SET)).all()
anchors = {"wet hours": (wet.sum(), 21), "evap L": (h.wet_evap_lph.sum(), 8203.34),
           "Q_in kWh_th": (h.q_inlet_precool_kw.sum(), 5566.5), "E_wet kWh": (h.wet_total_kw.sum(), 24690.0),
           "E_dry kWh": (h.dry_total_kw.sum(), 26335.5)}
for k, (got, want) in anchors.items():
    assert abs(got - want) <= 0.1, f"Step 34 anchor {k}: {got} != {want}"

# ---------------- Supply-air reconstruction and recommended-envelope screen ----------------
t_sup = np.minimum(h.tdb_c.to_numpy(), T_SET)  # free-cooling hours supply untreated outdoor air
pv_in = h.rh_pct.to_numpy() / 100 * p_ws(h.tdb_c.to_numpy())
w_in = 0.621945 * pv_in / (P_ATM - pv_in)
w = {"dry": w_in, "wet": w_in + h.wet_evap_lph.to_numpy() / (3600 * h.mdot_dry_air_kg_s.to_numpy())}
assert (w["wet"] >= w_in - 1e-12).all() and np.array_equal(w["wet"][~wet], w_in[~wet])

out = pd.DataFrame({"hour_utc": h.hour_utc, "tdb_c": h.tdb_c, "rh_pct": h.rh_pct, "w2_mode": h.w2_mode,
                    "t_supply_c": t_sup, "outdoor_dp_c": dew_point(w_in)})
# Sensible-only coil must not reach saturation in mechanically cooled hours.
assert (out.outdoor_dp_c[wet] <= T_SET).all(), "dry sensible-only coil would condense"
for mode in ("wet", "dry"):
    rh_s, dp_s = 100 * p_v(w[mode]) / p_ws(t_sup), dew_point(w[mode])
    assert np.isfinite(rh_s).all() and np.isfinite(dp_s).all() and (rh_s >= 0).all()
    checks = [(rh_s > 100 + 1e-9, "condensation/inconsistency"), (t_sup < T_MIN, "T too low"),
              (t_sup > T_MAX, "T too high"), (dp_s < DP_MIN, "dew point too low"),
              (dp_s > DP_MAX, "dew point too high"), (rh_s > RH_MAX, "RH too high")]
    out[f"{mode}_supply_rh_pct"], out[f"{mode}_supply_dp_c"] = rh_s, dp_s
    out[f"{mode}_recommended_pass"] = ~np.any([c for c, _ in checks], axis=0)
    out[f"{mode}_fail_reason"] = [";".join(r for c, r in checks if c[i]) for i in range(24)]
assert not out.wet_fail_reason.str.contains("inconsistency").any()
assert not out.dry_fail_reason.str.contains("inconsistency").any()
out.round(4).to_csv(HERE / "cooling_mode_feasibility_hourly.csv", index=False)

n_pass = {m: int(out[f"{m}_recommended_pass"].sum()) for m in ("wet", "dry")}
n_joint = int((out.wet_recommended_pass & out.dry_recommended_pass).sum())
full_day = n_pass["wet"] == 24 and n_pass["dry"] == 24
for m in ("wet", "dry"):
    reasons = out[f"{m}_fail_reason"].str.split(";").explode().loc[lambda s: s != ""].value_counts()
    print(f"{m}: pass {n_pass[m]}/24; supply dp {out[f'{m}_supply_dp_c'].min():.2f}..{out[f'{m}_supply_dp_c'].max():.2f} C, "
          f"RH {out[f'{m}_supply_rh_pct'].min():.1f}..{out[f'{m}_supply_rh_pct'].max():.1f}%; fails {reasons.to_dict()}")
print(f"joint pass {n_joint}/24; supply T {t_sup.min():.1f}..{t_sup.max():.1f} C; "
      f"max outdoor dp in cooled hours {out.outdoor_dp_c[wet].max():.2f} C")

# ---------------- One-at-a-time sensitivity (frozen heat duties, water and flags) ----------------
q_in, n_wet, V = h.q_inlet_precool_kw.sum(), int(wet.sum()), h.wet_evap_lph.sum()
rows = []
for name, cop, aux in CASES:
    e_wet = 24 * (IT_KW + P_COMMON) + aux * n_wet
    e_dry = 24 * (IT_KW + P_COMMON) + q_in / cop
    dE = e_dry - e_wet
    rows.append({"case": name, "cop": cop, "wet_aux_kw": aux, "wet_electricity_kwh": e_wet,
                 "dry_electricity_kwh": e_dry, "wet_evap_l": V, "delta_e_kwh": dE,
                 "delta_e_per_l_kwh_per_l": dE / V if V > 0 else np.nan,
                 "peak_wet_kw": IT_KW + P_COMMON + aux * wet.any(),
                 "peak_dry_kw": IT_KW + P_COMMON + h.q_inlet_precool_kw.max() / cop,
                 "wet_pass_hours": n_pass["wet"], "dry_pass_hours": n_pass["dry"], "joint_pass_hours": n_joint,
                 "full_day_recommended_feasible": full_day,
                 "interpretation": "full-day feasible" if full_day else
                 "hypothetical / not a fully recommended-envelope-feasible day"})
s = pd.DataFrame(rows).set_index("case")
b = s.loc["baseline"]
assert abs(b.wet_electricity_kwh - 24690) <= 0.1 and abs(b.dry_electricity_kwh - 26335.5) <= 0.1
assert abs(b.wet_evap_l - 8203.34) <= 0.1 and abs(b.delta_e_kwh - 1645.5) <= 0.1
assert np.isclose(b.peak_dry_kw, h.dry_total_kw.max()) and np.isclose(b.peak_wet_kw, h.wet_total_kw.max())
assert s.loc["cop_low"].dry_electricity_kwh > b.dry_electricity_kwh > s.loc["cop_high"].dry_electricity_kwh
assert s.loc["wet_aux_low"].wet_electricity_kwh < b.wet_electricity_kwh < s.loc["wet_aux_high"].wet_electricity_kwh
s.reset_index().round(5).to_csv(HERE / "cooling_mode_sensitivity_summary.csv", index=False)
pd.set_option("display.width", 220)
print(s.drop(columns=["interpretation"]).round(3).to_string())
print(f"Interpretation: {s.interpretation.iloc[0]}")

"""Step 34: electricity-heat-water balance of wet vs dry inlet conditioning (one day, fixed 1 MW IT).

Run from the repository root (needs a pandas with parquet support):
    ~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/cooling_mode_energy_water.py

Architecture: 100% outdoor-air, once-through. Outdoor air is conditioned to <= 25 C before the servers;
server exhaust carries the IT heat outdoors. Above 25 C the same airstream is either cooled by the Step 20
W2-Air direct evaporative model (wet) or sensibly by a waterless mechanical coil (dry). The coil cools
inlet air only, never the 1 MW IT load. P_COMMON, P_WET_AUX and COP are ILLUSTRATIVE, not calibrated.
Modeled power = IT + selected cooling/air-movement terms; not facility power, PUE or an M0 add-on.
"""
import contextlib
import io
import sys
from math import log
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True  # keep src/experiments untouched
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src" / "experiments"))
with contextlib.redirect_stdout(io.StringIO()):  # silence Step 20's self-test prints
    from w2_air_first import (direct_evap, humidity_ratio, PRESSURE_KPA,  # noqa: E402
                              SUPPLY_MAX_C, SERVER_RISE_C)

SIGNALS = ("/home/nacevedo/m0m1_overnight/06_runs/20261016T0527Z_m0m1/inputs/signals_2023_v1/"
           "site_S1b_springfield_2023.parquet")  # same frozen file as Step 33
DATE = "2023-06-25"
STEP33_EVAP_L, STEP33_WET_HOURS = 8203.3, 21  # step33_results.md (1 decimal)
IT_KW = 1000.0
P_COMMON = 20.0   # kW, illustrative common air movement, both modes
P_WET_AUX = 10.0  # kW, illustrative pump + pressure-loss allowance, only in wet hours
COP = 3.0         # illustrative dry system COP: inlet-air cooling kW_th per kW_e
RECOVERY = 0.8    # optional feed proxy = evap / 0.8 (not withdrawal)
H_FG = 2.45       # MJ/kg, 1 L ~ 1 kg

# ---------------- Weather: same source, QC and conversion as Step 33 ----------------
raw = pd.read_parquet(SIGNALS, columns=["t_utc", "Tdb_C", "RH_raw_pct", "wx_qc_flag"])
g = raw[raw.t_utc.dt.strftime("%Y-%m-%d") == DATE].sort_values("t_utc").reset_index(drop=True)
assert len(g) == 24 and (g.t_utc.to_numpy() == pd.date_range(DATE, periods=24, freq="h", tz="UTC").to_numpy()).all()
assert (g.wx_qc_flag == "ok").all() and np.isfinite(g[["Tdb_C", "RH_raw_pct"]]).all(axis=None)
assert g.Tdb_C.between(-40, 50).all() and g.RH_raw_pct.between(0, 100).all()

rows = []
for t, tdb, rh_pct in zip(g.t_utc, g.Tdb_C.astype(float), g.RH_raw_pct.astype(float)):
    rh = min(rh_pct, 100.0) / 100  # Step 33 convention
    w2 = direct_evap(tdb, rh, it_kw=IT_KW)
    assert w2["mode"] != "infeasible", f"{t}: W2 infeasible"
    hot = tdb > SUPPLY_MAX_C
    assert (w2["mode"] == "wet") == hot

    # Same dry-air flow in both modes (W2 sizes it from cp at supply humidity; kg/h -> kg/s).
    mdot = w2["air_kgda_h"] / 3600.0
    w_in = humidity_ratio(tdb, rh)
    w_supply_wet = w2["evaporation_lph"] / w2["air_kgda_h"] + w_in
    cp_in = 1.006 + 1.86 * w_in  # kJ/(kg dry air K), W2 moist-air convention at inlet humidity
    q_it_wet = mdot * (1.006 + 1.86 * w_supply_wet) * SERVER_RISE_C
    q_it_dry = mdot * cp_in * SERVER_RISE_C  # dry supply keeps inlet humidity

    # Dry coil must stay sensible-only: outdoor dew point <= 25 C (Magnus inverse of W2's pws).
    pv = w_in * PRESSURE_KPA / (0.621945 + w_in)
    dew = 243.04 * log(pv / 0.61094) / (17.625 - log(pv / 0.61094))
    if hot and dew > SUPPLY_MAX_C:
        sys.exit(f"{t}: dew point {dew:.2f} C > 25 C -- dry sensible-only model insufficient")

    q_in = mdot * cp_in * max(tdb - SUPPLY_MAX_C, 0.0)  # kW_th inlet-air precooling, not Q_IT
    evap = w2["evaporation_lph"]
    wet_aux = P_WET_AUX if hot else 0.0
    mech = q_in / COP
    rows.append({"hour_utc": t.strftime("%Y-%m-%dT%H:%MZ"), "tdb_c": tdb, "rh_pct": rh_pct,
                 "w2_mode": w2["mode"], "mdot_dry_air_kg_s": mdot, "q_it_kw": q_it_wet,
                 "q_inlet_precool_kw": q_in, "wet_evap_lph": evap, "wet_feed_lph": evap / RECOVERY,
                 "wet_aux_kw": wet_aux, "dry_mech_kw": mech,
                 "wet_total_kw": IT_KW + P_COMMON + wet_aux, "dry_total_kw": IT_KW + P_COMMON + mech,
                 "dry_condenser_heat_kw": q_in + mech,
                 "_q_it_dry": q_it_dry, "_q_lat": evap * H_FG / 3.6, "_dew": dew})

h = pd.DataFrame(rows)
hot = h.w2_mode == "wet"

# ---------------- Must-pass checks ----------------
n_wet, V_wet = int(hot.sum()), h.wet_evap_lph.sum()
print(f"W2 preflight: wet hours {n_wet}, evaporation {V_wet:.3f} L/day (Step 33: {STEP33_WET_HOURS}, {STEP33_EVAP_L})")
assert n_wet == STEP33_WET_HOURS and abs(V_wet - STEP33_EVAP_L) <= 0.05, "Step 33 anchor mismatch"
assert np.allclose(h.q_it_kw, IT_KW, rtol=1e-12)
assert np.allclose(h._q_it_dry, IT_KW, rtol=0.01)  # same airflow, slightly drier supply air
c = h[~hot]
assert (c.wet_total_kw == c.dry_total_kw).all() and (c.wet_evap_lph < 1e-8).all()
assert (c.q_inlet_precool_kw == 0).all() and (c.dry_mech_kw == 0).all() and (c.wet_aux_kw == 0).all()
assert (h[hot].q_inlet_precool_kw > 0).all() and (h[hot].wet_evap_lph > 0).all()

lat_err = ((h._q_lat - h.q_inlet_precool_kw) / h.q_inlet_precool_kw)[hot]
max_lat = lat_err.abs().max()
assert max_lat <= 0.10, f"latent vs sensible discrepancy {max_lat:.1%} > 10%: investigate"

E = {m: h[f"{m}_total_kw"].sum() for m in ("wet", "dry")}  # dt = 1 h
for m in E:
    assert np.isclose(E[m] - h[f"{m}_total_kw"].sub(IT_KW).sum(), 24 * IT_KW)
dE, dV = E["dry"] - E["wet"], V_wet
assert np.isclose(dE, h.dry_mech_kw.sum() - h.wet_aux_kw.sum())  # only mode-specific terms differ
cop_star = h.q_inlet_precool_kw.sum() / (P_WET_AUX * n_wet)

h.drop(columns=[c for c in h if c.startswith("_")]).round(4).to_csv(
    HERE / "cooling_mode_energy_water_hourly.csv", index=False)

summary = pd.DataFrame({
    "mode": ["wet", "dry"],
    "modeled_kwh": [E["wet"], E["dry"]],
    "cooling_air_kwh": [E["wet"] - 24 * IT_KW, E["dry"] - 24 * IT_KW],
    "evap_l": [V_wet, 0.0],
    "peak_kw": [h.wet_total_kw.max(), h.dry_total_kw.max()],
})
print(summary.round(2).to_string(index=False))
print(f"Q_in day {h.q_inlet_precool_kw.sum():.1f} kWh_th; dry condenser heat {h.dry_condenser_heat_kw.sum():.1f} kWh_th; "
      f"max dew point {h._dew.max():.2f} C; max hot-hour dew point {h._dew[hot].max():.2f} C")
print(f"DeltaE = {dE:.2f} kWh, DeltaV = {dV:.2f} L, DeltaE/DeltaV = {dE / dV:.5f} kWh/L avoided, "
      f"COP* = {cop_star:.2f}, max |Q_lat-Q_in|/Q_in (wet) = {max_lat:.2%} (signed range "
      f"{lat_err.min():+.2%} .. {lat_err.max():+.2%})")
print("PASS. COP, P_common and P_wet_aux illustrative; evaporation is W2 process loss, not withdrawal.")

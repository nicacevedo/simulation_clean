# EDA 02 — Reduced surrogates of W2-Air process evaporation

Run from the repo root with `python dc_resource_sim/eda/water_models/fit_simple_water.py`.
The **target is simulated W2-Air process evaporation** from Step 20 `direct_evap`, left unchanged. C0 and C1 are surrogates of that simulator. **This is not water-meter validation**, and W0's 0.5 L/kWh proxy is neither refit nor ranked against it. Feed is not fitted because it is just F_evap/η.

**Fixed:** 1 MW IT, f_air 1, supply 25 °C, ε_max 0.8, ΔT_server 15 °C (Fig 05 varies only ΔT_server).

## Fig 04 — `04_w2_air_surrogate_fit.png`: does C1 reproduce W2-Air?

The fit uses 14 training states at 18–31 °C and RH 20 %, all of them feasible. The held-out set is 32–38 °C × RH 10–90 %: 119 states, of which 37 are feasible and scored, and 82 are infeasible and excluded (N/A, not 0).

| Model | Coefficient | Held-out MAE (L/h) | P95 (L/h) | Max (L/h) | Train max (L/h) |
|---|---|---|---|---|---|
| C0 = c0·P | c0 = 0.14688 L/kWh IT | 767.7 | 1,117.8 | 1,117.8 | 439.9 |
| C1 = β·P·(T−25)₊ | β = 0.09788 L/(kWh IT·°C) | 3.42 | 7.82 | 7.82 | 0.51 |

These errors are in L/h at 1 MW. Load scaling at 800 and 1,200 kW (35/30 and 38/20) is exactly proportional in W2. C1's error scales the same way, from +3.1 to +9.4 L/h.

- **Takeaway:** Under fixed controls, one physics-derived coefficient reproduces W2-Air evaporation to within 0.6 % on hotter, unseen states, and β falls in the expected 0.097–0.098 range. C0 cannot shut off in dry mode, overpredicting by 147 L/h. It also cannot follow temperature, underpredicting by up to 1,118 L/h at 38 °C. C1 has a small positive bias that grows with temperature, because W2's per-degree intensity eases slightly (≈0.0979 at 30 °C to ≈0.0973 at 38 °C).
- **Limitation:** C1 carries no feasibility information. 82 of the 119 held-out states (69 %) are infeasible, and only W2's humidity check identifies them. A near-perfect fit shows the simulator can be simplified, not that C1 predicts real water.

## Fig 05 — `05_airflow_control_transfer.png`: where the fitted law stops transferring

Conditions are 30 °C / 30 % RH and 1 MW. `SERVER_RISE_C` is overridden temporarily and restored in `try/finally`, so the source is unchanged.

| ΔT_server | W2 (L/h) | ×W2(15) | C1 frozen (L/h), error | β₁₅·15/ΔT (L/h), error |
|---|---|---|---|---|
| 10 °C | 734.05 | 1.500 | 489.42, −244.6 | 734.14, +0.09 |
| 15 °C | 489.37 | 1.000 | 489.42, +0.06 | 489.42, +0.06 |
| 20 °C | 367.02 | 0.750 | 489.42, +122.4 | 367.07, +0.04 |

- **Takeaway:** A temperature-only coefficient does not transfer when the allowed server-air rise changes. With the same IT heat, the required airflow and evaporation scale as 1/ΔT_server, so the frozen C1 is off by −33 % to +33 %. The analytical correction β(ΔT) = β₁₅·15/ΔT, which is not fitted, recovers W2 within 0.1 L/h. The heat/airflow relation explains both the direction and the size of the change.
- **Limitation:** ΔT_server is an assumed control. The model computes neither fan electricity nor whether return-air limits allow that rise. Supply target, ε_max and recovery were held fixed, and changing them would move β too.

## Conclusion

For a fixed direct-air configuration, W2-Air evaporation reduces to a W1-type model, **F_evap ≈ 0.0979 · (15/ΔT_server) · P_IT · (T_db − 25)₊**, plus W2's separate feasibility flag. What W2 adds is (i) feasibility, which depends on humidity, and (ii) how the coefficient responds to operating assumptions. Nothing here ranks models against measured water.

**Stop here.** The next separate milestone is either a location-matched real-weather day replay with unchanged parameters, or a water-meter boundary audit.

---

# EDA 03 — Real-weather replay (frozen models)

Run from the repo root with `~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/replay_observed_weather.py`. The default `python` can't read parquet.

**Inputs:** measured ESIF hourly dry-bulb, RH, and IT power (`esif_facility_hourly.parquet`, read only; only hours with `valid_weather & valid_it`). Prineville weather is not in the repo, so ESIF (Golden, CO) is used. **The cooling system is hypothetical**, because ESIF is not direct-evaporative.

**Frozen:** W2-Air Step 20 parameters (supply 25 °C, ε_max 0.8, ΔT_server 15 °C) and C1 β = 0.09788 from EDA 02. Nothing is refit. Feed = evaporation / 0.8, using the illustrative Step 25 recovery.

**Week:** Jul 24–30 2023 (UTC), 168/168 valid hours. It is the complete 2023 week with the most wet hours. Conditions were Tdb 19.0–36.1 °C, RH 21–87 %, and measured IT 679–2,562 kW (2023 median ≈1.9 MW).

## Fig 06 — `06_observed_weather_replay.png`

| Metric | Replay week | All 2023 valid hours (7,990) |
|---|---|---|
| Hours dry / wet / infeasible | 76 / 92 / **0** | 7,214 / 776 / **0** |
| Max needed wet-bulb effectiveness (limit 0.80) | 0.721 | 0.765 |
| C1 − W2 MAE, max \|err\| (L/h) | 0.79, 10.14 (bias +0.44) | 0.14, 15.24 |
| Total W2 evaporation, C1 total | 71.34 m³, 71.41 m³ (+0.10 %) | 588.4 m³, 588.9 m³ |
| Peak W2 evaporation, peak feed at η = 0.8 | 2,370 L/h, 2,962 L/h (Jul 25 21:00 UTC) | — |

- **Takeaway:** On real hourly temperature–humidity combinations and measured, varying IT load, frozen C1 tracks W2-Air hour by hour (MAE < 1 L/h against a peak of 2.4 m³/h), and the weekly total agrees to 0.1 %. No hour in 2023 is infeasible, so in this climate the full-week and annual totals are valid without a fallback. The surrogate's usefulness holds beyond the constructed grid.
- **Where the water is:** Evaporation occurs only in the 776 wet hours, about 10 % of the year. This one week accounts for 12 % of annual evaporation. Water demand is concentrated in hot afternoons, and the peak feed of about 3 m³/h is set jointly by peak temperature and peak IT load.
- **Limitation:** The feasibility result is a property of a dry climate. The margin is thin, however: the worst 2023 hour needs ε = 0.765 against the 0.80 limit. The measured IT is ESIF's load, while the cooling architecture is assumed. None of this is a water-meter comparison.

## Decision for Experiment B

The plan's gate was "substantial infeasibility or water variability." There is no infeasibility at a 25 °C supply target, but the effectiveness margin is small (0.035). A **lower** supply target (23 °C) is therefore the only direction likely to create infeasible hours here. Experiment B is worth running only to locate that feasibility edge, and it must report server inlet limits. Otherwise, the next step is the Prineville measurement-boundary audit.

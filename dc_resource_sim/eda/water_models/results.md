# Water-model EDA (after Step 26) — results

Run from the repository root: `python dc_resource_sim/eda/water_models/plot_model_responses.py`.
It reuses Step 20 `direct_evap`, Step 18 `tower`, and Step 26 `run_day` without changing them, and asserts every anchor listed in `eda_context/eda01.md`. All of those checks pass.
These are **conditional model responses, not validated predictions.** None of these quantities is measured water.

## Fig 1 — `01_air_weather_feasibility.png` (W2-Air, process evaporation)
- **Varied:** T_db 18–38 °C (1 °C steps) × RH 10–90 % (5 % steps), at 1 MW IT. **Fixed:** supply target 25 °C, ε_max 0.8, ΔT_server 15 °C, f_air 1, 101.325 kPa.
- **Learned:** Of 357 states, 136 are dry (0), 113 are wet and 108 are infeasible (N/A, hatched). **Inside the feasible region, intensity depends only on T_db, not RH.** The spread across RH at a fixed T is < 0.001 %. Intensity is ≈ 0.098 L/kWh IT per °C above the supply target: 0.196 at 27 °C, 0.489 at 30 °C, 0.975 at 35 °C and 1.265 at 38 °C. The cause is that, with a fixed supply temperature on an adiabatic line, Δω ≈ c_p(T_in − T_sup)/h_fg. **Humidity decides only feasibility.** The maximum feasible RH drops from 80 % at 27 °C to 55 % at 30 °C and 20 % at 38 °C. The 30/30 and 30/50 cases therefore need the same water but different effectiveness.
- **Limits:** The result depends on the fixed-supply-target control rule. A controller that over-cools, or a different ε_max, would change it. No fallback (dry-cooler or chiller) exists for infeasible states, so the water model is undefined there.

## Fig 2 — `02_heat_water_by_architecture.png` (two architectures, two boundaries)
- **Varied:** (A) IT = server-air heat 0.5–1.5 MW at three fixed weather states. (B) Tower wet duty Q_wet 0.6–1.8 MW_th. **Fixed:** (A) Step 20 defaults. (B) α_lat 0.8, COC 4.
- **Learned:** Both models are straight lines through zero. Weather sets the slope in direct-air: 0, 0.48937 and 0.97504 L/kWh IT. In the tower, α_lat and COC set it: evaporation 1.1755 and makeup 1.5673 L/kWh_th, which gives 1,410.6 and 1,880.8 L/h at 1,200 kW_th. The W0 proxy (0.5) nearly matches W2-Air at 30 °C/30 % by coincidence. It is 0.5 L/kWh IT under **every** weather, while W2-Air spans 0 to about 1.3 L/kWh IT.
- **Sensitivity (no plot), 30 °C/30 %:** Reducing ΔT_server from 15 to 10 °C multiplies airflow and evaporation by 1.500. Changing η from 1.0 to 0.8 multiplies **feed** by 1.250 and leaves evaporation unchanged. Both are assumed equipment or control settings.
- **Limits:** Linearity follows from the model structure: no part-load effects, fan heat or recirculation. Q_wet is tower duty, not IT power or M0, so the two panels must not be merged into one coefficient.

## Fig 3 — `03_constructed_day_profiles.png` (Step 26 day, constructed weather)
- **Varied:** Hourly weather only: 20/50 for hours 00–07, 30/30 for 08–15 and 35/30 for 16–23. **Fixed:** IT 1 MW, M0 k = 1.0471 (25,130.4 kWh/day), w0 0.5, η 0.8.
- **Learned:** With constant electricity, W2 water runs 0 → 489 → 975 L/h for evaporation and 0 → 612 → 1,218.8 L/h for feed. Day totals are evaporation 11,715.2 L, feed 14,644.0 L and reject 2,928.8 L. W0 is a flat 12,000 L/day. The **daily volumes of W0 and W2 evaporation are within 2.4 %, yet the hourly profiles have nothing in common**: W2 is zero for 8 h, and at its peak W2 evaporation is 1.95× the W0 rate and W2 feed is 2.44× it. Daily-volume agreement therefore says nothing about peak water-supply capacity. F_feed = F_evap + F_reject holds every hour.
- **Test, not a figure:** Replacing hour 10 with 30 °C/70 % makes that hour infeasible, so the full-day W2 total is N/A rather than a partial sum.
- **Limits:** This is constructed weather, not Prineville. W0 and W2 have different water boundaries, and the overlay compares model behavior, not prediction error.

## Not done / not validated
- The optional Fig 4 (Step 15 cost vs grid-water) was skipped because Figs 1–3 tell the physical story. That trade-off is already documented in `s7_water_schedule.py` (122.5 L/day modeled advantage, reversible by a ±0.0239 L/kWh patterned factor error).
- No site withdrawal, WUE, measured water error or marginal grid-water saving is inferred. No fan or chiller power was added to M0.

**Suggested next step (pick one):** a Prineville measurement-boundary audit, **or** a single location-matched weather-day replay with unchanged parameters. Fig 1 implies the replay's water will be governed by hours above 25 °C, and its validity by how many hours are humid and infeasible.

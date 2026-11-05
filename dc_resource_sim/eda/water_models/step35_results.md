# Step 35 results — recommended inlet-air screen and equipment sensitivity

**Inputs and screen.** The only input is the Step 34 hourly CSV (Springfield, 2023-06-25 UTC); all Step 34 anchors match. The screen is the ASHRAE 2021 A1–A4 *recommended* envelope: 18–27 °C, dew point −9 to 15 °C, RH ≤ 70%, noncondensing. Supply air is outdoor air in free-cooling hours and 25 °C in the 21 cooled hours. The dry coil is sensible-only, with a maximum outdoor dew point of 21.0 °C (< 25 °C, so no condensation). Outputs are `cooling_mode_feasibility_hourly.csv` and `cooling_mode_sensitivity_summary.csv`.

| Mode | Pass hours | Fail: dew point > 15 °C | Fail: RH > 70% | Supply dew point (°C) |
|---|---|---|---|---|
| wet | 0 / 24 | 24 | 15 | 15.5–21.9 |
| dry | 8 / 24 (16–23 UTC) | 16 | 7 | 12.0–21.0 |
| joint | 0 / 24 | — | — | — |

| Case | COP | Wet aux (kW) | E_wet (kWh) | E_dry (kWh) | ΔE (kWh) | R (kWh/L) |
|---|---|---|---|---|---|---|
| cop_low | 2 | 10 | 24,690.0 | 27,263.3 | 2,573.3 | 0.314 |
| **baseline** | **3** | **10** | **24,690.0** | **26,335.5** | **1,645.5** | **0.201** |
| cop_high | 5 | 10 | 24,690.0 | 25,593.3 | 903.3 | 0.110 |
| wet_aux_low | 3 | 5 | 24,585.0 | 26,335.5 | 1,750.5 | 0.213 |
| wet_aux_high | 3 | 20 | 24,900.0 | 26,335.5 | 1,435.5 | 0.175 |

All cases use ΔV = 8,203.34 L. Every case is labelled **hypothetical / not a fully recommended-envelope-feasible day**.

**Conclusion.** Step 34 cannot be interpreted as a full-day feasible trade-off under the recommended envelope: no hour passes in both modes, and the binding constraint is always humidity, never temperature. Direct evaporation fails all 24 hours, and the dry coil passes only 8 because it preserves the outdoor dew point. Even the three untreated free-air hours fail, with an outdoor dew point of 19.4–20.6 °C. The conditional electricity penalty for avoiding W2 evaporation stays positive in all five cases (0.11–0.31 kWh/L), driven mainly by COP; the wet auxiliary changes R by at most 0.03 kWh/L. Neither parameter can fix the humidity failures, so the next question is how to represent humidity conditioning or a different air-handling architecture.

# Step 21 — Boundary and units audit (one reference case)

Hypothetical 1 MW facility, constant IT load, `dt = 1 h`; 24 h totals assume load (and, for W2, inlet air) held constant. No new model, fit, or data.

## Reference table

| Quantity | 1 hour | 24 h if held constant | Unit / boundary | Evidence status | Source |
|---|---:|---:|---|---|---|
| IT electrical input | 1,000 | 24,000 | kW / kWh, IT meter | Hypothetical input | — |
| M0 facility electrical input | 1,047.1 | 25,130.4 | kW / kWh, facility meter prediction | Derived from assumed load and fitted ESIF `k = 1.0471` | `s7_water_schedule.py`, `s0`–`s2` |
| M0 aggregate non-IT electrical input | 47.1 | 1,130.4 | kW / kWh, facility minus IT | Derived residual; **not identified** as chiller/fan/pump | — |
| Idealized heat produced by IT | 1,000 | 24,000 | kW / kWh thermal | Steady-state assumption, **not tower duty** | — |
| W0 direct consumption | 500 | 12,000 | L/h / L, site consumption basis | Assumed `w0 = 0.5 L/kWh IT`, unvalidated | `m0_first.py` |
| W2-Air evaporation (Step 20, 30 °C / 30% RH) | 489.4 | 11,745 | L/h / L, evaporative air stage | Conditional physics scenario | `w2_air_first.py` |
| W2-Tower evaporation (Step 17) | 1,469.4 | 35,265.3 | L/h / L, open cooling tower | Conditional, **different** architecture | `w2_tower_first.py` |
| W2-Tower makeup (Step 17) | 1,959.2 | 47,020.4 | L/h / L, cooling-tower intake | Evaporation + blowdown; **not** site consumption | `w2_tower_first.py` |

Roundoff: Step 20's script gives 489.366 L/h, so 24 h = 11,744.8 L. The Step 21 spec's ~11,746 comes from multiplying the rounded 489.4 × 24. Step 17 values are the script's printed daily totals; hourly evaporation is 35,265.3 / 24.

The W0 (500 L/h) vs W2-Air (489.4 L/h) closeness is coincidental and validates neither.

## Five checks

1. **Electrical identity — pass.** `P_DC = P_IT + P_nonIT` (1,047.1 = 1,000 + 47.1) and `E = P·dt` (×24). M0 `P_nonIT` is an aggregate residual only, not a cooling-component estimate.
2. **Heat boundary — pass.** `Q_IT ≈ P_IT` (steady state). No script uses M0 facility power as IT heat. Tower duty is always declared separately: Step 17 sets 1,000 kW thermal tower duty; Step 18 adds an explicit routing fraction `f_ch` and compressor heat (`Q_wet = f_ch·E_IT·(1 + 1/COP)`).
3. **Water basis — pass.** W0 = direct consumption; Step 20 = evaporation; Step 17 = evaporation and makeup. They are reported in separate rows and never added or equated.
4. **Architecture — pass.** W2-Tower and W2-Air are mutually exclusive archetypes; `COC` and the condenser-heat formula do not appear in `w2_air_first.py`.
5. **Cross-model compatibility — needs correction before any combination.** Step 18's all-chiller case (1,000 kW chiller load, `COP = 5`) implies 200 kW compressor electricity, > M0's total 47.1 kW non-IT. M0 + that chiller example cannot be one consistent facility. Each stand-alone demo is correct; the combination is not. Step 20 fan electricity is likewise not identified from M0.

## Evidence categories

- **Measured / fitted:** M0 coefficient `k = 1.0471` (ESIF-derived, applied to a hypothetical facility).
- **Assumed:** 1 MW IT load, `w0`, cooling architecture, tower duty, COC, COP, airflow, server air-temperature rise, evaporative effectiveness, inlet air states, pressure, water temperature.
- **Not identified:** actual cooling electricity by component, heat routing, site water intake/withdrawal, groundwater extraction.

## Interpretation

Facility electricity ≠ IT heat ≠ heat rejected by wet equipment, and evaporation ≠ process makeup ≠ facility water intake (not interchangeable, though some can coincide numerically under specific assumptions).

> M0 predicts aggregate facility electricity; the simple IT-heat balance approximates the IT thermal source; W0 represents assumed direct consumption; W2-Air predicts stage evaporation; W2-Tower predicts stage evaporation and makeup. None determines actual site water withdrawal or the causal change in cooling electricity without additional equipment and supply boundaries.

M0 cannot be combined directly with an independent cooling-electricity model because its non-IT term is a fitted aggregate residual from a different facility (ESIF); any component model (chiller, fans) must fit inside that residual, and Step 18's chiller does not.

## Assessment after EDA 02

EDA 02 is successful. I would stop fitting new water models for now and test the existing models under more informative operating conditions.

The two figures establish something valuable: our detailed W2-Air model can be reduced to a much simpler analytical relationship under fixed assumptions. The remaining modeling challenges are mainly cooling feasibility, operating controls, and actual measurement boundaries, rather than a more complicated evaporation equation.

## 1. What is newly established?

[Linear regression with statistics on top of a scatterplot](https://images.openai.com/static-rsc-4/8kMMLAPyQ5Iv2gXK4u94qSORSwG0pTkoWLr7iIYz3ooKr7k7JF5xuGuLVbtzSwb7iPJ5zlDaBnZw7lqqBKusu4ulr2J8zwcDUh68FeMk5buRAfYj9QaLmUp81AgTeUkVc9gH7bsrn6IjcDSCeSFr4fFmXMilCmEyDYELCY4hrDo?purpose=inline)

Figure 04 — A simple temperature model reproduces W2-Air

C1's held-out MAE is 3.42 L/h, compared with 767.7 L/h for C0. This strongly supports the reduced model within the simulated physical assumptions.

[Inverse Proportion | Definition, Examples, Graph, Formula](https://images.openai.com/static-rsc-4/WI6O8eaTEWV2ZHl0_q5GEQ47MCOnp_Gxe_6FABXrdHow8mm7Y_olpN0MEtqWoLKXFCpAXMnrc90Onn8V_vOll-ER2Iz_cB73nXNTJ_oV9ulwYBUbk-DiFP5v5wGwL0s5Nu_A5vkiux4B95hiFeLmDP7Squ6BJt9YJc8rS0Last4?purpose=inline)

Figure 05 — Heat-transfer assumptions determine the coefficient

Changing the server-air temperature rise from 15°C to 10°C increases evaporation by 50%. The inverse-temperature-rise correction explains this change almost exactly.

The resulting reduced model is:

\\[ \boxed{ \dot V^{evap} \approx 0.0979 \frac{15}{\Delta T\_{server}} P^{IT}(T\_{db}-25)\_+ } \\]

with power in kW, temperatures in °C, and evaporation in L/h.

Three important qualifications:

- This applies to the current direct-evaporative architecture and control assumptions, not data centers generally.
- C1 requires a separate cooling-feasibility check. In the test, 82 of 119 states were infeasible.
- The 37 feasible held-out points contain only seven distinct dry-bulb temperatures. Since W2's evaporation is nearly RH-independent within the feasible region, these are not 37 independent tests of different evaporation relationships.

The model's accuracy is largely explained by the equations used to generate its targets. It is not empirical validation.

## 2. Which water model should we retain?

| Model                                  | Current assessment                                                                    | Role                          |
| -------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------- |
| W0 — Constant WUE                      | Too simple to capture changing cooling conditions                                     | Essential baseline            |
| C1 — Temperature excess                | Best reduced evaporation model so far                                                 | Fast scenario calculations    |
| C1 + inverse-\\(\Delta T\\) correction | Explains variations in assumed server airflow                                         | Useful reduced physical model |
| W2-Air                                 | Required for psychrometric feasibility and more detailed operating-state calculations | Physical reference            |
| W2-Tower                               | Separate architecture, not directly comparable                                        | Retain unchanged              |

I recommend preserving C1 and W2-Air together. We do not need another regression or ML model.

The strongest conclusion is that the main complexity of W2-Air is currently in determining whether cooling is feasible, not in predicting evaporation once the operating state is fixed.

## 3. Next experiments: only two small additions

### Experiment A — Real-weather replay

Highest priority

Question: How often does the physical model predict dry cooling, wet cooling, or infeasibility under actual hourly weather?

Use one verified week of hourly dry-bulb temperature and RH from a single location. Prefer Prineville weather if readily available, keeping its cooling assumptions explicitly hypothetical.

Do not refit any coefficients.

Figure 06 — Weather, cooling regime, and water demand

One figure with two panels: observed weather and cooling operating mode above; C1 versus W2-Air evaporation/feed below. Mark infeasible hours separately.

Schematic layout only, not actual weather or model output.

Report just four metrics: hours dry/wet/infeasible, C1-versus-W2 error on feasible hours, total evaporation for fully feasible periods, and peak treatment feed.

Why it matters: This tests whether the simple surrogate remains useful over real combinations of temperature and humidity, rather than an artificial grid.

If any hour is infeasible, do not claim a valid full-week cooling-water total without a fallback.

### Experiment B — Operating assumptions and model validity

Question: Which assumed operating parameter most changes evaporation or cooling feasibility?

We already tested \\(\Delta T\_{server}\\). The next useful quantity is the supply-temperature target, which influences both evaporation demand and whether the evaporative cooler can satisfy the thermal constraint.

Figure 07 — Supply temperature versus water and feasibility

At fixed IT load, compare a few illustrative supply-temperature targets (23, 25, 27°C). Show predicted evaporation and the fraction of real-weather hours that remain feasible.

Conceptual trends only. Actual results depend on weather, controls, and equipment assumptions.

This experiment can establish a more meaningful water–cooling trade-off than introducing an arbitrary nonlinear regression.

It must also report the assumed server thermal limits; raising supply temperature cannot be treated as an unconstrained water-saving control.

## 4. Should we increase model complexity?

Not yet. We have enough model complexity to generate physically interpretable scenarios. We lack enough evidence to identify additional equipment parameters.

My recommended order is:

1. Run Experiment A using real weather, with all parameters frozen.
2. If the model predicts substantial infeasibility or water variability, run Experiment B.
3. Then return to the Prineville measurement-boundary audit, before calibrating site water demand.

I would postpone fan-power laws, recirculation, part-load cooling performance, detailed water-treatment modeling, and additional regression models.

These become valuable when there is either measured information to constrain them or a clear operational question they answer.

## 5. Final research assessment

We have established an increasingly useful model hierarchy:

\\[ \text{W0} \rightarrow \text{C1} \rightarrow \text{C1 + operating correction} \rightarrow \text{W2-Air + feasibility}. \\]

What is not yet established is which model best predicts actual water consumption.

For that, we need observations of facility water use, not further fits to W2 simulations.

My recommendation: Do one real-weather replay next. It is the smallest experiment that moves us beyond constructed operating states while keeping the physics unchanged. Add the supply-temperature sensitivity only if it materially clarifies the feasible operating range. Then prioritize real measurement boundaries over additional model complexity.

---

Context 1:

## Assessment after EDA 02

EDA 02 is successful. I would stop fitting new water models for now and test the existing models under more informative operating conditions.

The two figures establish something valuable: our detailed W2-Air model can be reduced to a much simpler analytical relationship under fixed assumptions. The remaining modeling challenges are mainly cooling feasibility, operating controls, and actual measurement boundaries, rather than a more complicated evaporation equation.

## 1. What is newly established?

[Linear regression with statistics on top of a scatterplot](https://images.openai.com/static-rsc-4/8kMMLAPyQ5Iv2gXK4u94qSORSwG0pTkoWLr7iIYz3ooKr7k7JF5xuGuLVbtzSwb7iPJ5zlDaBnZw7lqqBKusu4ulr2J8zwcDUh68FeMk5buRAfYj9QaLmUp81AgTeUkVc9gH7bsrn6IjcDSCeSFr4fFmXMilCmEyDYELCY4hrDo?purpose=inline)

Figure 04 — A simple temperature model reproduces W2-Air

C1's held-out MAE is 3.42 L/h, compared with 767.7 L/h for C0. This strongly supports the reduced model within the simulated physical assumptions.

[Inverse Proportion | Definition, Examples, Graph, Formula](https://images.openai.com/static-rsc-4/WI6O8eaTEWV2ZHl0_q5GEQ47MCOnp_Gxe_6FABXrdHow8mm7Y_olpN0MEtqWoLKXFCpAXMnrc90Onn8V_vOll-ER2Iz_cB73nXNTJ_oV9ulwYBUbk-DiFP5v5wGwL0s5Nu_A5vkiux4B95hiFeLmDP7Squ6BJt9YJc8rS0Last4?purpose=inline)

Figure 05 — Heat-transfer assumptions determine the coefficient

Changing the server-air temperature rise from 15°C to 10°C increases evaporation by 50%. The inverse-temperature-rise correction explains this change almost exactly.

The resulting reduced model is:

\\[ \boxed{ \dot V^{evap} \approx 0.0979 \frac{15}{\Delta T\_{server}} P^{IT}(T\_{db}-25)\_+ } \\]

with power in kW, temperatures in °C, and evaporation in L/h.

Three important qualifications:

- This applies to the current direct-evaporative architecture and control assumptions, not data centers generally.
- C1 requires a separate cooling-feasibility check. In the test, 82 of 119 states were infeasible.
- The 37 feasible held-out points contain only seven distinct dry-bulb temperatures. Since W2's evaporation is nearly RH-independent within the feasible region, these are not 37 independent tests of different evaporation relationships.

The model's accuracy is largely explained by the equations used to generate its targets. It is not empirical validation.

## 2. Which water model should we retain?

| Model                                  | Current assessment                                                                    | Role                          |
| -------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------- |
| W0 — Constant WUE                      | Too simple to capture changing cooling conditions                                     | Essential baseline            |
| C1 — Temperature excess                | Best reduced evaporation model so far                                                 | Fast scenario calculations    |
| C1 + inverse-\\(\Delta T\\) correction | Explains variations in assumed server airflow                                         | Useful reduced physical model |
| W2-Air                                 | Required for psychrometric feasibility and more detailed operating-state calculations | Physical reference            |
| W2-Tower                               | Separate architecture, not directly comparable                                        | Retain unchanged              |

I recommend preserving C1 and W2-Air together. We do not need another regression or ML model.

The strongest conclusion is that the main complexity of W2-Air is currently in determining whether cooling is feasible, not in predicting evaporation once the operating state is fixed.

## 3. Next experiments: only two small additions

### Experiment A — Real-weather replay

Highest priority

Question: How often does the physical model predict dry cooling, wet cooling, or infeasibility under actual hourly weather?

Use one verified week of hourly dry-bulb temperature and RH from a single location. Prefer Prineville weather if readily available, keeping its cooling assumptions explicitly hypothetical.

Do not refit any coefficients.

Figure 06 — Weather, cooling regime, and water demand

One figure with two panels: observed weather and cooling operating mode above; C1 versus W2-Air evaporation/feed below. Mark infeasible hours separately.

Schematic layout only, not actual weather or model output.

Report just four metrics: hours dry/wet/infeasible, C1-versus-W2 error on feasible hours, total evaporation for fully feasible periods, and peak treatment feed.

Why it matters: This tests whether the simple surrogate remains useful over real combinations of temperature and humidity, rather than an artificial grid.

If any hour is infeasible, do not claim a valid full-week cooling-water total without a fallback.

### Experiment B — Operating assumptions and model validity

Question: Which assumed operating parameter most changes evaporation or cooling feasibility?

We already tested \\(\Delta T\_{server}\\). The next useful quantity is the supply-temperature target, which influences both evaporation demand and whether the evaporative cooler can satisfy the thermal constraint.

Figure 07 — Supply temperature versus water and feasibility

At fixed IT load, compare a few illustrative supply-temperature targets (23, 25, 27°C). Show predicted evaporation and the fraction of real-weather hours that remain feasible.

Conceptual trends only. Actual results depend on weather, controls, and equipment assumptions.

This experiment can establish a more meaningful water–cooling trade-off than introducing an arbitrary nonlinear regression.

It must also report the assumed server thermal limits; raising supply temperature cannot be treated as an unconstrained water-saving control.

## 4. Should we increase model complexity?

Not yet. We have enough model complexity to generate physically interpretable scenarios. We lack enough evidence to identify additional equipment parameters.

My recommended order is:

1. Run Experiment A using real weather, with all parameters frozen.
2. If the model predicts substantial infeasibility or water variability, run Experiment B.
3. Then return to the Prineville measurement-boundary audit, before calibrating site water demand.

I would postpone fan-power laws, recirculation, part-load cooling performance, detailed water-treatment modeling, and additional regression models.

These become valuable when there is either measured information to constrain them or a clear operational question they answer.

## 5. Final research assessment

We have established an increasingly useful model hierarchy:

\\[ \text{W0} \rightarrow \text{C1} \rightarrow \text{C1 + operating correction} \rightarrow \text{W2-Air + feasibility}. \\]

What is not yet established is which model best predicts actual water consumption.

For that, we need observations of facility water use, not further fits to W2 simulations.

My recommendation: Do one real-weather replay next. It is the smallest experiment that moves us beyond constructed operating states while keeping the physics unchanged. Add the supply-temperature sensitivity only if it materially clarifies the feasible operating range. Then prioritize real measurement boundaries over additional model complexity.

---

Context 2:

I've prepared a concise Markdown context file for your local agent.

Download EDA 03 — Real-Weather Replay (.md)

### What the agent should do

One experiment, one figure, and minimal repository changes.

- Reuse existing measured ESIF dry-bulb temperature and relative humidity for one complete week.
- Compare the frozen C1 reduced model against W2-Air, without refitting either.
- Visualize observed weather, predicted evaporation, and infeasible cooling hours.
- Report cooling-mode counts, surrogate error, peak evaporation, and applicable water totals.

### Expected changes

```
dc_resource_sim/eda/water_models/
├── replay_observed_weather.py       # New
├── figures/
│   └── 06_observed_weather_replay.png  # New
└── results_fit.md                  # Append results
```

The instructions explicitly preserve Steps 00–26, require verified weather data, and prevent infeasible hours from being counted as zero-water operation.

The goal is to determine whether our simplified evaporation model remains useful under actual weather variability—not to introduce more physics or claim measured water-prediction accuracy.
# Water-model EDA 02 — Can a simple model reproduce W2-Air, and when does it fail?

**Based on:** `eda1.zip` (`eda1/water_models/results.md`, `plot_model_responses.py`, and the three figures). The previous EDA is **complete**; preserve its code and figures.

## Goal

Determine whether a reduced weather-dependent **evaporation** model can reproduce the existing physical W2-Air model over a defined operating range, and identify which *assumed control* breaks that approximation. This is an **emulator/surrogate exercise against simulated W2-Air outputs**, not water-meter validation or evidence of which model predicts real data-center consumption best.

**Only two new figures; one short Python script and one results note. No model refits using Prineville data, no optimization, no new source datasets.**

## 1. Established from EDA 01 (do not replot)

- Figure 1: On the 18–38°C, 10–90% RH grid, 136/357 states are dry, 113 wet and 108 infeasible. Under the **fixed 25°C supply target**, evaporation intensity in feasible wet states is approximately temperature-driven (RH spread <0.001% at fixed dry bulb). RH importantly affects feasibility; it is *not* generally irrelevant.
- Figure 2: W2-Air scales linearly with IT heat when weather, heat routing and server-air rise are fixed. At 30°C/30% RH, it is 0.48937 L/kWh IT; at 35°C/30% RH, 0.97504 L/kWh IT. The Step 18 tower branch is separately linear in wet thermal duty: 1.1755 L/kWh_th evaporation and 1.5673 L/kWh_th makeup with the selected latent-ratio/COC assumptions. **Do not fit one branch to the other.**
- Figure 3: The constructed day has W2 evaporation 11,715.2 L, feed 14,644 L, reject 2,928.8 L, and peak feed 1,218.8 L/h. W0's 12,000 L daily direct-consumption **proxy** is a different water category, not a calibration measurement.
- Under fixed equipment, $\Delta T_{server}$ from 15°C to 10°C raises modeled airflow/evaporation by a factor 1.5, while treatment recovery $\eta$ affects feed, not evaporation.

## 2. Model definitions — compare the **same target**

Use *simulated W2-Air process evaporation* $F^{evap}$ (L/h) as the common target in **both** simplified candidates. **Do not** silently relabel the original $w_0=0.5$ onsite-direct-consumption proxy as measured process evaporation.

- **C0: constant evaporation intensity** (same mathematical form as W0 but a *different output definition*):
  $$\hat F^{evap}_{C0}=c_0 P^{IT}.$$
- **C1: temperature-excess evaporation intensity** (a one-parameter reduced W1-type model):
  $$\hat F^{evap}_{C1}=\beta P^{IT}\max(T_{db}-25^\circ\mathrm C,0).$$
- **W2-Air: physical reference generator.** Compute air state, feasibility, and $F^{evap}$ using the existing `direct_evap` function; **W2-Air is not a fitted competitor** in this experiment.

Here $c_0$ has units L/kWh IT and $\beta$ L/(kWh IT·°C). Fit $c_0$ and $\beta$ by ordinary least squares **only on W2-Air-generated feasible states in the training set**. Both models assume the baseline $f_{air}=1$, $\Delta T_{server}=15^\circ$C, $T_{supply}=25^\circ$C, $\epsilon_{max}=0.8$. C0 and C1 alone do **not** determine cooling feasibility; that remains a separate W2-derived flag.

Under this control, expect $\beta$ on the order of **0.097–0.098 L/(kWh IT·°C)**. This is a consistency expectation from EDA 01, **not** a measured parameter.

## 3. Figure 04 — Does the reduced W1-type model reproduce W2-Air?

**Question:** On *unseen simulated weather states*, is C1 substantially more accurate than C0, and what information does C1 still omit?

**Minimal, reproducible split (by temperature, not random individual weather points):**

1. Training: 1 MW IT; dry bulb 18–31°C (one-degree steps), RH fixed at 20% (chosen to include feasible wet states). Filter out any infeasible states, as always. Fit C0 and C1 to the **same** simulated W2 evaporation values.
2. Held out: dry bulb 32–38°C, RH 10–90% in 5%-point steps. Evaluate C0 and C1 against W2 **only on feasible states**; count excluded infeasible states separately. Include dry states in training so C0's inability to shut off is visible.
3. Also verify structural load scaling at 800 and 1,200 kW for two held-out feasible states, using the fitted *intensity* coefficients. This is not independent empirical validation; it checks transfer across the model's assumed linear heat boundary.
4. Plot two small panels in **one figure**: (A) W2 evaporation intensity versus dry-bulb temperature with C0 and C1 predictions; emphasize 25°C cutoff and holdout range. (B) held-out prediction error versus temperature (L/kWh IT) for C0 and C1. Mark infeasible counts in a caption, **never as zero or as numerical prediction errors**. No overlapping swarm of RH-colored curves; the first EDA has already shown their near-coincidence where feasible.
5. Print on the same **held-out feasible rows**: MAE, P95 absolute error, max absolute error in L/h at 1 MW, and number of feasible/infeasible states. Do not use $R^2$ alone: it would conceal dry-mode and peak prediction errors. Reuse the unchanged W2 stage model as the reference.

**Expected qualitative result:** C1 fits the physical W2-Air generator very closely over the *fixed* controls; C0 cannot capture the dry/wet distinction or temperature dependence. The humidity feasibility flag cannot be learned from the fitted C1 evaporation law alone.

**Stopping rule:** If C1 is close, retain it as a **reduced W1-type scenario model**; do not interpret the fit as real-world water prediction accuracy. If errors are unexpectedly large, inspect simulator/units/fit definitions before increasing model complexity.

## 4. Figure 05 — Where does that fitted temperature law stop transferring?

**Question:** If temperature is the only predictor in C1, what happens when server-air thermal operation changes?

Keep **the same fitted $\beta$ from Figure 04**; do not refit it. With outdoor air fixed at **30°C / 30% RH** and IT load fixed at **1 MW**, evaluate W2-Air for *assumed* $\Delta T_{server}\in\{10,15,20\}^\circ$C. Supply target remains 25°C, and all other parameters remain unchanged.

- X: server-air temperature rise (°C).
- Y: W2 evaporation **L/h**. Overlay C1 prediction frozen at the 15°C-trained coefficient (a horizontal line here).
- Label at least the already checked anchor: $\Delta T_{server}=15^\circ$C gives ~489.37 L/h; 10°C should give ~1.5×; 20°C ~0.75× under this model's assumptions.
- Report the simple structural correction $\beta(\Delta T_{server})\approx\beta_{15}\,(15/\Delta T_{server})$ **as an analytical prediction**, not an additionally fitted parameter. Show it as an optional dotted line if it helps interpretation.
- Add a compact caption: **the same heat input can require different airflow and evaporation depending on the allowed air-temperature rise**. The change in modeled water is not a change in IT energy. The model does not calculate fan electricity or return-air control feasibility.

**Implementation caution:** The existing Step 20 module exposes `SERVER_RISE_C` as a module-level assumption. If temporarily varying it in the EDA script, store its original value and restore it in `try/finally`; leave the original source file unchanged. Do not change the supply target, treatment recovery or RH simultaneously in this figure.

**Stopping rule:** Demonstrate that a fixed-temperature-only water coefficient does not transfer across altered operating assumptions, whereas the explicit heat/airflow relation explains the direction and approximate magnitude. No fan-power or new control model is needed.

## 5. Implementation: keep EDA 02 separate and small

```text
dc_resource_sim/eda/water_models/
  plot_model_responses.py          # EDA 01, unchanged
  results.md                       # EDA 01, unchanged
  fit_simple_water.py              # ONE new script for EDA 02
  results_fit.md                   # Short 2-figure conclusions
  figures/
    01_air_weather_feasibility.png       # existing
    02_heat_water_by_architecture.png    # existing
    03_constructed_day_profiles.png     # existing
    04_w2_air_surrogate_fit.png          # new
    05_airflow_control_transfer.png      # new
```

- Reuse `direct_evap` from Step 20; simple NumPy least squares (or one-line closed-form coefficients) and Matplotlib are enough. No notebooks or new datasets.
- Keep scripts in Steps 00–26 unchanged. Step 20 may print its checks on import, as in EDA 01.
- Use a single `results_fit.md` with a compact numerical error table, the assumptions, and **one takeaway plus one limitation per plot**.
- Label every output as **simulated process evaporation** or as a separately identified feed/consumption proxy. Do not fit treatment intake because, under the current constant recovery, it is just $F^{evap}/\eta$; a second regression would add no information.

## 6. Why not the older optimization figures yet?

The original planning document listed F1 observed/predicted facility overhead, F2 physics surfaces, F3 scheduling, F4 cost–water Pareto and F5 a model-sufficiency/regret map:

- **F1:** empirical electricity fits (M0/M1/M2a) already have ESIF holdout results and an earlier EDA. It is still worth publishing later, but not a new water-model figure.
- **F2:** our EDA 01 **already produced** the core physical heat–water surfaces and feasibility map.
- **F3:** hourly scheduling experiments are already implemented. A new schedule plot does not help identify the physical water mapping right now.
- **F4:** the previous off-site grid-water ranking reversed under a small hourly factor error; a polished Pareto curve would exaggerate the evidential strength of that accounting result. The optional cost–water scatter was deliberately skipped.
- **F5:** a model-sufficiency decision map is valuable **after** our water responses are defensible under compatible boundaries, controls, and shared feasible decisions. It is not required to understand W2-Air now.

## 7. Final interpretation, before proceeding

**What we can establish:** a physics-derived, temperature-excess W1-type surrogate can explain how *this simulated direct-air model* maps IT heat and weather to process evaporation, while the full W2 provides a feasibility condition and accounts for operating parameters.

**What we cannot establish:** which water model best predicts measured water consumption at ESIF, Prineville or another site. The EDA has no paired, independent water-meter target; no candidate is empirically validated. **Do not rank W0's direct-consumption proxy against W2 evaporation as if they share the same measured target.**

**Stop after Figures 04 and 05.** The next *separate* EDA milestone, if useful, is replaying a verified location-matched weather day without retuning parameters, or auditing actual water-meter boundaries. Do not begin another optimization or groundwater model in this branch.

---

Context:

## Water-model EDA — Review and next experiments

I've reviewed the three figures, `plot_model_responses.py`, `results.md`, and the EDA plan in `eda1.zip`.

The three plots are successful and should be kept. They establish the fundamental behavior of our cooling-water models. However, they also reveal that we can represent much of the simulated water behavior with a substantially simpler model than the full psychrometric equations.

That is the most valuable direction for the next EDA: identify the simplest model that reproduces the physical model's output, understand when it works, and identify when it fails.

### 1. The fundamental insights established so far

| Finding                                                                                              | What it means for modeling                                                                  |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| W2-Air evaporation is nearly independent of RH at fixed dry-bulb temperature, within feasible states | RH primarily determines feasibility under our current fixed-supply-temperature control rule |
| Evaporation rises approximately 0.098 L/kWh IT per °C above 25°C                                     | A simple temperature-excess model may approximate W2-Air very well                          |
| At fixed weather, W2-Air evaporation scales linearly with IT heat                                    | No nonlinear heat model is yet justified by these simulations                               |
| Server-air temperature rise changes the required airflow                                             | The heat-to-water coefficient depends on operating assumptions                              |
| Treatment recovery changes feedwater, not evaporation                                                | Predicting evaporation is not the same as predicting water intake                           |
| W0 and W2 can have similar daily totals but different hourly peaks                                   | Daily accuracy alone is insufficient to evaluate water-demand behavior                      |

The most important qualification concerns humidity.

Your first figure correctly shows that humidity mainly determines whether the 25°C supply target is achievable. It does not establish that humidity is generally unimportant for water consumption.

That result follows from the specific controller: supply temperature fixed at 25°C whenever wet cooling is required. Different control rules, exhaust conditions, equipment limitations, or mixing arrangements may produce different responses.

### 2. The central relationship worth investigating

Our current model suggests the following approximation for feasible direct-evaporative operation:

\\[ \boxed{ \dot V^{evap}\approx \beta P^{IT}(T\_{out}-T\_{supply})\_+ } \\]

where \\((x)\_+=\max(x,0)\\), and \\(\beta\\) depends on the server-air temperature rise and thermodynamic assumptions.

With the present settings, the temperature coefficient is approximately:

\\[ \beta\approx0.098\ \frac{\mathrm{L}}{\mathrm{kWh\_{IT}}\cdot{}^\circ\mathrm C}. \\]

For example, at 1 MW IT and 30°C outside air, this predicts approximately 490 L/h of evaporation, close to the full W2-Air result of 489.37 L/h.

This is potentially a very useful W1 model: a simple weather-dependent water intensity derived from physics rather than an arbitrary statistical regression.

It is not yet a validated predictor of real facility consumption. We would be approximating one simulator with another.

## 3. What should we plot next?

I recommend only two new figures. Both should be added to the existing `eda/water_models/` directory.

Figure 04 — Which simple water model best reproduces W2-Air?

Compare a fitted constant evaporation intensity, a fitted temperature-excess model (W1-type), and the full W2-Air simulator.

Fit using simulated temperatures of 18–31°C and test on hotter, held-out feasible conditions of 32–38°C.

Plot the predicted evaporation intensities and held-out errors. Report MAE, 95th-percentile absolute error, and infeasible-state coverage separately.

What we learn: whether W1 captures almost everything W2 predicts under fixed equipment assumptions.

Figure 05 — When does the simpler model fail?

Fix weather at 30°C/30% RH and IT load at 1 MW. Change only the server-air temperature rise:

\\[ \Delta T\_{server}\in\\{10,15,20\\}^\circ\mathrm C. \\]

Compare W2-Air evaporation against the previously fitted W1 model without refitting it.

What we learn: whether a temperature-only water coefficient transfers when airflow or thermal operating conditions change.

These two figures complement the existing three rather than repeat them.

### The models to compare

| Model                   | Evaporation mapping                         | Expected finding                          |
| ----------------------- | ------------------------------------------- | ----------------------------------------- |
| C0 — Constant intensity | \\(F^{evap}=c_0P^{IT}\\)                    | Cannot capture dry/wet transitions        |
| C1 — Temperature excess | \\(F^{evap}=\beta P^{IT}(T\_{out}-25)\_+\\) | May approximate W2 very closely           |
| W2-Air                  | Full psychrometric model                    | Physical reference, including feasibility |

C0 uses the same mathematical form as W0, but it is fitted to simulated evaporation, not onsite consumption. The original W0 coefficient and accounting meaning remain unchanged.

Importantly, W2 generates the reference data. Therefore, a near-perfect C1 fit would demonstrate model simplification, not independent predictive validation.

## 4. Why we are not using all the previously suggested plots

The original research plan included five broader figures. We should not produce all of them just to follow the original list.

| Earlier figure                      | Current decision            | Reason                                                                             |
| ----------------------------------- | --------------------------- | ---------------------------------------------------------------------------------- |
| F1 — Observed/predicted electricity | Retain earlier ESIF results | Already investigated with measured electrical data                                 |
| F2 — Physical heat–water surfaces   | Completed                   | Covered by EDA 01                                                                  |
| F3 — Scheduling decisions           | Defer                       | Already tested numerically; not necessary for the current physics question         |
| F4 — Cost–water Pareto              | Defer                       | Off-site grid-water factors are too uncertain for stronger operational conclusions |
| F5 — Model-sufficiency map          | Later                       | Needs defensible common water boundaries and reference scenarios                   |

The optional fourth figure from the most recent EDA plan was deliberately skipped for the same reason: its grid-water scheduling result was already documented and highly sensitive to factor errors.

The most relevant missing figure now is a direct comparison of reduced water models against the W2 physical response.

## 5. Local implementation plan

I've prepared the detailed instructions, covering the training/testing split, model equations, fit metrics, checks, and both plots.

Download EDA 02 — Reduced Water Models and Operating Sensitivity (.md)

The new files should be limited to:

```
dc_resource_sim/eda/water_models/
  fit_simple_water.py
  results_fit.md
  figures/
    04_w2_air_surrogate_fit.png
    05_airflow_control_transfer.png
```

There is no need to modify Steps 00–26 or the original EDA scripts. Reuse `direct_evap` and the existing physical assumptions.

### What would count as a successful outcome?

The central question is:

Can we replace the detailed W2-Air evaporation calculation with a simple W1-type coefficient without losing important predictive behavior?

I expect the temperature-excess model to perform very well under fixed thermal settings. But I also expect it to lose accuracy when those settings change.

That would establish a useful hierarchy:

\\[ \boxed{ \text{W0: fixed intensity} \\;\longrightarrow\\; \text{W1: weather-dependent intensity} \\;\longrightarrow\\; \text{W2: physical model + feasibility} } \\]

The key is not to declare W2 universally superior. It is to determine which additional information each model needs and when that information meaningfully changes its predictions.

For the tower branch, the current fixed-latent-ratio model is already exactly linear in wet heat duty, so fitting another straight line would add little. We should revisit tower prediction once latent heat transfer, airflow, or operating measurements provide additional information.

## Final recommendation

Close EDA 01. Start EDA 02 with only Figures 04 and 05.

The strongest expected result is showing that W2-Air may be reducible to a very simple temperature-driven water model for a fixed cooling configuration, while its additional physics becomes important for feasibility and changes in operating conditions.

That is a more valuable modeling result than generating additional arbitrary weather or heat sensitivities.

After these two figures, the natural next step will be testing the reduced and physical models over real hourly weather—still as scenarios until independent water measurements become available.
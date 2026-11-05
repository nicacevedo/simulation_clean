# Focused EDA plan — Electricity → IT heat → direct water (after Step 26)

**Purpose:** Visualize the *behavior and limitations* of the models already implemented. This is a **small diagnostic study**, not a new model, a calibration, or an extension of the optimization. Keep it separate from the sequential experiment scripts.

**Local output folder:** `dc_resource_sim/eda/water_models/` with `plot_model_responses.py`, `figures/`, and `results.md`. Run the script from the repository root. Do not alter Steps 00–26 or the prior notebook. The directory contains generated plots and short interpretations, not copied source datasets.

## 1. Reusable modeling chain and boundaries

### Electricity and heat (M0, Step 22)

- Baseline: $P^{DC}=kP^{IT}$, $k=1.0471$; $P^{nonIT}=(k-1)P^{IT}$. M0 does **not** resolve fan, chiller, or pump power.
- Assume for this diagnostic $\dot Q^{air}=f_{air}P^{IT}$ and $f_{air}=1$, with $\Delta T_{server}=15^\circ$C. This identifies server-air heat, not tower or condenser heat.
- At one hour, convert power (kW) to energy (kWh) using $\Delta t=1$ h; do not mix thermal and electrical energy or add modeled cooling electricity on top of M0.

### W0 vs W2-Air (Steps 20, 23–26)

- **W0:** $F^{W0}=w_0P^{IT}$, where $w_0=0.5$ L/kWh IT is an **assumed onsite direct-consumption proxy**.
- **W2-Air:** for a feasible direct-evaporative operating condition,
  $$\dot m_{da}=\frac{3600 f_{air}P^{IT}}{c_{p,ma}\Delta T_{server}},\qquad F^{evap}\simeq\dot m_{da}(\omega_{sup}-\omega_{in}),$$
  $$\frac{F^{evap}}{P^{IT}}\simeq\frac{3600 f_{air}(\omega_{sup}-\omega_{in})}{c_{p,ma}\Delta T_{server}}\quad\text{L/kWh IT}.$$
  Here the approximation takes $\rho_w\approx1$ kg/L. Air humidity and feasible supply temperature determine $\Delta\omega$; server-air rise controls the airflow required for the same heat load.
- **Treatment feed:** $F^{feed}=F^{evap}/\eta$ and $F^{reject}=F^{feed}-F^{evap}$; use the already tested **illustrative** $\eta=0.8$.
- If the specified cooling target is **infeasible**, water for successfully meeting that target is *undefined*, never zero. Dry mode has zero *modeled evaporative-process* water, not necessarily zero total facility water.
- $F^{W0}$ (consumption proxy), $F^{evap}$ (physical evaporation), and $F^{feed}$ (process supply) have **different measurement boundaries**. Overlay them only as clearly labeled model-behavior comparisons, never as measured prediction errors.

### W2-Tower (Steps 17–19): a separate architecture

For the **simple Step 18 heat/latent scenario**, not the psychrometric Step 19 outlet-air model:
$$F^{evap}\simeq \frac{3.6}{2.45}\,\alpha_{lat}\,\dot Q^{wet},\qquad
F^{makeup}\simeq F^{evap}\frac{COC}{COC-1}.$$
Use $\alpha_{lat}=0.8$, $COC=4$ unless varying one parameter explicitly. $\dot Q^{wet}$ is actual tower heat duty, **not** automatically IT heat or M0 facility power. No common site water-meter comparison with W2-Air is justified. The constrained $\alpha_{lat}\in[0,1]$ is only a scenario simplification, not a universal psychrometric bound.

## 2. Only three required figures

### Figure 1 — Weather-response and feasibility map (new, highest value)

**Question:** At fixed IT heat, which outdoor states need evaporation, how much, and which cannot meet the selected supply-temperature target?

- Evaluate existing Step 20 `direct_evap(T_db, RH, it_kw=1000)` over a small grid, e.g. 18–38°C by 10–90% RH. Retain default supply target 25°C, maximum effectiveness 0.8, server rise 15°C and the model's standard pressure.
- X: dry-bulb temperature (°C). Y: RH (%). Heatmap value: **evaporation intensity** $F^{evap}/P^{IT}$ (L/kWh IT), conditional on feasible operation.
- **Dry region:** display 0 with distinct annotation; **infeasible region:** gray/hatched, *not zero*. Mark the existing verified examples (20/50 dry, 30/30 wet, 30/70 infeasible, 35/30 wet).
- Treat effectiveness as a feasibility test, not a fitted humidity coefficient. No smoothing or interpolation across infeasible states.
- Physical interpretation: weather affects the air-state change and cooling feasibility. At fixed supply target, two different RH values can require different effectiveness but nearly the same evaporation; the map should reveal this instead of imposing monotonic RH behavior.

**Sanity anchors:** 30°C/30% -> ~489.37 L/h; 35°C/30% -> ~975.04 L/h; 30°C/70% -> infeasible; 20°C/50% -> 0 L/h.

### Figure 2 — Heat and load → water, *by architecture* (new, two small panels in one figure)

**Question:** Which quantities control the slope between energy/heat and water when ambient state and equipment are held fixed?

- **Panel A, direct-air:** X: IT power = server-air heat (0.5–1.5 MW), Y: **process evaporation rate** (L/h). Show 20°C/50% RH (dry 0), 30°C/30% RH (wet), and 35°C/30% RH (wet). Add W0 $0.5P^{IT}$ only as a thin dashed **consumption proxy, not comparable water-meter quantity**. At fixed weather, W2-Air curves should be straight lines through zero; expected effective coefficients at 1 MW are 0, 0.48937 and 0.97504 L/kWh IT.
- **Panel B, cooling tower:** X: $\dot Q^{wet}$ (0.6–1.8 MW thermal), Y: **tower evaporation and tower makeup** (L/h) using the Step 18 simple scenario with $\alpha_{lat}=0.8$, $COC=4$. They are separate curves. Optionally annotate at $\dot Q^{wet}=1200$ kW thermal: evap ~1,410.6 L/h, makeup ~1,880.8 L/h. Do **not** relabel wet heat as IT power, or infer it from M0.
- **Do not join the two panels into one universal heat-to-water function.** The differences in physical boundaries are the result, not a nuisance.

**Optional one-row numeric sensitivity (no extra plot):** At fixed feasible weather, reducing server air rise from 15 to 10°C increases calculated airflow and evaporation by a factor ~1.5 in this idealized model; changing $\eta$ from 1 to 0.8 increases *feed*, not evaporation, by 25%. Note these are assumed controls/equipment conditions and not measured behavior.

### Figure 3 — The verified Step 26 24-hour day (new, one figure with two aligned axes/panels)

**Question:** How does hourly weather create different water demand profiles even when IT load and M0 electricity stay constant?

- Use **exactly** the constructed Step 26 day: hours 00–07: 20°C/50% RH; 08–15: 30°C/30% RH; 16–23: 35°C/30% RH. One MW IT, $k=1.0471$, $w_0=0.5$, $\eta=0.8$.
- Upper panel: outdoor dry-bulb temperature and RH (two lines with units; avoid confusing unlabelled dual axes). Lower panel: **W2 process evaporation**, **W2 treatment feed**, and **W0 direct-consumption proxy**, all L/h and unambiguously named. Shade/mark dry vs wet periods; include a clear note that W0 and W2 have different water boundaries.
- Mark peak W2 feed as a *rate* and annotate day totals as *volumes*. Never use a 24h graph to imply validated Prineville weather.
- **Sanity anchors:** dry/wet/infeasible = 8/16/0; evaporation 11,715.2 L/day; feed 14,644 L/day; reject 2,928.8 L/day; peak feed ~1,218.8 L/h; W0 proxy 12,000 L/day; M0 facility 25,130.4 kWh/day.
- Repeat the existing one-hour 30°C/70% RH failure as a **test**, not another figure; a day containing that hour has no valid full-day W2 total without a modeled fallback.

## 3. One optional optimization figure (only if helpful to the story)

### Figure 4 — Existing Step 15 cost vs *modeled off-site* water (no rerun)

Use only the known three schedules, from the existing `s7_water_schedule.py`: baseline ($862.05; 43,944.9 L grid water), cost-optimal ($834.32; 43,982.4 L), and water-optimal ($865.55; 43,859.9 L). Plot electricity cost ($/day) versus **grid-related modeled water** (L/day), with three labeled markers. Do not combine these with W2-Air direct evaporation or claim measured water savings. Add the Step 16 caveat: a patterned factor error of about $\pm0.0239$ L/kWh can reverse the water ranking of the two optimized schedules. This figure is a *decision-accounting caution*, not evidence about cooling physics. Skip it if the first three plots already suffice.

Do not repeat the extensive ESIF PUE/weather EDA from the existing notebook's Sections G/J/K or the Prineville monthly weather/billing plots in Section L. Existing M0/M2a electrical-prediction results are the empirical power anchor; these W2 figures are **conditional response surfaces only**, not held-out water predictions.

## 4. Minimal reproducible local execution

Suggested structure:

```text
dc_resource_sim/
  eda/
    water_models/
      plot_model_responses.py        # one script, no optimizer rewrite
      figures/
        01_air_weather_feasibility.png
        02_heat_water_by_architecture.png
        03_constructed_day_profiles.png
        04_grid_water_decisions.png     # optional
      results.md                    # 1–2 paragraphs per figure; assumptions, insight, limitation
```

- **Reuse** the existing `direct_evap` (Step 20), Step 18 tower equations, and Step 26 fixed day. Reuse results from Step 15 if drawing Figure 4. No duplicated physics implementation, new datasets, fitting, or changes to the experiment scripts.
- Python: standard library + matplotlib/numpy for plots. Run with the Python environment that already supports them. Direct imports of Step 20 may print its top-level tests, as previously observed; don't change those scripts just for this EDA.
- Plot titles should include architecture and output boundary. Label axes, units, and assumed constants. Clearly denote infeasible areas (N/A) distinct from 0.
- Use a short `results.md` to record **what varied / what stayed fixed / what was learned / what was not validated**. Save figures in PNG (and optionally SVG for papers); avoid notebooks, dashboard scaffolding, Monte Carlo, new optimization and broad parameter grids.

## 5. Validation and stopping rule

Only proceed once these checks pass:

1. **Model anchors:** Figure 1 matches the Step 20 reference cases; Figure 2 passes linear load/heat scaling and retains separate architecture boundaries; Figure 3 reproduces Step 26 totals.
2. **Balance:** every feasible direct-air point has nonnegative evaporation; $F^{feed}=F^{evap}+F^{reject}$ at every Step 26 hour; tower makeup is at least evaporation for $COC>1$.
3. **Feasibility:** infeasible air states are masked, not assigned zero or extrapolated. A day with an infeasible hour is not summarized as a fully served W2 day.
4. **Interpretation:** **No** inference of site total withdrawal, Prineville WUE, measured water-prediction error, or marginal grid-water savings. No add-on fan/chiller power to M0.
5. **Scope:** maximum 3 core figures (+1 optional existing optimization diagnostic); one new script and one `results.md`. No changes to Steps 00–26.

**Then stop.** The subsequent small step can be a measurement-boundary audit for Prineville (previously proposed Step 27), or a single location-matched weather-day replay *without changing parameters*. Do not do both simultaneously.

## 6. Overall takeaway for the research plan

Keep a model ladder rather than jumping to a comprehensive water predictor:

**W0:** direct water as fixed intensity of IT electricity (proxy) → **W2-Air:** weather, cooling feasibility and heat-driven airflow → **W2-Air + treatment:** required process feed and reject → **W2-Tower (separate branch):** wet heat rejection, evaporation and tower makeup.

The present contribution is **physical interpretation and reproducible response analysis**, not externally validated predictive accuracy. Measurements of airflow/controls, treatment recovery and site water intake will be needed before fitting, ranking or transferring site-level water models.

---

Context:

## Revised water-model EDA plan — After Step 26

Step 26 is complete. We now have a working chain from IT electricity to heat, airflow, evaporation, treatment feed, and reject water.

I recommend a short EDA campaign before adding any more physics. The goal is to understand the relationships already present in our models, identify which variables actually matter, and visualize when the models behave differently.

I've prepared a reproducible plan for local experimentation:

Download Water Models EDA Plan (.md)

### 1. What we should understand first

Our most useful physical relationship is:

\\[ \frac{\dot V^{evap}}{P^{IT}} \approx \frac{3600f\_{air}(\omega\_{supply}-\omega\_{in})} {c\_{p,ma}\Delta T\_{server}} \\]

For a feasible direct-evaporative operating state, this connects:

- IT electricity and heat transferred to air.
- Server airflow and allowable temperature rise.
- Outdoor weather and humidity change.
- Process evaporation.

Treatment recovery then determines the required feed water:

\\[ \dot V^{feed}=\frac{\dot V^{evap}}{\eta}. \\]

These relationships already exist in our scripts. We should visualize and test their implications before introducing additional parameters.

## 2. The plots I recommend

[Frontiers | Passive evaporative coolers for postharvest storage of fruit and vegetables: Where to best deploy them and how well do they perform](https://images.openai.com/static-rsc-4/UYq7IgNtJNFyQtPlp6nAyuq-fbM4KyfK9G6jU-oiNwBqU1av8bdSx99pTbpkU0QK-Hyo6pV92tR4Wm4nfYD1oSAQxZuaDAZ_bzn_w_LSufPQIR0trk_ZDjQ9vJ4vNX66MLY1aERqRh6TvMiPlzhG7H45KweIHUhX0p8UgbykaeY?purpose=inline)

Figure 1 — Weather → evaporation and cooling feasibility

Plot dry-bulb temperature against relative humidity, with color showing W2-Air evaporation intensity in L/kWh IT.

Distinguish dry, wet, and infeasible operating regions. This is our highest-value new figure: it shows the environmental conditions under which the water model applies.

[Effect of (L/G) ratio on cooling tower effectiveness Conclusions   | Download Scientific Diagram](https://images.openai.com/static-rsc-4/iX3_4HN_ZOkQRjKN62y7_gVMDiCS45a-VO4a-CtAnZbwz7V4TQEAbpz6KGGHnAPac-mVLG_XGrbQq6bAIP7-LKdDYR6yS35QiVm0ASiJ6wofPswGve51SgU4qQO-uV0pTOBpriDFQfqD3o7G6NK9SETGFsQ1PPRRsSKmL6q605U?purpose=inline)

Figure 2 — Heat and load → water

Two panels: direct-air evaporation versus IT heat at fixed weather, and cooling-tower evaporation/makeup versus wet heat rejection.

Include W0 as a clearly labeled reference in the direct-air panel. This will show when water scales linearly with IT power and why the two cooling architectures cannot share one generic heat-to-water coefficient.

[Smart Building — SENSEi-IoT](https://images.openai.com/static-rsc-4/FsI8VY5Q0VrvFDHo0FuPNq3u2F5cJ_pWkAWTdPezME2VPJz3q_cJRfowD8cyEN64Ijg6ODcNo1popQamSGPhMIHSO6ATm1O2wasvnZTIYth_FZPc8-diI9LQnnqEVTtFGaBX2xD5kZQCR9UsB92Cu6DYHPnRYFPgHXhbnsv22Xo?purpose=inline)

Figure 3 — Complete 24-hour electricity–heat–water behavior

Reuse Step 26's constructed day. Show weather above and W0 proxy, W2 evaporation, and treatment feed below.

Highlight dry/wet operation, daily totals, and peak water-feed rate. This demonstrates why matching daily volumes can hide very different hourly behavior.

[Improving Water and Energy Resource Management: A Comparative Study of Solution Representations for the Pump Scheduling Optimization Problem](https://images.openai.com/static-rsc-4/nErrqAICJup5PcataWZhLC5epnU6oCNhkKaoSjlQ5Hk8zipxnPRyzrpxDCRf86apvCE-lceVtPM-lHdFvckcy7sa_edsD-AiNWaM-wMy6mDWPfr4u8sjNTOZ6W40399oEt0QBGFJqFEa4DtvHKpDQ_L8-azhmucG7UvHrgGXu7g?purpose=inline)

Figure 4 — Existing optimization trade-off (optional)

Replot only the three Step 15 schedules: baseline, cost-optimal, and water-optimal.

Show electricity cost against modeled grid-water consumption, and annotate the sensitivity found in Step 16. No optimization reruns.

Images are illustrative chart-style references, not outputs of our models. The actual plots should be generated from the verified local scripts.

### 3. Keep everything separate from the sequential experiments

Use:

```
dc_resource_sim/
  eda/
    water_models/
      plot_model_responses.py
      figures/
      results.md
```

The full plan specifies the input ranges, reference values, physical checks, and interpretation for each plot.

I would not introduce another notebook, download new datasets, refit models, or modify Steps 00–26.

### 4. What we should expect to learn

| Relationship                    | Expected insight                                                                       |
| ------------------------------- | -------------------------------------------------------------------------------------- |
| Weather → direct-air water      | Water intensity changes with air state; some conditions are infeasible                 |
| IT heat → evaporation           | At fixed weather and operating assumptions, W2-Air scales linearly with IT load        |
| Server temperature rise → water | Airflow and evaporation depend on the assumed permissible temperature rise             |
| Treatment recovery → feed water | Lower recovery increases intake requirements, not evaporation                          |
| Tower heat rejection → makeup   | Heat duty, latent heat transfer, and COC determine process water                       |
| Scheduling → water              | The previously observed grid-water trade-off is small and sensitive to modeled factors |

One important distinction: We are investigating model response, not yet predictive accuracy. We do not have synchronized measured water data with which to calculate meaningful W2 prediction errors.

### 5. Stopping rule

I recommend completing the first three plots and recording only three things for each: what variables were changed, what relationship was observed, and which assumptions limit the result.

Add the fourth plot only if it helps connect this physical EDA to our earlier optimization work.

Afterward, we can choose the next physical refinement based on what these figures reveal—not simply because a more complicated model is available.

My recommendation: Treat this as a small, separate EDA milestone, not Step 27. It should consolidate our understanding of W0, W2-Air, W2-Tower, heat, weather, and process water before we continue extending the simulator.
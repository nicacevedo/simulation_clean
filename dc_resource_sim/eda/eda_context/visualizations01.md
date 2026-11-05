# Local agent plan — Five figures that summarize the completed DC electricity–water experiments

**Scope:** Curate **five** final figures, but **make only three new plots**. The other two have already been produced and verified in the water-model EDA. This is a **results-communication branch**, not a new experiment, model fit, optimization, or Step 31. Preserve existing scripts, datasets, and results. Follow the physical accounting boundaries throughout.

**Main story:** (1) facility-power models do not transfer uniformly across load/weather regimes; (2) water demand is conditional on cooling architecture and ambient feasibility; (3) a simple water surrogate can approximate the detailed *simulator* across aggregation levels; (4) improved resource information matters operationally only when it alters a decision, a constraint, or a relevant water accounting comparison.

## 0. What is supported (freeze the claims)

- **Power, ESIF 2023:** 7,200 hourly observations from 300 complete days, reference facility power derived from reported IT power and PUE (**not an independently measured facility-meter reference**). For weather-matched power comparisons: **7,050** hours, with no interpolation.
- **Direct-air water:** W2-Air is a conditional psychrometric **process-evaporation** simulator. C1 ($0.09788 P^{IT}(T_{db}-25)_+$ L/h, with $P^{IT}$ kW) is a frozen surrogate of this simulator under assumed 25°C supply target, $\Delta T_{server}=15$°C, $f_{air}=1$, and effectiveness ceiling 0.8. C1 has **no feasibility check**. W0 ($0.5$ L/kWh IT) is an illustrative **onsite direct-consumption proxy**, not C0, nor a measured evaporation coefficient.
- **Tower water:** tower evaporation/makeup (Steps 17–19) uses wet heat-rejection duty and concentration assumptions; it is **not** the same technology or water boundary as W2-Air. Do not turn wet heat duty into IT power by relabeling the axis.
- **Water aggregation (Step 29):** W2-Air is the *simulated reference*, not measured water. **290 complete UTC days**, 6,960 hours, 726 wet hours; incomplete days excluded. These data are complete-day **sampled** subtotals, not full-year or full-calendar-month consumption.
- **Optimization:** facility-capacity results were model-reference scenarios; grid-water results use **modeled average MISO factors**, not identified marginal savings. **Step 30 has been planned but not reported as executed**; do not display its proposed outcomes as results.

## 1. Final figure set, ordered as a research narrative

| Figure | Purpose / single takeaway | Reuse or create | Source |
|---|---|---|---|
| **F1. Power-model transfer** | Different load/weather regimes change prediction accuracy and hourly underprediction risk | **New** | `runs/esif_hourly_2023.csv`, `runs/esif_weather_hourly_2023.csv`; same train/test definitions as `s5_affine_weather.py` |
| **F2. Weather and cooling feasibility** | Dry-bulb governs evaporation intensity under the specified supply target, while RH gates physical feasibility | **Reuse** | `eda/water_models/figures/01_air_weather_feasibility.png` |
| **F3. Heat-to-water by cooling architecture** | Water scales with heat within fixed assumptions, but **air evaporation** and **tower makeup** are different physical mappings | **Reuse** | `eda/water_models/figures/02_heat_water_by_architecture.png` |
| **F4. How much water-model complexity?** | C1 is very close to W2 at hourly, daily and sampled-month scales; frozen C0 fails on this replay | **New** | `eda/water_models/aggregation_summary.csv` from Step 29 |
| **F5. What was the decision value?** | Cost–grid-water scheduling moves hours, but the modeled gain is small and fragile to factor errors | **New** | verified Step 15–16 results in `src/experiments/s7_water_schedule.py` and `runs/price_water_24h.csv` |

**Do not produce extra figures** for the Step 26 constructed day, original Figure 04 surrogate fit, Figure 05 airflow sensitivity, and Figure 06 real-weather week: those are already documented and are supporting material, not additional principal summary plots. Do not reproduce Prineville monthly billing charts here.

## 2. Exact instructions for the three new plots

### F1 — `01_power_model_transfer.png` (new; *measured inputs, PUE-implied reference*)

**Question:** Which added power-model complexity generalizes, and at what hourly capacity-risk cost?

Use **two small panels** with identical model ordering and colors:

- **Left: held-out hourly MAE (kW)** for M0, M1-fixed and M2a-fixed, grouped by two time splits:
  - **Warm holdout:** train Jan–Jul 2023, test Aug 2023 (weather-matched; 628 test hours).
  - **High-load holdout:** train Jan–Aug, test Sep–Dec 2023 (weather-matched; 1,965 test hours).
- **Right: held-out fraction of hours exceeding the model's training-derived $h_{95}$ headroom (%)**, with the same groups/colors. Define positive underprediction $e_t=\max(P^{ref}_{DC,t}-\hat P_{DC,t},0)$; $h_{95}$ is its training 95th percentile. Test exceedance means **$P^{ref}_{DC}-\hat P_{DC}>h_{95}$**. This is a *historical prediction diagnostic*, not an observed capacity-limit violation or guaranteed coverage probability.
- For each split fit **train-only**: M0 $k=\sum P^{ref}/\sum P^{IT}$, M1-fixed $a=\operatorname{mean}(P^{ref}-P^{IT})$, M2a-fixed $P^{ref}\approx P^{IT}+a+c(T_{wb}-T_0)$ with $T_0$ = training mean wet-bulb. No slope on IT for the fixed variants; no test-data fitting.
- **Use common weather-matched rows for all three models in each split**, no filling or leakage.

**Expected approximate regression tests (verified from the attached 2023 hourly CSVs):**

| Holdout | Model | MAE kW | % test hours above its training $h_{95}$ |
|---|---|---:|---:|
| Warm Aug | M0 | 14.36 | 0.80 |
| Warm Aug | M1-fixed | 23.15 | 2.71 |
| Warm Aug | M2a-fixed | 11.63 | 0.32 |
| High-load Sep–Dec | M0 | 84.89 | 0.00 |
| High-load Sep–Dec | M1-fixed | 12.85 | 0.25 |
| High-load Sep–Dec | M2a-fixed | 9.19 | 0.71 |

**Interpretation:** M2a-fixed improves average facility-power prediction in both these holdouts, but the safety/headroom ranking is not identical to the accuracy ranking. M0 overpredicts under high load and has zero headroom exceedances there; M1-fixed does not capture warm overhead as well. **These are two historical splits, not evidence of universally optimal coefficients or causal load/weather effects.** Reference is PUE-implied, not an independent facility meter.

**Design:** grouped horizontal dot/bar display rather than raw 7,050-point scatter; direct-label model names, clearly separate warm and high-load split, show numerical results on bars/markers, avoid tiny text. One short subtitle: “2023 ESIF, same weather-matched hours per model; historical holdouts”. Avoid a red/green “safe/unsafe” classification from empirical coverage alone.

### F2 — **reuse existing** `01_air_weather_feasibility.png`

The existing figure already correctly displays **dry = zero modeled evaporation**, **wet = calculated evaporation**, and **infeasible = N/A (hatched)** for dry-bulb × RH, with the hypothetical W2-Air settings. Do not regenerate unless the file is missing or its labels are unreadable.

Required interpretation in the figure index: at the fixed 25°C supply rule, **temperature governs the modeled evaporation intensity *within the feasible region*, while humidity largely controls feasibility**. This is architecture- and controller-specific, **not a universal RH independence law**. The map is **not** site water use or a weather-frequency forecast.

### F3 — **reuse existing** `02_heat_water_by_architecture.png`

This is already a concise, correctly separated **two-panel** comparison: W2-Air evaporation vs IT/server-air heat for fixed weather; W2-Tower evaporation and makeup vs **wet tower duty** for fixed latent fraction and CoC. It also labels W0 as an accounting proxy, not an observed evaporative flow.

**Do not draw a single combined line or compare tower makeup and air-side evaporation as if both were measured onsite consumption.** The fixed-equipment lines are linear by model construction; this cannot establish real-world part-load linearity.

### F4 — `04_aggregation_model_sufficiency.png` (new; *simulated W2 reference*)

**Question:** How much does complexity change *simulated evaporation* error when we aggregate in time?

One clean line/dot chart: X = hourly / complete-day / sampled-month; Y = WAPE (%), **explicit logarithmic scale** because C0 and C1 differ by orders of magnitude. Two series, C0 and C1; put numeric values directly beside points, no invented uncertainty bands or smoothing. Mark the axis as log and report the sample support visibly: **290 complete days, 6,960 matched hours, 726 wet hours**.

Expected from Step 29:

| Model | Hourly WAPE | Daily WAPE | Sampled-month WAPE |
|---|---:|---:|---:|
| C0 (constant simulated evaporation intensity) | 400.2% | 334.2% | 281.6% |
| C1 (temperature excess) | 0.19% | 0.14% | 0.10% |

Keep the **peak** and **wet-hour** metrics in the figure caption, not as extra axes: W2 hourly peak ≈3,377 L/h; C0 peak error −2,818 L/h and wet-hour MAE 568.9 L/h; C1 peak error +13.8 L/h and wet-hour MAE 1.49 L/h.

**Strict interpretation:** frozen C0's coefficient was generated using a *different synthetic state distribution*; this does not prove all constant-intensity calibrations fail. C1 approximates **W2-generated evaporation**, not meter readings. WAPE generally drops under aggregation because signed errors cancel; monthly closeness alone does not imply peak-hour suitability. Sampled-month sums are not calendar-month totals.

### F5 — `05_cost_gridwater_decision.png` (new; *conditional accounting decision*)

**Question:** Did previously tested water-aware scheduling materially change modeled cost and grid-water accounting?

Use **one 2D scatter plot** with three labeled points, each evaluated on the same Step 15 July 1, 2023 **Springfield/MISO** scenario:

- X: **additional electricity cost relative to the cost-optimal schedule ($/day)**.
- Y: **change in modeled grid-water consumption relative to cost-optimal (L/day)** (negative = modeled reduction).
- Mark and label *Cost-optimal* ($834.32, 43,982.4 L), *Baseline* ($862.05, 43,944.9 L), and *Water-optimal* ($865.55, 43,859.9 L). Use the differences on axes: cost (0, +27.73, +31.23); grid-water (0, −37.5, −122.5). All schedules have **12,000 L modeled direct W0 consumption**; do not attribute the differences to direct cooling.
- One small annotation: **the 122.52 L ranking advantage between the two optimized schedules reverses under an adversarial, hour-patterned factor error of ±0.0239 L/kWh (Step 16)**. This is a **threshold**, not a confidence interval; do **not** draw statistical error bars.
- Annotate that factors are *modeled average grid-water consumption*, **not marginal dispatch responses or measured savings**. Prices and factors describe Springfield/MISO, not ESIF or Prineville. Do not combine withdrawal with consumption.

**Avoid overclaim:** The absolute difference is about 0.2% of ≈56,000 L modeled total accounting, and source uncertainty dominates. This figure is a caution about decision relevance and data quality, not a demonstrated water-conservation benefit.

## 3. Minimal local repository changes

Create exactly one plotting script and one short index note, plus the **three** new PNGs. Reuse the other two existing PNGs by relative link rather than copying them:

```text
dc_resource_sim/eda/
  summary/
    make_summary_figures.py          # NEW: only generates F1, F4, F5
    README.md                        # NEW: five ordered relative links + source/interpretation notes
    figures/
      01_power_model_transfer.png   # NEW
      04_aggregation_model_sufficiency.png  # NEW
      05_cost_gridwater_decision.png        # NEW
  water_models/figures/
      01_air_weather_feasibility.png        # REUSE, untouched (F2)
      02_heat_water_by_architecture.png     # REUSE, untouched (F3)
```

**Inputs:** local 2023 ESIF hourly power/weather CSVs already written in `dc_resource_sim/runs/`; Step 29 `aggregation_summary.csv` (if missing, rerun the original `aggregation_compare.py` unchanged); recorded Step 15–16 outcome and `price_water_24h.csv` / `s7_water_schedule.py`. Where Step 15 outputs were not saved as structured rows, you may embed **only the three already verified point values** shown above in the summary plotting script, with explicit provenance in a comment; never fabricate additional scenarios. Do not edit S7 to add a new export merely for plotting. Never use `run5.zip` as an expected path inside the local repository.

**Dependencies:** Matplotlib, pandas/numpy already used in EDA. No downloads, no new packages, no notebook, no modifications to prior EDA, model, optimizer, or data-extraction scripts. Do not run Step 30 or generate a Step 30 decision-value result here: that experiment has not yet been reported completed.

**Suggested execution:** `python dc_resource_sim/eda/summary/make_summary_figures.py` from the repo root with an environment supporting the existing plotting dependencies. One script, no CLI scaffolding. Create output directories if absent, but do not overwrite historical figures.

## 4. Visual and scientific quality gates

1. **Keep a consistent style** across new plots: white background, readable labels at normal slide size, restrained colorblind-friendly hues, thin horizontal grids, no 3D, no decorative icons, no dual-axis charts, no arbitrary smoothing. Use the same color for each model everywhere it appears. PNG at ≥160 dpi; optionally save SVG if effortless.
2. **A claim in every title:** F1 “Power-model performance depends on regime”; F2 “Humidity determines evaporative feasibility”; F3 “Heat-to-water mappings depend on cooling architecture”; F4 “C1 reproduces simulated evaporation at all three scales”; F5 “Modeled grid-water scheduling gains are small and fragile”. Use precise, not causal, wording.
3. **Source status in each caption/README:** F1 “ESIF measured IT / PUE-implied facility reference”; F2–F4 “conditional W2-Air or W2-Tower simulations”; F5 “modeled average grid-water accounting scenario”. Explain that none validates metered onsite cooling water or groundwater extraction.
4. **Never omit denominators:** F1 train/test dates and matched-hour counts; F4 valid complete-day counts and wet-hour sample; F5 reference schedule and $/day, L/day. Express temperatures, intensities, thermal duty, and feed/evaporation boundaries explicitly where plotted.
5. **Check numeric anchors before exporting:** F1 numbers in table (allow a reasonable small numerical tolerance, e.g. MAE ±0.1 kW, exceedance ±0.05 percentage point); F4 WAPE ±0.02 percentage point; F5 source point cost ±$0.01 and water ±0.2 L. Fail or clearly report a mismatch rather than silently plotting inconsistent values.
6. **Inspect final PNGs at slide-scale.** Confirm text does not overlap, legends do not obscure marks, log axis is labeled, dry/infeasible are distinguished, and the color mapping is consistent. If visually crowded, remove annotation text, **not** important scientific distinctions.
7. **One README summary:** five links, one key observation + one limitation for each, and two-sentence overall conclusion. No extra plots or broad new simulation campaign.

## 5. Final agent instruction (paste directly into local work session)

> Create the **five-figure research summary** exactly as described in this plan. **Reuse** the two existing verified water figures (F2/F3); **generate only F1/F4/F5** in one new `make_summary_figures.py` under `dc_resource_sim/eda/summary/`. Start by checking the specified source CSVs, Step 29 summary, and the verified Step 15–16 numbers; do not infer any additional outputs. Use the same train-only splits and common rows for F1. Preserve the measured/derived/simulated/accounting distinctions and all water boundaries. Put the five relative figure links with concise interpretations in `README.md`. Run the script and verify numeric anchors and layout. **Do not modify any existing script, dataset, or plot; do not refit water models or run new optimizations.** Return the list of created files, the five principal takeaways, and any unresolved input mismatch.

**Stop** after generating the three new PNGs, checking both existing PNGs, and writing the short README. The resulting five-figure story is enough for an internal project review or research presentation; add more figures only if a subsequent experiment produces genuinely new decision-relevant evidence.

---

Context:

## Final plan — Five figures, only three new plots

After reviewing the existing EDA figures, the Step 29 results, the ESIF data, and our previous optimization experiments, I recommend five figures total, but creating only three new ones.

This is sufficient to communicate the most important conclusions without repeating experiments or introducing unnecessary complexity.

Download the complete local-agent visualization plan (.md)

### 1. The five figures

| Figure                                  | Main research question                                                                                                              | Action         |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| F1. Power-model transfer                | When do M0, M1-fixed, and M2a-fixed predict facility electricity accurately, and when do they underestimate capacity needs?         | Create         |
| F2. Weather and cooling feasibility     | How do temperature and humidity determine whether evaporative cooling is needed and feasible?                                       | Reuse existing |
| F3. Heat-to-water relationships         | How do IT heat, wet heat rejection, and cooling architecture determine evaporation and makeup?                                      | Reuse existing |
| F4. Model complexity versus aggregation | How much accuracy do we gain from C1 over a constant-intensity model at hourly, daily, and monthly scales?                          | Create         |
| F5. Operational decision value          | How much do water-aware decisions change electricity cost and modeled grid-water consumption, and how robust are those differences? | Create         |

### 2. Why these are the best choices

The five figures communicate a coherent scientific progression:

F1 — Empirical electricity prediction

What can we predict from measured operating data?

F2–F3 — Physical heat and water relationships

Which environmental and equipment variables determine cooling-water demand?

F4 — Model sufficiency

When can a simpler model replace the detailed simulator?

F5 — Optimization relevance

When does additional resource information actually matter for decisions?

F1 will compare the two verified ESIF holdouts using consistent samples. F4 will use Step 29's WAPE results, with C0 and C1 shown on a clearly labeled logarithmic scale. F5 will show the three existing cost/grid-water scheduling outcomes, including the small uncertainty threshold that reverses their ranking.

### 3. Minimal implementation

The local agent should create only:

```
dc_resource_sim/eda/summary/
├── make_summary_figures.py
├── README.md
└── figures/
    ├── 01_power_model_transfer.png
    ├── 04_aggregation_model_sufficiency.png
    └── 05_cost_gridwater_decision.png
```

The other two figures already exist in `eda/water_models/figures/` and should simply be linked in the README.

The Markdown plan includes exact source paths, expected numerical values, model definitions, plotting instructions, checks, figure captions, and a copy-ready local-agent instruction.

### 4. The most important quality requirement

Every figure must distinguish what has been demonstrated from what is still conditional.

For electricity, we have measured operating signals and a PUE-implied facility-power reference. For water, we have physically consistent simulations and an accurate surrogate of those simulations, but not independent water-meter validation.

Likewise, our grid-water scheduling results are conditional accounting outcomes, not demonstrated physical savings.

We should also not visualize Step 30 as a completed optimization result, because that experiment has only been planned.

### Final recommendation

I would stop at these five figures. They cover the central findings of our electricity, heat, water, model-complexity, and optimization work while requiring just one new plotting script, one README, and three new images.

The main message should emerge naturally:

Model complexity is valuable when it improves prediction under relevant operating conditions, captures physical feasibility, or changes an important decision—not merely because it produces a more detailed equation.
# Findings inventory — Steps 00–30

**Purpose:** Single source of truth for what was actually established, the nature of the evidence, and whether the current five-figure summary covers it. This is a research record, **not an additional visualization plan**.

**Evidence types:** `Test` = synthetic numerical/model-balance check; `Empirical proxy` = ESIF IT/weather/components and PUE-implied facility reference; `Simulation` = conditional physical model; `Decision scenario` = optimization evaluated under an assumed accounting/physical reference; `Billing` = reported city/Meta water quantities.

| Steps | Question / hypothesis | Main result already obtained | Evidence and limitation | Five-figure coverage |
|---|---|---|---|---|
| **00–03** | Does the simplest M0/W0 accounting close, and does fitted constant PUE transfer between dates? | Synthetic equal-energy profiles conserve facility electricity and W0 water while peak demand differs; fitting ESIF PUE lowers errors, but PUE is not constant (Jul 1 ~1.0474; Dec 1 ~1.0210). | Test + empirical proxy, **not independent facility metering**. | Partly F1 |
| **04–07** | What causes seasonal overhead variation? | On the analyzed hours, overhead increased ~30.7 kW from Jan–Apr to May–Aug; cooling +26.0 kW and pumps +9.8 kW account for more than the increase, offset by other categories. Component sum matches derived overhead. | Empirical component accounting; internal reconciliation does not independently validate each meter or causation. | Not directly |
| **05–14** | Which simple facility-power form transfers across operating regimes? | On matched-holdout comparisons, M2a-fixed best MAE (warm 11.6 kW; high-load 9.2 kW). Free IT-load slopes transfer poorly when load shifts outside training range. MAE and underprediction/headroom violations measure **different risks**. | Empirical proxy, two historical splits; training headroom is not guaranteed coverage. | **F1** |
| **08–11** | When does a power model change scheduling? | With no binding facility limit, constant-PUE and fixed-overhead models gave the same schedule. Under a binding assumed limit, model choice changed feasibility (e.g., 16.9 kW violation in a cross-model reference scenario). With observed MISO day-ahead prices, feasible cost regret was ≤$0.49/day in tested cases. | Decision scenario; model-to-model feasibility is **not observed** grid-limit violation. | Not directly |
| **11–14** | Is historical underprediction/headroom safe year-round? | Summer underprediction was substantial for fixed overhead. Weather-dependent overhead improved hourly errors once warm conditions were represented in training; free IT-power slopes risked high-load extrapolation. | Empirical proxy; the observed 2023 high-load regime was generally *overpredicted* by M0 despite synthetic cross-model violation scenarios. | **F1**, partial |
| **15–16** | Does hourly grid-water accounting change the objective, and is it robust? | Water- versus cost-optimal schedules differed by 122.5 L/day of **modeled grid water** for +$31.23/day. Their ranking can reverse under adversarial hourly factor errors of ±0.0239 L/kWh. Direct W0 water stayed 12,000 L/day across schedules. | Decision/accounting scenario using **average**, not identified marginal, grid-water factors. | **F5** |
| **17–19** | How do tower wet-duty, latent fraction, and concentration cycles translate to process water? | The tower energy and makeup balances close; makeup varies with COC and wet-duty, and tower duty is **not automatically IT heat**. | Simulation only; no tower hardware/site calibration. | **F3** |
| **20–26** | How do IT heat, air-side conditions, cooling feasibility, and treatment recovery affect water? | W2-Air predicts dry/wet/infeasible states; airflow ∝ IT heat / assumed server temperature rise; evaporation depends on air-state change; feed = evaporation / recovery, with reject tracked separately. The constructed 24-h run gave 11,715 L evaporation and 14,644 L treatment feed. | Test + simulation; air cooling and tower models are different architectures. W0 consumption proxy ≠ W2 evaporation ≠ process feed. | **F2–F3**, partial |
| **EDA 02–03 (after Step 26)** | Can physical W2-Air be simplified without losing its response? | Frozen C1 = 0.09788·P_IT·(Tdb−25)₊ matched held-out feasible W2 states (3.42 L/h MAE at 1 MW); 15/ΔT_server correction captured airflow-rise changes. The 2023 ESIF-weather replay had 7,990 valid hours, 776 wet, no infeasible, ~588 m³ modeled evaporation over **valid hours only**. | Simulation with **real weather/IT inputs**, hypothetical direct-air equipment. Not a full-year water measurement. | **F2–F4**, partial |
| **27–28** | Are reported city water quantities compatible with Meta’s annual withdrawal report? | 2023 data-center water-coded meter subtotal 58,230 billing units (~164.89 ML), provisional addition of bill-dated bulk ~14.87 ML → ~179.76 ML, close to Meta's rounded 180 ML withdrawal. | Billing/reporting consistency only; overlap, source/purpose, chronology and return-water boundaries unresolved. | Not covered; rightly peripheral |
| **29** | Do simplified evaporation models stay accurate after hourly→daily→monthly aggregation? | On 290 complete days (6,960 h), C1 vs W2 WAPE = **0.191% / 0.143% / 0.098%**; frozen C0 = **400% / 334% / 282%** (fit on different synthetic conditions). C1's hourly peak error +13.8 L/h. | *Simulator agreement*, not measured water-prediction accuracy; sampled-month sums are not full months. C0 failure is not universal proof that constant-intensity models fail. | **F4** |
| **30** | Does reduced model C1 preserve the W2-optimal *water-only scheduling decision*? | Attached script and `schedule_decision_summary.csv` show 2023-07-24: no-shift 8,680.5 L W2 evaporation; C1- and W2-optimal 8,458.8 L; **221.7 L/day (~2.55%)** lower than no shift; **C1 regret = 0** under W2; peak illustrative treatment feed **increases** from 1,353.8 to 1,452.0 L/h. | One hypothetical 1 MW site on a measured-weather day, with assumed 20% flexibility, fixed cooling settings and 80% recovery; process evaporation, not observed water savings. Equal objective need not imply identical hour-by-hour schedules. | **Missing; README falsely states Step 30 not run** |

## Overall conclusions now warranted

1. **Power:** Simple electricity models can be useful, but load/weather regime and constraint boundaries determine their transfer and operational risk. Low MAE and safe upper prediction are not the same criterion.
2. **Water physics:** Cooling-water response depends on technology, heat-routing, outdoor air, equipment controls and treatment. The W2-Air and tower results are **separate conditional physical scenarios**.
3. **Sufficiency:** For the tested fixed direct-air architecture, C1 is an excellent surrogate of W2 and has zero reported conditional scheduling regret on the one Step 30 day. W2 remains needed for feasibility/control changes.
4. **Decisions:** Electrical capacity constraints, daily water volume, peak process-water feed, and grid-water cost tradeoffs are distinct; improving one need not improve the others.
5. **External validation:** No synchronized facility-water observations verify W0/C1/W2 onsite water predictions; groundwater externalities and multi-site planning are **not yet evaluated**.

## Recommended editorial action (no new simulations)

- **First:** update `eda/summary/README.md` to remove the incorrect sentence “Step 30 has not been run.” Add its verified result and the volume-versus-peak trade-off as a compact **nonfigure** note, with path to `eda/water_models/schedule_decision_summary.csv`.
- **Second:** retain F1–F5 as the *executive summary*, not an exhaustive record. Link this ledger for remaining findings, especially seasonal component accounting, power-constraint feasibility, Step 30 and Prineville measurement scope.
- **Third:** note that F5's input points are manually transcribed from prior verified results, not generated from a committed structured Step 15 run. That provenance should remain visible. Do not silently represent them as recomputed.
- **Only later, if one more plot is warranted:** consider a direct-water scheduling figure (Step 30: daily evaporation saving vs peak feed), preferably **replacing**, rather than automatically adding to, F5 for a physical-water-focused talk.

**Do not refit, infer missing calendar hours, claim metered water validation, or confuse withdrawal, consumption, evaporation, treatment feed and modeled average grid-water factors.**

---

Discussion (for reference):

## Assessment: The five figures are good, but we should consolidate the findings first

I reviewed the five summary figures, the plotting code, README, and additional EDA files in `eda.zip`.

My assessment: keep the five figures. They provide a clear, scientifically defensible overview of our progress. However, they are not sufficient to communicate every important finding from Steps 00–30.

| Criterion               | Assessment                                                                                      |
| ----------------------- | ----------------------------------------------------------------------------------------------- |
| Scientific accuracy     | Strong — model boundaries and evidence limitations are generally explicit                       |
| Visual quality          | Good — readable, consistent, and relatively uncluttered                                         |
| Simplicity              | Very good — no unnecessary dashboards or repeated plots                                         |
| Research relevance      | High — covers electricity prediction, cooling physics, model sufficiency, and optimization      |
| Coverage of Steps 00–30 | Good overview, but incomplete                                                                   |
| Reproducibility         | Good overall; F5 has weaker provenance because its values were transcribed from earlier results |

### The most important gaps

Three conclusions deserve better visibility:

- Electricity-model errors can change capacity feasibility, even when electricity-cost regret is negligible. F1 illustrates prediction risk, but not the scheduling consequences established in Steps 08–14.
- Prediction accuracy is different from decision quality. We need to distinguish a model's numerical error from whether it changes a feasible or optimal decision.
- Step 30 has now been executed, according to the attached files. Its results are missing from the five-figure summary, and the README incorrectly says Step 30 has not been run.

The attached Step 30 output reports that C1 and W2-Air achieved the same reference-optimal daily evaporation, saving 221.7 L relative to no shifting, with zero conditional regret for C1. However, peak modeled treatment feed increased from 1,353.8 to 1,452.0 L/h.

That is especially relevant: a schedule can reduce total water demand while increasing peak water-supply requirements.

These omissions do not require redesigning the five figures. They show why a short, comprehensive findings inventory should come before further visualization work.

## Yes — the findings inventory should be our next reference document

I created a consolidated inventory covering the main hypotheses, experiments, numerical results, evidence types, and limitations from Steps 00–30.

Download Findings and Conclusions — Steps 00–30 (.md)

It groups the work into 11 research findings and identifies which ones are already represented by the five figures.

### What I would do next

| Priority | Action                                                                             | Reason                                                                |
| -------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| 1        | Adopt the findings inventory as the reference                                      | Prevents repeating experiments or overlooking established conclusions |
| 2        | Correct the summary README to include Step 30                                      | Its current statement is outdated                                     |
| 3        | Preserve all five existing figures                                                 | They already provide a strong, concise research overview              |
| 4        | Keep the capacity-feasibility and Step 30 results available as supporting evidence | Both are important for understanding decision value                   |
| 5        | Postpone additional plotting                                                       | No clear need for more figures before reviewing the complete findings |

For a presentation focused on physical cooling-water models and scheduling, we could eventually replace F5 with a Step 30 direct-water decision figure. But I would not make that change yet.

### Overall conclusion

We have made substantial progress on three questions: how facility electricity depends on operating conditions, how cooling physics determines water requirements, and when simpler models reproduce more detailed ones.

The remaining gap is not primarily visualization. It is determining when the additional physical detail produces materially better planning decisions and which findings are supported by measurements rather than simulations.

My recommendation is to treat the five figures as the concise presentation layer and the new findings inventory as the underlying research record. Together, they provide a much stronger foundation for assessing the next simulations than adding another round of EDA.
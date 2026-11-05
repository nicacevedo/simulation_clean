# Research plan: From M0 to decision-relevant energy–water models

## 1. Recommended modeling strategy

I recommend building a small, modular simulator with three connected layers:

Layer A — Workload and IT electricity

How much computing is performed, when, where, and with what electrical demand?

Layer B — Facility power, heat and cooling

IT electricity → heat → cooling mode → auxiliary electricity and direct water

Layer C — Grid and optimization

Electricity prices, emissions, off-site water, capacity, scheduling and decision regret

The important design choice is to separate power-model complexity from water-model complexity. We should be able to run an affine electricity model with either constant WUE or physical cooling-tower water calculations, without rebuilding the simulator.

This follows the physical decomposition used in LBNL's data-center prototype models, DOE cooling-water guidance, and recent workload-level water research.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://datacenters.lbl.gov\&sz=32)

datacenters.lbl.gov+2



### Keep the problem small initially

- Time resolution: Hourly, with 24-hour and seven-day optimization horizons.
- Decisions: When to process flexible IT workload; later, where to process it and which cooling mode to use.
- Outputs: IT/facility electricity, heat rejected, electricity cost, carbon, direct water, off-site water, hourly electrical peak, peak makeup demand and decision regret.
- Validation: Physical balances, held-out prediction performance where measurements exist, and common-reference evaluation of optimization decisions.

Do not begin with detailed thermal CFD, Modelica simulation, water-distribution hydraulics, batteries, or machine-learning schedulers.

## 2. Define the physical boundaries and variables first

Every model must use the same units and accounting conventions.

| Quantity                 | Symbol                     | Unit        | Definition                                                 |
| ------------------------ | -------------------------- | ----------- | ---------------------------------------------------------- |
| Completed computation    | \\(q\_{s,t}\\)             | Work units  | Work served at site \\(s\\), hour \\(t\\)                  |
| IT electricity           | \\(E^{IT}\_{s,t}\\)        | kWh         | Electricity used by computing equipment                    |
| Facility electricity     | \\(E^{DC}\_{s,t}\\)        | kWh         | IT plus non-IT facility electricity                        |
| Thermal duty             | \\(Q^{cool}\_{s,t}\\)      | kWh thermal | Heat removed by cooling equipment                          |
| Wet heat rejection       | \\(Q^{wet}\_{s,t}\\)       | kWh thermal | Heat entering wet heat-rejection equipment                 |
| Direct water withdrawal  | \\(V^{wd}\_{s,t}\\)        | L           | Water drawn into the facility boundary                     |
| Direct water consumption | \\(V^{con}\_{s,t}\\)       | L           | Water not returned to its source                           |
| Off-site water           | \\(V^{grid}\_{s,t}\\)      | L           | Electricity-related water, using a stated accounting basis |
| Electrical peak          | \\(P^{peak}\_{s,\Delta}\\) | kW          | Maximum average demand over interval \\(\Delta\\)          |
| Peak makeup flow         | \\(F^{peak}\_{s}\\)        | L/h         | Maximum hourly freshwater supply requirement               |

Use \\(\Delta t=1\\) hour initially, so power and hourly energy have the same numerical value but remain conceptually distinct.

Three fundamental equations apply throughout:

\\[ E^{DC}=E^{IT}+E^{overhead} \\]

\\[ V^{total,b}=V^{direct,b}+\gamma^{grid,b}E^{DC} \\]

\\[ Q^{heat}\_{IT}\approx E^{IT} \\]

The superscript \\(b\\) means withdrawal or consumption. Never combine withdrawal and consumption in the same total.

The heat equation is an energy-equivalent approximation: virtually all IT electricity becomes heat, but the fraction entering a particular cooling system depends on heat reuse, storage and equipment boundaries.

## 3. Exact model progression

Keep the original M0–M2 power naming. Add water refinements on a separate axis.

### Power models

| Model              | Mapping                                        | Purpose                                        | Status from our EDA                      |
| ------------------ | ---------------------------------------------- | ---------------------------------------------- | ---------------------------------------- |
| M0                 | \\(P\_{DC}=kP\_{IT}\\)                         | Mandatory constant-PUE benchmark               | Strong simple baseline                   |
| M1                 | \\(P\_{DC}=a+bP\_{IT}\\)                       | Separate fixed from load-dependent electricity | Preferred simple model at ESIF/Frontier  |
| M2a                | \\(P\_{DC}=a+c(T-T_0)+bP\_{IT}\\)              | Weather-dependent overhead                     | Valuable at Marconi100                   |
| M2                 | \\(P\_{DC}=a+c(T-T_0)+[b+d(T-T_0)]P\_{IT}\\)   | Weather-dependent marginal electricity         | Not consistently justified yet           |
| Physical extension | IT + explicit cooling and auxiliary components | Evaluate cooling-mode interventions            | Scenario first; calibrate where possible |

Start with wet-bulb temperature as the weather input for the common model comparison, while using dry bulb, temperature lift, or measured coolant conditions when appropriate to the actual cooling technology.

For the first physical extension:

\\[ P\_{DC,m} = P\_{IT}+P\_{other,m} +\frac{Q\_{cool}}{COP_m(T,\mathrm{PLR})} +P\_{pump,m}+P\_{fan,m}. \\]

Here \\(m\\) is the cooling mode. All component boundaries must be checked to avoid double-counting.

In the first simulations, fix COP and other mode coefficients for each hour using weather and a reference operating condition. This keeps the optimization tractable. Add part-load effects only if they materially change results.

### Water models

| Water model | Mapping                                                      | Purpose                                          |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------ |
| W0          | \\(V\_{direct}=w_0E\_{IT}\\)                                 | Constant WUE baseline                            |
| W1          | \\(V\_{direct}=w(z_t)E\_{IT}+V\_{base,t}\\)                  | Test weather- and mode-dependent water intensity |
| W2-Tower    | Heat rejection → evaporation → blowdown/makeup               | Cooling-tower physics                            |
| W2-Air      | Airflow × humidity-ratio change → evaporation → supply water | Direct-evaporative physics                       |

For W1, \\(z_t\\) represents weather and operating context. Its coefficients are currently scenario parameters, not identified marginal WUE measurements.

#### W2-Tower

\\[ E\_{evap,t}\\,[L]\approx 1.47\\,\alpha\_{lat,t}\\,Q^{wet}\_{t}\\,[kWh\_{th}] \\]

\\[ V\_{makeup,t}\approx E\_{evap,t}\frac{COC}{COC-1} \\]

The numerical coefficient assumes typical latent heat of vaporization and water density. The approximation neglects drift, leakage and storage variation.

#### W2-Air

\\[ V\_{evap,t}= \frac{\dot m\_{dry\\,air,t}\Delta t}{\rho_w} \left(\omega\_{supply,t}-\omega\_{outdoor,t}\right) \\]

for positive humidification/evaporation demand, with consistent time units.

Additional purification reject and unrecovered losses determine freshwater supply. This model is specifically relevant to Prineville-type misting, rather than cooling towers.

### The critical rule

Do not add a separate cooling-power model on top of a fitted total-facility PUE model. That would double-count cooling.

For cooling-mode simulations, either use an explicit component model or apply a clearly defined difference relative to the fitted baseline operating mode.

## 4. Controllable inputs: What does the optimizer actually decide?

We should distinguish controls, external conditions, and parameters. Many EDA variables are predictors but are not independently controllable.

| Variable                                 | Role                                | Initial treatment                                 |
| ---------------------------------------- | ----------------------------------- | ------------------------------------------------- |
| IT energy scheduled each hour            | Control                             | Optimize                                          |
| Flexible workload fraction               | Scenario constraint                 | 0%, 20%, 40%                                      |
| Hourly IT capacity                       | Physical constraint                 | Start at 125% of baseline                         |
| Workload deadline                        | Operational constraint              | Daily or weekly completion                        |
| Cooling mode: wet/dry                    | Control when installed and feasible | Initially compare fixed-mode cases                |
| Cooling setpoint                         | Potential control                   | Keep fixed initially                              |
| Cycles of concentration                  | Water-treatment setting             | Sensitivity parameter, not an hourly free control |
| Outdoor temperature and humidity         | External inputs                     | Real hourly weather                               |
| Electricity price, grid water and carbon | External inputs                     | Real or explicitly modeled hourly signals         |
| PUE/WUE coefficients                     | Model parameters                    | Fitted, reported or scenario-based                |

### First optimization formulation

Let \\(x_t\\) be IT energy scheduled in hour \\(t\\), and \\(x_t^0\\) the baseline.

For each allowed shifting window \\(\mathcal H\\):

\\[ \sum\_{t\in\mathcal H}x_t = \sum\_{t\in\mathcal H}x_t^0 \\]

\\[ (1-\phi)x_t^0 \le x_t \le P^{IT,max}\_t\Delta t. \\]

Here \\(\phi\\) is the flexible fraction.

This conserves IT energy, not necessarily completed computational work. It is the right simplification for the first pilot.

Later, replace it with:

\\[ \sum_t q_t\Delta t=Q\_{\mathrm{required}}, \qquad P\_{IT,t}=f(q_t,\text{hardware},N\_{\mathrm{active}}). \\]

The SPECpower and MLPerf measurements can support this extension.

### Additional operational constraints

Initially enforce a facility-power limit:

\\[ P\_{DC,t}\le P^{DC,max}. \\]

For cooling scenarios, also impose cooling-capacity and weather-feasibility constraints. A dry cooler, for example, cannot be assumed to satisfy a supply-temperature requirement in every weather condition.

Hourly makeup-water limits can be added as scenario constraints, but should not be described as measured Prineville limits.

The scheduling scenarios correspond to realistic demand-flexibility approaches discussed by ASHRAE and DOE: deferring noncritical jobs, controlling peak demand, adapting cooling operation, and eventually shifting workloads across locations.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.ashrae.org\&sz=32)

AI Data Center Energy Performance Framework+1



## 5. How to use the cluster's existing data

Do not download more data yet. The local repository inventory already supports the first complete campaign.

### Data-to-model mapping

| Data available in the repository                 | What to extract                                                         | How to use it                                                         |
| ------------------------------------------------ | ----------------------------------------------------------------------- | --------------------------------------------------------------------- |
| NLR 300 — ESIF, including full 2015–2025 archive | IT, cooling, pumps, HVAC, facility electricity, weather                 | Fit M0/M1/M2 and validate overhead                                    |
| ORNL Frontier, 2023                              | IT/facility electricity, auxiliary power, coolant temperatures and flow | Independently test facility power and thermal relationships           |
| Marconi100 ExaData                               | Chiller, CRAC, pump and IT electricity, weather                         | Test chiller-based architecture and weather dependence                |
| NLR Eagle 288/295/301                            | Node power, job times, allocation                                       | Later: realistic workload shapes and peaks                            |
| SPECpower, MLPerf, H100 measurements             | Power versus utilization or completed work                              | Later: convert fixed-energy to fixed-workload scheduling              |
| Prineville billing and Meta disclosures          | Monthly water patterns and annual reference values                      | Water accounting and seasonal sensitivity—not hourly WUE fitting      |
| NOAA + MISO/ERCOT + Open Grid Emissions          | Weather, electricity price, average carbon intensity                    | Real 2023 operating scenarios                                         |
| Macknick grid-water factors                      | Technology-specific withdrawal/consumption coefficients                 | Estimated grid-water accounting scenarios                             |
| Modelica v14 / EnergyPlus references             | Cooling modes, COP, tower and pump relationships                        | Parameterize physical scenarios; do not execute full plant models yet |

### The best site signals to start with

Use the already processed:

`data/frozen/signals_2023_v1`

with:

- Springfield, Illinois — MISO
- Dallas–Fort Worth, Texas — ERCOT

These contain an unusually useful combination of real regional weather and price signals, plus source-derived carbon and water factors.

The data-center installations at those locations will initially be hypothetical facilities. ESIF or Frontier coefficients used with these regions are technology templates, not site-matched observations.

Before running simulations, check the frozen signal files carefully: the inventory reports 8,904 rows, whereas calendar year 2023 has 8,760 hours. Resolve timestamp boundaries, duplicate hours and time zones rather than silently truncating or filling records.

Also preserve the distinction between historical average grid emission/water factors and causal marginal effects. The Water IMPACT methodology is useful for accounting but does not turn historical hourly averages into identified marginal generator responses.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://industrialapplications.lbl.gov\&sz=32)

Industrial Applications



### Cooling archetypes

Use three archetypes—not one universal facility model.

| Archetype                           | Representative evidence | Physical water mapping                                           |
| ----------------------------------- | ----------------------- | ---------------------------------------------------------------- |
| A. Efficient hybrid/free-cooled HPC | ESIF, Frontier          | Wet heat rejection fraction × evaporation/tower balance          |
| B. Chiller-based HPC/data center    | Marconi100              | Cooling load, COP, condenser rejection and tower makeup          |
| C. Direct-evaporative air-side      | Prineville PRN1         | Outdoor-air humidity, airflow, misting and purification/recovery |

Prineville's published PRN1 system uses outside-air economization and evaporative misting with reverse-osmosis treatment and recapture. Those characteristics should not automatically be assigned to every building on the expanded campus.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.opencompute.org\&sz=32)

Open Compute Project



## 6. The actual simulation experiments

I would define five experiments, but run only the first three initially.

### Experiment S0 — Verify the accounting and optimization

Purpose: Establish a working baseline with no complicated physics.

Use one hypothetical facility, 24 hours, and real 2023 regional price signals.

- Power: M0.
- Water: W0.
- Controls: 20% flexible IT energy.
- Constraints: fixed total IT energy, hourly capacity.
- Compare: no shifting versus minimum electricity-cost scheduling.

Expected verification: total IT energy is conserved, facility energy scales by constant PUE, and direct water is identical across schedules.

If direct water changes under constant WUE and fixed total IT energy, there is an accounting or implementation error.

### Experiment S1 — Does electricity-model complexity change decisions?

Compare M0, M1, M2a and M2 under identical scenarios.

Run two cases:

1. Facility peak capacity is nonbinding.
2. Facility peak capacity becomes binding.

This directly tests a major finding from the EDA.

Expected negative control: A weather-dependent intercept that is independent of the decision should not change the unconstrained optimal schedule, even if it improves prediction accuracy.

When a facility-power constraint binds, that same intercept can change which hours are feasible.

This is an important experiment because it distinguishes predictive improvement from decision value.

### Experiment S2 — Does water-model complexity change decisions?

Compare W0, W1 and W2-Tower, holding the power model fixed initially.

Use real weather and hourly modeled grid-water factors.

Compare three objectives:

- Minimize electricity cost.
- Minimize total water consumption.
- Minimize electricity cost subject to a water budget.

Water budgets provide an intuitive way to visualize the trade-off without relying entirely on arbitrary monetary weights for water.

Run both a constant-water reference and a weather-dependent physical scenario.

Key question: Under what conditions does additional information about water change the chosen schedule enough to matter?

The literature on water-aware cloud scheduling explicitly identifies possible conflicts between carbon and water objectives. Our experiment should test when those conflicts appear under our own assumptions, not presume their magnitude.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://arxiv.org\&sz=32)

arxiv.org



### Experiment S3 — Wet versus dry cooling

After S0–S2 work, add two cooling choices.

For each hour, define:

\\[ \Delta E_t=E\_{dry,t}-E\_{wet,t} \\]

\\[ \Delta V_t=V\_{wet,t}-V\_{dry,t}. \\]

For a water-consumption objective, dry cooling is preferable when:

\\[ \boxed{\Delta V_t>\gamma^{grid}\_t\Delta E_t} \\]

assuming both choices are feasible and direct and grid water use the same consumption basis.

Start by evaluating a fixed wet mode versus fixed dry mode over each test horizon. This avoids binary optimization and makes the physics easier to audit.

Only then add hour-by-hour switching, operating-mode constraints, and switching costs.

Include the electricity used by chillers, pumps and fans in the mode comparison exactly once.

### Experiment S4 — Geographic workload shifting

Use Springfield/MISO and Dallas/ERCOT.

Give both sites explicit capacities, cooling archetypes, and migration eligibility. Optimize where flexible work is performed, under shared work-completion requirements.

Compare cost, carbon, direct water and grid water.

This is a realistic published scenario family, but these two facilities remain representative simulated sites, not a measured pair of operational data centers.

Keep separate regional water outcomes visible. Equal liters of withdrawal or consumption at two locations do not necessarily imply equal local water scarcity impacts.

### Initial campaign size

| Stage                | Scope                                                                       | Approximate runs |
| -------------------- | --------------------------------------------------------------------------- | ---------------- |
| Local smoke test     | S0, 2–3 representative days                                                 | 10–20            |
| First research pilot | S0–S2, two regions, selected weeks, limited parameter sensitivities         | 40–80            |
| Small cluster study  | S0–S4, 24-hour and weekly horizons, multiple reference assumptions          | 100–300          |
| Targeted expansion   | Only scenarios showing meaningful regret, infeasibility or decision changes | As justified     |

Use representative cool, warm and high-price periods, rather than exhaustively simulating all combinations immediately.

## 7. The most important experimental method: Decision regret

For each experiment, solve the same feasible problem using different coefficient models.

Then evaluate every solution under a common reference scenario.

\\[ \boxed{ R_i= J\_{\mathrm{ref}}(x_i) - J\_{\mathrm{ref}}(x^\*\_{\mathrm{ref}}) } \\]

Report absolute regret, feasibility, peak violations and computational time.

If useful, also report:

\\[ R_i^{saving} = \frac{ J\_{\mathrm{ref}}(x_i)-J\_{\mathrm{ref}}(x^\*\_{\mathrm{ref}}) }{ J\_{\mathrm{ref}}(x\_{\mathrm{baseline}}) -J\_{\mathrm{ref}}(x^\*\_{\mathrm{ref}}) }. \\]

Only calculate this fraction when the achievable saving is meaningfully positive.

### Avoid favoring a complicated model by construction

Do not use M2/W2 as the only reference.

Run at least three reference cases:

| Reference                   | Purpose                                                  |
| --------------------------- | -------------------------------------------------------- |
| Simple reference            | Test scenarios where M0/W0 is actually correct           |
| Weather-dependent reference | Test the value of contextual information                 |
| Physical cooling reference  | Test model robustness under wet/dry operating mechanisms |

Keep parameter uncertainty separate from model structure. A model may fail because its coefficients are wrong, not because its functional form is inadequate.

Hourly water scenarios should remain labeled as simulations, because we still lack synchronized empirical water and IT measurements.

### A particularly important finding to test

Under fixed IT energy, a month-specific constant WUE does not change scheduling within that same month if no other terms change the decision.

Therefore, monthly WUE can improve water accounting yet provide little benefit for daily workload shifting.

Hourly variation, site allocation, cooling-mode control and capacity constraints are the mechanisms that can make water modeling more decision-sensitive.

This deserves a dedicated negative-control result.

## 8. Clean implementation and cluster workflow

### Recommended repository organization

Keep data preparation, physics, optimization, experiments and plots separate.

```
dc_resource_sim/
├── configs/
│   ├── pilot.yaml
│   ├── facility_parameters.yaml
│   └── source_registry.yaml
├── src/
│   ├── data/
│   │   ├── load_signals.py
│   │   └── validate_inputs.py
│   ├── models/
│   │   ├── power.py
│   │   ├── heat.py
│   │   └── water.py
│   ├── optimization/
│   │   ├── scheduling.py
│   │   └── evaluation.py
│   └── experiments/
│       └── run_scenario.py
├── tests/
├── runs/
└── notebooks/
    └── results_review.ipynb
```

Use the existing local cluster source folders read-only. Do not modify the frozen datasets or redownload large archives inside simulation jobs.

For the first implementation, Python, NumPy, pandas and SciPy's HiGHS linear-programming interface are sufficient.

### Standardize one hourly input table

Minimum fields:

| Field                              | Required                |
| ---------------------------------- | ----------------------- |
| `timestamp_utc`, `site_id`         | Yes                     |
| `price_usd_per_kwh`                | Yes                     |
| `temp_db_c`, `temp_wb_c`, `rh_pct` | Weather-dependent cases |
| `carbon_kg_per_kwh`                | Carbon scenarios        |
| `grid_water_consumption_l_per_kwh` | Off-site consumption    |
| `grid_water_withdrawal_l_per_kwh`  | Off-site withdrawal     |
| `baseline_it_kwh`                  | Yes                     |

Add source and accounting-basis metadata.

The model parameter file should contain reference IT capacity, calibrated or assumed \\(a,b,c,d\\), WUE definitions, cooling architecture, COP assumptions, wet heat fraction, latent fraction, CoC, and valid operating ranges.

Never silently substitute an illustrative water coefficient for a missing measured field. Mark scenario inputs explicitly and stop incompatible comparisons.

### Minimal run configuration

```

experiment: pilot_2023
regions: [Springfield_IL, Dallas_TX]
time_resolution_hours: 1
horizons_hours: [24, 168]

workload:
  baseline_it_kw: 1000
  flexible_shares: [0.0, 0.2]
  capacity_multiplier: 1.25
  preserve: it_energy

power_models: [M0, M1, M2a]
water_models: [W0, W1_scenario, W2_tower_scenario]

objectives:
  - electricity_cost
  - total_water_consumption
  - cost_with_water_budget

evaluation:
  references: [constant, weather_dependent, physical]
  check_peak_power: true
  check_water_balance: true

solver: highs
seed: 42

```

Use a facility's measured coefficients only over supported load ranges; for hypothetical 1 MW facilities, normalize and scale fixed overhead appropriately rather than copying absolute intercepts from a much smaller system.

### What every run should save

Each run needs only four essential outputs:

- `config.json` — exact inputs, assumptions, seed and code version.
- `summary.parquet` — one row per scenario/model/objective, including cost, water, peak, regret, feasibility and runtime.
- `hourly.parquet` — selected representative schedules and physical outputs.
- `validation.json` — mass/energy-balance tests, constraint violations, input coverage and solver status.

Also record source-file checksums and the training period used to fit the coefficients.

Do not save thousands of redundant plots or duplicate raw datasets in each run.

Once local tests pass, submit independent scenarios as a Slurm array, with one configuration per task and no downloads performed by worker jobs.

## 9. The figures that will tell us whether the refinements matter

Limit the first results to five principal figures.

F1

Observed and modeled resource mapping

Facility overhead versus IT load and wet bulb, including observed/predicted residuals and sample support. Establishes where M0–M2 are credible.

F2

Physical heat–water surfaces

Tower makeup versus wet heat rejection and CoC; direct-evaporative demand versus dry bulb and humidity at fixed airflow. Label both as physics/scenario mappings.

F3

Actual scheduling decisions

Hourly electricity price, grid-water intensity, weather, baseline IT demand, and M0/M2 schedules over the same representative week.

F4

Electricity-cost versus water trade-off

Pareto curve across water budgets, showing where water-conscious operation becomes more expensive and which decisions change.

F5

Model-sufficiency map

A heatmap of decision regret versus workload flexibility and water/weather variability, separated by cooling architecture.

F5 is the main research output we ultimately want. It directly identifies where a simple resource model is adequate and where an additional parameter matters.

## 10. What should trigger the next model refinement?

Do not refine models merely because their error is nonzero. Use an explicit progression.

| Observed result                                                | Next action                                                   |
| -------------------------------------------------------------- | ------------------------------------------------------------- |
| M0 predicts adequately and decisions barely change             | Keep M0                                                       |
| M1 reduces predictive error but schedules remain identical     | Retain M1 for accounting; no need for optimization complexity |
| Weather-dependent coefficients change decisions or constraints | Promote M2a/M2 for that application                           |
| Wet/dry choices drive large water–electricity trade-offs       | Add physical heat-rejection and mode models                   |
| Peak demand is underestimated or constraints violated          | Add native-resolution peak profiles or robust headroom        |
| Fixed-energy and fixed-workload solutions differ               | Introduce calibrated server/workload-power curves             |
| Thermal inertia changes feasible cooling schedules             | Add a simple one-state heat-storage model                     |
| Water-system hydraulics limit actual delivery                  | Only then consider detailed hydraulic simulation              |

This sequence keeps complexity tied to evidence.

## Final recommendation: What to implement first

I would begin with one self-contained simulator, separate from the large EDA notebook, implementing:

1. M0/M1/M2a facility electricity and W0 constant water.
2. Real hourly 2023 MISO/ERCOT signals from the local repository.
3. Fixed-energy workload shifting with daily deadlines and capacity limits.
4. Hourly grid-water accounting, with withdrawal and consumption separated.
5. W1 and simple W2-Tower water scenarios.
6. Common-reference decision regret, physical consistency checks, and five concise plots.

Run S0–S2 first. Add cooling-mode and multi-site decisions only when those work correctly.

The central hypothesis to test is:

> Constant PUE/WUE may be sufficient for many aggregate accounting and scheduling problems, while time-varying marginal water, cooling-mode feasibility, grid-water signals, and peak constraints may be the specific refinements that change operational decisions.

This is consistent with our existing EDA and with the literature, but its decision consequences remain to be established by the simulations.

The first objective is not to build the most realistic data-center simulator. It is to produce a reproducible model-sufficiency experiment that identifies, one refinement at a time, which physical relationships actually matter for electricity, heat, water and optimization decisions.


---

Updates after step 20:

# Revised research plan — Facility electricity, heat, and water

**Scope:** One facility and one hour first, followed by one 24-hour profile. Preserve completed Steps 00–20. Work through the physical and measurement boundaries before returning to optimization or groundwater planning.

**Immediate priority:** M0 → IT heat → W0 → one cooling architecture → evaporation → supply-water demand. Make one small change at a time, with an explicit check and stopping rule.

## 1. Why this revision is necessary

The original plan, *From M0 to decision-relevant energy–water models*, correctly proposed separate electricity, cooling, water, and optimization layers, and progressive model families M0–M2 and W0–W2. We should **keep that structure**. The later proposed overhaul moved too quickly to water networks and groundwater before we finished understanding the facility-level mappings. We should **defer that overhaul**.

Steps 00–20 answered important preliminary questions, but they do not constitute a calibrated facility electricity–water model. The most useful corrections are:

1. **Do not infer cooling electricity or cooling heat from total PUE alone.** $P^{DC}=kP^{IT}$ gives an aggregate electrical total. It does not identify which parts heat the servers, coolant, building air, or outdoors.
2. **Do not equate IT heat, chiller cooling load, wet-tower heat rejection, and evaporative cooling duty.** Each crosses a different physical boundary. In particular, a direct-evaporative air system does **not** send IT heat to a cooling tower.
3. **Do not equate evaporation, cooling-tower makeup, site water intake, billed municipal delivery, water consumption, and groundwater extraction.** They may differ substantially.
4. **Do not add modeled chiller/fan/pump electricity to an existing total-facility PUE prediction.** That double-counts overhead. Physical cooling electricity replaces the corresponding empirical component, or is used in a separate explicitly component-based model.
5. **Treat Steps 17–20 as correctly implemented conditional physics examples, not independent validation.** Their parameters were assumptions. A balance closing or an assertion passing does not establish a site's measured water use.
6. **Treat fitted IT-load slopes as predictive, not automatically causal.** The high-load holdout showed that extrapolating unrestricted $a+bP^{IT}$ can fail even when $b$ is stable across fitted periods.

The original proposal's groundwater, multi-sector allocation, and planning objectives remain longer-term motivations. They do not need to be implemented this week.

## 2. What is already established (do not repeat)

| Evidence | Main result | Status for this plan |
|---|---|---|
| Steps 00–04 | M0 energy accounting, ESIF 2023 day/hour checks, daily PUE and overhead variation | Keep as verified baselines |
| Steps 05–07 | M1-fixed generally generalizes better than unrestricted M1 in the high-load split; summer cooling/pumps explain the extra ~31 kW overhead, with an *accounting* identity | Do not redo EDA; no independent meter validation from the identity |
| Steps 08–10 | M0/M1-fixed scheduling equivalence without binding facility limits; differences under capacity limits; small real-price regret | Keep optimization code, pause new optimizations |
| Steps 11–14 | Hourly capacity errors matter; M2a-fixed, $P^{DC}=P^{IT}+a+c(T_{wb}-T_0)$, is the strongest simple predictive candidate across selected tests; one held-out-day decision test has small cost consequences | Keep as empirical evidence; do not use M2a coefficients as cooling equipment parameters |
| Steps 15–16 | W0 direct water unchanged by constant-energy scheduling; modeled grid-water choice changes schedule but is highly sensitive to time-pattern errors | Close this scenario, do not claim physical water savings |
| Steps 17–18 | Tower evaporation, blowdown, makeup, chiller condenser heat and latent-ratio scenarios pass balances | Keep for **tower/chiller** archetype only |
| Step 19 | Psychrometric tower calculation with assumed airflow and saturated leaving air passes; heat fraction is derived, not identified | Keep for **tower** archetype; no calibrated airflow/outlet state |
| Step 20 | Direct-evaporative air-side model passes dry/wet/infeasible cases and moist-air balances | Keep for **air-side** archetype; no site-specific controls or water treatment |
| Step 23 | `w0_water_basis.py`: A and B both 24,000 kWh IT → 12,000 L/day; peak modeled rate 500 vs 600 L/h; `water_basis = "onsite_direct_consumption_proxy"` | W0 is a constant *onsite direct-consumption* proxy per kWh of IT electricity. It is invariant to workload timing if total IT energy is fixed. Its hourly output is not a measured intake/makeup flow. It contains no information about cooling architecture, weather, temperature, airflow, treatment losses, or the origin of the water. |

### What the empirical evidence does and does not establish

- ESIF 2023 **does** provide measured or derived electrical operating signals and weather, allowing hourly facility-power model evaluation. PUE-implied overhead reconciling its components is not independent validation if PUE is computed from those same components.
- Prineville records **do** provide billed monthly water categories. Without synchronized facility IT electricity, operating mode, treatment flows, and meter boundaries, they do not identify hourly evaporation or WUE.
- The illustrative physical models **do** conserve energy and mass under their assumptions. They do not show that the assumed cooling technology, flow rates, controls or supply-water treatment describe a real facility.

## 3. The physical model: variables and boundaries first

Use **power** (kW) and **heat rate** (kW thermal) within each hour, **electricity and thermal energy** (kWh and kWh thermal) over time, and **water flow** (L/h) or **volume** (L). Set $\Delta t=1$ hour for the first checks; do not confuse numerical equality with physical equality of units.

### A. Electrical meter boundary

$$
P_t^{DC}=P_t^{IT}+P_t^{nonIT}, \qquad E_t^{DC}=P_t^{DC}\Delta t.
$$

**M0** is $P_t^{DC}=kP_t^{IT}$, so it identifies only $P_t^{nonIT}=(k-1)P_t^{IT}$. We cannot assign all of this overhead to a chiller or a fan.

**M1-fixed**, **M1**, and **M2a-fixed** remain alternative *empirical predictors* of the same facility meter; their use is not a separate cooling-plant energy source.

### B. IT thermal boundary

For an idealized steady-state server-room experiment,

$$
\dot Q_t^{IT\rightarrow room}\simeq P_t^{IT}.
$$

More generally, track heat exported, heat stored, and internal sources explicitly. A useful *accounting identity* is

$$
\dot Q_t^{IT\rightarrow room}=P_t^{IT}-\dot Q_t^{other\ destinations}-\frac{dU_{IT}}{dt}
$$

where terms excluded by the simplified model are zero **assumptions**, not measured zeroes. Do not replace the left side by total $P^{DC}$ without locating non-IT heat sources.

### C. Cooling architecture: keep two different branches

**Branch A — Direct evaporative air cooling:** outside air enters a misting/evaporative stage, conditioned supply air absorbs server-room heat, and warm air leaves or recirculates. The air stream carries server heat; **IT heat is not equated to evaporative latent duty**. Use the psychrometric and airflow balances from Step 20.

**Branch B — Water-cooled chiller and cooling tower:** the chiller removes a thermal load; if all compressor input reaches its water-cooled condenser, $\dot Q^{tower}\approx\dot Q^{chiller\ load}+P^{compressor}$. Tower evaporation and blowdown follow Steps 17–19. Other paths (dry rejection, pump heat, storage) are explicit exclusions or separate terms.

Do **not** connect Branch A's humidification directly to Branch B's tower cycles of concentration. These are different systems.

### D. Water accounting boundary

Define and report **separately**:

- $V^{evap}$ — water evaporated by the chosen cooling process (part of onsite consumption).
- $V^{makeup}$ — process water required to replace losses, e.g. tower evaporation + blowdown (not identical to evaporation).
- $V^{intake}$ — water delivered/withdrawn across the facility boundary, potentially including treatment reject, other uses and storage changes.
- $V^{discharge}$ — water leaving to sewer, surface water or other sinks; the destination matters.
- $V^{consumption}$ — water not returned to the relevant water-resource boundary during the accounting period.
- $V^{groundwater}$ — source-specific groundwater withdrawals; **not** inferred automatically from municipal supply.

For a clearly specified site boundary and period, use the complete mass balance

$$
V^{in}+V^{other\ imports}=V^{evap}+V^{discharge}+V^{other\ exports}+\Delta V^{storage}.
$$

Avoid counting internal recirculation twice. State the return-flow boundary before claiming net consumption.

**W0** is an explicit baseline $V^{direct,con}=w_0E^{IT}$ **only if** $w_0$ is defined on a direct-consumption basis. If the actual data measure intake, use a separately named intake intensity, not the same $w_0$.

### E. An important interpretation check from Steps 18–19

The diagnostic ratio $Q_{latent}/Q_{tower}$ can exceed 1 if sensible heat transfers in the opposite direction; Step 19 found 1.019 in one scenario. Therefore, a "latent fraction" restricted to $[0,1]$ is a convenient **scenario assumption** in Step 18, not a universal physical bound. Report the sensible/latent sign convention rather than clipping a derived value.

## 4. Small-step implementation sequence

**Rule:** One conceptual addition per step. Reuse the verified scripts rather than rewrite them. Every step produces a compact table, assertions where appropriate, and a short statement of what is *measured*, *inferred*, or *assumed*.

### Step 21 — Freeze one reference case and audit its boundaries **(DO THIS NEXT)**

**Question:** Are M0, IT heat, W0, tower evaporation/makeup and direct-air evaporation being compared with consistent definitions?

**Inputs:** A constant 1,000 kW IT load for one hour and 24 hours; $k=1.0471$, $w_0=0.5$ L/kWh IT; Steps 17–20's existing published illustrative assumptions.

**Checks:**

1. $P^{DC}=1047.1$ kW, non-IT electricity $=47.1$ kW. In 24 hours: $E^{IT}=24,000$ kWh, $E^{DC}=25,130.4$ kWh, non-IT $=1,130.4$ kWh.
2. Idealized IT heat is $1000$ kW thermal, or $24,000$ kWh thermal per day; **do not** call the 47.1 kW overhead "chiller heat" without a component boundary.
3. W0 direct consumption is $500$ L/h and $12,000$ L/day **by illustrative assumption**.
4. Under Step 20's *different* direct-air assumptions (30°C, 30% RH), evaporation is approximately $489.4$ L/h. It is not site intake, and numerical similarity to W0 is not calibration.
5. Under Step 17's *different* tower assumptions, makeup is approximately $1,959.2$ L/h. Do **not** add tower and air results or compare them as if they shared equipment.

**Deliverable:** One compact model-boundary table and a short `boundary_and_units.md` (or append it to the current modeling context); no new physics script is needed. **Stop** when every flow has its proper physical boundary, unit and empirical/assumed status.

### Step 22 — Connect M0 to IT heat, without inventing a cooler

**Question:** What can IT electricity alone tell us about the heat that a particular cooling architecture must handle?

**Action:** Reuse constant and 0.8/1.2 MW IT profiles, and the one-hour/24-hour accounting. Explicitly introduce $f_{room}$, the share of IT electrical energy appearing as heat in the cooling boundary: $Q^{room}=f_{room}E^{IT}$; use $f_{room}=1$ as the initial limiting case. Do not replace this by the tower wet-rejection fraction or a universal equipment coefficient.

**Check:** With equal total IT energy and fixed $f_{room}$, the daily thermal load matches; the peak thermal duty differs. If time-varying heat storage or reuse is not modeled, mark it excluded.

**Deliverable:** A one-hour and one-day heat ledger with assumptions; no model fitting. **Stop** once heat destinations are clear.

### Step 23 — Establish W0 and its **measurement meaning**

**Question:** Is the simple direct-water model predicting evaporation, intake, or total onsite consumption?

**Action:** Keep $V^{direct,con}=w_0E^{IT}$ with $w_0=0.5$ L/kWh IT as an explicit scenario. Show the same total water for both load profiles and different peak water rate; do **not** infer this coefficient from Prineville bills. Add a separate `water_basis` label to the result, not a more complex WUE formula.

**Check:** $\sum_tV_t^{W0}$ is invariant to energy-preserving scheduling. Withdrawal and consumption are never summed together. Report peak L/h separately from total L.

**Deliverable:** Small W0 table and one invariance assertion. **Stop** when the basis is unambiguous.

### Step 24 — Bring in **one** physical water branch: direct evaporative air

**Question:** How does water evaporation arise from *airflow and humidity change*, instead of from an assumed WUE?

**Action:** Reuse Step 20's verified psychrometric functions with the same 1 MW IT case. Reproduce only (i) 20°C/50% RH dry, (ii) 30°C/30% RH wet, (iii) 30°C/70% RH infeasible. Keep the original assumed temperature rise, supply limit and saturation effectiveness. Do not implement mixing, recapture, RO, extra fans or chiller fallback in this step.

**Checks:** Air and water balances, supply saturation check, equipment-effectiveness feasibility, and $V^{evap}=m_{da}\Delta\omega/\rho_w$. A physically infeasible hour is **flagged**, not assigned zero use and called served.

**Deliverable:** Three-row mapping from ambient air + IT heat to airflow, cooling feasibility and evaporation. No new model is required beyond Step 20. **Stop** when the physical explanation, including the limited role of RH at a fixed target supply temperature, is clear.

### Step 25 — Add exactly one supply-water parameter to W2-Air

**Question:** How does evaporation differ from water delivered to the cooling process?

**Action:** Add an explicitly hypothetical treatment yield $\eta$ to **the idealized direct-air branch only**. In the simplest no-recovery/no-other-losses example:

$$
V^{process\ intake}=V^{evap}/\eta, \qquad V^{treatment\ reject}=V^{process\ intake}-V^{evap}.
$$

Check $\eta=1$ and $\eta=0.8$. For $489.4$ L/h evaporation, $\eta=0.8$ gives approximately $611.7$ L/h intake and $122.3$ L/h reject. **These are scenario quantities, not Prineville RO measurements.** In a real system, recovery, drain, sanitary use and storage require additional explicit terms.

**Checks:** All values nonnegative; intake = evaporation + reject in this simplified system; a lower yield raises intake without changing process evaporation. Do not call all intake "consumption" or "groundwater".

**Deliverable:** One extra parameter and a two-row comparison. **Stop** before adding recapture, losses or a fitted yield.

### Step 26 — One 24-hour water/heat trajectory (only after Steps 21–25)

**Question:** What changes when weather varies over time, while the equipment assumptions stay fixed?

**Action:** Use one explicitly hypothetical 24-hour set of ambient states or one verified location-matched weather day. Keep IT power at 1 MW and avoid optimizer decisions. Compute hourly M0 electricity, IT thermal duty, W0, W2-Air evaporation, process intake and feasibility, plus daily totals and peak L/h. Do not fill an infeasible hour with zero water: indicate unmet supply-temperature conditions and do **not** claim a feasible complete-day total unless a fallback is specified.

**Checks:** Each feasible hour obeys its balances; 24-hour energy totals reconcile; treatment intake and reject balance; no mixing of site-specific ESIF power coefficients with claims about Prineville operations.

**Deliverable:** One compact 24-row table and summary, with a clear note about any infeasible hours. **Stop** after one day.

### Step 27 — Minimal data-boundary check, not calibration

**Question:** Which components of our outputs are independently observable in the current Prineville records?

**Action:** Reuse the previously drafted Step 21 Prineville meter-ledger instructions, but perform a bounded 2023 meter/category audit **after** the modeling meanings are stable. Preserve municipal delivery, bulk delivery, well-for-sewer, discharge and annual corporate withdrawal boundaries separately. Use the meter-swap history. Do not fit an hourly WUE or treatment yield from monthly totals.

**Deliverable:** A one-page measured/missing-variable matrix and monthly source ledger. **Stop** after unit and date checks, without attempting to force an annual reconciliation.

### Step 28 — Power/cooling coupling, only after we understand each branch

**Question:** If cooling choice changes fan/pump/chiller demand, how can we update facility electricity **without counting it twice**?

**Action:** State two alternatives clearly: (A) use empirical total-facility $P^{DC}=kP^{IT}$ for the accounting baseline and **do not** add explicit cooling electricity; (B) use $P^{DC}=P^{IT}+P^{other}+P^{fan}+P^{pump}+P^{chiller}$ with mutually exclusive components and the correct cooling architecture. Only use (B) for cooling interventions if physical coefficients or transparent ranges are available. Do not transfer ESIF coefficients to Prineville without labeling this a hypothetical template.

**Check:** Component sums match the chosen meter boundary; no term appears twice; if explicit cooling terms are absent, do not claim an electricity–water technology trade-off.

**Deliverable:** One boundary-consistent energy/water comparison, not a new large regression campaign.

### Step 29 — Return to water-sensitive decisions (later)

Only when W0 and at least one W2 branch have traceable, internally consistent inputs, compare (i) fixed load, (ii) cost-optimal load, and (iii) one water-constrained alternative. Hold the power model fixed when testing water complexity. Report feasibility under wet cooling, energy cost, direct consumption, intake/peak supply and any constraint violations. A reference case is a **declared scenario**, not empirical water truth unless synchronized site data exist. Do not resume broader site shifting or groundwater planning within this short sequence.

## 5. Model progression without mixing complexity

| Stage | Electrical model | Heat model | Water model | What can be concluded |
|---|---|---|---|---|
| **A — Baseline** | M0 total electricity | $Q^{IT}\simeq E^{IT}$, declared boundary | W0 consumption intensity | Accounting and energy-conservation checks only |
| **B — Physical water** | **Same M0** | Server-air heat balance **or** chiller/tower heat balance | W2-Air **or** W2-Tower | Conditional evaporation/makeup and cooling feasibility |
| **C — Water supply** | **Same M0** | Same selected branch | Treatment yield / discharge / storage | Intake versus consumption versus sewer/return flows |
| **D — Electrical refinement** | Existing fitted M1-fixed or M2a-fixed for *prediction*, or explicit components for *technology comparison* | Same branch, boundaries audited | Same water mapping | Predictive and/or conditional technology differences, not automatic causal effects |
| **E — Decision value** | Chosen defensible power mapping | Explicit feasibility | W0 versus W2 scenarios | Conditional scheduling implications and model sufficiency |

**Do not jump diagonally in this table.** When a water assumption changes, leave electrical assumptions unchanged; when a power model changes, keep the water model fixed.

## 6. What to do this week

**Minimum successful week (recommended):** complete **Steps 21–23**. This means (i) audit the boundary/units, (ii) explicitly connect M0 to *IT* heat while identifying unknown heat destinations, and (iii) make W0's consumption basis unambiguous.

**If those are clearly resolved:** do **Step 24** by reviewing the already coded W2-Air model as a physical extension. **Only if time remains:** add Step 25's one-parameter supply balance.

Do **not** plan Step 26's weather day, Step 27's meter cleanup, or any new optimization as commitments for this week. They remain next steps conditioned on passing the simpler checks.

### The expected outcome this week

A self-consistent one-site, one-hour/one-day set of statements:

- Given IT electricity, **M0 predicts facility electricity**.
- Given IT electrical input and an explicitly chosen thermal boundary, we know how much **IT heat** must be handled under the steady-state assumption; we do **not** know its equipment destination automatically.
- Given $w_0$, **W0 predicts a stated water-accounting category** without claiming cooling physics.
- Given one air-cooling architecture and its parameters, **W2-Air predicts evaporation and feasibility**, not automatically total site intake.
- Given a water-treatment yield, a *separate* balance can estimate process intake and reject under transparent assumptions.

If a quantity is unobserved, label it as such. We should prefer a correct, small, partially identified model to a complicated model that appears to predict variables we cannot measure.

## 7. Rules for evidence, implementation, and stopping

1. **Evidence tags:** `measured`, `derived from measured`, `assumed engineering input`, `modeled scenario`, `unidentified`. Record them alongside every principal coefficient and output.
2. **No architectural leakage:** ESIF electricity coefficients are not Meta/Prineville fan or chiller measurements. Tower and direct-air models never share water-treatment assumptions automatically.
3. **No compensating fits:** do not tune airflow, efficiency, cooling split, treatment yield or WUE to make unrelated municipal totals appear to match.
4. **No fake validation:** assertions verify code and physics; independence of the reference data is required for empirical validation.
5. **No unnecessary scaffolding:** reuse `w2_tower_first.py`, `w2_tower_heat_boundary.py`, `w2_tower_psychrometric.py`, and `w2_air_first.py`. One small change or note per step; do not refactor the repository or create a large run matrix.
6. **Explicit success criteria:** after each step, report one physical balance, one key number, the most important assumption and the one thing the result does *not* establish.
7. **No optimization before boundaries:** water-sensitive scheduling resumes only after evaporation, intake and consumption are correctly distinguished.

## 8. Longer-term objectives retained from the original plan

The original S0–S4 experimental structure remains useful but should resume only after the relevant facility models are stable:

- **S0:** M0/W0 accounting and scheduling invariant — already demonstrated.
- **S1:** power-model decision relevance — already demonstrated under controlled capacity limits.
- **S2:** water-model decision relevance — grid-water accounting completed as a fragile conditional scenario; **direct W2** still needs physical boundary and measurement review before stronger conclusions.
- **S3:** wet/dry cooling comparisons — defer until both electricity penalties and water savings are represented without double counting, and all modes satisfy thermal constraints.
- **S4:** geographic workload shifting — defer until site archetypes and source-water categories are comparable.

Groundwater/source-aware planning and the proposal's agricultural/municipal competition questions remain important **subsequent** research stages, not the next coding task.

## 9. Single immediate instruction

**Next: Step 21 — do not write another full water model.** Produce a one-page energy–heat–water boundary ledger for M0/W0 and the two previously verified cooling architectures using the constant 1 MW case. Correct any mistaken equivalences, mark every assumption, and stop. Only after the ledger is unambiguous should we add the next relationship.

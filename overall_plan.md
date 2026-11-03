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
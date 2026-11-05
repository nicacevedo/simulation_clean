# Data-center electricity, heat, and water: current model and experiments

**Status:** through Step 31 (November 2026). **Scope:** one hypothetical data center, hourly models and 24-hour workload scheduling, with some relationships evaluated using measured 2023 ESIF inputs. This is a concise description of the *implemented research setup*, not the full groundwater-planning formulation.

## 1. Question and system boundary

**Research question:** Which additional information or physical detail is necessary to predict data-center electricity and cooling-water requirements **and make materially better planning decisions**?

Current chain: **scheduled IT electricity → IT heat → facility overhead and cooling → process evaporation/feed**, optionally combined with electricity prices and modeled **off-site grid water**. Each simpler model is judged on two separate questions: **model reduction** (does it reproduce the more detailed model?) and **decision sufficiency** (does optimizing with it give a schedule that is feasible and near-optimal under the detailed model?).

We keep the following quantities distinct:

- **Electricity:** IT energy, non-IT overhead, and total facility energy.
- **Thermal energy:** IT-generated heat, heat entering the *specific cooling process*, and wet heat-rejection duty. They need not be equal.
- **Water:** W0's illustrative onsite-consumption proxy; W2-Air **process evaporation**; treatment **feed** and **reject**; tower **evaporation** and **makeup**; utility **withdrawal**; and modeled **grid-related water consumption**. These cannot be treated as interchangeable or combined without matching their boundaries.

The eventual project concerns **data-center siting, source-specific withdrawals, groundwater networks, agricultural/municipal competition, and policy**. Those groundwater and multi-site components are **not implemented or validated** in the present single-site experiments.

## 2. Notation and units

Use hourly intervals $t=0,\ldots,23$, with $\Delta t=1$ h in the current scheduling tests. Power and one-hour energy are numerically equal **only** at this time step.

| Symbol | Definition | Unit |
|---|---|---|
| $x_t$ | IT electricity scheduled in hour $t$ (optimization variable) | kWh |
| $P_t^{IT}=x_t/\Delta t$ | Average IT electrical power | kW |
| $P_t^{DC}$, $P_t^{over}$ | Total facility power and non-IT overhead | kW |
| $Q_t^{air}$, $Q_t^{wet}$ | Heat to server air and heat to wet rejection, as rates | kW thermal |
| $T_{db,t}$, $T_{wb,t}$, $RH_t$ | Outdoor dry-bulb, wet-bulb and relative humidity | °C, °C, fraction |
| $V_t^{evap}$, $V_t^{feed}$, $V_t^{reject}$ | Process evaporation, treatment feed and liquid reject **over an hour** | L |
| $F_t^{feed}=V_t^{feed}/\Delta t$ | Average hourly treatment-feed rate | L/h |
| $\pi_t$, $\gamma_t$ | Electricity price and **average** grid-water consumption factor | $/kWh, L/kWh |
| $\phi$, $\eta$ | Flexible IT-energy share and treatment-water recovery | dimensionless |

**Accounting:** $E_t^{DC}=P_t^{DC}\Delta t=E_t^{IT}+E_t^{over}$, and $V_t^{grid,cons}=\gamma_t E_t^{DC}$. Grid-water factors used so far are modeled **average** consumption factors, not marginal physical savings.

## 3. Electricity and heat models

| Model | Mapping for hourly average facility power | Added information / assumption |
|---|---|---|
| **M0** | $P^{DC}=kP^{IT}$ | Constant PUE $k$ |
| **M1-fixed** | $P^{DC}=P^{IT}+a$ | Constant non-IT overhead |
| **M1** | $P^{DC}=a+bP^{IT}$ | Fit load slope $b$ |
| **M2a-fixed** | $P^{DC}=P^{IT}+a+c(T_{wb}-T_0)$ | Weather-dependent overhead, fixed IT slope $1$ |
| **M2a** | $P^{DC}=a+bP^{IT}+c(T_{wb}-T_0)$ | Free IT slope and weather term |

$T_0$ is the training-window mean wet-bulb temperature. Parameters are **specific to the training window and site**. For example, the Jan–Aug 2023 ESIF fit (Step 05) gave $k\approx1.0471$ and M1-fixed $a\approx73.13$ kW; the Jan–Aug M2a-fixed fit (Step 14) gave $c\approx1.80$ kW/°C with $T_0\approx6.22$°C. These are not universal equipment coefficients. The ESIF facility reference is **IT power × reported PUE**, not an independent facility meter.

Almost all IT electricity ultimately appears as heat, but the relevant cooling boundary is explicit:

$$Q_t^{air}=f_{air}P_t^{IT}, \qquad Q_t^{wet}\ \text{is separately specified by the cooling architecture.}$$

Here $f_{air}$ is an **assumed** share; all W2-Air experiments use $f_{air}=1$. **Do not add modeled chiller, fan or pump electricity to an already fitted total-facility PUE model** without first redefining the overhead boundary; that would double-count cooling power. Likewise, the fitted overhead describes **ESIF's actual cooling plant**, not the hypothetical W2-Air plant (whose fan and pump electricity is not modeled), so combining them in one objective requires an explicit electricity boundary for the hypothetical plant.

## 4. Water-model ladder (separate physical boundaries)

| Model | Hourly water mapping | What it estimates |
|---|---|---|
| **W0** | $V_t^{W0}=w_0 x_t$, with illustrative $w_0=0.5$ L/kWh IT | Onsite **direct-consumption proxy** only |
| **C0** | $V_t^{C0}=c_0x_t$, with frozen $c_0=0.14688$ L/kWh IT | Constant **process-evaporation** surrogate of W2-Air |
| **C1** | $V_t^{C1}=\beta x_t(T_{db,t}-25)_+$, $\beta=0.09788$ L/(kWh IT·°C) | Temperature-excess **process evaporation**, frozen at $\Delta T_{server}=15$°C |
| **W2-Air** | $V_t^{evap}\approx \dot m_{da,t}(\omega_{sup,t}-\omega_{oa,t})\Delta t/\rho_w$ | Psychrometric **process evaporation** plus cooling feasibility |
| **W2-Tower** | $V_t^{evap}\approx1.47\alpha_{lat,t}Q_t^{wet}\Delta t$; $V_t^{makeup}\approx V_t^{evap}COC/(COC-1)$ | Evaporation and **tower makeup** for a distinct wet-rejection architecture |

W2-Air uses dry-airflow $\dot m_{da}\approx3600Q^{air}/(c_{p,ma}\Delta T_{server})$ in kg dry air/h when $Q^{air}$ is in kW and moist-air heat capacity $c_{p,ma}$ is in kJ/(kg·°C); $\rho_w$ is in kg/L. The water equation then uses $\Delta t$ in hours and humidity-ratio change $\Delta\omega=\omega_{sup}-\omega_{oa}$ (supply minus outdoor air, kg water/kg dry air). Its **specific assumed controller** sets modeled evaporative-process use to zero at $T_{db}\le25$°C. At warmer conditions, it checks whether the target supply $T_{sup}=25$°C can be achieved with evaporative effectiveness $\varepsilon=(T_{db}-T_{sup})/(T_{db}-T_{eq})\le0.8$, where $T_{eq}\approx T_{wb}$ is the adiabatic-saturation temperature; **infeasible means N/A, not zero**. The real ESIF system has **not** been shown to have this hypothetical cooling configuration.

**Why C1 matches W2-Air.** In a feasible wet hour, W2-Air's adiabatic energy balance gives exactly $\Delta\omega=c_{p,oa}(T_{db}-T_{sup})/h_{fg,eff}$, and the airflow's $c_{p,ma}$ is evaluated at supply humidity ($c_{p,sup}$). Hence

$$V_t^{evap}=\frac{3600\,f_{air}\,x_t\,(T_{db,t}-T_{sup})}{\rho_w\,h_{fg,eff}\,\Delta T_{server}}\cdot\frac{c_{p,oa,t}}{c_{p,sup,t}},$$

with $c_p=1.006+1.86\,\omega$ kJ/(kg·°C) and $h_{fg,eff}=2501+1.86\,T_{sup}-4.186\,T_{water}\approx2443$ kJ/kg ($T_{sup}=T_{water}=25$°C). With $f_{air}=1$ and $\Delta T_{server}=15$°C the leading factor is 0.0982 L/(kWh IT·°C); the only other weather dependence is the ratio $c_{p,oa}/c_{p,sup}\approx0.99$–$1.00$. C1 was fitted numerically to W2 outputs, but its form and coefficient (0.09788) follow from this identity, and its error is the variation of that ratio. C1's accuracy is therefore evidence that W2-Air **reduces** under these assumptions, not independent evidence of predictive accuracy. C1 must be re-derived (or W2 used) when $f_{air}$, $\Delta T_{server}$, $T_{sup}$ or the controller change, and it cannot flag infeasible hours. The identity also shows W2 evaporation is proportional to $x_t$ at given weather, so the hourly intensities $w_t^{W2}$ in §5 are exact.

For the **illustrative direct-air treatment** (Step 25 onward), with recovery $\eta=0.8$ and no storage or extra water uses:

$$V_t^{feed}=V_t^{evap}/\eta,\qquad V_t^{reject}=V_t^{feed}-V_t^{evap}.$$

Changing recovery affects feed and reject, not the modeled evaporation. **Feed is not necessarily utility withdrawal or groundwater extraction.** W2-Tower instead uses wet rejection duty, latent heat fraction $\alpha_{lat}$ and cycles of concentration $COC$; its 1.47 L/kWh thermal is $3.6/h_{fg}$ with $h_{fg}=2.45$ MJ/kg. It must not be conflated with W2-Air. This branch closed after Steps 17–19 and is not used in decision experiments.

## 5. Scheduling experiment: variables, objectives, constraints

**Implemented single-day reference (Steps 30–31):** hypothetical constant **1,000 kW IT** for 24 h ($24{,}000$ kWh), $\phi=20\%$ flexible, **1,250 kW IT cap**, observed **ESIF weather on 2023-07-24 UTC** (all 24 hours W2-feasible), assumed direct-air cooling and $\eta=0.8$. **Fixed IT energy is a workload proxy; we have not modeled variable GPU performance or fixed computational work.**

Let $b_t=1{,}000$ kWh be baseline hourly IT energy, $f_t=(1-\phi)b_t=800$ kWh be nonflexible energy, $r_t=\phi b_t=200$ kWh be newly available flexible energy, and $y_t$ be flexible energy served. Then $x_t=f_t+y_t$ is the decision.

$$\begin{aligned}
0 &\le y_t\le P^{IT,max}\Delta t-f_t,\\
\sum_{\tau=0}^t y_\tau &\le \sum_{\tau=0}^t r_\tau && \text{(no work before arrival)},\\
\sum_{t=0}^{23}y_t&=\sum_{t=0}^{23}r_t=4{,}800\ \text{kWh} && \text{(all work completed)}.
\end{aligned}$$

The **same feasible workload problem** is solved under different models. Tested objectives include:

- **Electricity cost:** $\min_x\sum_t\pi_t P_t^{DC}(x_t)\Delta t$.
- **Modeled direct-air evaporation:** $\min_x\sum_tw_t^m x_t$, where $m\in\{C1,W2\}$ and $w_t^m$ is a frozen hourly **evaporation intensity** (L/kWh IT).
- **Modeled grid-water consumption (separate earlier scenario):** $\min_x\sum_t\gamma_t E_t^{DC}(x_t)$.

**Constant intensities cannot change a water-only schedule.** Every feasible schedule has $\sum_tx_t=24{,}000$ kWh, so any constant intensity $w$ (W0, C0) gives the same total $24{,}000\,w$ for all of them (W0: 12,000 L/day). Water-only scheduling becomes decision-relevant only with hour-varying intensities ($w_t^{C1}$, $w_t^{W2}$, $\gamma_t$).

The LP may also impose a facility power cap $P_t^{DC}\le P^{DC,max}$, and **Step 31** adds an assumed hourly process-feed cap:

$$\frac{w_t^m x_t}{\eta\Delta t}\le F_{max}\qquad\forall t.$$

W2 and C1 each use **their own** intensities in optimization and in their capacity constraints; their resulting schedules are then **both scored under W2**. If a C1 solution violates the W2-evaluated cap, it is **infeasible**, not a low-regret solution. For feasible schedules, conditional regret is:

$$R_{C1}=\sum_tw_t^{W2}x_t^{C1}-\min_{x\in\mathcal F_{W2}}\sum_tw_t^{W2}x_t.$$

The common feasible reference $\mathcal F_{W2}$ includes the **same** workload restrictions and any W2-evaluated cap. **No electricity-cost-versus-direct-evaporation joint objective has been tested in Steps 30–31.**

## 6. Inputs, evidence, and what has been established

| Input / reference | Used for | Interpretation / qualification |
|---|---|---|
| **NLR (formerly NREL) ESIF 2023** IT, PUE, overhead components, outdoor weather | Power-model fitting; physical-weather replay | Real observations; facility reference is PUE-implied. Historical power and water replays have **different sample filters/coverage**. |
| **2023 ESIF weather on July 24** | Steps 30–31 | Real weather driving a **hypothetical** 1 MW direct-evaporative plant. |
| **MISO prices / modeled grid-water factors** | Earlier cost/grid-water scheduling | Regional scenarios, not site-matched ESIF measurements or causal marginal grid-water savings. |
| **Prineville city bills + Meta annual disclosure** | Annual water-accounting check | Reported municipal billing and rounded withdrawals; meter overlap and sources unresolved. **Not** W2 validation. |

**Main hypotheses and observed outcomes (only for the tested cases):**

| Hypothesis / question | Steps (record) | Result | Evidence boundary |
|---|---|---|---|
| **H1. A fixed PUE describes different operating regimes.** | 00–07, 12–14 (`findings.md` #1–3) | Not reliably: ESIF overhead changes with operating conditions, and M0 can overpredict high-load facility demand. | PUE-implied power reference, historical holdouts. |
| **H2. Better average power prediction necessarily means safer power limits.** | 11 (`findings.md` #4) | No: MAE and hourly underprediction/headroom risk rank models differently. | Model predictions; hypothetical facility limits. |
| **H3. Power-model choice materially changes cost-optimal schedules.** | 08–10, 14 (`step09.md`, `step15.md`) | In the tested cost-minimization formulations, model choice changed the schedule when the facility limit became binding: the M0 schedule then exceeds the limit by **16.90 kW** under M1-fixed, and the M1-fixed schedule costs **$30.77** more than necessary under M0. With real MISO prices on one day, weather-dependent overhead was worth **< $1.25/day**. | Model-to-model counterfactuals; hypothetical limits; synthetic prices, then one real price day. |
| **H4. Grid-water-aware scheduling materially reduces modeled water.** | 15–16 (`step16.md`) | No: the schedule changes, but saves only **122.5 L/day** of modeled grid water (0.28%; 0.22% of total modeled water including W0) for **+$31.23/day**; a patterned factor error of **±0.0239 L/kWh** reverses the ranking. Onsite W0 water is unchanged. | Average, not marginal, grid-water factors; one regional scenario. |
| **H5. A temperature-excess C1 model is sufficient to reproduce W2-Air evaporation.** | EDA 02, 29 (`aggregation_summary.csv`) | Yes **under fixed equipment, by construction** (§4): C1 versus W2 WAPE ~0.19% / 0.14% / 0.10% hourly / daily / sampled-month on 2023 ESIF weather. | Reduction of the simulator, **not** measured water accuracy. |
| **H6. Shifting flexible IT energy reduces direct-air evaporation without consequences for peaks.** | 30 (`schedule_decision_summary.csv`) | Daily evaporation fell **8,680.5 → 8,458.8 L** (2.6%) on July 24, but the unconstrained peak feed rose **1,353.8 → 1,452.0 L/h**. | One simulated 1 MW facility driven by real weather. |
| **H7. Preserving the baseline feed peak eliminates most water-saving potential.** | 31 (`step31_results.md`) | No on this day: the baseline cap retained **219.8 / 221.7 L/day** (99.1%) of the achievable saving; across three caps C1 was W2-feasible with **0.10–0.11 L/day** regret. | Hypothetical feed limits; no observed intake. |

**Still untested:** Whether C1/W2 predicts measured onsite water, how results generalize across cooling architectures or workload performance, and how location-specific groundwater withdrawals affect other water users.

## 7. Where the project stands

**Established:** numerical mass/energy balances; reproducible power-model holdouts using PUE-derived reference; conditional cooling physics; an energy-balance reduction of W2-Air (C1) under fixed equipment; the effect of model choice on several scheduling scenarios.

**Not established:** measured direct-water prediction accuracy; generalized decision robustness across equipment and weather; electricity-versus-onsite-water economic value; physical water-source attribution; groundwater or multi-region planning.

**Next scientific question:** How much electricity cost must be paid to reduce **modeled onsite process evaporation** under the same workload and physical constraints? This proposed next experiment is **not yet a result**. **Prerequisite:** define an electricity boundary consistent with the hypothetical W2-Air plant (§3); the ESIF-fitted overhead cannot simply be paired with W2-Air evaporation.

**Supporting records (not needed to understand this document):** `eda/summary/findings.md` (experiment-by-experiment results), `eda/summary/README.md` (five summary figures), `eda/water_models/step31_results.md` and the saved Step 29–31 CSVs (numerical results), plus `context/stepNN.md` (individual protocols). Keep this file stable and update it only when a **model, assumption, optimization problem, or central conclusion** changes.

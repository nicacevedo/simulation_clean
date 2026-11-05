## Step 14 — Close the power-model comparison and test decision value

### 1. First, restore M0 as the reference

I checked the attached `runs2.zip` and reproduced the relevant comparisons. M0 should remain in every model-comparison table, even if it is not the preferred model.

Here are the Step 13 results with M0 added, using exactly the same weather-matched observations and training periods.

| Test      | Model     | Hourly MAE | P95 underprediction | Hours exceeding \\(h\_{95}\\) |
| --------- | --------- | ---------- | ------------------- | ----------------------------- |
| Warm      | M0        | 14.4 kW    | 20.2 kW             | 0.8%                          |
|           | M1-fixed  | 23.1 kW    | 35.6 kW             | 2.7%                          |
|           | M1        | 15.8 kW    | 23.1 kW             | 1.1%                          |
|           | M2a-fixed | 11.6 kW    | 13.4 kW             | 0.3%                          |
|           | M2a       | 11.4 kW    | 11.9 kW             | 0.0%                          |
| High-load | M0        | 84.9 kW    | 0 kW                | 0.0%                          |
|           | M1-fixed  | 12.8 kW    | 28.3 kW             | 0.3%                          |
|           | M1        | 64.7 kW    | 16.8 kW             | 0.0%                          |
|           | M2a-fixed | 9.2 kW     | 17.6 kW             | 0.7%                          |
|           | M2a       | 27.5 kW    | 53.5 kW             | 0.1%                          |

P95 underprediction here means the 95th percentile among hours with positive prediction error, matching the reported Step 13 convention. It is not the 95th percentile over all hours.

One critical interpretation: M0's zero underprediction during high-load operation is not proof that it is a good model. Its 84.9 kW MAE reflects substantial overprediction, which can waste usable capacity.

Conclusion: M2a-fixed is the most balanced of the models tested across these two holdouts. Unrestricted M2a improves the warm test marginally but extrapolates poorly to high IT loads. This supports retaining \\(b=1\\) for our next controlled experiment, not declaring it a universal physical law.

I would now stop fitting power models and return to the original research plan's decision-value experiments.

### 2. The next critical question

Our original plan seeks to identify when a more accurate model actually produces a better operational decision.

We have already demonstrated this mechanism with M0 and M1-fixed under synthetic and real electricity prices. What remains untested is whether the weather-dependent overhead we measured in ESIF leads to meaningfully better capacity-constrained scheduling decisions.

This is the appropriate objective for Step 14.

### 3. Recommended experiment — One held-out day, three models

Use one real 24-hour operating profile, with the same scheduling formulation from Steps 08–10.

| Item            | Choice                                          |
| --------------- | ----------------------------------------------- |
| Test date       | September 1, 2023                               |
| Training        | January–August 2023                             |
| Workload        | Measured ESIF hourly IT-load profile            |
| Weather         | Measured ESIF hourly wet-bulb                   |
| Price           | Same-day Springfield/MISO hourly price          |
| Flexibility     | 20% deferrable IT energy, as before             |
| IT capacity     | 125% of the day's maximum baseline IT load      |
| Models          | M0, M1-fixed, M2a-fixed                         |
| Facility limits | 4,400 kW (control), 3,400 kW (binding scenario) |

I verified that September 1 has 24 matched power/weather observations in the attached dataset. Its IT load ranges from approximately 2,394 to 3,283 kW, within the January–August training range.

The facility limits are hypothetical, not measured ESIF ratings. Reuse the existing `price_day.py` to extract September 1 prices, and verify all 24 UTC timestamps.

The model coefficients must come only from January–August training:

\\[ \begin{aligned} \text{M0:}\quad & \hat P_t=kP_t^{IT}\\\ \text{M1-fixed:}\quad & \hat P_t=P_t^{IT}+a\\\ \text{M2a-fixed:}\quad & \hat P_t=P_t^{IT}+a+c(T\_{wb,t}-T_0). \end{aligned} \\]

From the attached data, the training coefficients are approximately \\(k=1.0475\\), \\(a=73.9\\) kW and \\(c=1.80\\) kW/°C, with \\(T_0\approx6.22^\circ C\\).

### 4. The most important improvement: a common empirical reference

Rather than treating M1-fixed or M2a-fixed as ground truth, use the observed September 1 overhead:

\\[ H_t^{ref}=P_t^{DC,ref}-P_t^{IT,observed}. \\]

For evaluating candidate schedules, define

\\[ \boxed{P_t^{ref}(x)=x_t+H_t^{ref}.} \\]

This creates a common reference against which all three models can be judged.

Important assumption: The realized hourly overhead is held fixed when IT workload is shifted. This is a controlled counterfactual approximation, not a measured response to workload shifting. It is appropriate for testing the decision mechanism, but cannot establish the actual facility's response to an intervention.

Use this reference to compute each schedule's facility-limit violations and its cost relative to the reference-optimal feasible schedule.

### 5. Test the value of a simple safety allowance

The previous experiments also produced training-derived allowances \\(h\_{95}\\).

For each model, compare two scheduling policies:

\\[ \hat P_t^{DC}(x_t)\le P^{max} \\]

and

\\[ \hat P_t^{DC}(x_t)+h\_{95}\le P^{max}. \\]

The second simply reserves additional capacity based on training prediction errors.

This gives us three models × two headroom policies × two limits: 12 small linear programs, reusing the existing optimizer. Also solve the reference optimization once per limit.

No new model fitting or physical equations are needed.

### 6. What to implement

Create only:

`dc_resource_sim/src/experiments/s6_decision_value.py`

Reuse the LP constraints, solver, and assertions from `s2_real_prices.py`. Replace its constant IT baseline with September 1's measured hourly IT profile, and add model-specific hourly overhead and optional training headroom.

For every schedule, report:

| Output                       | Interpretation                                       |
| ---------------------------- | ---------------------------------------------------- |
| Reference feasibility        | Does the schedule respect the common facility limit? |
| Maximum violation (kW)       | How serious is any violation?                        |
| Feasible cost regret ($/day) | What does conservatism or poor scheduling cost?      |

Keep the original workload-arrival, completion, and IT-capacity checks. If a model's optimization is infeasible, report that rather than forcing a result.

For the nonbinding case, schedules should have equivalent optimal costs under the common reference, apart from solver ties.

For the binding case, investigate whether M2a-fixed improves reference feasibility or reduces conservative cost regret compared with M0 and M1-fixed.

Do not add plots, model interactions, additional days, or more parameters yet.

### 7. Stopping rule

Step 14 is complete when we can answer:

1. Does M2a-fixed improve scheduling feasibility compared with M0 and M1-fixed?
2. Does its training-derived headroom reduce violations without excessive extra cost?
3. Are the differences large enough to justify using weather information in the optimization?

A finding of little decision improvement is also valuable. It would indicate that more accurate weather predictions are not necessarily worth additional operational complexity under the tested conditions.

Afterward, the next research direction should be the original plan's water-model decision experiments, rather than continuing to expand the power-model family.

Final recommendation: Restore M0 to the Step 13 comparison, close predictive-model refinement, and use Step 14 to connect the empirically supported power models to actual scheduling decisions under a common observed-overhead reference. This is the most direct next contribution to the project's model-sufficiency objective.
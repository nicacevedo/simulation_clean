## Step 08 — First workload-scheduling optimization (S0)

Step 07 is complete. The 2023 component data explain the summer overhead increase, consistent with our earlier EDA. No further power-model investigation is necessary before starting optimization.

The next valuable experiment is to establish a correct, minimal scheduling problem and verify one fundamental result:

M0 and M1-fixed should produce identical cost-optimal schedules when facility capacity is nonbinding, even though they predict different electricity consumption and costs.

This result is mathematically guaranteed under the assumptions below. The experiment verifies our implementation.

### 1. Minimal experimental setup

Use synthetic hourly electricity prices first, so no new data preparation is needed.

| Input              | Value                              | Reason                        |
| ------------------ | ---------------------------------- | ----------------------------- |
| Facility           | One hypothetical facility          | No geographic decisions       |
| Horizon            | 24 hours                           | Simplest daily scheduling     |
| Baseline IT load   | 1,000 kW                           | Constant, easy to verify      |
| Flexible workload  | 20%                                | Work may be deferred          |
| IT capacity        | 1,250 kW                           | Limits scheduling             |
| Deadline           | End of the day                     | All work must finish          |
| Electricity prices | Higher first 12 h, lower last 12 h | Controlled incentive to shift |
| M0                 | \\(k=1.0471\\)                     | Previously calibrated         |
| M1-fixed           | \\(a=73.13\\) kW                   | Previously calibrated         |
| W0                 | 0.5 L/kWh IT                       | Illustrative, unchanged       |

The electricity-model parameters come from the previous January–August fit. They are used as representative coefficients, not as ground truth.

Do not introduce weather, cooling models, grid water, or a facility-power limit yet.

### 2. Optimization model

Let \\(x_t\\) be IT energy processed in hour \\(t\\), with baseline \\(x_t^0\\).

We minimize electricity cost:

\\[ \min_x \sum_t p_t E_t^{DC}(x_t). \\]

Compare:

\\[ \begin{aligned} \text{M0:}\quad & E_t^{DC}=kx_t\\\ \text{M1-fixed:}\quad & E_t^{DC}=a\Delta t+x_t. \end{aligned} \\]

For the 1-hour time step, \\(a\Delta t\\) is 73.13 kWh.

Use the same constraints for both models:

\\[ x_t=(1-\phi)x_t^0+y_t \\]

\\[ 0\leq y_t,\qquad x_t\leq E^{IT,\max} \\]

\\[ \sum\_{\tau=1}^{t}y\_\tau \leq\phi\sum\_{\tau=1}^{t}x\_\tau^0 \\]

\\[ \sum\_{t=1}^{24}y_t =\phi\sum\_{t=1}^{24}x_t^0. \\]

The cumulative constraint prevents processing flexible work before it arrives.

Because both models have a constant positive marginal electricity coefficient, their scheduling objectives differ only by a positive multiplier and a decision-independent term. Their optimal schedules must therefore be identical under the shared constraints, apart from possible ties.

### 3. Minimal implementation

Create only:

`dc_resource_sim/src/experiments/s0_schedule.py`

```
"""Step 08: First 24-hour scheduling experiment."""import numpy as npfrom scipy.optimize import linprogT = 24phi = 0.20it_max = 1250.0  # kW, with 1-hour stepsbaseline = np.full(T, 1000.0)  # kWh per hourwater_intensity = 0.5  # L/kWh IT# Synthetic $/kWh; distinct prices avoid tied optimaprices = np.r_[    0.20 + 0.001 * np.arange(12),    0.05 + 0.001 * np.arange(12)]# y[t] = flexible energy processed in hour tfixed = (1 - phi) * baselinearrivals = phi * baselineconstraints = dict(    A_ub=np.tril(np.ones((T, T))),    b_ub=np.cumsum(arrivals),    A_eq=np.ones((1, T)),    b_eq=[arrivals.sum()],    bounds=[(0, it_max - v) for v in fixed],    method="highs",)models = {    "M0": (0.0, 1.0471),    "M1-fixed": (73.13, 1.0),}schedules = {}
```

This needs only NumPy and SciPy, with no new datasets, configuration files, or plotting infrastructure.

### 4. Expected results

I verified the code using SciPy's HiGHS solver.

| Outcome                    | M0           | M1-fixed     |
| -------------------------- | ------------ | ------------ |
| Baseline electricity cost  | $3,279.52    | $3,361.04    |
| Optimized electricity cost | $2,899.58    | $2,998.19    |
| Facility electricity       | 25,130.4 kWh | 25,755.1 kWh |
| Direct water               | 12,000 L     | 12,000 L     |
| Optimized peak             | 1,308.9 kW   | 1,323.1 kW   |
| Optimal IT schedule        | Same         | Same         |

The optimized total facility electricity equals its respective model's baseline total. Electricity costs fall because demand shifts to cheaper hours.

The models predict different cost savings and facility peaks, despite choosing the same IT schedule.

These are model-specific accounting results, not decision-regret estimates.

### 5. What constitutes success?

Only four checks are necessary:

- All IT energy is completed, with no work processed before arrival.
- The optimized electricity cost is lower than the baseline.
- Facility energy and direct water are conserved within each model.
- M0 and M1-fixed choose identical schedules.

If all pass, close Step 08 immediately.

Do not add real MISO/ERCOT prices yet. They are unnecessary for verifying this fundamental result.

## What Step 09 should test

Introduce one common physical facility-power limit:

\\[ P_t^{DC}\le P^{DC,\max}. \\]

Now M0 and M1-fixed imply different feasible IT loads. The models may therefore choose different schedules.

The important follow-up will be to evaluate both solutions under a common reference model, checking:

1. Whether each schedule satisfies the reference facility limit.
2. Whether either model leads to a worse feasible decision.
3. Whether the difference is substantial enough to justify the more accurate model.

This is the first meaningful decision-value experiment in the original plan.

Final recommendation: One script, two models, one 24-hour optimization, and four checks. Step 08 should establish the mathematical and computational baseline; Step 09 should investigate when model accuracy actually affects decisions.
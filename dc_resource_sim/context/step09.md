## Step 09 — When does a facility-power limit change the optimal schedule?

Step 08 is complete. We established that M0 and M1-fixed produce identical cost-optimal schedules without binding facility-power constraints, despite predicting different electricity consumption.

The next experiment should answer:

Can an inaccurate facility-power model produce a schedule that appears optimal but violates the facility's actual power limit?

This is our first meaningful test of the decision value of the power models.

### 1. Minimal experiment

Keep everything from Step 08 unchanged except for one additional constraint:

\\[ P_t^{DC}\leq P^{DC,\max}. \\]

For each model,

\\[ P_t^{DC}=a+bx_t \\]

so the equivalent IT-power limit is

\\[ \boxed{x_t\leq\min\left(1250,\frac{P^{DC,\max}-a}{b}\right)} \\]

where \\(x_t\\) is hourly IT energy in kWh, numerically equal to average kW because \\(\Delta t=1\\) hour.

Use two cases:

| Case           | Facility limit | Purpose                                       |
| -------------- | -------------- | --------------------------------------------- |
| A — Nonbinding | 1,400 kW       | Reproduce Step 08: identical schedules        |
| B — Binding    | 1,250 kW       | Test differences in schedules and feasibility |

Keep the previously fitted coefficients:

- M0: \\(a=0,\ b=1.0471\\).
- M1-fixed: \\(a=73.13\\) kW, \\(b=1\\).

All workload, price, arrival, deadline, and IT-capacity assumptions remain unchanged.

### 2. The critical evaluation rule

Optimize under each model, but evaluate both schedules under the same reference model.

For the first comparison, use M1-fixed as the reference because it performed best in the previous high-load validation. However, it is still an estimated model, not ground truth.

Report:

1. Optimal IT schedule and predicted peak.
2. Maximum facility-limit violation under M1-fixed.
3. Electricity cost evaluated using M1-fixed.
4. Decision regret only when the schedule is feasible under the reference.

Do not count a cheaper but infeasible schedule as a successful improvement.

For an additional robustness check, evaluate the schedules under M0 as the reference too. This requires no additional optimization formulation and avoids assuming M1-fixed is necessarily correct.

### 3. Minimal implementation

Create one new file:

`dc_resource_sim/src/experiments/s1_power_limit.py`

Keep `s0_schedule.py` unchanged.

```
"""Step 09: Decision value of a facility-power limit."""import numpy as npfrom scipy.optimize import linprogT = 24baseline = np.full(T, 1000.0)phi = 0.20fixed = (1 - phi) * baselinearrivals = phi * baselineprices = np.r_[0.20 + 0.001*np.arange(12),               0.05 + 0.001*np.arange(12)]IT_MAX = 1250.0models = {"M0": (0.0, 1.0471),          "M1-fixed": (73.13, 1.0)}for limit in [1400.0, 1250.0]:    schedules = {}    print(f"\nFacility limit: {limit:.0f} kW")    for name, (a, b) in models.items():        it_cap = min(IT_MAX, (limit - a) / b)        result = linprog(            b * prices,            A_ub=np.tril(np.ones((T, T))),            b_ub=np.cumsum(arrivals),            A_eq=np.ones((1, T)),            b_eq=[arrivals.sum()],            bounds=[(0, it_cap - v) for v in fixed],            method="highs"        )        assert result.success, result.message        x = fixed + result.x
```

This preserves the original scheduling formulation and changes only the model-specific maximum allowable IT power.

### 4. Expected results

Using the stated coefficients and synthetic prices, the binding-capacity case should produce approximately:

| Reference model | Schedule | Maximum violation | Cost regret |
| --------------- | -------- | ----------------- | ----------- |
| M1-fixed        | M1-fixed | 0 kW              | $0          |
| M1-fixed        | M0       | 16.90 kW          | Infeasible  |
| M0              | M0       | 0 kW              | $0          |
| M0              | M1-fixed | 0 kW              | $30.77      |

These are illustrative counterfactual evaluations, not measured operating outcomes.

They demonstrate two possible consequences:

- If M1-fixed better represents the facility, M0 can underestimate peak demand and produce an infeasible schedule.
- If M0 better represents the facility, M1-fixed may be unnecessarily conservative, increasing electricity cost.

For the 1,400 kW limit, both models should reproduce the identical Step 08 schedule with zero violations and zero decision regret.

### 5. Completion criteria

Step 09 is complete when:

- The nonbinding case reproduces Step 08.
- The binding case produces different feasible schedules under the respective models.
- Both schedules are evaluated under identical reference assumptions.
- Infeasible schedules are explicitly identified, never assigned ordinary cost regret.

One limitation: the capacity constraint represents maximum hourly average power, not instantaneous electrical demand. That is sufficient for this first experiment.

## What comes after Step 09?

The next meaningful step is to repeat this experiment with one real hourly electricity-price profile and assess how sensitive the decision differences are to the facility limit. But first, establish the mechanism under controlled conditions.

Final recommendation: Do not introduce water, weather, another power model, or additional scenarios yet. Step 09 should demonstrate the first concrete consequence of model error: an apparently economical workload schedule can violate a physical facility limit, even when the two models give similar aggregate electricity predictions.
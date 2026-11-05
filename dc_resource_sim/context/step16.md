## Step 16 — Is the water-aware scheduling benefit robust to uncertainty?

Step 15 is complete. The next step should be a very small uncertainty check before introducing physical cooling models.

The key result is that water-aware scheduling changes decisions, but the modeled benefit is only 122.5 L relative to cost-optimal scheduling, at an additional $31.23.

Modeled water reduction

# 122.5 L

0.22% of cost-optimal total

Additional electricity cost

# $31.23

Approximately $0.255/L

The most important limitation is that the grid-water intensities are modeled historical average factors, not marginal water impacts.

Furthermore, the reported uncertainty is much larger than the observed hourly differences. We should determine whether the preference for the water-optimal schedule is sensitive to small changes in those factors.

I would not introduce W1 or W2 yet. First close this accounting-based experiment with a clear statement of what the available water information can and cannot establish.

### 1. The single question

How inaccurate would the hourly grid-water factors need to be to reverse the water ranking of the two schedules already obtained?

Let

\\[ \Delta V = k\sum_t\gamma_t(x_t^{cost}-x_t^{water}) =122.5\ \mathrm{L}. \\]

If the actual factor differs from the modeled factor by \\(\delta_t\\), with

\\[ |\delta_t|\leq\epsilon, \\]

the maximum adverse change to this difference is

\\[ k\epsilon\sum_t|x_t^{cost}-x_t^{water}|. \\]

Therefore, the pairwise water ranking is guaranteed to remain unchanged for every error pattern within this hypothetical bound when

\\[ \boxed{ \epsilon< \frac{\Delta V} {k\sum_t|x_t^{cost}-x_t^{water}|} } \\]

This tests only the ranking of the two existing schedules, not whether the water-optimal schedule remains globally optimal.

I checked the attached `price_water_24h.csv` and reproduced the two schedules using the Step 15 linear program. They differ by 4,900 kWh in absolute hourly allocations summed across the day.

The resulting threshold is:

Pairwise reversal threshold

# 0.0239 L/kWh

Approximately 1.4% of the day's mean grid-water intensity.

This is a small threshold. An appropriately patterned error of this magnitude could eliminate the modeled advantage of the water-aware schedule.

It does not mean a reversal is likely: that depends on the temporal correlation of the uncertainty, which we have not identified.

### 2. Minimal implementation

Modify only `dc_resource_sim/src/experiments/s7_water_schedule.py`.

Append the following after the existing schedules and accounting calculations. No new LP, data loading, or dependencies.

```
# Step 16 — Sensitivity of the water-schedule advantagedx = x_cost - x_waterassert np.isclose(dx.sum(), 0)  # Same total IT energygain_l = k * np.dot(g, dx)sensitivity = k * np.abs(dx).sum()epsilon = gain_l / sensitivityprint(f"Modeled water advantage: {gain_l:.2f} L")print(f"Absolute schedule difference: {np.abs(dx).sum():.0f} kWh")print(f"Reversal threshold: {epsilon:.4f} L/kWh")# Worst-case pairwise advantage under illustrative error boundsfor bound in [0.01, 0.02, 0.03]:    worst_gain = gain_l - bound * sensitivity    print(f"±{bound:.2f} L/kWh: worst-case advantage = {worst_gain:.1f} L")
```

Expected results:

| Maximum hourly factor error | Worst-case water advantage |
| --------------------------- | -------------------------- |
| ±0.01 L/kWh                 | +71.2 L                    |
| ±0.02 L/kWh                 | +19.9 L                    |
| ±0.03 L/kWh                 | −31.4 L                    |

These are mathematical worst-case bounds, not estimated probabilities or observed uncertainty realizations.

### 3. Critical interpretation

There are two different kinds of uncertainty:

- Common level error: If every hourly factor has the same additive bias, the water difference between schedules is unchanged because their total facility electricity is identical. A common positive multiplicative scaling also preserves the ranking.
- Hourly-pattern error: If the relative intensities across hours are inaccurate, the scheduling preference may reverse. This is the uncertainty that actually matters for this experiment.

The low/high factors in the original data source should not automatically be interpreted as independent hourly confidence intervals or feasible joint trajectories. Verify their definition before using them for probabilistic or robust optimization.

More fundamentally, even a perfectly stable ranking under average accounting factors would not establish actual water savings caused by shifting electricity demand.

### 4. Stopping rule

Step 16 is complete once the threshold and worst-case comparison reproduce correctly.

If the ranking can reverse under small differential errors—as the preliminary calculation indicates—stop extending the grid-water scheduling experiment. Record its results as conditional accounting scenarios, not demonstrated operational savings.

Do not add Monte Carlo simulations, arbitrary error distributions, new models, or additional regions at this stage.

## 5. What comes next?

I recommend that Step 17 begin the first physics-based direct-water mapping, which is substantially more relevant to our longer-term groundwater-planning objective:

\\[ \text{IT electricity} \rightarrow \text{Heat rejection} \rightarrow \text{Evaporation} \rightarrow \text{Freshwater makeup}. \\]

Start with one clearly defined cooling-tower archetype, distinguish consumption from withdrawal, and test the physical balances before introducing optimization.

We should not assume that the ESIF architecture or the Prineville direct-evaporative system uses the same heat-to-water relationship.

Final recommendation: Step 16 should be just this small robustness calculation. Its value is determining whether the scheduling improvement survives uncertainty in the very signal that drives it. Then move toward physically grounded direct-water modeling, rather than investing further in uncertain average grid-water signals.
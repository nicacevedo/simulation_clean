# Step 31 — Water-saving schedules under a peak treatment-feed limit

Run from the repository root: `~/.conda/envs/dc_externalities/bin/python dc_resource_sim/eda/water_models/peak_feed_capacity_compare.py` → `peak_feed_capacity_summary.csv`.
Setup: July 24, 2023 ESIF weather (observed), a hypothetical 1 MW IT load with 20 % flexible work, W2-Air and recovery η = 0.8, all as in Step 30. Each model optimizes against its own cap. Every schedule is then scored with W2. "Feed" means hypothetical treatment feed (evaporation/η, L/h). It is not withdrawal or groundwater extraction.

**Checks passed.** Step 30 anchors reproduced within 0.01: no-shift 8,680.498 L/day at a peak of 1,353.818 L/h; W2-optimal 8,458.781 L/day at 1,451.983 L/h. All six LPs are feasible with 24,000 kWh, satisfy the arrival and 1,250 kW constraints, and keep every W2 schedule under its cap. No-shift is feasible at all caps. The W2 optimum does not increase as the cap rises, and cap C recovers Step 30.

| Cap (L/h) | W2-opt saving (L/day) | C1 saving (L/day) | C1 W2 peak (L/h) | C1 regret (L/day) |
|---|---:|---:|---:|---:|
| A 1,353.818 | 219.796 | 219.696 | 1,348.685 | 0.100 |
| B 1,402.901 | 220.757 | 220.653 | 1,397.581 | 0.104 |
| C 1,451.983 | 221.717 | 221.610 | 1,446.478 | 0.108 |

1. **How much of the saving survives at the no-shift peak?** 219.8 of 221.7 L/day (99.1 %) remains. This is a modeled saving with no increase in the hypothetical peak feed.
2. **How much more does added capacity buy?** Very little. The extra 98.2 L/h (+7.3 %) of peak capacity adds only 1.9 L/day (0.9 %), split about evenly between A→B and B→C. Under this setup, the peak-feed limit is almost not decision-relevant.
3. **Does C1 stay W2-feasible and near-optimal?** Yes, at every cap. C1 never violates the W2 cap; its realized W2 peak is about 5 L/h below each cap. Its regret against the capacity-constrained W2 optimum is 0.10–0.11 L/day, or under 0.05 % of the achievable saving. The reason is that C1 overpredicts W2 by 0.2–0.5 % in the hottest hours, so its own cap binds first. This makes C1 conservative, not infeasible. Without a cap, C1 had zero regret (Step 30), so the cap introduces a small, safe-side loss.

**Implication.** On this day, a cap at the existing peak removes almost none of the water saving, and C1 remains decision-sufficient. That weakens the case for adding capacity-aware water demand to the planning model next. These results apply only to one weather day and to hypothetical equipment, flexibility and recovery. No plot was made because the capacity–saving relationship is nearly flat and the table shows it fully.

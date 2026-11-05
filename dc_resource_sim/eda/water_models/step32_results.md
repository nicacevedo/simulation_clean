# Step 32 results — cost vs. modeled W2 evaporation (`cost_evaporation_summary.csv`)

Constructed scenario: 2023-07-01 MISO ILLINOIS.HUB day-ahead prices (Springfield, IL) paired by hour-of-day with 2023-07-24 ESIF weather. The dates and regions do not coincide, so these are not actual operations. Facility energy is 25,130.4 kWh/day in every row; all schedules meet the Step 31 cap A (1353.818 L/h). Anchors reproduced: no-shift 8680.498 L, cap-A W2 optimum 8460.703 L (Step 31: 8460.702).

1. **Yes, but by very little.** Cost-optimal scheduling evaporates 7.381 L/day more than water-optimal (8468.083 vs 8460.703 L/day), which is 0.087% of cost-optimal evaporation. Cost-optimal scheduling alone already saves 212.4 of the 219.8 L/day achievable versus no shift.
2. Reaching minimum evaporation costs **$4.912/day extra** (0.589% above the cost-optimal $834.319). That is about $0.67 per litre of extra modeled evaporation avoided.
3. The midpoint budget captures 50% of the 7.381 L water gap, which the budget definition makes binding. It costs $0.869/day, or 17.7% of the maximum extra cost (≈$0.24/L). The second half of the gap costs ≈$1.10/L. With three points this is not a smooth frontier.

**Conclusion:** price-driven and evaporation-driven shifting are mostly aligned here, because cheap hours overlap with low-evaporation hours. The remaining conflict is real but small in litres. This result is conditional on the price–weather pairing; the next test is a co-timed price trace.

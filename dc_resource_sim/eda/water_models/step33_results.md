# Step 33 results — matched price–weather robustness (`matched_price_weather_summary.csv`)

**Inputs.** Frozen `signals_2023_v1` site S1b (Springfield, IL). Weather is NOAA GHCNh station USW00093822 (`Tdb_C`, `RH_raw_pct`), using only hours with `wx_qc_flag=ok`. Prices are MISO day-ahead ex-post LMP at ILLINOIS.HUB, converted from $/MWh to $/kWh. The raw price hours are EST hour-ending and map exactly to UTC interval start, so price and weather are joined on the same UTC hour.

**Coverage.** The file has 8,904 raw rows, of which 144 fall outside 2023. That leaves 8,760 UTC hours in 2023 with no duplicates. Of the 365 days, 324 are eligible; 11 were excluded for invalid or missing hours and 30 because a W2 hour was infeasible.

**Days.** I chose them from weather and the W2 no-shift baseline only:
- Dry: 2023-01-02 (earliest of 217 dry days).
- Typical wet: 2023-05-28, the lower median of the 107 wet days (7 wet hours, 1,147.8 L baseline).
- High wet: 2023-06-25 (21 wet hours, 8,203.3 L baseline).

| Day | Max saving | Cost-only saving (share) | Remaining gap | Extra cost | $/L of gap | corr(price, w) |
|---|---|---|---|---|---|---|
| Dry | 0 | 0 (N/A) | 0 | $0.000 | N/A | N/A |
| Typical wet | 26.95 L | 26.95 L (100%) | 0.00 L | ≈$0 (−0.001, within the tie-break tolerance) | N/A | 0.79 |
| High wet | 589.3 L | 502.0 L (85.2%) | 87.3 L | $2.97 | $0.034 | 0.87 |

**Compared with Step 32** (constructed pairing; cost-only captured 96.6%; a 7.4 L gap closed for $4.91 at $0.67/L): alignment holds on the matched days but is weaker on the high-evaporation day. There the conflict is larger in litres (87 L, 1.1% of cost-optimal evaporation) yet about 20 times cheaper per litre to close.

**Conclusion.** Mostly aligned, with a degree of misalignment that depends on the scenario. On both matched wet days, regional wholesale prices are high in the same hours as evaporation (r ≈ 0.8–0.9, descriptive only). Cost-only scheduling therefore captures most or all of the W2 saving, and the residual conflict grows on the hottest day.

**Limitations.** These are three selected days from one region, not a representative sample. Prices are a hub wholesale proxy, not a facility tariff. W2 is simulated process evaporation. M0 cost assumes fixed facility energy with no cooling-mode electricity. The feed cap is a hypothetical per-day no-shift peak, not a withdrawal or groundwater limit.

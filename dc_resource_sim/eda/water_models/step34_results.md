# Step 34 results — cooling electricity–heat–water balance (`cooling_mode_energy_water_hourly.csv`)

**Setup.** Springfield, IL, 2023-06-25 00–23 UTC. Inputs are the Step 33 frozen NOAA weather, with all 24 hours qc-ok. IT load is a constant 1,000 kW. The system uses 100% outdoor air in a once-through configuration: air is conditioned to ≤ 25 °C before the servers, and the exhaust carries the IT heat outdoors. Both modes use the same dry-air flow (≈ 64.6 kg/s) and a 15 °C server rise, so Q_IT = 1,000 kW. When outdoor air is at or below 25 °C, both modes use free air (3 hours). Above 25 °C (21 hours), the wet mode uses W2-Air direct evaporation with Step 20 defaults, and the dry mode uses a sensible-only mechanical coil that cools the *inlet air only*. **Illustrative, uncalibrated:** P_common = 20 kW (both modes), P_wet_aux = 10 kW (wet hours only), dry system COP = 3.0.

**Feasibility.** Every W2 hour is feasible. The W2 anchor matches Step 33: 21 wet hours and 8,203.34 L/day (Step 33 reported 8,203.3). The maximum outdoor dew point is 21.0 °C, below 25 °C, so the dry coil never condenses.

| Mode | Modeled electricity (kWh) | Cooling + air movement (kWh) | Evaporation (L) | Peak (kW) |
|---|---|---|---|---|
| wet | 24,690.0 | 690.0 | 8,203.3 | 1,030.0 |
| dry | 26,335.5 | 2,335.5 | 0 | 1,168.1 |

- **ΔE = E_dry − E_wet = +1,645.5 kWh/day.** The waterless mode uses more electricity. The difference comes entirely from the 1,855.5 kWh of mechanical input minus the 210 kWh of wet auxiliaries.
- **ΔV = 8,203.3 L/day** of avoided W2 process evaporation (the optional feed proxy, evap/0.8, would be 10,254 L). **ΔE/ΔV = 0.201 kWh per litre avoided.** This is a mode-switch energy trade-off, not a water price.
- **Heat balance.** Inlet precooling is Q_in = 5,566.5 kWh_th/day, about 23% of the 24,000 kWh of IT heat. In wet hours, latent transfer (V × 2.45/3.6) exceeds Q_in by at most **0.29%**. The dry-mode condenser rejects Q_in + P_mech = 7,422.0 kWh_th/day to ambient.
- **Break-even COP\* = 26.5.** The two mode-specific daily inputs would tie only at a dry-system COP of about 26.5, given the assumed 10 kW wet auxiliary. This is an illustrative threshold, not an equipment property.

**Conclusion.** The bookkeeping is internally consistent. Both modes contain exactly 24,000 kWh of IT energy and the same 20 kW common term, the latent and sensible loads agree within 0.3%, and the IT heat leaves with the exhaust in both modes. Under this one once-through architecture and these assumed parameters, avoiding W2 evaporation on the hottest Step 33 day costs about 0.2 kWh/L, or +6.7% modeled electricity (+13% at peak).

**Boundary.** Modeled power is IT plus selected cooling and air-movement terms. It is not facility power or PUE, and it is not added to M0. Zero dry-mode evaporation is not a proven zero facility withdrawal. Supply-air humidity acceptability is not established for either mode. The results cover one day and one architecture, with no sensitivity sweep.

## Step 18 — Connect cooling architecture to wet heat rejection and evaporation

Step 17 is complete. The energy-to-water balances work, including the effects of workload distribution and cycles of concentration.

The next step should answer two separate questions:

1. How much heat actually reaches the wet cooling tower?
2. What fraction of that heat is removed through evaporation rather than sensible heat transfer?

These are the two missing physical relationships. We should not treat either as known from PUE or WUE.

### 1. Choose one cooling architecture

Start with a water-cooled electric chiller connected to an open-recirculating cooling tower.

The chiller adds compressor heat to the cooling load before the condenser rejects that heat to the tower.

For this architecture, the condenser heat balance is

\\[ Q_t^{wet}=Q_t^{evap,chiller}+E_t^{compressor}. \\]

With a simplified chiller coefficient of performance, \\(COP=Q^{evap,chiller}/E^{compressor}\\), this becomes

\\[ \boxed{Q_t^{wet}=f\_{ch}E_t^{IT}\left(1+\frac{1}{COP}\right)} \\]

where \\(f\_{ch}\\) is the fraction of IT heat handled by that chiller. The remaining heat is assumed to leave through an independent dry route.

This follows the standard condenser energy balance described by ASHRAE.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://handbook.ashrae.org\&sz=32)

handbook.ashrae.org+1



Important: This equation assumes all relevant compressor input reaches the water-cooled condenser. Pump heat, tower fan heat, and other auxiliary sources are excluded until their actual thermal destinations are established. Do not multiply IT electricity by PUE and then add compressor heat again.

### 2. Keep the latent fraction explicit

Extend Step 17's evaporation equation to

\\[ \boxed{V_t^{evap} =\frac{3.6}{2.45}\alpha\_{lat,t}Q_t^{wet}} \\]

and retain

\\[ V_t^{blowdown}=\frac{V_t^{evap}}{COC-1}, \qquad V_t^{makeup}=V_t^{evap}+V_t^{blowdown}. \\]

Here \\(\alpha\_{lat,t}\\) represents the fraction of tower heat rejection attributed to evaporation.

Do not assume that wet-bulb temperature alone determines \\(\alpha\_{lat}\\). ASHRAE explains that dry-bulb temperature and relative humidity can substantially change the split between sensible and latent cooling, even at the same wet-bulb temperature.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://handbook.ashrae.org\&sz=32)

handbook.ashrae.org



For Step 18, treat \\(\alpha\_{lat}\\) as an explicitly uncertain scenario parameter, not a calibrated weather function.

### 3. Minimal experiment and expected results

Use the same 24-hour profiles from Step 17, with illustrative parameters:

\\[ f\_{ch}=1,\qquad COP=5,\qquad \alpha\_{lat}=0.8,\qquad COC=4. \\]

These are scenario assumptions, not measured equipment parameters.

I executed the reference script and verified the following results:

| Case                                   | Wet heat (kWh thermal) | Evaporation (L) | Makeup (L) | Peak makeup (L/h) |
| -------------------------------------- | ---------------------- | --------------- | ---------- | ----------------- |
| Step 17 limiting case                  | 24,000                 | 35,265          | 47,020     | 1,959             |
| Water-cooled chiller, constant 1 MW    | 28,800                 | 33,855          | 45,140     | 1,881             |
| Same chiller, variable 0.8/1.2 MW      | 28,800                 | 33,855          | 45,140     | 2,257             |
| Half of IT heat routed through chiller | 14,400                 | 16,927          | 22,570     | 940               |

The particularly useful result is that adding compressor heat increases the tower duty, but accounting for sensible cooling can still reduce calculated evaporation relative to Step 17.

Changing only the assumed latent ratio also has a large effect:

| Latent ratio | Daily makeup |
| ------------ | ------------ |
| 0.6          | 33,855 L     |
| 0.8          | 45,140 L     |
| 1.0          | 56,424 L     |

This shows why we cannot infer water consumption from heat rejection alone.

### 4. Implementation

I prepared the complete, tested specification:

Download step18.md

Save it to `dc_resource_sim/context/step18.md`.

The specification creates just one script:

`dc_resource_sim/src/experiments/w2_tower_heat_boundary.py`

It uses standard-library Python, reproduces Step 17 as a limiting case, verifies the energy and water balances, and tests heat routing, compressor input, latent fraction, and peak makeup demand.

### 5. Stopping rule

Close Step 18 once those checks pass. Do not introduce optimization, fit a WUE coefficient, or treat the illustrative latent fraction as measured.

The next high-value step will be a psychrometric evaporation model, where air humidity changes and mass flow determine evaporation, rather than assuming a latent ratio. ASHRAE's cooling-tower analysis supports this distinction.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://handbook.ashrae.org\&sz=32)

handbook.ashrae.org



Final recommendation: Step 18 should establish a correct architecture-to-heat-to-water mapping. Its main scientific contribution is identifying which physical inputs we still need—particularly the fraction of heat routed through wet equipment, compressor energy, and the latent/sensible split—before claiming realistic direct-water predictions or using them in groundwater-aware optimization.

--- 

Context:

## Step 18 — Connect cooling architecture to wet heat rejection and evaporation

Step 17 is complete. The energy-to-water balances work, including the effects of workload distribution and cycles of concentration.

The next step should answer two separate questions:

1. How much heat actually reaches the wet cooling tower?
2. What fraction of that heat is removed through evaporation rather than sensible heat transfer?

These are the two missing physical relationships. We should not treat either as known from PUE or WUE.

### 1. Choose one cooling architecture

Start with a water-cooled electric chiller connected to an open-recirculating cooling tower.

The chiller adds compressor heat to the cooling load before the condenser rejects that heat to the tower.

For this architecture, the condenser heat balance is

\\[ Q_t^{wet}=Q_t^{evap,chiller}+E_t^{compressor}. \\]

With a simplified chiller coefficient of performance, \\(COP=Q^{evap,chiller}/E^{compressor}\\), this becomes

\\[ \boxed{Q_t^{wet}=f\_{ch}E_t^{IT}\left(1+\frac{1}{COP}\right)} \\]

where \\(f\_{ch}\\) is the fraction of IT heat handled by that chiller. The remaining heat is assumed to leave through an independent dry route.

This follows the standard condenser energy balance described by ASHRAE.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://handbook.ashrae.org\&sz=32)

handbook.ashrae.org+1



Important: This equation assumes all relevant compressor input reaches the water-cooled condenser. Pump heat, tower fan heat, and other auxiliary sources are excluded until their actual thermal destinations are established. Do not multiply IT electricity by PUE and then add compressor heat again.

### 2. Keep the latent fraction explicit

Extend Step 17's evaporation equation to

\\[ \boxed{V_t^{evap} =\frac{3.6}{2.45}\alpha\_{lat,t}Q_t^{wet}} \\]

and retain

\\[ V_t^{blowdown}=\frac{V_t^{evap}}{COC-1}, \qquad V_t^{makeup}=V_t^{evap}+V_t^{blowdown}. \\]

Here \\(\alpha\_{lat,t}\\) represents the fraction of tower heat rejection attributed to evaporation.

Do not assume that wet-bulb temperature alone determines \\(\alpha\_{lat}\\). ASHRAE explains that dry-bulb temperature and relative humidity can substantially change the split between sensible and latent cooling, even at the same wet-bulb temperature.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://handbook.ashrae.org\&sz=32)

handbook.ashrae.org



For Step 18, treat \\(\alpha\_{lat}\\) as an explicitly uncertain scenario parameter, not a calibrated weather function.

### 3. Minimal experiment and expected results

Use the same 24-hour profiles from Step 17, with illustrative parameters:

\\[ f\_{ch}=1,\qquad COP=5,\qquad \alpha\_{lat}=0.8,\qquad COC=4. \\]

These are scenario assumptions, not measured equipment parameters.

I executed the reference script and verified the following results:

| Case                                   | Wet heat (kWh thermal) | Evaporation (L) | Makeup (L) | Peak makeup (L/h) |
| -------------------------------------- | ---------------------- | --------------- | ---------- | ----------------- |
| Step 17 limiting case                  | 24,000                 | 35,265          | 47,020     | 1,959             |
| Water-cooled chiller, constant 1 MW    | 28,800                 | 33,855          | 45,140     | 1,881             |
| Same chiller, variable 0.8/1.2 MW      | 28,800                 | 33,855          | 45,140     | 2,257             |
| Half of IT heat routed through chiller | 14,400                 | 16,927          | 22,570     | 940               |

The particularly useful result is that adding compressor heat increases the tower duty, but accounting for sensible cooling can still reduce calculated evaporation relative to Step 17.

Changing only the assumed latent ratio also has a large effect:

| Latent ratio | Daily makeup |
| ------------ | ------------ |
| 0.6          | 33,855 L     |
| 0.8          | 45,140 L     |
| 1.0          | 56,424 L     |

This shows why we cannot infer water consumption from heat rejection alone.

### 4. Implementation

I prepared the complete, tested specification:

Download step18.md

Save it to `dc_resource_sim/context/step18.md`.

The specification creates just one script:

`dc_resource_sim/src/experiments/w2_tower_heat_boundary.py`

It uses standard-library Python, reproduces Step 17 as a limiting case, verifies the energy and water balances, and tests heat routing, compressor input, latent fraction, and peak makeup demand.

### 5. Stopping rule

Close Step 18 once those checks pass. Do not introduce optimization, fit a WUE coefficient, or treat the illustrative latent fraction as measured.

The next high-value step will be a psychrometric evaporation model, where air humidity changes and mass flow determine evaporation, rather than assuming a latent ratio. ASHRAE's cooling-tower analysis supports this distinction.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://handbook.ashrae.org\&sz=32)

handbook.ashrae.org



Final recommendation: Step 18 should establish a correct architecture-to-heat-to-water mapping. Its main scientific contribution is identifying which physical inputs we still need—particularly the fraction of heat routed through wet equipment, compressor energy, and the latent/sensible split—before claiming realistic direct-water predictions or using them in groundwater-aware optimization.
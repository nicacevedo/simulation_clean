# Step 21 — One reference case: audit electricity, heat and water boundaries

**Purpose.** Confirm that the results already produced by M0/W0 and Steps 17–20 are correctly defined before adding any new equation. **Do not calibrate, fit, optimize, or introduce new cooling physics.**

## 1. Freeze the inputs

- Reference IT load: **1,000 kW constant**, with `dt = 1 h` and a separate **24 h** constant-load total.
- M0: `k = 1.0471` (ESIF-derived, applied here to a **hypothetical** 1 MW facility; not a measurement of this facility).
- W0: `w0 = 0.5 L/kWh IT`, explicitly an **assumed onsite direct-consumption intensity**.
- For illustration only, reuse Step 17's tower case (1,000 kW of thermal tower duty; COC = 4; 100% evaporative heat rejection) and Step 20's **different** direct-air case (30°C / 30% RH, 25°C supply target, 15°C server temperature rise, 0.8 maximum effectiveness).
- **Do not combine tower and direct-air water flows or imply they describe the same site.**

## 2. Reproduce the numerical boundary table

| Quantity | 1 hour | 24 h if held constant | Unit/boundary | Evidence status |
|---|---:|---:|---|---|
| IT electrical input | 1,000 | 24,000 | kW / kWh, IT meter | Hypothetical input |
| M0 facility electrical input | 1,047.1 | 25,130.4 | kW / kWh, facility meter prediction | Derived from assumed load and fitted ESIF coefficient |
| M0 **aggregate non-IT** electrical input | 47.1 | 1,130.4 | kW / kWh, facility minus IT | Derived; **not identified** as chiller/fan/pump |
| Idealized heat produced by IT | 1,000 | 24,000 | kW thermal / kWh thermal | Steady-state assumption, **not tower duty** |
| W0 *direct consumption* | 500 | 12,000 | L/h / L, site consumption basis | Assumed intensity, no measured validation |
| W2-Air *evaporation*, Step 20 case | ~489.4 | ~11,746 | L/h / L, evaporative air stage | Conditional physics scenario; daily total only if inlet and load are fixed |
| W2-Tower *evaporation*, Step 17 case | ~1,469.4 | ~35,265 | L/h / L, open cooling tower | Conditional **different** physical scenario |
| W2-Tower *makeup*, Step 17 case | ~1,959.2 | ~47,020 | L/h / L, cooling-tower intake | Includes evaporation + blowdown, **not** equivalent to site consumption |

Use script outputs as already generated; a short note or 10–20 line assertion-only check is enough. If roundoff differs at the last decimal, explain it.

## 3. Make five checks

1. **Electrical identity:** `P_DC = P_IT + P_nonIT` and `E = P*dt`. M0 `P_nonIT` is an aggregate residual only.
2. **Heat boundary:** `Q_IT ≈ P_IT` under steady state. Check that nobody substitutes M0 total facility power for IT heat or assumes all IT heat reaches a tower without declaring a separate routing assumption.
3. **Water basis:** W0 is labeled **direct consumption**; Step 20 predicts **evaporation**; Step 17 predicts both **evaporation** and **makeup**. Do not equate or add different water bases.
4. **Architecture:** W2-Tower and W2-Air are mutually exclusive archetypes for this comparison. Step 17's `COC` has no automatic role in Step 20's direct-air case.
5. **Critical cross-model inconsistency:** Step 18's *different* all-chiller assumption (`COP = 5`, 1,000 kW chiller load) implies **200 kW compressor electricity**, already greater than M0's total **47.1 kW non-IT** prediction. Therefore M0 + that chiller example **cannot** be treated as one internally consistent facility. This is a boundary/model-compatibility warning, not an error in either stand-alone demonstration. Step 20's fan electricity is also not identified from M0.

## 4. Deliverable and stopping rule

Create or append **one short `boundary_and_units.md`** containing the table, the five checks (pass or needs correction), and the one-sentence interpretation:

> M0 predicts aggregate facility electricity; the simple IT-heat balance approximates the IT thermal source; W0 represents assumed direct consumption; W2-Air predicts stage evaporation; W2-Tower predicts stage evaporation and makeup. None determines actual site water withdrawal or the causal change in cooling electricity without additional equipment and supply boundaries.

Keep Steps 00–20 untouched. **Do not create a new model, weather dataset, optimization scenario, or calibration.** Stop once the table reconciles and all incompatible combinations are clearly flagged.

## 5. Next (Step 22, not part of this step)

Take the *same* 1 MW example and identify the **IT-room heat boundary** in one short balance: electrical input, thermal heat carried away by server air/coolant, possible heat stored or exported. Reuse Step 20's server-air energy balance to show how the required airflow follows from a **stated** air-temperature rise. Do not calculate makeup or calibrate Prineville at Step 22.

---

Context:

## Step 21 — Verify the electricity, heat, and water boundaries

Objective: Confirm that the models developed in Steps 00–20 are physically and mathematically consistent, and understand exactly what each model predicts.

My recommendation is to avoid introducing any new equations or datasets in this step. Instead, use one reference case to identify which relationships are established, which are assumptions, and which quantities cannot yet be connected.

I prepared a complete implementation plan:

Download Step 21 — Boundary and Units Audit (.md)

### 1. Start with one reference case

Keep the same hypothetical facility:

- IT power: 1,000 kW, constant over 24 hours.
- M0: \\(P^{DC}=1.0471P^{IT}\\).
- W0: \\(V^{direct,con}=0.5E^{IT}\\) L.
- Reuse the existing cooling-tower and direct-evaporative examples separately.

The first output should be this table:

| Quantity                       | 1 hour            | 24 hours           |
| ------------------------------ | ----------------- | ------------------ |
| IT electricity                 | 1,000 kWh         | 24,000 kWh         |
| M0 facility electricity        | 1,047.1 kWh       | 25,130.4 kWh       |
| M0 non-IT electricity          | 47.1 kWh          | 1,130.4 kWh        |
| Idealized IT thermal energy    | 1,000 kWh thermal | 24,000 kWh thermal |
| W0 direct water consumption    | 500 L             | 12,000 L           |
| W2-Air evaporation (Step 20)   | 489.4 L           | \~11,746 L         |
| W2-Tower evaporation (Step 17) | 1,469.4 L         | \~35,265 L         |
| W2-Tower makeup (Step 17)      | 1,959.2 L         | \~47,020 L         |

The water figures come from different hypothetical cooling architectures. The daily W2-Air total also assumes its outdoor conditions stay constant for all 24 hours.

The numerical agreement between W0's 500 L/h and W2-Air's 489.4 L/h does not validate either model.

### 2. Five checks to perform

| Check                  | What to confirm                                                            | Why it matters                                                  |
| ---------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------- |
| A. Electricity         | \\(P^{DC}=P^{IT}+P^{nonIT}\\)                                              | Confirms M0 accounting, not cooling-component identification    |
| B. IT heat             | \\(\dot Q^{IT}\approx P^{IT}\\) under steady-state assumptions             | Establishes the thermal source, not where the heat goes         |
| C. Water basis         | W0 consumption, W2 evaporation, and W2 makeup are distinguished            | Prevents invalid comparisons                                    |
| D. Architecture        | Tower and direct-air models are evaluated separately                       | Prevents combining incompatible cooling systems                 |
| E. Power compatibility | Cooling-component power must fit within the chosen facility-power boundary | Prevents double counting and inconsistent equipment assumptions |

Check E is particularly valuable because it reveals a real limitation in our previous examples.

Step 18's illustrative chiller model used a 1 MW chiller load and COP = 5:

\\[ P^{compressor}=\frac{1000}{5}=200\text{ kW}. \\]

But our M0 reference predicts only 47.1 kW of total non-IT electricity.

Therefore, those two models cannot represent the same facility operating under the same assumptions. Both calculations may be correct independently, but combining them would be inconsistent.

This is exactly the kind of physical issue Step 21 should uncover before we proceed.

### 3. Implementation

Use the scripts already developed. No additional physics code is needed.

Create only one short note:

`dc_resource_sim/context/boundary_and_units.md`

It should contain the reference table, the five checks marked as passed or requiring correction, and three explicit categories for every important quantity:

- Measured or fitted: for example, the ESIF-derived M0 coefficient.
- Assumed: the 1 MW load, W0 intensity, cooling architecture, airflow, and equipment parameters.
- Not identified: actual cooling electricity, heat routing, site water intake, and groundwater withdrawals.

Do not change the earlier scripts. No optimization or weather analysis is required.

### 4. Stopping rule

Close Step 21 when we can correctly explain the differences among:

\\[ \boxed{ \text{Facility electricity} \\;\neq\\; \text{IT heat} \\;\neq\\; \text{Heat rejected by wet equipment} } \\]

and

\\[ \boxed{ \text{Evaporation} \\;\neq\\; \text{Process makeup} \\;\neq\\; \text{Facility water intake}. } \\]

Here the inequalities mean the quantities are not interchangeable; some can be numerically equal under particular assumptions.

We should also be able to state why M0 cannot be combined directly with an independent cooling-electricity model.

## Step 22 — The next small improvement

Only after Step 21 is complete, focus on IT electricity → IT heat → server airflow.

We will take the same 1 MW IT load and investigate:

\\[ \dot Q^{IT}\approx P^{IT} \\]

followed by the server-air heat balance:

\\[ \dot Q^{IT}\approx\dot m\_{air}c_p(T\_{return}-T\_{supply}). \\]

The new question will be:

Given an IT heat load and an allowable server-air temperature rise, how much airflow is necessary?

This is the most natural next physical relationship. It connects our power model to the cooling requirements without yet introducing water-intake assumptions, weather variation, or optimization.

My recommendation: Complete just Step 21 now. Its highest-value outcome is not another set of numerical predictions, but a consistent understanding of the physical boundaries—especially the distinction between IT heat and cooling electricity.
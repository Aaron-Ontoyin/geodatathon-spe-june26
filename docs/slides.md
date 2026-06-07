# GEOTHERM: Slide Script (for review)

Plain text first. Once the wording is settled, this becomes the PowerPoint.
Style: short lines, plain words, no em dashes, large bullets, help text small and rare.

Fill before submission: team member names and SPE numbers (slide 1), GitHub link (slide 14).

---

## Slide 1: Title

**Geothermal Heating and Cooling for Utrecht**

A least-cost design delivering at least 10 MWth of heat and 5 MWth of cooling from the Rotliegend.

Team GEOTHERM. [member names + SPE numbers]. SPE Africa Geothermal Datathon 2026.

**Visual:** dark cover, warm accent bar, thin layered bands at the bottom (a nod to rock layers). No image needed.

---

## Slide 2: The challenge

**Heat and cool an Utrecht district at the lowest cost**

- Source must be the Rotliegend only.
- Every well is costed.
- Optimize for the lowest cost.

**Visual:** three number cards on the right. `>=10 MWth` heating, `>=5 MWth` cooling, `min EUR/GJ` objective.

---

## Slide 3: Our approach

**One pipeline, from raw data to a costed plan**

Small line under title: *Everything runs from one config, so every number is reproducible.*

- An AI agent runs the full pipeline, and a live app lets you explore it.

**Visual:** a 5-step row of numbered cards: 1 Data, 2 Resource, 3 System, 4 Cost, 5 Decision, with arrows between them.

---

## Slide 4: The data

**The provided data needed correction before use**

- Depths labelled TVD were along-hole. PKP-01 read 323 m too deep.
- JUT-01 logs were in feet. One sheet had the wrong well name.
- Two wells had no porosity.

Small line: *We reconstructed true vertical depth to within a centimetre and imputed the missing porosity from the density log.*

**Visual:** small table on the right comparing our porosity to the ThermoGIS model.

| Well | Ours | ThermoGIS | Source |
|------|------|-----------|--------|
| BLT-01 | 16.4 % | 17.0 % | measured |
| EVD-01 | 11.8 % | 9.0 % | imputed |
| JUT-01 | 13.7 % | 11.0 % | imputed |
| PKP-01 | 9.0 % | 9.0 % | measured |

Caption: *Measured wells agree within 1 point, imputed wells within 3.*

---

## Slide 5: One external dataset

**A second opinion that agreed**

- We downloaded the public ThermoGIS map of the whole area, every 1 km square, not just the four wells.
- We ran a separate search over every location to find where the cheapest doublet would sit.
- It came back with one doublet, the same answer the four wells gave.

Small line: *The recommendation comes from the four provided wells. The grid is an independent check. All sources are cited.*

**Visual (optional):** a screenshot of the ThermoGIS map viewer zoomed on Utrecht.

---

## Slide 6: Challenge 1, the resource

**Two wells are viable. We site by the best one.**

- BLT-01 is the strongest: hot and permeable, about 5 MW.
- JUT-01 is secondary. EVD-01 and PKP-01 barely flow.
- The new doublet is sited 0.5 km from demand, about 4.8 MW.
- An independent grid search selects one doublet.

**Visual:** bar chart of power per doublet. BLT-01 about 5.1, JUT-01 about 2.3, EVD-01 = 0, PKP-01 = 0 (MW).
**Visual (optional):** a small map of the four wells and the new drill site near the district.

---

## Slide 7: Challenge 2A, the system

**Cooling keeps the wells in use all year, which lowers the cost**

- Geothermal carries the base load. The heat pump tops it up.
- Summer surplus heat is stored underground and used in winter.
- Cooling uses capacity that is otherwise idle in summer.

**Visual:** a 4-box flow. Geothermal doublet, then heat pump, then seasonal storage, then cooling.
Callout card: **59% to 99%**, caption *geothermal utilisation, heating only versus heating and cooling*.

---

## Slide 8: Challenge 2B, the cost

**Fewer wells plus storage give the lowest cost**

Big number: **21.1 EUR/GJ** (about 75 EUR/MWh).
Under it: CAPEX EUR 19.7 M. Geothermal 6.1 MWth. Heat and cool 44.5 and 12.4 GWh per year.

- The cost model is built from the provided spreadsheet.
- Well cost is set by the actual reservoir depth.
- Cooling reduces the cost by about a fifth.

**Visual:** bar chart of cost by size. 1 doublet 21.1, 2 doublets 31.4, 3 doublets 42.0 (EUR/GJ).

---

## Slide 9: Risk and what matters most

**A wide cost range, set mainly by one assumption**

Three cards: **P10 16.7. P50 21.1. P90 36.8** (EUR/GJ).

Small line: *The range is wide because the reservoir is uncertain. A second nearby well sits in the same rock, so it does not lower the risk.*

Key assumption: One doublet works with cold reinjection near 30 C. At a conservative 39 C, two doublets are needed.

**Visual:** horizontal bar chart (tornado) of what moves the cost most.
Reinjection temp 8.0. Power price 5.4. Discount rate 4.2. Well cost 4.0. Heat-pump cost 2.1. Gas price 0.0 (EUR/GJ swing).

---

## Slide 10: What we recommend

**Drill one doublet. Test it. Expand only if the data support it.**

- One doublet, with a heat pump, seasonal storage and cooling.
- Meets the targets at about 21 EUR/GJ, the lowest option we found.
- Test before scaling. A second well sits in the same rock.
- An independent site search also selects one doublet.

**Visual:** dark slide, four short points with small markers. No image needed.

---

## Slide 11: Bonus

**An AI workflow and a live app**

Two cards:

- **The AI workflow.** Runs the full pipeline and logs every decision. No API key required.
- **The live app.** Change any input and the cost updates. Search for the lowest-cost design within set limits.

Small line: *Built as a tool: typed, tested (151 tests), run with one command.*

**Visual (strongly recommended):** a real screenshot of the app (the live cost and dispatch view).

---

## Slide 12: Where this fits in Africa

**The reservoir is Dutch. The method transfers.**

Three cards:

- **Same problems elsewhere.** Few wells, messy data, large unknowns. The workflow handles all three.
- **Cooling matters more here.** Cold chains and farming need it. Direct use already runs at Olkaria.
- **Drill one, then grow.** Start small and scale on results, which suits a tight budget.

Small line: *The hot, shallow reservoir and heating-led demand are specific to this case. The workflow and economics are general.*

**Visual (optional):** a small map of East Africa or a photo of Olkaria.

---

## Slide 13: What we do not claim

**Where we kept the model simple, on purpose**

Five small cards:

- A monthly energy balance, not a transient simulation. Sufficient for this study, per the brief.
- Absorption cooling at 77 C is marginal. It may need a boost or more electric cooling.
- One doublet depends on cold reinjection and on storage covering the winter peak.
- The resource map uses four wells, two of them viable. More data would sharpen it.
- Demand is an estimate, set on the cautious side, so the cost is not flattered.

**Visual:** five small cards in a grid. No image needed.

---

## Slide 14: In short

**One doublet, a heat pump, storage and cooling, delivering district heat and cooling at the lowest cost**

- Cooling integration is what makes it economic.
- About 21 EUR/GJ. Test before scaling.

Code, app and report: [GitHub link]

Team GEOTHERM.

**Visual:** dark closing slide, matching the cover. No image needed.

---

### Optional real images that would lift the deck
- Slide 5: ThermoGIS map viewer screenshot (Utrecht).
- Slide 6: a simple map of the four wells and the new drill site.
- Slide 7: a clean system schematic (doublet, heat pump, storage, cooling loop).
- Slide 11: a screenshot of the live app.
- Slide 12: a small East Africa map or an Olkaria photo.

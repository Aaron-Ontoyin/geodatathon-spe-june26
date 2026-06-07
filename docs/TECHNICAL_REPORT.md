# Geothermal District Heating and Cooling for Utrecht: Technical Report

SPE Africa Geothermal Datathon 2026. Design of a least-cost geothermal district heating
and cooling system for a mixed urban district in Utrecht, Netherlands, targeting the
Rotliegend (Slochteren) sandstone, with a reproducible, agent-driven analysis pipeline.

---

## 1. Executive summary

We recommend a **staged single-doublet geothermal system**: one deep doublet paired with a
central heat pump, seasonal high-temperature aquifer thermal energy storage (HT-ATES), and
heat-driven cooling. It meets the brief's demand (at least 10 MWth heating and at least
5 MWth cooling) at an all-in levelized cost of energy of **21.1 EUR/GJ** (P10 16.7,
P50 21.1, P90 36.8), with near-zero backup.

The decisive design choices and findings:

- **Cooling makes the economics work.** Doing cooling as well as heating raises geothermal
  utilisation from 59 percent (heating only) to **99 percent**, because summer cooling and
  seasonal storage employ capacity a heating-only system would leave idle. This is the single
  largest lever on cost.
- **One doublet beats more.** LCoE rises monotonically with doublet count (1: 21.1, 2: 31.4,
  3: 42.0 EUR/GJ): the demand is fixed, so extra wells add capital without adding delivered
  energy. Fewer wells plus storage win.
- **Resource risk is large and not diversifiable by a second nearby well.** The Monte-Carlo
  LCoE band is wide and right-skewed (16.7 to 36.8 EUR/GJ); a second well in the same
  formation shares the same geology and does not de-risk it. The recommendation is therefore
  to drill one doublet, well-test it, and expand only if the data justify it.
- **The result is sensitive to one operational assumption.** Reinjection temperature is the
  top sensitivity (7.96 EUR/GJ swing across 30 to 42 C); the one-doublet result depends on
  heat-pump-enabled reinjection near 30 C.

An independent, unbiased search over the ThermoGIS regional grid (110 candidate sites in the
area of interest, each costed with its own depth and transmission) independently confirms a
single doublet, corroborating the recommendation across siting methods.

---

## 2. Problem statement

Design a geothermal-based system supplying a mixed residential, office and public district in
the Utrecht region with at least 10 MWth of heating and at least 5 MWth of cooling, from the
Rotliegend (Slochteren) reservoir. The judging metric is the levelized cost of energy at
adequate capacity, not maximum capacity; drilling cost is counted for every well, existing or
new. The work spans the two graded challenges (Challenge 1, resource assessment, 60 percent;
Challenge 2, integrated system design and economics, 40 percent) and a bonus for an
AI-assisted, automated workflow.

---

## 3. Data

### 3.1 Provided data (the core)

- **Four appraisal wells** (BLT-01, EVD-01, JUT-01, PKP-01): wireline logs (LAS), directional
  surveys, and lithostratigraphic tops.
- **Per-sample target-lithology table** (`target_lithologies.csv`).
- **ThermoGIS per-well sheets**: Rotliegend reservoir properties (transmissivity, temperature,
  porosity, permeability, thickness) as P10/P50/P90 distributions.
- **LCOE.xlsx**: the TNO/ECN levelized-cost spreadsheet, used as the economic reference.

The four wells are real field logs (logging contractor, tool serials, quarter-foot sampling,
measured bottom-hole temperature), not synthetic exports. They are the only independent
ground truth in the study.

### 3.2 Supplementary data (documented per the brief)

We use one external dataset beyond the provided files, documented here as the brief requires
(what it is, how it was obtained, and how it influenced the design).

- **What.** The public **ThermoGIS regional grids** for the Upper Rotliegend, produced by TNO
  and distributed through the Dutch national subsurface portal NLOG. These are gridded reservoir
  properties (depth, net-to-gross, permeability, thickness, temperature and doublet power) on a
  1 km lattice in RD-New coordinates, with the ThermoGIS engine being DoubletCalc1D.
- **How obtained.** Downloaded from the ThermoGIS export (thermogis.nl / NLOG) as NetCDF grids.
  We keep only the slice the analysis actually reads, the Upper Rotliegend BaseCase and Heat
  Pump scenarios, six properties each (about 3 MB of the roughly 195 MB national export), so the
  repository is self-contained without shipping unused data. The path is configurable via
  `GEO_THERMOGIS_ROOT`.
- **How it influenced the design.** The grid serves one supporting role: it is the resource
  source for the **independent grid-based siting confirmation** (Section 4.6), an unbiased
  search over every viable cell in the area of interest that independently arrives at a single
  doublet, corroborating the recommendation. The **canonical result rests on the provided
  data** (the four wells and LCOE.xlsx); the external grid is a second, independent check that
  agrees, not the source of the answer. (The porosity validation in Section 5.1 uses the
  provided per-well ThermoGIS sheets, which are part of the supplied data, not this grid.)

### 3.3 Data quirks handled

- `target_lithologies.csv` stores **along-hole depths** despite columns named `_tvd`, and the
  true-vertical-depth column is empty. Reconstructed from the directional surveys.
- The JUT-01 LAS carries both **feet and metre** depth channels; normalised to metres.
- The ThermoGIS BLT-01 sheet mislabels its inner well-name cell as PKP-01; keyed by sheet
  name and coordinates instead.

---

## 4. Methodology

The pipeline runs from a single typed configuration (`Assumptions`), so every number is
reproducible offline. The end-to-end flow is: data foundation, resource assessment, integrated
system design, techno-economics, recommendation (see `docs/methodology-flowcharts.md`).

### 4.1 Data foundation

- **Along-hole to true vertical depth** by the minimum-curvature method (the industry standard
  for directional surveys). The reconstruction reproduces the provider's own survey TVD to
  **0.009 m** (about 1 cm) across all wells, so downstream depths are trustworthy.
- **Porosity imputation.** Porosity is missing for two wells (EVD-01, JUT-01). It is estimated
  from the bulk-density log via the physics-based density-porosity relation, linearly
  calibrated on the two cored wells (BLT-01, PKP-01). A physics-anchored relation calibrated on
  two wells generalises better than a free-form fit on the same two.
- **Independent validation.** The imputed porosity is checked against ThermoGIS, a regional
  model built without these logs, so for the imputed wells it is a genuine out-of-sample test.
  Observed wells match ThermoGIS to within 1 porosity point; imputed wells land within about
  2.75 points (Section 5.1). Permeability is derived from porosity via a log-linear poro-perm
  trend fitted to the ThermoGIS P50 values.

### 4.2 Resource assessment (Challenge 1)

Per-well doublet power is computed as P10/P50/P90 bands from a deliverability model calibrated
to ThermoGIS (flow scales with transmissivity above a viability threshold and is capped at a
realistic pump ceiling; thermal power is flow times the brine heat capacity times the
production-to-reinjection temperature drop). Only two of the four wells are viable (Section
5.1). A new doublet is sited in the proven trend, near the demand district, by an
inverse-distance-weighted resource map scored on power and proximity to demand.

### 4.3 Integrated system design (Challenge 2A)

The system is modelled at an assessment-level monthly energy balance (per the brief), not a
transient reservoir or thermodynamic simulation:

- **Heating** each month: geothermal upgraded by the heat pump, then HT-ATES discharge, then a
  small backup boiler for any residual.
- **Cooling** each month: an absorption chiller driven by spare summer geothermal heat, then
  free cooling, then an electric compression chiller.
- **Seasonal storage**: summer surplus geothermal heat charges the HT-ATES for winter.

The heat pump enables a low reinjection temperature, which maximises the heat extracted from
the brine; the cooling and storage soak up capacity that heating alone would leave idle.

### 4.4 Techno-economics (Challenge 2B)

- **LCoE model**: a Python port of LCOE.xlsx, calibrated to reproduce its base case exactly
  (5.77 EUR/GJ), then extended for the hybrid system. We verified that the single effective
  discount rate (9.3 percent) is equivalent to the spreadsheet's full levered, post-tax,
  equity-discounted cash flow across the design space (both are linear in capex, opex and
  energy; the opex and energy discount factors cancel in the ratio).
- **Depth-dependent well cost**: the spreadsheet's own well-cost formula (cell D12) evaluated
  at the Utrecht reservoir depth (about 2281 m), not its 1800 m worked example, so wells are
  not under-costed.
- **Transmission**: the cost of the main from the doublet to the demand district is included,
  so the headline LCoE is all-in.
- **Uncertainty**: a Monte-Carlo over the (large) lognormal transmissivity uncertainty
  produces the P10/P50/P90 LCoE band. The model treats the field as a single correlated draw,
  which is why a second nearby well does not reduce the risk.

### 4.5 Two execution modes

- **Evaluate**: run the chain once for a fixed set of inputs and report the design, LCoE and
  band.
- **Optimise**: sample the design levers across user-specified ranges (crossed with doublet
  count), screen each candidate against feasibility constraints (backup fraction cap, CAPEX
  and LCoE budgets, demand met), and select the least-cost feasible configuration.

### 4.6 Independent grid-based siting confirmation

A separate, unbiased search treats every 1 km cell in the demand-centred 20 by 20 km area of
interest, plus the four wells, as equal candidates. Each is costed as a single doublet at its
own depth with its own transmission distance; candidates are ranked by their actual LCoE, and a
combinatorial program search returns the least-cost well program. This cross-checks the well
count and siting independently of the demand-proximity heuristic used for the headline design.

### 4.7 Agentic workflow and demo app (bonus)

- An **agentic workflow** runs the whole pipeline and records a decision log (action, decision,
  key metrics) at each stage. It is deterministic and needs no API key; an optional LLM layer
  can narrate it and falls back gracefully without one.
- A **FastAPI plus React** application exposes the pipeline interactively: change any
  assumption, run Evaluate or Optimise, and see the headline metrics, dispatch, design
  comparison, Monte-Carlo band, sensitivity tornado, the full report, and the decision log,
  with live progress over server-sent events. It imports and exports the same TOML the CLI
  uses. The backend can serve the built frontend so a single process hosts both.

---

## 5. Results

### 5.1 Resource

Doublet power per well (P90/P50/P10, MW), calibrated to ThermoGIS:

| Well | P90 | P50 | P10 | Viable |
| --- | --- | --- | --- | --- |
| BLT-01 | 0.72 | 5.13 | 23.21 | yes |
| JUT-01 | 1.05 | 2.30 | 4.98 | yes |
| EVD-01 | 0.00 | 0.00 | 0.00 | no |
| PKP-01 | 0.00 | 0.00 | 0.00 | no |

Only BLT-01 and JUT-01 are viable; the other two are too tight. Porosity validation against
the independent ThermoGIS model:

| Well | Porosity (ours) | Porosity (ThermoGIS) | Difference | Source |
| --- | --- | --- | --- | --- |
| BLT-01 | 16.4 | 17.0 | -0.6 | observed |
| EVD-01 | 11.8 | 9.0 | +2.8 | imputed |
| JUT-01 | 13.7 | 11.0 | +2.7 | imputed |
| PKP-01 | 9.0 | 9.0 | +0.0 | observed |

Observed wells agree to within 1 point; the imputation lands within about 2.8 points, and the
uncertainty concentrates in the two non-viable wells, so the resource decision is robust.

### 5.2 Recommended design

| Quantity | Value |
| --- | --- |
| Doublets | 1 |
| Geothermal capacity | 6.14 MWth |
| Firm heating capacity (with heat pump) | 7.89 MWth |
| All-in LCoE | 21.1 EUR/GJ (75 EUR/MWh) |
| LCoE band P10 / P50 / P90 | 16.7 / 21.1 / 36.8 EUR/GJ |
| CAPEX | 19.7 MEUR |
| Backup fraction | 0 percent |
| Geothermal capacity factor | 99 percent (59 percent heating only) |
| Heat delivered | 160,308 GJ/yr (44.5 GWh) |
| Cooling delivered | 44,676 GJ/yr (12.4 GWh) |

### 5.3 Design comparison and sensitivity

Design comparison (lowest LCoE wins):

| Doublets | LCoE (EUR/GJ) | CAPEX (MEUR) |
| --- | --- | --- |
| 1 | 21.1 | 19.7 |
| 2 | 31.4 | 34.1 |
| 3 | 42.0 | 50.2 |

Sensitivity (one-way swing in the optimal LCoE across each plausible range):

| Assumption | Range | LCoE swing (EUR/GJ) |
| --- | --- | --- |
| Reinjection temperature | 30 to 42 C | 7.96 |
| Electricity price | 100 to 200 EUR/MWhe | 5.36 |
| Discount rate | 6 to 12 percent | 4.21 |
| Well cost | 2 to 5 MEUR | 3.99 |
| Heat-pump cost | 500 to 900 kEUR/MWth | 2.10 |
| Gas price | 20 to 60 EUR/MWhth | 0.00 |

Reinjection temperature is the most decision-critical lever: it sets doublet capacity and so
whether one doublet meets demand. The one-doublet result depends on heat-pump-enabled
reinjection near 30 C; at a conservative bare-doublet return near 39 C a second doublet would
be needed. Gas price and demand-distance weight do not move the optimum (the design barely
uses backup, and the sited well is already near demand).

### 5.4 Independent siting confirmation

The unbiased grid search over 110 viable candidate cells in the area of interest independently
selects a single doublet, agreeing with the recommendation. Its grid LCoE is somewhat higher
because it charges each cell its own transmission and deeper-cell drilling cost; the agreement
on well count is the robustness result.

---

## 6. Practical applicability to Africa

The case study is Dutch because the subsurface data is public, but it is a transferable
template. What carries to an East African Rift context is the method and the economics, not the
specific reservoir numbers.

- **The data-science workflow transfers directly.** Operators appraising a new field (for
  example KenGen or GDC in Kenya) face the same problems this pipeline solves: few wells,
  missing or mislabelled logs, and large resource uncertainty. The reusable parts are
  reservoir-agnostic: depth reconciliation, ML imputation of missing petrophysics, probabilistic
  resource assessment, a transparent LCoE model, and the agentic automation.
- **Cooling is more valuable in Africa than in the Netherlands.** Space-cooling and cold-chain
  demand (food, agriculture, pharmaceuticals) are large and growing; the heating-plus-cooling
  integration, especially the cooling and storage logic, maps onto African demand better than a
  heating-only scheme. Geothermal direct use for cooling, drying and greenhouses is already
  practised at Olkaria.
- **Lowest-LCoE, staged development fits a capital-constrained setting.** Running the resource
  hard for the lowest credible cost, and drilling one well then expanding only on evidence, is
  how a risk- and capital-constrained developer should sequence a project.

What does not transfer: the absolute resource (Rift volcanic systems are hotter and shallower
than the Dutch Rotliegend), the heating-led demand shape, and the specific costs. A local team
would re-run the same workflow on local data.

---

## 7. Reusability and how to run

The solution is built as a tool, not a one-off notebook.

- **Single typed configuration.** Every economic, design and siting lever is a field on the
  `Assumptions` model, with documented defaults and bounds. Changing one value reruns the whole
  chain consistently.
- **Command line** (no API key):
  - `uv run geo-datathon template --out inputs.toml` writes a starting input file.
  - `uv run geo-datathon report --input inputs.toml` runs the pipeline and prints the report.
  - `uv run geo-datathon workflow` runs the agent and prints the decision log.
- **Interactive app**: build the frontend once and run one process (`uv run uvicorn
  geothermal.api:app`), or run the Vite dev server for hot reload. See `README.md`.
- **Extensibility through a provider seam.** Resource properties are read through a single
  interface (`properties_at`), so the backing source can change (the current ThermoGIS grid, a
  full-percentile grid, or a live query) without touching the search or the cost model. To apply
  the analysis elsewhere, point `GEO_THERMOGIS_ROOT` at a ThermoGIS export with the same layout
  and adjust the area-of-interest centre in the config.
- **Quality**: the library is fully type-annotated, linted (ruff) and type-checked (pyright),
  with 151 tests covering the petrophysics, resource, design, economics, optimiser, grid
  pipeline and report.

---

## 8. Limitations

- The system is a monthly energy balance, not a transient reservoir or thermodynamic
  simulation. In particular it treats geothermal heat as fungible MW; a single-effect absorption
  chiller wants 80 to 90 C drive heat, marginal at the about 77 C production, so absorption
  cooling may need a two-stage lift or more compression cooling than the balance implies.
- Doublet capacity is most sensitive to reinjection temperature. The power model is calibrated
  to ThermoGIS near 39 C and extrapolated to the heat-pump-enabled 30 C; the one-doublet result
  depends on that assumption (the tornado quantifies the swing; the count flips near 37 C).
- The resource map is built from four wells (two viable); a denser regional grid sharpens it.
  The bulk ThermoGIS grid we use is P50 only, so where the analysis interpolates between wells
  the uncertainty is modelled rather than read.
- The Monte-Carlo assumes a single correlated transmissivity field; partial spatial correlation
  would narrow the band somewhat.
- The demand profile is an assumption (the brief gives only peak loads): a degree-day-shaped
  Dutch monthly demand, about 4,450 heating and 2,480 cooling full-load hours, conservative
  against the LCOE.xlsx 6,000 hours. The energy delivered, and hence the LCoE, scales with these
  hours.

---

## 9. Conclusion

A single geothermal doublet, paired with a heat pump, seasonal HT-ATES storage and heat-driven
cooling, meets the district's heating and cooling demand at an all-in levelized cost of about
21 EUR/GJ, the lowest of the configurations considered. Cooling integration, not more wells, is
what makes it economic; the recommendation is to drill and test one doublet before any
expansion. The result is reproduced by an independent grid-based siting search and is delivered
through an auditable, reusable, agent-driven pipeline that transfers, in method if not in
specific numbers, to African geothermal appraisal.

---

### Appendix: repository layout

```
src/geothermal/      library: io, petrophysics, resource, design, economics, agent, api
frontend/            React + Vite demo app
tests/               pytest (151 tests)
notebooks/           runnable analysis notebooks
data/                provided datasets + the ThermoGIS grid subset used
docs/                brief, FAQ, methodology flowchart, this report, design spec
scripts/             deck/figure builder
```

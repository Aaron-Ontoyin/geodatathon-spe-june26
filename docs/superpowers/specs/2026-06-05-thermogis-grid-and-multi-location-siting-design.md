# ThermoGIS Grid Resource + Multi-Location Siting + Honest Risk: Design

Date: 2026-06-05
Status: Proposed (awaiting review)

## 1. Why this work

A long working session re-examined the foundations of our solution and surfaced
several things that change the design. All are verified against code, the provided
data, the downloaded ThermoGIS grid, and the ThermoGIS documentation.

What we established:

1. **ThermoGIS owns the resource map, by design.** The organizers built the case on
   public Dutch data and told us to use ThermoGIS for new locations. The per-cell
   resource (power, transmissivity, temperature, depth, etc.) is a ThermoGIS product
   (its engine is DoubletCalc1D). Recomputing it is not the value-add.
2. **The provided 4-well ThermoGIS sheets are point samples of the regional grid.**
   We confirmed this: reading the downloaded grid at the 4 well coordinates reproduces
   the provided sheet values (e.g. BLT-01 transmissivity 10.4 vs 9.3 Dm; temperature,
   porosity, permeability all match to rounding). The grid is a strict superset.
3. **The 4 well logs are the only independent data we have.** They are real field logs
   (logging contractor, tool serials, quarter-foot sampling, measured BHT), not
   ThermoGIS output. Their honest role is the Challenge-1 petrophysics plus validating
   and locally calibrating ThermoGIS, not being the resource source.
4. **The current siting is biased and the current Monte-Carlo is too pessimistic.**
   - Siting repelled new wells from the 4 existing wells (1.5 km exclusion) and so
     never considered reusing them; it also pivoted on a single best cell.
   - The design scales one "representative" doublet by N rather than placing N distinct
     sited doublets.
   - The Monte-Carlo draws one shared transmissivity for all doublets (correlated-field
     assumption), so it cannot show real diversification across separated wells.
5. **The log-derived petrophysics does not currently reach the LCoE.** `porosity_final`
   and `permeability_md` have no consumers outside the petrophysics/report modules;
   power and LCoE ride on ThermoGIS transmissivity. So the 60%-weighted resource work
   is, today, parallel to the number that decides the result.
6. **Cooling and the integrated heating+cooling system are not in ThermoGIS.** Verified
   on the ThermoGIS pages: heat pumps upgrade heat only; HT-ATES is "heat storage only";
   "cooling is not part of ThermoGIS." Since the challenge requires >=5 MWth cooling,
   the deciding part of the work is exactly what ThermoGIS does not produce.

The conclusion that drives this design: **ThermoGIS gives the rock and a heating-only
economic potential. We win on the well program, the heating+cooling integration, and
the combined LCoE, automated end to end.** This spec re-scopes the resource and siting
layers to that reality and gives the logs a genuine economic role.

## 2. Goals / non-goals

**Goals**
- Use the downloaded ThermoGIS regional grid as the resource source for the area of
  interest, behind a single provider interface.
- Replace single-well siting with an unbiased multi-location doublet-program search.
- Give the 4 well logs a real role: petrophysics + validation + local calibration, and
  make reservoir **depth** drive well CAPEX (so the logs/grid reach the LCoE).
- Make the Monte-Carlo per-well and independent, with honest measured-vs-modeled risk.
- Keep everything config-driven (no hard-coded literals) and documented for judges.

**Non-goals**
- Recomputing the ThermoGIS resource physics ourselves (we align to / cite DoubletCalc1D
  rather than reimplement it).
- Changing the heating+cooling system design itself (Challenge 2A logic stays; it is the
  differentiator and is already sound).
- A full geostatistical (kriging) uncertainty model.
- Independent producer/injector placement within a doublet (a doublet remains one site).

## 3. Verified facts and numbers (inputs to the design)

- **Area of interest:** 20x20 km box centered on the demand district at RD
  (141171, 454890), the trilaterated Utrecht Science Park location.
- **Grid:** NetCDF, 1 km cells, RD-New coordinates (same system as the wells), national
  extent, `data` variable + `oblique_stereographic` CRS var. Path layout:
  `<root>/6_Permian/Upper Rotliegend Gp (RO)/<scenario>/RO_STACKED_<prop>[_HP].nc`.
- **Scenarios:** BaseCase, Heat Pump, Well Stimulation, Well Stimulation & Heat Pump.
  We use **Heat Pump** (matches our design intent).
- **Properties per scenario:** depth, porosity, permeability_p50, net_to_gross,
  thickness_p50, temperature, flow_rate_p50, power_p50, heat_in_place,
  potential_recoverable_heat, economic_potential.
- **Critical limitation:** the bulk download is **P50 only**. There are no P10/P90 grids.
  We have real P10/P50/P90 only at the 4 wells (provided sheets). Lattice-cell
  uncertainty must therefore be **modeled** (see 4.6), not read.
- **In our box (Heat Pump scenario):** Rotliegend present in 100% of 400 cells; power
  ranges 0-7 MW; ~59% of cells >= 2 MW, ~46% >= 3 MW. So presence is not the filter
  here, **viability** is.
- **DoubletCalc1D uncertainty method:** triangular distribution from min-med-max of each
  property, >1000 Monte-Carlo draws -> P10/P50/P90. Our per-well bands follow this shape.
- **ThermoGIS economic defaults (to align our cost model):**
  - Geothermal well CAPEX = `(375000 + 1150*d + 0.3*d^2) * 1.5` EUR, d = along-hole depth.
  - HT-ATES well CAPEX = `100000 + 1000*d + 0.3*d^2` EUR.
  - Fixed surface CAPEX 3 MEUR; variable 300 EUR/kW; contingency 15%.
  - OPEX: 100 EUR/kW fixed + 0.19 EURct/kWh heat + pump electricity.
  - Injection/return temperature 30 C (matches our `injection_temp_c`).
  - Pump efficiency 60%; 6000 full-load hours; economic life 30 yr (15 yr subsidy);
    electricity 8 EURct/kWh; discount 5% loan + 14.5% equity.
  - Doublet spacing optimized so production cools <=10% over 50 years; pump pressure
    capped at 300 bar + regulator injection limits. Our fixed 1.5 km is a simplification
    of this, to be cited as such.

## 4. Design

### 4.1 Property provider seam (the key abstraction)

One interface that everything downstream calls. Swapping the underlying source must not
touch the search, cost model, or risk step.

```
SiteProperties:
    transmissivity_dm: float
    temperature_c: float
    power_mw_p50: float
    depth_m: float
    sigma_log_trans: float     # uncertainty width (log-space), from data or modeled
    source: Literal["measured", "thermogis_grid"]

properties_at(x, y) -> SiteProperties
```

Two providers, selected by config:
- **`thermogis_grid`** (default for lattice cells): reads the NetCDF grids at (x, y).
  Returns ThermoGIS power/temperature/depth directly; transmissivity from
  permeability*thickness*net_to_gross; `sigma_log_trans` modeled (4.6); `source =
  thermogis_grid`.
- **`measured`** (the 4 wells): values anchored to the provided per-well sheets/logs,
  `sigma_log_trans` from the real P10/P50/P90, `source = measured`.

This is the seam that lets a future full-percentile grid or a live ThermoGIS call drop in
without downstream changes.

### 4.2 Area of interest

Config: `aoi_center_rd = (141171, 454890)`, `aoi_size_km = 20`. The grid is cropped to
this box for all candidate generation and siting. Outside-box cells are never candidates.
The 4 wells remain available for petrophysics/validation even if a well falls outside the
box (PKP-01 is 22.7 km away, so it is a data anchor, not a candidate site).

### 4.3 Candidate set

`candidates = lattice ∪ {the 4 wells at exact coordinates}`, then filtered.

- **Lattice:** regular grid at `min_well_spacing_km` pitch (default 1.5 km) over the AOI.
  Equal pitch both generates candidates and auto-enforces inter-candidate spacing.
- **Inject the 4 wells at their true coordinates** (do not snap to lattice nodes; snapping
  would move the one place we have measured data). Drop any lattice point within
  `min_well_spacing_km` of an injected well to avoid sub-spacing pairs.
- **Filters:** keep a cell iff it is inside the AOI AND Rotliegend is present (grid value
  non-NaN) AND `power_mw_p50 >= viability_floor_mw` (config; ThermoGIS power already folds
  in net-to-gross and reservoir quality). In our box only the viability floor bites.

All candidates are treated **equally** in the search: no reference-well privilege. The
only difference between a measured well and a lattice cell is its `sigma`/`source`, which
affects risk, not ranking.

### 4.4 Multi-location doublet-program search

Option A (candidate-shortlist + exhaustive combinations), chosen for faithfulness:

1. Reduce candidates to a shortlist of the strongest cells (local power maxima + the 4
   wells + demand-near cells, deduped by spacing) of size ~20-40.
2. For program size k = 1, 2, 3, ... evaluate every spaced combination of k shortlist
   sites. For each combination:
   - total geo capacity = sum of each site's per-doublet capacity (location-specific,
     from its own properties), and
   - run the full integrated system once (design -> dispatch -> LCoE) on that total.
   - enforce `min_well_spacing_km` between any two chosen sites.
3. Keep the best feasible program (meets the district demand) by the objective.

**Stopping rule is objective-driven, not a fixed cap:**
- `min_lcoe` (default): LCoE is U-shaped in k (cost grows, delivered energy saturates at
  demand). Stop when adding a doublet no longer lowers LCoE.
- `min_capex`: stop at the fewest doublets that stay feasible.
- `max_capacity`: bounded by the CAPEX/LCoE cap constraints, not by demand.
Natural hard bound: cannot exceed the number of spaced shortlist sites. Any truncation is
logged (no silent caps).

This replaces both `recommend_new_well` (single cell) and the N-copies scaling in
`evaluate_candidate`.

### 4.5 The logs' economic role (depth-driven CAPEX)

Use the provided LCOE.xlsx well-cost formula so that reservoir **depth** drives CAPEX,
which is what makes the logs/grid reach the LCoE (see Revisions, section 10):

`well_capex(d) = 1.5 * (0.2*d^2 + 700*d + 250000) * 1e-6`   (M€)

per LCOE.xlsx cell D12, where d is along-hole depth (= cell TVD x `well_curvature_factor`,
1.1). Ported in `geothermal.economics.well_cost`. Deeper cell -> costlier well -> worse LCoE.

The 4 wells additionally:
- exercise the Challenge-1 petrophysics (TVD reconstruction, porosity imputation),
- **validate** ThermoGIS locally (porosity and measured BHT are independent), and
- optionally **bias-correct** the grid by the well residuals (deferred; documented as a
  possible refinement, off by default).

### 4.6 Honest Monte-Carlo (per-well, independent)

Per scenario draw: each chosen doublet gets its **own independent** transmissivity draw
(not one shared field), then sum capacities -> one system -> one LCoE. Combination rule:
capacity is additive (pre-summable per well); LCoE is not (shared surface plant + demand
saturation), so it is computed once at the system level inside the run.

Per-site uncertainty width:
`sigma_site^2 = sigma_geology^2 + sigma_interp(d)^2`, where
- `sigma_geology` = the base reservoir spread. At a **measured** well it is the real
  P10/P50/P90 from the provided sheet (narrow). At a lattice cell we lack a band (P50-only
  grid), so we use a base spread calibrated from the 4 wells' relative bands.
- `sigma_interp(d)` grows with `d` = **distance to the nearest logged well** (min over the
  4), and is **zero at a logged well**. This encodes "the further from real data, the less
  we trust the P50."

Rationale for min-distance over weigh-by-all: robust to the clustered, sparse 4-well
layout; one-sentence explainable; collapses to zero at a well. A full kriging variance is
out of scope.

Note: if P10/P90 grids are later obtained, `sigma_interp` is dropped and `sigma_geology`
comes straight from the grid bands, with no downstream change (that is the point of the
provider seam returning `sigma`).

### 4.7 Cost model alignment

Extend the existing LCoE model so its geothermal cost physics match ThermoGIS/DoubletCalc
where they should (depth-dependent wells, injection temp 30 C, spacing rationale), then
keep our hybrid extensions (heat pump sizing, HT-ATES, and the cooling integration that
ThermoGIS does not model). Where our defaults intentionally differ from ThermoGIS
(electricity price, discount structure, lifetime), document the difference and the reason
so the report can defend it. Reconcile our base case against ThermoGIS economic potential
at the well cells as a sanity check.

## 5. Config additions (all knobs, no literals)

- `thermogis_grid_root: Path`, `thermogis_scenario: Literal[...] = "heat_pump"`.
- `aoi_center_rd: tuple[float, float]`, `aoi_size_km: float = 20`.
- `viability_floor_mw: float`.
- `min_well_spacing_km` (already exists; now also the lattice pitch + inter-doublet rule).
- `well_curvature_factor` (well-cost coefficients live in `geothermal.economics.well_cost`).
- `sigma_interp_*` (decay of interpolation uncertainty with distance).
- `objective` and the existing demand/cost constraints.
- `shortlist_size`, max program size guard (large, just a backstop).

## 6. Dependencies, data, provenance

- New deps: `xarray`, `netCDF4` (NetCDF reading), under a data extra.
- The ThermoGIS grid is supplementary public data: document in the report which dataset
  (ThermoGIS v2.x RO grids, TNO/NLOG), how it was obtained, and how it influenced the
  design, exactly as the brief requires. Keep the raw `.nc` out of git (large); load from
  a configured path; record provenance and a checksum.
- Cite DoubletCalc1D (nlog.nl/tools) and pythermogis as the resource engine we align to.

## 7. Testing

- Provider: grid lookups at the 4 well coordinates reproduce the provided sheet values
  within tolerance (the consistency check we already ran becomes a test).
- AOI/candidate: box crop count, viability filter drops the known tight cells, the 4 wells
  are injected and sub-spacing lattice points removed.
- Search: a synthetic field where a separated pair beats the single best cell is found by
  Option A (and missed by greedy) -> proves faithfulness; objective stopping rules each
  terminate correctly.
- Monte-Carlo: independent draws give a narrower band than the shared-field draw for a
  separated 2-doublet program; measured site -> narrower band than a far lattice site.
- Cost: `well_capex(d)` monotonic in depth; base case still reproduces the known optimum
  within tolerance.

## 8. Limitations (to state in the report)

- Grid is P50-only; lattice uncertainty is modeled, not measured.
- Doublet modeled as a single point (no intra-doublet producer/injector geometry).
- A doublet remains one sited location; spacing/interference handled by the 1.5 km rule,
  a simplification of ThermoGIS's 50-year 10%-cooling optimization.
- ThermoGIS properties are themselves model-derived from a porosity-depth trend; only the
  4 wells are measurements.

## 9. Decisions locked (from the design session)

Candidate = demand-centered 20 km box; lattice at 1.5 km ∪ 4 wells at true positions,
deduped, viability-filtered; equal treatment; Option A exhaustive search; objective-driven
stop (no fixed cap); one-point doublets; per-well independent Monte-Carlo; per-site sigma
with min-distance interpolation term; provider seam returning value+sigma+source; ThermoGIS
grid as the resource source with depth-driven well CAPEX; cooling integration confirmed as
our differentiator. All thresholds are config inputs.

## 10. Revisions (2026-06-06, post plan-review)

A careful review of the implementation plan corrected four points; this section supersedes
the corresponding text above.

- **4.5 well CAPEX — use the LCOE.xlsx formula directly.** A correctness pass found the
  provided spreadsheet has its OWN well-cost formula (cell D12:
  `1.5*(0.2*d^2 + 700*d + 250000)*1e-6`, d = along-hole depth), which differs from
  ThermoGIS's. We port the spreadsheet's (now in `geothermal.economics.well_cost`, validated
  to reproduce its 3.237 M€ at 1800 m). The old flat 3.237 default was the spreadsheet's
  1800 m example and under-costs our ~2281 m wells; corrected to 4.331 M€ (formula at the
  Utrecht depth). The multi-site search costs each site at its own grid depth
  (`depth_m * curvature`); per-site well costs are summed, not averaged.
- **Two further LCoE bugs were fixed in the existing code during this pass** (not just the
  plan): a circulation-pump electricity **double-count** (the spreadsheet's variable O&M IS
  the pumping cost, which we also modelled explicitly), and confirmation that the **9.3%
  single-rate LCoE is mathematically equivalent** to the spreadsheet's levered DCF across the
  design space (so no DCF port is needed). Net headline change was small (20.9 -> 20.85
  €/GJ) and 1 doublet still wins, the recommendation is robust.
- **4.6 base sigma is a config input** (`base_sigma_log_trans`, default ~1.5 from the wells'
  P10/P90 bands), not a hardcoded constant. The measured tier needs no separate provider:
  the interpolation term is zero at a well, so well cells get the narrow base band directly.
- **Search is bounded.** The exhaustive shortlist is ~12 with a doublet backstop of 4 to keep
  the combinatorics tractable; the early stop normally halts at 1-2 doublets.
- **Objectives.** `search_program` implements `min_lcoe` (the deciding metric); `min_capex`
  and `max_capacity` are deferred (the parameter-space optimizer already covers objectives).

## 11. Revisions (2026-06-06, post-implementation)

The full grid pipeline was built (loader, provider, AOI lattice, program search, per-well
Monte-Carlo, transmission cost) and is tested and live. During integration we found that
making the grid path the **canonical** result is not the right call:

- `shortlist_from_grid` ranks candidates by raw power and keeps the top N, so near-demand
  moderate-power cells are excluded from the search; and with depth-dependent well cost in
  play, the search prefers a shallower, cheaper-to-drill cell ~4 km from the district. A
  distance-based transmission cost was added (and is correct economics) but cannot pull
  siting back, because near-demand cells are not in the power-ranked shortlist.
- The result was a far shallow site with a higher, assumption-sensitive LCoE (~23-28),
  diverging from the clean, validated legacy headline (1 doublet in the proven BLT trend,
  99% capacity factor, ~20.8 EUR/GJ).

**Decision:** keep the legacy near-demand pipeline as the **canonical** recommendation, and
present the unbiased grid multi-location search as an **independent robustness check** in the
workflow (it confirms the doublet count). The grid pipeline remains fully built and tested;
making it canonical would need an LCoE-/demand-aware shortlist (a future enhancement), not a
power-ranked one.

# SPE Africa Geothermal Datathon 2026 — Solution Design

- **Date:** 2026-06-03
- **Status:** Approved (brainstorming) — awaiting spec review before planning
- **Team strategy:** "Balanced flagship" — win on rigorous geoscience + techno-economics AND an agentic AI workflow + interactive app. Deadline is NOT a constraint (officially extended); build extensive, complete, correct work.

---

## 1. Context & problem

Design a **geothermal-based district heating + cooling system** for a mixed urban district (residential / offices / public) in the **Utrecht region, Netherlands** (a simplified version of a real NL development). Target reservoir: **Rotliegend (Slochteren) sandstone** — the deep formation only; shallow reservoirs are disqualified.

**Hard requirement:** supply **≥10 MWth heating AND ≥5 MWth cooling.**

**Scoring (from kick-off webinar + challenge slides):**
- Challenge 1 (60%): assess geothermal potential; decide well count, location(s), depth to meet base load.
- Challenge 2 (40%): design the integrated heating+cooling system + compute **LCoE**.
- Bonus: AI-assisted/agentic workflow automating the design pipeline (organizers will RUN the code and reward effort/creativity).
- FAQ criteria: technical rigor, innovation/creativity, clarity, practical applicability to Africa.

**Decisive judging insight (stated twice):** more MW is *not* better. The winner delivers ~**10–15 MWth heat + ≥5 MWth cool at the lowest, most credible LCoE**, with reproducible reasoning. Drilling cost counts for **every** well, including the 4 provided.

## 2. Success criteria

1. A correct, TVD-accurate, gap-filled dataset usable by all downstream stages.
2. Probabilistic (P10/P50/P90) resource assessment + a spatial map that justifies chosen well locations (incl. *new* sites).
3. An integrated heating+cooling design whose narrative is "cooling monetizes idle summer capacity → lower LCoE."
4. An **LCoE optimization** (not a point estimate) with uncertainty bands, meeting the ≥10/≥5 MW constraint at minimum cost.
5. A reproducible agentic workflow (with deterministic, no-API-key fallback) + focused demo app.
6. All three graded deliverables complete and within limits (repo; 10–15 slide deck; 3–5 min narrated video).

## 3. Constraints & non-goals

- **Tooling:** `uv` + `ruff` + `pyright` for Python; `FastAPI` + `React`/`Vite` for the demo app. Notebooks must be runnable for D1.
- **Altitude (anti-over-engineering):** assessment-level engineering, **no transient reservoir/CFD simulation, no detailed thermodynamic chiller/heat-pump models** (COP assumptions only) — the organizer explicitly framed it this way.
- **Non-goals:** chasing >~15 MW; 30-page report / 30 slides; app gold-plating (no auth, DB, accounts).
- Core solution must use provided data; supplementary public data (esp. ThermoGIS, thermogis.nl) is allowed but must document *what / how extracted / how it influenced design*.

## 4. Provided data & known quirks (must handle)

- `data/raw/*.las` — wireline logs. BLT-01 log-rich (GR, NPHI, RHOB, DTC/DTS, PE, resistivity, spectral GR); EVD/PKP/JUT sparser. **JUT-01 LAS depth runs to a bogus ~11,220 — feet/metre unit collision; must fix.**
- `data/Well Path Data.xlsx` — deviation surveys (MD, incl, azim, TVD, X/Y offset). JUT-01 strongly deviated (MD ≫ TVD).
- `data/Lithostratigraphic Data.xlsx` — formation tops/bottoms per well. NB: "Röt Fringe Sandstone" (Triassic) is NOT the target; Rotliegend sits below Zechstein.
- `data/ThermoGIS Data.xlsx` — per-well Rotliegend P10/P50/P90 (perm, top depth, thickness, porosity, N/G, transmissivity, temperature, flow, power, heat-in-place). **QUIRK: the sheet named "BLT-01" has its Well Name cell wrongly = "PKP-01"; coords (141577.55, 456881.76) prove it is BLT-01.** Resource is marginal/uneven: only BLT (~5.1 MW P50) and JUT (~2.3 MW P50) viable; EVD & PKP ≈ 0 MW (transmissivity 0.1–0.4 Dm).
- `data/LCOE.xlsx` — TNO/ECN cash-flow LCoE model (geothermal heat + power only); must be extended for hybrid heating+cooling.
- `data/target_lithologies.csv` — 3455 rows. **THE TRAP: every row flagged "AH depth — deviated well needs TVD conversion"; the `formation_top_tvd`/depth values are actually along-hole, not TVD. `depth_tvd_m` is 100% null; ~30% of `porosity_pct` is null; `bulk_density_gcc` null for all JUT-01 rows.**

## 5. Architecture — module decomposition

```
            ┌──────────── AGENTIC AI WORKFLOW (bonus) ────────────┐
            │   orchestrates stages, makes + narrates decisions,   │
            │   deterministic fallback so judges can always run it │
            └──────────────────────────────────────────────────────┘
 raw data                                                        deliverables
   │                                                                  ▲
   ▼                                                                  │
 ① Data foundation → ② Resource assessment → ③ System design → ④ Techno-economics
   petrophysics        (Ch.1, 60%)             heat+cool          LCoE optimization
   TVD + ML impute      P10/50/90 + map        HP/ATES/chiller     (Ch.2, 40%)
   │                                                                  │
   └───────────────────────► ⑤ FastAPI + React app ◄─────────────────┘
```

### Module 1 — Data foundation (petrophysics)  *[biggest differentiator]*
- Parse LAS + surveys; **build per-well MD→TVD function from deviation surveys (minimum-curvature consistent)**; re-depth all log samples and formation tops. Assume vertical above first survey station.
- Fix JUT-01 feet/metre LAS artifact; general QC (nulls, outliers, units).
- **ML imputation of missing porosity** from logs (GR, RHOB, NPHI, sonic), trained on log-rich wells with held-out validation; **porosity→permeability transform** (learned regression and/or Kozeny-Carman) for permeability.
- Output: one clean, TVD-correct, gap-filled reservoir dataset + QC report.

### Module 2 — Resource assessment (Challenge 1, 60%)
- Geothermal power per well: `P_th = Q·ρ·cp·ΔT` (ρ≈1078 kg/m³, cp≈4250 J/kg·K per LCOE sheet), with `Q` from transmissivity (k·h) / ThermoGIS flow. Propagate **P10/P50/P90** → power distribution per well.
- **Spatial resource map** across the 20×20 km box: interpolate/krige transmissivity & temperature from the 4 wells + ThermoGIS regional grid → continuous resource surface; **propose optimal new well locations** (the 4 wells alone can't meet load; EVD/PKP are duds).
- Decide well program: number of doublets, locations, depth. Likely ~2 doublets in the BLT/JUT-favorable NE trend.

### Module 3 — Integrated system design (Challenge 2A) *[signature creative bet]*
- **Geothermal doublet(s) in Rotliegend** → base-load heat via heat exchanger.
- **Central heat pump** lifts to district supply temp and deepens ΔT (colder injection ⇒ more MW); COP-based.
- **Seasonal HT-ATES** (high-temperature aquifer thermal energy storage) banks summer heat surplus for winter — executes the organizer's explicit hint; cites NL HEATSTORE practice.
- **Cooling (≥5 MW):** summer idle geothermal capacity drives **absorption chillers** and/or **free cooling from cold ATES well**.
- **Peak/backup** (gas or electric) for coldest days — included for honest LCoE.
- Monthly demand profiles + capacity factors (assessment level). **Headline narrative: heating+cooling is one system that is cheaper *because* it does both** (raises utilization).

### Module 4 — Techno-economics (Challenge 2B) *[deciding metric]*
- **Port `LCOE.xlsx` into Python**; extend for hybrid (HP capex/opex + electricity at COP, chiller, ATES capex + round-trip losses, backup). Full drilling cost for every well.
- **Optimize** over {well count, flow rate, injection temp, HP & storage sizing} to **minimize LCoE s.t. ≥10 MW heat & ≥5 MW cool**.
- **Monte Carlo** over resource uncertainty → LCoE **P10/P50/P90** bands.

### Module 5 — Agentic workflow + app (bonus)
- Agent orchestrates ingest→QC→TVD→impute→assess→site→design→optimize→report, **making + narrating decisions**; **deterministic fallback runs with no API key** (reproducibility for judges).
- **FastAPI + React/Vite** demo: upload data → watch pipeline → explore resource map, design, LCoE. No auth/DB/accounts.

### Module 6 — Deliverables
- **D1** repo (README: title/team/problem/methodology/repro; runnable notebooks; uv lock/requirements).
- **D2** deck (10–15 slides): problem framing, EDA incl. the TVD trap, methodology, resource map, design, LCoE result, limitations, recommendations; title slide = names + SPE numbers.
- **D3** video (3–5 min): I write script + storyboard; **user records** narration (720p+, public link).

## 6. Build order (each phase independently demoable)

| Phase | Module | Rationale |
|---|---|---|
| 0 | Repo scaffold (uv/ruff/pyright), structure, data loaders | reproducible foundation for D1 |
| 1 | Data foundation: TVD, QC, ML imputation | everything depends on correct depths/properties |
| 2 | Resource assessment + spatial map (Ch.1) | the 60%; needs clean data |
| 3 | System design: geothermal + HP + ATES + cooling (Ch.2A) | needs resource numbers |
| 4 | Techno-economics: LCoE port + optimization + Monte Carlo (Ch.2B) | deciding metric; needs the design |
| 5 | Agentic workflow + deterministic fallback | bonus; orchestrates 1–4 |
| 6 | FastAPI + React app | demo layer |
| 7 | Deliverables: report, deck, video script | what's actually graded |

## 7. Key risks & open questions

- **TVD reconciliation:** provided depths are AH; must verify our MD→TVD against survey TVD stations and against ThermoGIS top depths (which appear to be TVD). Resolve any residual mismatch and document.
- **ThermoGIS scraping** for new-location siting: must document method + how it influenced design (per rules). Decide how much regional grid to pull.
- **Absorption vs compression chiller** for cooling: pick based on LCoE; both are COP-level assumptions.
- **Agentic LLM dependency:** keep core deterministic; LLM layer is orchestration/narration only, never a hidden requirement to reproduce numbers.
- **Repo / git:** not yet a git repo; init in Phase 0 (with user confirmation before any commit, per user's global rules).

## 8. Human-only tasks (user)

Record the 3–5 min narrated video; provide team name + member SPE numbers for the title slide; final review of technical claims before submission.

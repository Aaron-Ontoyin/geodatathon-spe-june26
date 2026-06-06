# D2 — Slide Deck Outline (10–15 slides)

Build target: PDF, 13 slides. Each slide below has **on-slide content** (concise, what the
audience reads) and **notes** (what the presenter says — these also seed the D3 video script).
Numbers are the current corrected model outputs; regenerate `outputs/technical_report.md`
(`uv run geo-datathon report --out outputs/technical_report.md`) before final export to confirm.

Maps to the four judging criteria: technical rigor (4–9), innovation/creativity (6, 10),
clarity (whole deck), Africa applicability (11).

---

## Slide 1 — Title
- **Geothermal District Heating & Cooling for Utrecht — the lowest-cost path to ≥10 MWth heat + ≥5 MWth cooling**
- Team **<NAME>** · members + **SPE membership numbers** <fill in>
- SPE Africa Geothermal Datathon 2026
- One line: *"Not the most megawatts — the lowest, most credible LCoE."*

Notes: introduce the team and the one-sentence thesis. The deciding metric is LCoE at
adequate capacity, and everything in the deck builds to that number.

## Slide 2 — Problem framing
- District in Utrecht (NL): mixed residential/office/public load.
- Must deliver **≥10 MWth heating AND ≥5 MWth cooling** from the **Rotliegend (Slochteren)** reservoir.
- Winner = **lowest LCoE at adequate capacity** (going big is penalised).
- Drilling cost counts for every well, existing or new.

Notes: state the constraints and, crucially, that the score is cost-driven. This reframes the
whole problem from "maximise resource" to "minimise cost of meeting the demand."

## Slide 3 — Our approach (the pipeline)
- A reproducible, **agent-driven pipeline**: data → resource → design → techno-economics.
- Balanced flagship: rigorous geoscience + techno-economics **and** an AI workflow + interactive app.
- One typed config drives everything; every number is reproducible offline.
- [diagram: 5 boxes — Data foundation → Resource (Ch1) → System design (Ch2A) → LCoE (Ch2B) → Agentic workflow/app]

Notes: we built it as a tool, not a one-off notebook. The same code reruns end to end and the
organisers can audit every step.

## Slide 4 — Data foundation / EDA
- Four wells, deliberately messy: **along-hole depths mislabelled as TVD**, empty TVD column,
  missing porosity (2 wells), a sheet with a mislabelled well name, feet/metre channel mix.
- Fixes: **minimum-curvature TVD reconstruction** (reproduces the survey TVD to **~0.01 m**),
  density-log porosity imputation **validated against ThermoGIS** (agree to within ~2.7 porosity points).
- [figure: AH vs TVD correction; porosity-imputed vs ThermoGIS table]

Notes: most teams will trip on the depth and unit traps. We caught them and validated against an
independent regional model, so the foundation is clean and defensible.

## Slide 5 — Resource assessment (Challenge 1)
- P10/P50/P90 doublet power per well; only **2 of 4 wells are viable** (BLT, JUT).
- **ThermoGIS** regional grid (1 km, public TNO data) is the resource truth; our 4 wells validate it.
- Sited a new doublet in the proven trend, near demand: ~6 MW P50 class.
- [figure: spatial power map + sited location]

Notes: the resource map is a public ThermoGIS product, so we use it and verify it, rather than
pretend to out-compute it. The value is the decision: where and how many wells.

## Slide 6 — Integrated system design (Challenge 2A) — the key idea
- Geothermal doublet → **heat pump** (low 30 °C reinjection) → seasonal **HT-ATES** storage → **heat-driven cooling**.
- **Cooling monetises otherwise-idle summer capacity**: geothermal utilisation rises from **59% → 99%**.
- Firm heating capacity **7.9 MWth**; HT-ATES covers the winter peak with near-zero backup.
- [figure: monthly dispatch — heating winter, cooling summer, storage charge/discharge]

Notes: this is the creative core and the reason the cost is low. Running the wells hard all year,
heating in winter, cooling in summer, storing the surplus, is what drives the LCoE down.

## Slide 7 — Techno-economics (Challenge 2B)
- LCoE model is a **port of the provided LCOE.xlsx** (validated: reproduces its 5.77 €/GJ base case),
  extended for the hybrid; **depth-dependent well cost** from the spreadsheet's own formula.
- Design comparison (lowest wins):
  | Doublets | LCoE €/GJ | CAPEX |
  |---|---|---|
  | **1** | **20.8** | **19 M€** |
  | 2 | 30.8 | 33 M€ |
  | 3 | 41.2 | 49 M€ |
- **One doublet wins** — fewer wells + storage beats more wells.

Notes: our economics are consistent with the organisers' own spreadsheet, then extended for
cooling and storage. One doublet is decisively cheapest.

## Slide 8 — Risk (Monte-Carlo)
- Transmissivity uncertainty → LCoE band **P10 16.7 / P50 21.1 / P90 36.8 €/GJ** (right-skewed).
- A second nearby well **does not de-risk** it (same, correlated geology).
- Recommendation: **drill one doublet, well-test it, expand only if data justify it.**
- [figure: LCoE histogram with P10/50/90]

Notes: the band is wide and skewed because the resource is uncertain. The honest move is a staged
drill-and-test, not committing to multiple wells up front.

## Slide 9 — What actually moves the cost (sensitivity)
- Tornado: **injection temperature is the #1 driver** (~7.7 €/GJ swing), then electricity price, discount rate, well cost.
- Honest headline: the one-doublet result **depends on heat-pump-enabled 30 °C reinjection**; at a
  conservative ~39 °C a second doublet is needed (flips near ~37 °C).
- [figure: tornado chart]

Notes: we surface the assumption the result is most sensitive to, rather than hide it. This is the
number a reviewer should probe, and we show it ourselves.

## Slide 10 — Agentic workflow + interactive app (bonus)
- An agent runs the whole pipeline and records a **decision log** (what it chose and why); no API key needed.
- Interactive app: change any assumption, re-run, see LCoE/band/dispatch live; import/export the same config the CLI uses.
- [screenshots: decision log + app dashboard]

Notes: the organisers said they will run the code and reward automation. The agent makes the whole
analysis reproducible and explorable, and the app lets a non-coder test scenarios.

## Slide 11 — Practical applicability to Africa
- **Method transfers** to East African Rift appraisal (KenGen/GDC): messy-data petrophysics,
  probabilistic resource, LCoE optimisation, agentic automation, all reservoir-agnostic.
- **Cooling + cascaded direct-use** matter more in Africa (cold-chain, agriculture; already practised at Olkaria).
- **Lowest-LCoE, staged development** fits a capital-constrained setting.
- Honest: the Rift volcanic *resource* and heating-led demand don't transfer; the *workflow and framing* do.

Notes: the case is Dutch because the data is public, but it's a template. A local team reruns the
same pipeline on Rift data; the cooling and cost discipline are if anything more relevant in Africa.

## Slide 12 — Limitations (we state them)
- Monthly energy balance, not a transient reservoir/thermodynamic sim.
- Resource map from sparse wells; P50-grid uncertainty modelled.
- 1-doublet result depends on 30 °C injection and on HT-ATES covering the winter peak.
- Absorption cooling at ~77 °C is thermodynamically marginal; demand profile is an assumption.

Notes: we are explicit about what the model does and does not do, and which assumptions carry the
result. Transparency is part of the rigor.

## Slide 13 — Recommendation & conclusion
- **Stage a single geothermal doublet + heat pump + HT-ATES + heat-driven cooling.**
- Meets ≥10 MWth heat and ≥5 MWth cooling at **~21 €/GJ P50** (P10 17 / P90 37).
- Cheapest credible option; de-risks before scaling; reproducible and transferable.
- Repo + app + report: <github link>.

Notes: close on the headline number and the staged, low-risk, lowest-cost recommendation, and point
to the working code, app and report.

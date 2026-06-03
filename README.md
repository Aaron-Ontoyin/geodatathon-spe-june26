# Geothermal Datathon 2026 — Utrecht Heating & Cooling

Solution for the **SPE Africa Geothermal Datathon 2026**: assess the Rotliegend
(Slochteren) geothermal resource near Utrecht (NL) and design a **least-cost
integrated district heating + cooling system** delivering **≥10 MWth heating** and
**≥5 MWth cooling**.

> Winning thesis: not maximum megawatts, but the **lowest, most credible LCoE** at
> adequate capacity — with a correct data foundation, a sited well program, a
> heating+cooling design where cooling monetises otherwise-idle summer capacity,
> and a reproducible, agent-driven workflow.

## Pipeline

| Stage | Module | What it produces |
|------|--------|------------------|
| ① Data foundation | `geothermal.petrophysics` | TVD-correct, gap-filled reservoir dataset |
| ② Resource (Ch.1) | `geothermal.resource` | P10/50/90 power per well + spatial map + well siting |
| ③ System design (Ch.2A) | `geothermal.design` | geothermal + heat pump + HT-ATES + cooling |
| ④ Techno-economics (Ch.2B) | `geothermal.economics` | LCoE optimisation + Monte-Carlo bands |
| ⑤ Agentic workflow (bonus) | `geothermal.agent` | orchestrates ①–④, narrates decisions |
| ⑥ Demo app | `app/` (FastAPI + React) | interactive walkthrough |

## Data quirks handled (see `tests/test_loaders.py`)

- `target_lithologies.csv` depths are **along-hole** despite `_tvd` names; `depth_tvd_m`
  is empty → reconciled via the directional surveys (minimum curvature).
- **JUT-01 LAS** carries feet *and* metre depth channels → normalised to metres.
- **ThermoGIS** `BLT-01` sheet mislabels its inner *Well Name* cell as `PKP-01`
  → keyed by sheet name + coordinates instead.

## Setup

```bash
uv sync --all-extras        # create .venv and install deps (incl. notebooks)
uv run pytest               # run tests
uv run ruff check .         # lint
uv run ruff format .        # format
uv run pyright              # type-check
```

## Layout

```
src/geothermal/      # library code (io, petrophysics, resource, design, economics, agent)
tests/               # pytest
notebooks/           # runnable analysis notebooks (D1 deliverable)
data/                # provided datasets (+ data/raw/*.las)
docs/                # challenge brief, FAQ, submission guidelines, design spec
outputs/             # generated figures/tables (gitignored)
```

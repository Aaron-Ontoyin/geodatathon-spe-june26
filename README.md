# Geothermal Datathon 2026: Utrecht Heating and Cooling

**Project:** A least-cost geothermal district heating and cooling system for Utrecht.
**Event:** SPE Africa Geothermal Datathon 2026.

**Team QUANTIVE:**

| Member | SPE member number |
|--------|-------------------|
| Aaron Ontoyin Yin | 5585251 |
| Kojo Ohene Obeng | 5899103 |
| Ebenezer Tutu Ainoo | 5901046 |
| Shahima Mubarik | 5677072 |
| Joel Mensah | 5001276 |

## Problem statement

Assess the Rotliegend (Slochteren) geothermal resource near Utrecht in the Netherlands
and design a district energy system that delivers at least 10 MWth of heating and at
least 5 MWth of cooling. The judging metric is the levelized cost of energy (LCoE) at
adequate capacity, not raw capacity, and drilling cost is counted for every well.

## Solution summary

The whole solution is built to find the lowest credible cost at adequate capacity
rather than the largest system. The recommended design is a staged single-doublet
scheme (one geothermal doublet, a central heat pump, seasonal HT-ATES storage, and
heat-driven cooling) that meets the demand at an all-in **21.1 EUR/GJ** (P10 16.7,
P50 21.1, P90 36.8). Doing cooling as well as heating pushes geothermal utilisation
from 59% to 99%, which is the main reason the cost comes out low.

The codebase does three things:

1. Runs the full analysis pipeline (data cleaning, resource assessment, system design,
   techno-economics) from one typed configuration.
2. Exposes that pipeline as a command-line tool and as a FastAPI backend.
3. Ships a React demo app that drives the backend so you can evaluate a design or
   search for the least-cost one interactively.

A full write-up is in `docs/TECHNICAL_REPORT.md`; the methodology at a glance is below.

The codebase does three things:

1. Runs the full analysis pipeline (data cleaning, resource assessment, system design,
   techno-economics) from one typed configuration.
2. Exposes that pipeline as a command-line tool and as a FastAPI backend.
3. Ships a React demo app that drives the backend so you can evaluate a design or
   search for the least-cost one interactively.

## Pipeline

| Stage | Module | What it produces |
|-------|--------|------------------|
| 1. Data foundation | `geothermal.petrophysics` | TVD-correct, gap-filled reservoir dataset |
| 2. Resource (Ch.1) | `geothermal.resource` | P10/50/90 power per well, spatial map, well siting |
| 3. System design (Ch.2A) | `geothermal.design` | geothermal + heat pump + HT-ATES + cooling |
| 4. Techno-economics (Ch.2B) | `geothermal.economics` | LCoE optimisation and Monte-Carlo bands |
| 5. Agentic workflow (bonus) | `geothermal.agent` | orchestrates stages 1 to 4 and records its decisions |
| 6. Demo app | `geothermal.api` + `frontend/` | interactive walkthrough (FastAPI + React) |

Everything is driven by one frozen `Assumptions` config (`geothermal.assumptions`), so a
judge can reproduce every number offline with no API key.

## Data quirks handled

These are the traps in the provided data that the loaders correct (see
`tests/test_loaders.py`):

- `target_lithologies.csv` stores along-hole depths even though the columns are named
  `_tvd`, and the `depth_tvd_m` column is empty. True vertical depth is reconstructed
  from the directional surveys using minimum curvature.
- The JUT-01 LAS file carries both feet and metre depth channels. These are normalised
  to metres.
- The ThermoGIS `BLT-01` sheet mislabels its inner *Well Name* cell as `PKP-01`, so the
  loader keys wells by sheet name and coordinates instead of that cell.

## Prerequisites

There are two tiers. The analysis (the graded result) needs only Python. The interactive
app is optional and additionally needs Node.

- **Python 3.11 or newer**, with [uv](https://docs.astral.sh/uv/) (the package and
  environment manager). All Python dependencies are pinned in `pyproject.toml` and
  `uv.lock`, with a plain `requirements.txt` provided for pip users.
- **Node 18+ and [pnpm](https://pnpm.io/)** only if you want to run the demo app. They are
  not needed to reproduce any number, figure or report.

Why the main dependencies are here: numpy/pandas/scipy (numerics), scikit-learn (the
porosity imputation), lasio (read the LAS well logs), openpyxl (read the provided Excel
sheets and the LCOE model), pykrige and pyarrow (spatial interpolation and the cached
dataset), pydantic (the typed, self-validating `Assumptions` config), xarray and netCDF4
(read the ThermoGIS regional grid, under the optional `data` extra), and fastapi/uvicorn
plus the React app (the optional `web` extra) for the demo.

## Setup

```bash
uv sync --all-extras        # create .venv and install Python deps (incl. web, data, notebooks)
uv run pytest               # run the test suite
uv run ruff check .         # lint
uv run pyright              # type-check
```

Plain pip alternative (no uv): `pip install -r requirements.txt`.

Everything below this point that starts with `uv run` is the analysis and needs only the
Python setup above. The frontend build is required only for the optional browser app.

## Using it from the command line

The CLI is `geo-datathon`. It runs the whole pipeline from a small TOML file and needs
no API key. Start by writing a template you can edit:

```bash
uv run geo-datathon template --out inputs.toml
```

Then run the analysis. With no `--input`, it uses the documented default assumptions
(the recommended design):

```bash
uv run geo-datathon report                       # print the technical report to stdout
uv run geo-datathon report --out report.md       # or write it to a file
uv run geo-datathon report --input inputs.toml   # use your edited assumptions
```

If your TOML file defines search ranges and constraints, the report command optimises
over them and reports the least-cost design that satisfies the constraints.

To run the agentic workflow instead, which executes the same pipeline while recording a
decision log of what it chose and why:

```bash
uv run geo-datathon workflow
uv run geo-datathon workflow --input inputs.toml
```

`inputs.example.toml` shows the full input format, including the search block.

## Using it from the browser (optional)

The app is a convenience, not needed to reproduce the results. The backend serves the
frontend as static files, but those files must be built first: `pnpm build` compiles the
React app into `frontend/dist`, which is exactly what FastAPI then serves. So the build
step is still required the first time (and after any frontend change). This runs as a
single process, no separate frontend server.

```bash
cd frontend && pnpm install && pnpm build && cd ..
uv run uvicorn geothermal.api:app --port 8000
```

Then open `http://localhost:8000`. The backend serves the built UI from `frontend/dist`
and the API from the same origin. Rebuild (`pnpm build`) whenever the frontend changes.

If you are working on the frontend itself, run the Vite dev server for hot reload
instead. This needs two terminals, one for each process:

```bash
uv run uvicorn geothermal.api:app --reload --port 8000   # terminal 1: API
cd frontend && pnpm dev                                  # terminal 2: UI
```

Open the URL Vite prints (usually `http://localhost:5173`). In dev the UI calls the API
at `http://localhost:8000`; set `VITE_API_BASE` to point elsewhere if needed.

The app has two modes:

- **Evaluate** computes the design and LCoE for the exact inputs you set.
- **Optimise** searches the parameters you mark as ranges and returns the least-cost
  design within your constraints.

You can import or export the same `inputs.toml` the CLI uses, so you can move a
configuration between the two without retyping it.

## Layout

```
src/geothermal/      # library: io, petrophysics, resource, design, economics, agent, api
frontend/            # React + Vite demo app (TypeScript)
tests/               # pytest
notebooks/           # runnable analysis notebooks (D1 deliverable)
data/                # provided datasets (plus data/raw/*.las)
data/thermogis_grid/ # ThermoGIS Rotliegend grids (subset actually used; see below)
docs/                # challenge brief, FAQ, submission guidelines, design spec
outputs/             # generated figures and reports (gitignored, regenerated)
```

### Supplementary data: ThermoGIS grids

`data/thermogis_grid/` holds the public ThermoGIS regional grids (TNO / NLOG) for the
Upper Rotliegend (RO). We include **only the subset actually used**: the BaseCase and
Heat Pump scenarios, six properties each (depth, net-to-gross, permeability P50, power
P50, temperature, thickness P50), about 3 MB. These drive the independent grid-based
siting check; the canonical pipeline runs without them. To use a different location or
the full dataset, point `GEO_THERMOGIS_ROOT` at a ThermoGIS export with the same layout.

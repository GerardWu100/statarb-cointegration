# Project Overview

## File Tree

```text
statarb-cointegration/
├── GUIDE_OVERVIEW.md
├── GUIDE_ROOT.md
├── README.md
├── pyproject.toml
├── scripts/
│   ├── GUIDE_scripts.md
│   └── run_pipeline.py
├── docs/
│   ├── user/
│   │   └── README.md
│   └── reference/
│       ├── GUIDE_reference.md
│       ├── notebook_split.md
│       └── statarb-cointegration.ipynb
├── notebooks/
│   ├── GUIDE_notebooks.md
│   └── demo.ipynb
├── src/
│   ├── GUIDE_src.md
│   └── statarb_cointegration/
│       ├── GUIDE_statarb_cointegration.md
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── pipeline.py
│       └── steps/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── outputs/
│   ├── figures/
│   ├── tables/
│   ├── reports/
│   └── runs/
├── logs/
└── tests/unit/
```

## Purpose

Preserves the notebook workflow as ordered Python step scripts for data download, spread modeling, Monte Carlo simulation, and backtesting.

## Flow

1. `uv run statarb-pipeline`, `scripts/run_pipeline.py`, or `notebooks/demo.ipynb` calls the package pipeline.
2. The pipeline builds a shared execution context with project paths and optional smoke-test overrides.
3. The step scripts in `src/statarb_cointegration/steps/` execute in notebook order.
4. Outputs are written under `outputs/`, while `docs/reference/` holds the original notebook and the split map.

## Main Assumptions

- The generated step scripts should stay close to the notebook code instead of being deeply refactored.
- Notebook state is preserved through one shared execution context.
- Any data bundled in `data/processed/` is local to this project copy and does not mutate the original `one-time-projects` files.

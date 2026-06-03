# GUIDE_ROOT.md

## Part 1: Conceptual Explanation

This repository is a notebook-to-project conversion. The notebook reference materials live under `docs/reference/`, and the executable workflow is split into ordered Python step scripts under `src/statarb_cointegration/steps/`. The root folder stays thin: `scripts/` and the `statarb-pipeline` console entry run the pipeline, `pyproject.toml` defines the Python 3.13 environment, `notebooks/` holds the thin execution notebook, `docs/` records the section split and the original notebook, and `data/` plus `outputs/` hold local inputs and generated artifacts.

The execution model intentionally mirrors notebook semantics. Each step script is executed in order inside one shared namespace, so variables, functions, and imported modules persist across sections just as they did in the original notebook. This keeps the code close to the source notebook while moving the reusable logic out of the new notebook wrapper.

## Part 2: Code Reference

- `scripts/run_pipeline.py`: Thin wrapper around `statarb_cointegration.cli.main`.
- `statarb-pipeline` (console script): Same CLI via `pyproject.toml` entry point.
- `pyproject.toml`: Python 3.13 package metadata and dependencies for `uv`.
- `src/statarb_cointegration/config.py`: Defines project paths and builds the shared execution context.
- `src/statarb_cointegration/pipeline.py`: Runs each generated step script in notebook order.
- `src/statarb_cointegration/steps/`: Notebook-derived Python scripts, one file per major notebook section.
- `notebooks/demo.ipynb`: Thin notebook that only calls the backend pipeline.
- `docs/reference/statarb-cointegration.ipynb`: Unchanged copy of the original source notebook.
- `docs/reference/notebook_split.md`: Maps notebook sections to generated script files.

## Part 3: Short Journal

- 2026-04-16: Split the original notebook into ordered step scripts while preserving the raw notebook under `docs/reference/`.
- 2026-05-20: Moved CLI into `src/statarb_cointegration/cli.py` and `scripts/`; removed duplicate `notebook_reference.md`.

# GUIDE_scripts.md

## Part 1: Conceptual Explanation

The `scripts/` folder holds thin entrypoints that parse arguments (when needed) and delegate to the installable package under `src/statarb_cointegration/`. Reusable logic stays in the package; scripts exist so you can run workflows with `uv run python scripts/...` without installing a console script.

## Part 2: Code Reference

- `run_pipeline.py`: Calls `statarb_cointegration.cli.main()` to run the full notebook-derived pipeline.
- Console alternative: `uv run statarb-pipeline` (defined in `pyproject.toml`).

## Part 3: Short Journal

- 2026-05-20: Moved root `run_pipeline.py` here during project-structure refactor.

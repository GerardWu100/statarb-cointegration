# GUIDE_notebooks.md

## Part 1: Conceptual Explanation

This folder holds the new thin notebook wrapper for the project. The notebook is intentionally minimal: it imports the backend pipeline and runs it. All substantive logic lives in `src/`, while the untouched source notebook is preserved in `docs/reference/`.

## Part 2: Code Reference

- `demo.ipynb`: Thin execution notebook that calls `statarb_cointegration.pipeline.run_pipeline()` and displays the returned metrics.

## Part 3: Short Journal

- 2026-04-16: Replaced backend notebook logic with a single pipeline call so the notebook stays a front-end wrapper.
- 2026-07-13: Kept the notebook thin while switching its result from a shared execution context to a typed backtest result.

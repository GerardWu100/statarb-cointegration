# GUIDE_ROOT.md

## Part 1: Conceptual Explanation

This repository is a reproducible, frozen-data study of a KO-PEP cointegration hypothesis. The live path estimates one fixed pre-period price relation, tests its residual for stationarity, computes rolling signals from information available at each close, and backtests holdings that match the same regression hedge.

The timing convention is causal. A signal at close $t$ sets holdings for the price move from $t$ to $t+1$. Rolling mean and standard deviation use residuals through $t-1$. Daily equity includes open-position profit and loss, one-way turnover cost, short borrow, and long financing.

`config.toml` is the single place for research parameters. The package reads the frozen processed parquet and writes generated tables under `outputs/`. The bilingual article has its own frozen input and chart workflow under `blog/`. The original notebook under `docs/reference/` is historical evidence, not executable ground truth.

## Part 2: Code Reference

- `config.toml`: Training, dates, z-score thresholds, exposure, cost rates, annualization, and significance level.
- `pyproject.toml`: Python 3.13 package metadata, runtime libraries, test tools, and console entry point.
- `src/statarb_cointegration/`: Estimation, signal construction, backtest state, and orchestration.
- `scripts/run_pipeline.py`: Thin wrapper for the package command line.
- `tests/unit/test_research.py`: Causal-timing, hedge-sign, cost, marking, and failed-test reporting checks.
- `data/processed/`: Frozen adjusted closes used by the package pipeline.
- `outputs/tables/`: Generated daily account history, completed trades, and summary.
- `blog/`: Canonical English and French posts, frozen post data, chart code, and images.
- `docs/reference/statarb-cointegration.ipynb`: Unchanged original notebook retained for comparison.

## Part 3: Short Journal

- 2026-04-16: Split the original notebook into ordered scripts while retaining the source notebook.
- 2026-07-13: Replaced shared `exec` state with typed functions because the strategy required auditable timing, matched holdings, costs, daily marking, and formal residual tests.
- 2026-07-13: Kept the failed-cointegration backtest as a labelled diagnostic counterfactual rather than treating it as a deployable strategy.

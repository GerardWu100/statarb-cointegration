# GUIDE_statarb_cointegration.md

## Part 1: Conceptual Explanation

The package estimates a fixed pre-period relation

$$
P^{KO}_t=\alpha+\beta P^{PEP}_t+\varepsilon_t
$$

and tests whether the fitted residual $\varepsilon_t$ is stationary. It reports both the ordinary Augmented Dickey-Fuller diagnostic and the Engle-Granger test, whose critical-value distribution accounts for estimating the residual.

The rolling z-score uses a mean and sample standard deviation built from the prior $L$ residuals. A signal at close $t$ selects holdings for the move from $t$ to $t+1$. For direction $s_t$ and scale $q_t$, KO shares equal $s_tq_t$ and PEP shares equal $-s_t\beta q_t$. Gross profit and loss is therefore $s_tq_t\Delta\varepsilon_{t+1}$.

Daily account value subtracts one-way turnover cost plus annualized short-borrow and long-financing charges. Open positions are marked every day. A completed-trade ledger is derived from the same daily state rather than maintained as a separate accounting system.

## Part 2: Code Reference

- `config.py`: `ResearchConfig` validates thresholds and resolves project paths; `load_config` reads `config.toml`.
- `research.py`: `fit_cointegration` estimates the relation and tests its residual; `compute_causal_signal` builds lagged z-scores; `_target_holdings` replicates the hedge; `run_backtest` owns the state machine, costs, daily marking, trades, and metrics.
- `pipeline.py`: `run_pipeline` loads frozen prices, selects the pre-period sample, calls the research functions, and writes the three CSV outputs.
- `cli.py`: `main` accepts an optional configuration path and prints summary metrics.
- `__init__.py`: Package marker.

Start with `research.py` for the financial logic and `pipeline.py` for the executable flow.

## Part 3: Short Journal

- 2026-07-13: The Engle-Granger p-value of 0.225 failed the 5% research prerequisite; the package reports that failure while retaining the backtest as a diagnostic counterfactual.
- 2026-07-13: Position sizing now uses the regression hedge exactly, and daily equity includes transaction, borrow, and financing costs.

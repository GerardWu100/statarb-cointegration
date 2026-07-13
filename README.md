# Statistical Arbitrage Cointegration Study: Coca-Cola vs Pepsi

This project tests whether Coca-Cola (KO) and Pepsi (PEP) adjusted prices support a fixed residual mean-reversion trade. The current research version replaces the original notebook execution model with typed, directly tested Python code.

The result is negative. A regression can fit price levels well while its residual remains non-stationary. On the 5,000-day training sample, the price regression has $R^2=0.960$, but the Engle-Granger p-value is 0.225. At a 5% significance level, the study does not find cointegration.

The historical strategy is retained as a diagnostic counterfactual. It uses coefficients frozen before the test period, lagged rolling statistics, holdings that replicate the fitted residual, explicit trading and carrying costs, and daily mark-to-market profit and loss.

## Model

For KO adjusted price $P^{KO}_t$ and PEP adjusted price $P^{PEP}_t$, the training regression is

$$
P^{KO}_t=\alpha+\beta P^{PEP}_t+\varepsilon_t.
$$

The residual $\varepsilon_t$ is tested with an Augmented Dickey-Fuller diagnostic and the formal Engle-Granger cointegration test. A long-residual position holds $q$ KO shares and $-\beta q$ PEP shares, so gross profit and loss is proportional to $\Delta\varepsilon_t$.

## Run

```bash
uv sync
uv run statarb-pipeline
uv run python scripts/run_pipeline.py
uv run pytest -q
uv run ruff check src tests scripts blog/generate_charts.py
uv run python blog/generate_charts.py
```

All research settings live in `config.toml`. Each option is documented there.

## Layout

```text
statarb-cointegration/
├── config.toml                  # research, signal, exposure, and cost settings
├── src/statarb_cointegration/   # typed estimation and backtest code
├── scripts/                     # thin command-line wrapper
├── tests/unit/                  # timing, hedge-sign, cost, and marking tests
├── data/processed/              # frozen adjusted closes
├── outputs/tables/              # generated daily history, trades, and summary
├── blog/                        # bilingual post, frozen evidence, and charts
├── notebooks/                   # thin package demonstration
└── docs/reference/              # unchanged historical notebook
```

## Main limitations

- Adjusted closes are research inputs, not executable bid and ask prices.
- Borrow availability, dividends on short stock, market impact, and broker-specific collateral terms are absent.
- The diagnostic backtest proceeds despite the failed cointegration test to measure the consequence of ignoring that prerequisite. It is not a trading recommendation.
- Parameter-stability estimates that use the test period are post-mortem diagnostics and never enter prior signals.

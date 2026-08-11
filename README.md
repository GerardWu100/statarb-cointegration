# Statistical Arbitrage Cointegration Study: Coca-Cola vs Pepsi

This project tests whether Coca-Cola (KO) and Pepsi (PEP) adjusted prices support a fixed residual mean-reversion trade. The research version replaces the original notebook execution model with typed, directly tested Python code.

## What it does

The pipeline fits a fixed price relation between KO and PEP on a training sample, tests the residual for stationarity, and backtests a pairs trade built from that residual.

The result is negative. A regression can fit price levels well while its residual remains non-stationary. On the 5,000-day training sample, the price regression has $R^2=0.960$, but the Engle-Granger p-value is 0.225. At a 5% significance level, the study does not find cointegration.

The historical strategy is retained as a diagnostic counterfactual. It uses coefficients frozen before the test period, lagged rolling statistics, holdings that replicate the fitted residual, explicit trading and carrying costs, and daily mark-to-market profit and loss.

## Model

For KO adjusted price $P^{KO}_t$ and PEP adjusted price $P^{PEP}_t$, the training regression is

$$
P^{KO}_t=\alpha+\beta P^{PEP}_t+\varepsilon_t.
$$

The residual $\varepsilon_t$ is tested with an Augmented Dickey-Fuller diagnostic and the formal Engle-Granger cointegration test (`statsmodels.tsa.stattools.adfuller` and `coint`). A long-residual position holds $q$ KO shares and $-\beta q$ PEP shares, so gross profit and loss is proportional to $\Delta\varepsilon_t$.

## Requirements

- Python 3.13.
- No external service or API key. The pipeline reads a frozen parquet file already checked into `data/processed/`.

## Setup

```bash
uv sync
```

## Usage

```bash
uv run statarb-pipeline                                    # run the study via the console entry point
uv run python scripts/run_pipeline.py                      # equivalent thin script wrapper
uv run python scripts/run_pipeline.py --config other.toml  # use an alternate configuration file
uv run pytest -q                                            # timing, hedge-sign, cost, and marking tests
uv run python blog/generate_charts.py                       # reproduce the blog post's figures and tables
```

## Configuration

All research settings live in `config.toml`, and each option is documented there. The main knobs are the training window size, the out-of-sample date range, the entry/exit/stop z-score thresholds, gross exposure, transaction cost in basis points, short-borrow and financing rates, and the Engle-Granger significance level that gates whether the strategy is allowed to trade.

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

## Output

`uv run statarb-pipeline` writes to `outputs/tables/`:

- `summary.csv`: fitted relation, stationarity tests, and performance metrics;
- `daily_backtest.csv`: daily prices, signals, holdings, costs, profit and loss, and marked equity;
- `trades.csv`: completed-trade ledger with gross profit and loss, costs, and net profit and loss.

`cointegration_passed=0` in the summary means the Engle-Granger p-value exceeded the configured significance level; the diagnostic backtest still runs so the consequence of ignoring that failed prerequisite is measurable. See `docs/user/README.md` for more on interpreting the output.

## Main limitations

- Adjusted closes are research inputs, not executable bid and ask prices.
- Borrow availability, dividends on short stock, market impact, and broker-specific collateral terms are absent.
- The diagnostic backtest proceeds despite the failed cointegration test to measure the consequence of ignoring that prerequisite. It is not a trading recommendation.
- Parameter-stability estimates that use the test period are post-mortem diagnostics and never enter prior signals.

## License

All rights reserved. See [LICENSE](LICENSE).

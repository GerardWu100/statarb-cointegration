# User guide

## Run the research pipeline

From the project root:

```bash
uv sync
uv run statarb-pipeline
```

The equivalent thin script is `uv run python scripts/run_pipeline.py`. Use `--config path/to/config.toml` with either command to supply another configuration.

## Inputs and outputs

The pipeline reads `data/processed/ko_pep_combined_adj_close_price.parquet`. It writes:

- `outputs/tables/summary.csv`: fitted relation, stationarity tests, and performance metrics;
- `outputs/tables/daily_backtest.csv`: daily prices, signals, holdings, costs, profit and loss, and marked equity;
- `outputs/tables/trades.csv`: completed-trade ledger with gross profit and loss, costs, and net profit and loss.

Run `uv run python blog/generate_charts.py` to reproduce the post's figures and frozen derived tables.

## Interpretation

`cointegration_passed=0` means the Engle-Granger p-value exceeded the configured significance level. The pipeline still reports a diagnostic strategy history so the consequence of ignoring that failed prerequisite remains measurable. Do not interpret the diagnostic backtest as approval to trade.

"""Orchestrate the frozen-data cointegration research pipeline."""

from __future__ import annotations

from pathlib import Path

from .config import ResearchConfig, load_config
from .research import BacktestResult, fit_cointegration, load_prices, run_backtest


def run_pipeline(config_path: Path | None = None) -> BacktestResult:
    """Estimate the pre-period relation and run the cost-aware backtest.

    Parameters
    ----------
    config_path
        Optional path to a TOML configuration file.

    Returns
    -------
    BacktestResult
        Daily account history, trade ledger, and summary metrics. The same
        artifacts are written under ``outputs/tables``.
    """

    config: ResearchConfig = load_config(config_path)
    prices = load_prices(config)
    training = prices.loc[prices.index < config.backtest_start].tail(config.training_observations)
    if len(training) != config.training_observations:
        raise ValueError("The price file does not contain the configured training history.")
    fit = fit_cointegration(training)
    result = run_backtest(prices, fit, config)

    tables_dir = config.outputs_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    result.daily.to_csv(tables_dir / "daily_backtest.csv")
    result.trades.to_csv(tables_dir / "trades.csv", index=False)
    Path(tables_dir / "summary.csv").write_text(
        "metric,value\n" + "".join(f"{key},{value}\n" for key, value in result.metrics.items()),
        encoding="utf-8",
    )
    return result

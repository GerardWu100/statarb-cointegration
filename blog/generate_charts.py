"""Regenerate the cointegration post's frozen evidence and technical charts.

Inputs
------
data/ko_pep_adjusted_close.parquet
    Frozen KO and PEP adjusted closes in US dollars.
../config.toml
    Signal, exposure, and cost assumptions shared with the research package.

Outputs
-------
data/analysis_summary.csv
    Model tests and cost-aware backtest statistics cited by both posts.
data/daily_backtest.csv
    Daily marked account history used by the performance chart.
images/01_spread_regime_shift.png
    Fixed training residual and causal rolling bands.
images/02_parameter_drift.png
    Hedge-ratio, fit, and residual-volatility estimates by period.
images/03_backtest_equity.png
    Daily net equity, gross counterfactual equity, and drawdown.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statarb_cointegration.config import load_config
from statarb_cointegration.research import (
    compute_causal_signal,
    fit_cointegration,
    run_backtest,
)

BLOG_ROOT = Path(__file__).resolve().parent
DATA_PATH = BLOG_ROOT / "data" / "ko_pep_adjusted_close.parquet"
SUMMARY_PATH = BLOG_ROOT / "data" / "analysis_summary.csv"
DAILY_PATH = BLOG_ROOT / "data" / "daily_backtest.csv"
IMAGES_DIR = BLOG_ROOT / "images"
FIGURE_DPI = 180
COLORS = {
    "navy": "#14213D",
    "blue": "#277DA1",
    "red": "#C44536",
    "gold": "#E9C46A",
    "green": "#2A9D8F",
    "gray": "#6C757D",
}


@dataclass(frozen=True, slots=True)
class PeriodEstimate:
    """Price-regression diagnostics for one sample.

    Parameters
    ----------
    name
        Chart label.
    beta
        PEP shares per KO share in the fitted residual.
    r_squared
        Coefficient of determination of the price regression.
    residual_std_usd
        Sample residual standard deviation in US dollars.
    """

    name: str
    beta: float
    r_squared: float
    residual_std_usd: float


def load_frozen_prices() -> pd.DataFrame:
    """Load the post's immutable adjusted-close sample.

    Returns
    -------
    pandas.DataFrame
        Sorted KO and PEP prices with a daily timestamp index.
    """

    prices = pd.read_parquet(DATA_PATH).loc[:, ["KO", "PEP"]].astype(float).sort_index()
    prices.index = pd.DatetimeIndex(pd.to_datetime(prices.index), name="date")
    return prices


def estimate_period(name: str, prices: pd.DataFrame) -> PeriodEstimate:
    """Estimate a price relation for a visual parameter-stability check.

    Parameters
    ----------
    name
        Human-readable sample label.
    prices
        Adjusted closes in US dollars.

    Returns
    -------
    PeriodEstimate
        Slope, fit, and fitted-residual volatility.
    """

    fit = fit_cointegration(prices)
    residual = prices["KO"] - fit.alpha_usd - fit.beta * prices["PEP"]
    return PeriodEstimate(name, fit.beta, fit.r_squared, float(residual.std(ddof=1)))


def plot_residual(prices: pd.DataFrame, training: pd.DataFrame) -> None:
    """Plot the frozen residual and causal 60-day normalization band.

    Parameters
    ----------
    prices
        Complete frozen price history.
    training
        Pre-backtest observations used in the fixed regression.
    """

    config = load_config()
    fit = fit_cointegration(training)
    signal = compute_causal_signal(prices, fit, config.rolling_window).loc[
        "2021-01-01" : config.backtest_end
    ]
    upper = signal["rolling_mean_usd"] + config.entry_z * signal["rolling_std_usd"]
    lower = signal["rolling_mean_usd"] - config.entry_z * signal["rolling_std_usd"]
    fig, ax = plt.subplots(figsize=(13, 6.5), constrained_layout=True)
    ax.plot(
        signal.index,
        signal["residual_usd"],
        color=COLORS["navy"],
        linewidth=1.5,
        label="Fixed residual",
    )
    ax.plot(
        signal.index,
        signal["rolling_mean_usd"],
        color=COLORS["green"],
        linewidth=1.4,
        label="Lagged 60-day mean",
    )
    ax.fill_between(
        signal.index,
        lower,
        upper,
        color=COLORS["gold"],
        alpha=0.25,
        label="Entry band (+/- 1.5 z)",
    )
    ax.axvline(
        pd.Timestamp(config.backtest_start),
        color=COLORS["red"],
        linestyle="--",
        label="Backtest starts",
    )
    ax.set_title("The fitted KO-PEP residual left its training regime")
    ax.set_xlabel("Date")
    ax.set_ylabel("Residual (USD per KO share)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, ncols=2)
    fig.savefig(IMAGES_DIR / "01_spread_regime_shift.png", dpi=FIGURE_DPI)
    plt.close(fig)


def plot_parameter_drift(estimates: list[PeriodEstimate]) -> None:
    """Plot regression instability across non-overlapping research periods.

    Parameters
    ----------
    estimates
        Ordered pre-period and backtest estimates.
    """

    labels = [estimate.name for estimate in estimates]
    x = np.arange(len(labels))
    panels = (
        ("beta", "Hedge ratio (beta)", COLORS["blue"]),
        ("r_squared", "Price-regression R-squared", COLORS["gold"]),
        ("residual_std_usd", "Residual volatility (USD)", COLORS["red"]),
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5), constrained_layout=True)
    for ax, (field, title, color) in zip(axes, panels, strict=True):
        values = [float(getattr(estimate, field)) for estimate in estimates]
        bars = ax.bar(x, values, color=color, alpha=0.88)
        ax.axhline(0.0, color="#222222", linewidth=0.8)
        ax.set_title(title)
        ax.set_xticks(x, labels, rotation=18, ha="right")
        ax.grid(axis="y", alpha=0.2)
        for bar, value in zip(bars, values, strict=True):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                f"{value:.3f}",
                ha="center",
                va="bottom" if value >= 0 else "top",
            )
    fig.suptitle("The fitted price relation was not stable", fontsize=15)
    fig.savefig(IMAGES_DIR / "02_parameter_drift.png", dpi=FIGURE_DPI)
    plt.close(fig)


def plot_equity(daily: pd.DataFrame, initial_capital_usd: float) -> None:
    """Plot daily marked gross and net equity with net drawdown.

    Parameters
    ----------
    daily
        Daily backtest state and profit-and-loss components.
    initial_capital_usd
        Account value at inception in US dollars.
    """

    gross_equity = initial_capital_usd + daily["gross_pnl_usd"].cumsum()
    peak = daily["equity_usd"].cummax().clip(lower=initial_capital_usd)
    drawdown = daily["equity_usd"] / peak - 1.0
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(13, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1]},
        constrained_layout=True,
    )
    axes[0].plot(
        daily.index,
        gross_equity,
        color=COLORS["gray"],
        linewidth=1.7,
        label="Before costs",
    )
    axes[0].plot(
        daily.index,
        daily["equity_usd"],
        color=COLORS["blue"],
        linewidth=2.1,
        label="After costs",
    )
    axes[0].axhline(initial_capital_usd, color="#222222", linestyle="--", linewidth=1.0)
    axes[0].set_title("Daily mark-to-market exposes both losses and carrying costs")
    axes[0].set_ylabel("Account value (USD)")
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.22)
    axes[1].fill_between(
        drawdown.index, drawdown * 100.0, 0.0, color=COLORS["red"], alpha=0.55
    )
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Drawdown (%)")
    axes[1].grid(alpha=0.22)
    fig.savefig(IMAGES_DIR / "03_backtest_equity.png", dpi=FIGURE_DPI)
    plt.close(fig)


def main() -> None:
    """Run the frozen analysis and regenerate all cited evidence."""

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()
    prices = load_frozen_prices()
    training = prices.loc[prices.index < config.backtest_start].tail(
        config.training_observations
    )
    fit = fit_cointegration(training)
    result = run_backtest(prices, fit, config)
    estimates = [
        estimate_period("20-year training", training),
        estimate_period("Prior 2 years", prices.loc["2021-10-11":"2023-10-10"]),
        estimate_period(
            "Backtest", prices.loc[config.backtest_start : config.backtest_end]
        ),
    ]
    plot_residual(prices, training)
    plot_parameter_drift(estimates)
    plot_equity(result.daily, config.initial_capital_usd)
    pd.Series(result.metrics, name="value").rename_axis("metric").to_csv(SUMMARY_PATH)
    result.daily.to_csv(DAILY_PATH)
    print(f"Generated 3 charts and {len(result.trades)} completed trades.")


if __name__ == "__main__":
    main()

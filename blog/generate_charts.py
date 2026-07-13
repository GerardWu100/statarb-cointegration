"""Generate reproducible technical charts for the cointegration blog post.

Inputs
------
data/ko_pep_adjusted_close.parquet
    Frozen daily adjusted closes with a ``DatetimeIndex`` and ``KO``/``PEP``
    columns. Prices are in US dollars.

Outputs
-------
images/01_spread_regime_shift.png
    Spread history around the October 2023 calibration date.
images/02_parameter_drift.png
    Hedge-ratio, fit, and spread-volatility comparisons by period.
images/03_backtest_equity.png
    Completed-trade equity from the rolling z-score strategy.
data/analysis_summary.csv
    Frozen metrics cited by the English and French posts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BLOG_ROOT = Path(__file__).resolve().parent
DATA_PATH = BLOG_ROOT / "data" / "ko_pep_adjusted_close.parquet"
SUMMARY_PATH = BLOG_ROOT / "data" / "analysis_summary.csv"
IMAGES_DIR = BLOG_ROOT / "images"

TRADE_DATE = pd.Timestamp("2023-10-09")
BACKTEST_START = pd.Timestamp("2023-10-11")
BACKTEST_END = pd.Timestamp("2025-09-30")
HISTORICAL_OBSERVATIONS = 5_000
ROLLING_WINDOW = 60
ENTRY_Z = 1.5
EXIT_Z = 0.2
STOP_Z = 2.5
INITIAL_CAPITAL_USD = 100_000.0
FIGURE_DPI = 180

COLORS = {
    "navy": "#14213D",
    "blue": "#277DA1",
    "red": "#C44536",
    "gold": "#E9C46A",
    "green": "#2A9D8F",
    "gray": "#6C757D",
}


@dataclass(frozen=True)
class PeriodEstimate:
    """Regression and spread estimates for one date range.

    Parameters
    ----------
    name
        Human-readable period label.
    beta
        Ordinary least-squares slope in ``KO = alpha + beta * PEP``.
    r_squared
        Fraction of KO price variation explained by the price regression.
    spread_mean_usd
        Mean of ``KO - beta * PEP``, in US dollars.
    spread_std_usd
        Sample standard deviation of the spread, in US dollars.
    observations
        Number of aligned daily observations.
    """

    name: str
    beta: float
    r_squared: float
    spread_mean_usd: float
    spread_std_usd: float
    observations: int


def load_prices() -> pd.DataFrame:
    """Load and validate the frozen adjusted-close sample.

    Returns
    -------
    pandas.DataFrame
        Sorted daily prices with a ``DatetimeIndex`` and float ``KO`` and
        ``PEP`` columns, measured in US dollars.

    Raises
    ------
    ValueError
        If required columns are absent or prices contain missing values.
    """

    prices = pd.read_parquet(DATA_PATH).loc[:, ["KO", "PEP"]].sort_index()
    prices.index = pd.to_datetime(prices.index)
    if prices.isna().any().any():
        raise ValueError("Frozen KO/PEP prices must not contain missing values.")
    return prices.astype(float)


def estimate_period(name: str, prices: pd.DataFrame) -> PeriodEstimate:
    """Fit the project price regression and summarize its residual spread.

    Parameters
    ----------
    name
        Label saved with the estimate.
    prices
        Daily adjusted prices with ``KO`` and ``PEP`` columns.

    Returns
    -------
    PeriodEstimate
        Slope, coefficient of determination, and spread moments.
    """

    beta, alpha = np.polyfit(prices["PEP"].to_numpy(), prices["KO"].to_numpy(), 1)
    fitted = alpha + beta * prices["PEP"].to_numpy()
    residual_sum_squares = np.square(prices["KO"].to_numpy() - fitted).sum()
    total_sum_squares = np.square(prices["KO"].to_numpy() - prices["KO"].mean()).sum()
    r_squared = 1.0 - residual_sum_squares / total_sum_squares
    spread = prices["KO"] - beta * prices["PEP"]
    return PeriodEstimate(
        name=name,
        beta=float(beta),
        r_squared=float(r_squared),
        spread_mean_usd=float(spread.mean()),
        spread_std_usd=float(spread.std()),
        observations=len(prices),
    )


def run_backtest(prices: pd.DataFrame, beta: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reproduce the project's rolling z-score trade logic.

    Parameters
    ----------
    prices
        Backtest-period adjusted closes with ``KO`` and ``PEP`` columns.
    beta
        Fixed historical hedge ratio in ``KO - beta * PEP``.

    Returns
    -------
    trades
        One row per completed trade. Columns record entry/exit dates, side,
        entry/exit z-scores, holding days, exit reason, and profit and loss in
        US dollars.
    equity
        Account value after each completed trade. The index is the completion
        date and ``equity_usd`` is measured in US dollars.

    Notes
    -----
    The calculation deliberately follows the repository implementation. It
    omits transaction costs, borrow fees, dividends, and mark-to-market values
    between exits.
    """

    spread = prices["KO"] - beta * prices["PEP"]
    rolling_mean = spread.rolling(ROLLING_WINDOW).mean()
    rolling_std = spread.rolling(ROLLING_WINDOW).std()
    z_score = (spread - rolling_mean) / rolling_std

    ko_shares = int(INITIAL_CAPITAL_USD / prices["KO"].iloc[0])
    pep_shares = int(INITIAL_CAPITAL_USD / prices["PEP"].iloc[0])
    position = 0
    entry_date: pd.Timestamp | None = None
    entry_ko = 0.0
    entry_pep = 0.0
    entry_z = 0.0
    records: list[dict[str, object]] = []
    equity_dates = [prices.index[ROLLING_WINDOW]]
    equity_values = [INITIAL_CAPITAL_USD]

    for date, current_z in z_score.iloc[ROLLING_WINDOW:].items():
        if np.isnan(current_z):
            continue
        if position == 0 and abs(current_z) > ENTRY_Z:
            # Positive spread -> short KO/long PEP; negative spread -> reverse.
            position = -1 if current_z > ENTRY_Z else 1
            entry_date = date
            entry_ko = float(prices.at[date, "KO"])
            entry_pep = float(prices.at[date, "PEP"])
            entry_z = float(current_z)
            continue
        if position == 0 or not (abs(current_z) < EXIT_Z or abs(current_z) > STOP_Z):
            continue

        exit_ko = float(prices.at[date, "KO"])
        exit_pep = float(prices.at[date, "PEP"])
        ko_move = (exit_ko - entry_ko) * ko_shares
        pep_move = (exit_pep - entry_pep) * pep_shares
        pnl_usd = ko_move - pep_move if position == 1 else -ko_move + pep_move
        reason = "mean reversion" if abs(current_z) < EXIT_Z else "stop loss"
        assert entry_date is not None
        records.append(
            {
                "entry_date": entry_date,
                "exit_date": date,
                "side": "long spread" if position == 1 else "short spread",
                "entry_z": entry_z,
                "exit_z": float(current_z),
                "holding_days": int((date - entry_date).days),
                "exit_reason": reason,
                "pnl_usd": pnl_usd,
            }
        )
        equity_dates.append(date)
        equity_values.append(equity_values[-1] + pnl_usd)
        position = 0
        entry_date = None

    trades = pd.DataFrame.from_records(records)
    equity = pd.DataFrame({"equity_usd": equity_values}, index=pd.DatetimeIndex(equity_dates))
    equity.index.name = "date"
    return trades, equity


def plot_spread_regime(prices: pd.DataFrame, beta: float) -> None:
    """Plot the fixed-beta spread before and after the calibration date.

    Parameters
    ----------
    prices
        Full frozen adjusted-price history.
    beta
        Historical hedge ratio.
    """

    plot_prices = prices.loc["2021-01-01":BACKTEST_END]
    spread = plot_prices["KO"] - beta * plot_prices["PEP"]
    calibration_spread = spread.loc[:TRADE_DATE].tail(ROLLING_WINDOW)
    mean_usd = calibration_spread.mean()
    std_usd = calibration_spread.std()

    fig, ax = plt.subplots(figsize=(13, 6.5), constrained_layout=True)
    ax.plot(spread.index, spread, color=COLORS["navy"], linewidth=1.7, label="Fixed-beta spread")
    ax.axhline(mean_usd, color=COLORS["green"], linewidth=1.8, label="Pre-trade 60-day mean")
    ax.axhspan(
        mean_usd - 2.0 * std_usd,
        mean_usd + 2.0 * std_usd,
        color=COLORS["green"],
        alpha=0.12,
        label="Pre-trade mean +/- 2 standard deviations",
    )
    ax.axvline(TRADE_DATE, color=COLORS["red"], linestyle="--", linewidth=1.8, label="Calibration date")
    ax.set_title("The KO-PEP spread left its calibration regime")
    ax.set_xlabel("Date")
    ax.set_ylabel("KO - beta x PEP (USD)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, ncols=2)
    fig.savefig(IMAGES_DIR / "01_spread_regime_shift.png", dpi=FIGURE_DPI)
    plt.close(fig)


def plot_parameter_drift(estimates: list[PeriodEstimate]) -> None:
    """Plot regression and spread diagnostics across estimation periods.

    Parameters
    ----------
    estimates
        Ordered period estimates for the 20-year, recent, and backtest samples.
    """

    labels = [estimate.name for estimate in estimates]
    x = np.arange(len(labels))
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5), constrained_layout=True)
    panels = (
        ("beta", "Hedge ratio (beta)", COLORS["blue"], 0.0),
        ("r_squared", "Price-regression R-squared", COLORS["gold"], 0.0),
        ("spread_std_usd", "Spread volatility (USD)", COLORS["red"], 0.0),
    )
    for ax, (field, title, color, baseline) in zip(axes, panels, strict=True):
        values = [float(getattr(estimate, field)) for estimate in estimates]
        bars = ax.bar(x, values, color=color, alpha=0.88)
        ax.axhline(baseline, color="#222222", linewidth=0.8)
        ax.set_title(title)
        ax.set_xticks(x, labels, rotation=18, ha="right")
        ax.grid(axis="y", alpha=0.2)
        for bar, value in zip(bars, values, strict=True):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                value,
                f"{value:.3f}" if field != "spread_std_usd" else f"${value:.2f}",
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=9,
            )
    fig.suptitle("A fixed hedge ratio did not survive the regime change", fontsize=15)
    fig.savefig(IMAGES_DIR / "02_parameter_drift.png", dpi=FIGURE_DPI)
    plt.close(fig)


def plot_backtest_equity(equity: pd.DataFrame) -> None:
    """Plot account value after each completed historical trade.

    Parameters
    ----------
    equity
        Account values indexed by completed-trade date.
    """

    fig, ax = plt.subplots(figsize=(12.5, 6), constrained_layout=True)
    ax.plot(
        equity.index,
        equity["equity_usd"],
        color=COLORS["blue"],
        linewidth=2.2,
        marker="o",
        markersize=4,
    )
    ax.axhline(INITIAL_CAPITAL_USD, color=COLORS["gray"], linestyle="--", label="Initial capital")
    ax.fill_between(
        equity.index,
        equity["equity_usd"],
        INITIAL_CAPITAL_USD,
        where=equity["equity_usd"] < INITIAL_CAPITAL_USD,
        color=COLORS["red"],
        alpha=0.16,
    )
    ax.set_title("Historical completed-trade equity, October 2023 to September 2025")
    ax.set_xlabel("Exit date")
    ax.set_ylabel("Account value (USD)")
    ax.yaxis.set_major_formatter(lambda value, _: f"${value / 1_000:.0f}k")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False)
    fig.savefig(IMAGES_DIR / "03_backtest_equity.png", dpi=FIGURE_DPI)
    plt.close(fig)


def save_summary(
    historical: PeriodEstimate,
    recent: PeriodEstimate,
    backtest: PeriodEstimate,
    backtest_prices: pd.DataFrame,
    calibration_mean_usd: float,
    calibration_std_usd: float,
    trades: pd.DataFrame,
    equity: pd.DataFrame,
) -> None:
    """Write the cited model and backtest statistics to a tidy CSV file.

    Parameters
    ----------
    historical, recent, backtest
        Regression estimates for the three analysis periods.
    backtest_prices
        Adjusted closes used by the historical strategy test.
    calibration_mean_usd, calibration_std_usd
        Fixed-beta spread moments over the 60 days before the trade date.
    trades
        Completed historical trades.
    equity
        Completed-trade account values.
    """

    pnl = trades["pnl_usd"]
    metrics = {
        "historical_beta": historical.beta,
        "historical_r_squared": historical.r_squared,
        "historical_spread_std_usd": historical.spread_std_usd,
        "recent_beta": recent.beta,
        "recent_r_squared": recent.r_squared,
        "backtest_beta": backtest.beta,
        "backtest_r_squared": backtest.r_squared,
        "calibration_spread_mean_usd": calibration_mean_usd,
        "calibration_spread_std_usd": calibration_std_usd,
        "backtest_fixed_beta_spread_mean_usd": (
            float(backtest_prices["KO"].sub(historical.beta * backtest_prices["PEP"]).mean())
        ),
        "backtest_fixed_beta_spread_std_usd": (
            float(backtest_prices["KO"].sub(historical.beta * backtest_prices["PEP"]).std())
        ),
        "completed_trades": float(len(trades)),
        "winning_trades": float((pnl > 0).sum()),
        "win_rate": float((pnl > 0).mean()),
        "total_pnl_usd": float(pnl.sum()),
        "total_return": float(equity["equity_usd"].iloc[-1] / INITIAL_CAPITAL_USD - 1.0),
        "average_holding_days": float(trades["holding_days"].mean()),
        "best_trade_usd": float(pnl.max()),
        "worst_trade_usd": float(pnl.min()),
    }
    pd.Series(metrics, name="value").rename_axis("metric").to_csv(SUMMARY_PATH)


def main() -> None:
    """Generate the frozen metrics and all technical figures."""

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    prices = load_prices()
    historical_prices = prices.loc[prices.index < TRADE_DATE].tail(HISTORICAL_OBSERVATIONS)
    recent_prices = prices.loc["2021-10-09":"2023-10-08"]
    backtest_prices = prices.loc[BACKTEST_START:BACKTEST_END]

    historical = estimate_period("20-year fit", historical_prices)
    recent = estimate_period("Prior 2 years", recent_prices)
    backtest = estimate_period("Backtest", backtest_prices)
    fixed_spread = historical_prices["KO"] - historical.beta * historical_prices["PEP"]
    calibration_spread = fixed_spread.tail(ROLLING_WINDOW)
    trades, equity = run_backtest(backtest_prices, historical.beta)

    plot_spread_regime(prices, historical.beta)
    plot_parameter_drift([historical, recent, backtest])
    plot_backtest_equity(equity)
    save_summary(
        historical,
        recent,
        backtest,
        backtest_prices,
        float(calibration_spread.mean()),
        float(calibration_spread.std()),
        trades,
        equity,
    )
    print(f"Generated 3 charts and {len(trades)} completed-trade observations.")


if __name__ == "__main__":
    main()

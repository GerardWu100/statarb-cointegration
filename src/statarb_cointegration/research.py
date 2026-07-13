"""Cointegration estimation and a causal, daily marked pairs backtest."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint

from .config import ResearchConfig


@dataclass(frozen=True, slots=True)
class CointegrationFit:
    """Fixed training-sample relation and residual-stationarity diagnostics.

    Parameters
    ----------
    alpha_usd
        Intercept in US dollars in ``KO = alpha + beta * PEP + residual``.
    beta
        PEP shares hedged per KO share in the residual portfolio.
    r_squared
        Fraction of training KO price variation explained by the regression.
    adf_statistic, adf_pvalue
        Augmented Dickey-Fuller statistic and p-value on fitted residuals.
    engle_granger_statistic, engle_granger_pvalue
        Cointegration statistic and MacKinnon p-value accounting for the
        estimated residual.
    observations
        Number of training rows.
    """

    alpha_usd: float
    beta: float
    r_squared: float
    adf_statistic: float
    adf_pvalue: float
    engle_granger_statistic: float
    engle_granger_pvalue: float
    observations: int


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Daily account history, completed trades, and summary statistics.

    Parameters
    ----------
    daily
        One row per backtest close, including prior-close signals, holdings,
        gross and net profit and loss, costs, and marked equity.
    trades
        One row per completed position with cost-aware profit and loss.
    metrics
        Scalar performance and model diagnostics.
    """

    daily: pd.DataFrame
    trades: pd.DataFrame
    metrics: dict[str, float]


def load_prices(config: ResearchConfig) -> pd.DataFrame:
    """Load sorted, positive KO and PEP adjusted close prices.

    Parameters
    ----------
    config
        Research settings containing the project-relative parquet path.

    Returns
    -------
    pandas.DataFrame
        Daily US-dollar adjusted closes indexed by unique timestamps.
    """

    prices = pd.read_parquet(config.prices_path).loc[:, ["KO", "PEP"]].astype(float).sort_index()
    prices.index = pd.DatetimeIndex(pd.to_datetime(prices.index), name="date")
    if prices.index.has_duplicates or prices.isna().any().any() or (prices <= 0.0).any().any():
        raise ValueError("Prices must be positive, complete, and uniquely indexed.")
    return prices


def fit_cointegration(training_prices: pd.DataFrame) -> CointegrationFit:
    """Estimate ``KO = alpha + beta * PEP + residual`` and test the residual.

    Parameters
    ----------
    training_prices
        In-sample adjusted closes in US dollars.

    Returns
    -------
    CointegrationFit
        Regression coefficients, fit, and two residual-stationarity tests.

    Notes
    -----
    The Engle-Granger p-value is the formal trading gate because its critical
    values account for estimating the residual. The ordinary Augmented
    Dickey-Fuller result is retained as a transparent diagnostic.
    """

    x = training_prices["PEP"].to_numpy()
    y = training_prices["KO"].to_numpy()
    beta, alpha = np.polyfit(x, y, 1)
    fitted = alpha + beta * x
    residual = y - fitted
    residual_ss = float(np.square(residual).sum())
    total_ss = float(np.square(y - y.mean()).sum())
    adf_statistic, adf_pvalue, *_ = adfuller(residual, regression="c", autolag="AIC")
    eg_statistic, eg_pvalue, _ = coint(y, x, trend="c", autolag="aic")
    return CointegrationFit(
        alpha_usd=float(alpha),
        beta=float(beta),
        r_squared=1.0 - residual_ss / total_ss,
        adf_statistic=float(adf_statistic),
        adf_pvalue=float(adf_pvalue),
        engle_granger_statistic=float(eg_statistic),
        engle_granger_pvalue=float(eg_pvalue),
        observations=len(training_prices),
    )


def compute_causal_signal(
    prices: pd.DataFrame,
    fit: CointegrationFit,
    rolling_window: int,
) -> pd.DataFrame:
    """Compute residuals and z-scores using only information known at each close.

    Parameters
    ----------
    prices
        Adjusted closes containing training context and backtest dates.
    fit
        Coefficients frozen before the backtest.
    rolling_window
        Number of lagged residuals in the mean and standard deviation.

    Returns
    -------
    pandas.DataFrame
        Residual, lagged rolling mean, lagged rolling standard deviation, and
        z-score. The rolling statistics are shifted by one day, so today's
        residual never normalizes itself.
    """

    residual = prices["KO"] - fit.alpha_usd - fit.beta * prices["PEP"]
    lagged = residual.shift(1)
    rolling_mean = lagged.rolling(rolling_window).mean()
    rolling_std = lagged.rolling(rolling_window).std(ddof=1)
    return pd.DataFrame(
        {
            "residual_usd": residual,
            "rolling_mean_usd": rolling_mean,
            "rolling_std_usd": rolling_std,
            "z_score": (residual - rolling_mean) / rolling_std,
        },
        index=prices.index,
    )


def _target_holdings(
    ko_price: float,
    pep_price: float,
    beta: float,
    side: int,
    config: ResearchConfig,
) -> tuple[float, float]:
    """Size holdings that exactly replicate the fitted residual direction.

    Parameters
    ----------
    ko_price, pep_price
        Entry prices in US dollars per share.
    beta
        Fitted PEP shares per KO share.
    side
        ``+1`` for long residual and ``-1`` for short residual.
    config
        Capital and gross-exposure settings.

    Returns
    -------
    tuple[float, float]
        Signed KO and PEP shares. Their ratio is always ``PEP = -beta * KO``.
    """

    target_gross = config.initial_capital_usd * config.gross_exposure_multiple
    ko_units = target_gross / (ko_price + abs(beta) * pep_price)
    return side * ko_units, -side * beta * ko_units


def run_backtest(
    prices: pd.DataFrame,
    fit: CointegrationFit,
    config: ResearchConfig,
) -> BacktestResult:
    """Run the out-of-sample strategy with daily marking and explicit costs.

    Parameters
    ----------
    prices
        Complete price history, including pre-backtest rolling context.
    fit
        Cointegration relation estimated strictly before the backtest.
    config
        Signal, exposure, cost, and date settings.

    Returns
    -------
    BacktestResult
        Daily account state, completed trades, and scalar metrics.

    Notes
    -----
    A z-score observed at close ``t`` determines holdings after that close.
    Those holdings earn the price move from ``t`` to ``t+1``. Therefore no
    price change is earned before its signal exists. Trading cost is charged
    on close-to-close turnover; borrow and funding costs accrue on the prior
    close's short and long market values.
    """

    signal = compute_causal_signal(prices, fit, config.rolling_window)
    sample = prices.loc[config.backtest_start : config.backtest_end]
    if sample.empty:
        raise ValueError("The configured backtest interval contains no prices.")

    cost_rate = config.transaction_cost_bps / 10_000.0
    daily_rate = 1.0 / config.trading_days_per_year
    ko_shares = 0.0
    pep_shares = 0.0
    side = 0
    entry_date: pd.Timestamp | None = None
    trade_net_pnl = 0.0
    trade_gross_pnl = 0.0
    trade_cost = 0.0
    rows: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity = config.initial_capital_usd
    previous_prices: pd.Series | None = None

    for row_number, (date, current_prices) in enumerate(sample.iterrows()):
        gross_pnl = 0.0
        borrow_cost = 0.0
        financing_cost = 0.0
        if previous_prices is not None:
            gross_pnl = (
                ko_shares * (float(current_prices["KO"]) - float(previous_prices["KO"]))
                + pep_shares * (float(current_prices["PEP"]) - float(previous_prices["PEP"]))
            )
            short_value = max(-ko_shares * float(previous_prices["KO"]), 0.0) + max(
                -pep_shares * float(previous_prices["PEP"]), 0.0
            )
            long_value = max(ko_shares * float(previous_prices["KO"]), 0.0) + max(
                pep_shares * float(previous_prices["PEP"]), 0.0
            )
            borrow_cost = short_value * config.short_borrow_rate_annual * daily_rate
            financing_cost = long_value * config.financing_rate_annual * daily_rate

        z_score = float(signal.at[date, "z_score"])
        old_ko, old_pep = ko_shares, pep_shares
        exit_reason = ""
        is_last_date = row_number == len(sample) - 1
        if side != 0 and (abs(z_score) <= config.exit_z or abs(z_score) >= config.stop_z or is_last_date):
            exit_reason = (
                "end of sample"
                if is_last_date
                else "mean reversion"
                if abs(z_score) <= config.exit_z
                else "stop loss"
            )
            ko_shares = 0.0
            pep_shares = 0.0
        elif side == 0 and config.entry_z <= abs(z_score) < config.stop_z and not is_last_date:
            side = -1 if z_score > 0.0 else 1
            ko_shares, pep_shares = _target_holdings(
                float(current_prices["KO"]), float(current_prices["PEP"]), fit.beta, side, config
            )
            entry_date = date

        turnover = abs(ko_shares - old_ko) * float(current_prices["KO"]) + abs(
            pep_shares - old_pep
        ) * float(current_prices["PEP"])
        transaction_cost = turnover * cost_rate
        net_pnl = gross_pnl - borrow_cost - financing_cost - transaction_cost
        equity += net_pnl

        if side != 0 or exit_reason:
            trade_gross_pnl += gross_pnl
            trade_cost += borrow_cost + financing_cost + transaction_cost
            trade_net_pnl += net_pnl
        if exit_reason:
            assert entry_date is not None
            trades.append(
                {
                    "entry_date": entry_date,
                    "exit_date": date,
                    "side": "long residual" if side == 1 else "short residual",
                    "exit_reason": exit_reason,
                    "holding_days": int((date - entry_date).days),
                    "gross_pnl_usd": trade_gross_pnl,
                    "cost_usd": trade_cost,
                    "net_pnl_usd": trade_net_pnl,
                }
            )
            side = 0
            entry_date = None
            trade_net_pnl = trade_gross_pnl = trade_cost = 0.0

        rows.append(
            {
                "date": date,
                "ko_price_usd": float(current_prices["KO"]),
                "pep_price_usd": float(current_prices["PEP"]),
                "residual_usd": float(signal.at[date, "residual_usd"]),
                "z_score": z_score,
                "ko_shares": ko_shares,
                "pep_shares": pep_shares,
                "gross_pnl_usd": gross_pnl,
                "transaction_cost_usd": transaction_cost,
                "borrow_cost_usd": borrow_cost,
                "financing_cost_usd": financing_cost,
                "net_pnl_usd": net_pnl,
                "equity_usd": equity,
            }
        )
        previous_prices = current_prices

    daily = pd.DataFrame(rows).set_index("date")
    trade_frame = pd.DataFrame(trades)
    returns = daily["net_pnl_usd"] / daily["equity_usd"].shift(1).fillna(config.initial_capital_usd)
    running_peak = daily["equity_usd"].cummax().clip(lower=config.initial_capital_usd)
    drawdown = daily["equity_usd"] / running_peak - 1.0
    return_std = float(returns.std(ddof=1))
    sharpe = float(returns.mean() / return_std * np.sqrt(config.trading_days_per_year)) if return_std else np.nan
    metrics = {
        "alpha_usd": fit.alpha_usd,
        "beta": fit.beta,
        "training_r_squared": fit.r_squared,
        "adf_statistic": fit.adf_statistic,
        "adf_pvalue": fit.adf_pvalue,
        "engle_granger_statistic": fit.engle_granger_statistic,
        "engle_granger_pvalue": fit.engle_granger_pvalue,
        "cointegration_passed": float(
            fit.engle_granger_pvalue <= config.cointegration_significance
        ),
        "completed_trades": float(len(trade_frame)),
        "win_rate": float((trade_frame["net_pnl_usd"] > 0.0).mean()),
        "gross_pnl_usd": float(daily["gross_pnl_usd"].sum()),
        "total_cost_usd": float(
            daily[["transaction_cost_usd", "borrow_cost_usd", "financing_cost_usd"]].sum().sum()
        ),
        "net_pnl_usd": float(daily["net_pnl_usd"].sum()),
        "total_return": float(equity / config.initial_capital_usd - 1.0),
        "annualized_sharpe": sharpe,
        "maximum_drawdown": float(drawdown.min()),
    }
    return BacktestResult(daily=daily, trades=trade_frame, metrics=metrics)

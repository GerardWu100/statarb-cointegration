"""Unit tests for cointegration signals, holdings, costs, and marking."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from statarb_cointegration.config import ResearchConfig
from statarb_cointegration.research import (
    CointegrationFit,
    _target_holdings,
    compute_causal_signal,
    run_backtest,
)


def make_config(**overrides: object) -> ResearchConfig:
    """Create a compact valid configuration for deterministic unit tests.

    Parameters
    ----------
    **overrides
        Field values replacing the defaults.

    Returns
    -------
    ResearchConfig
        Test configuration rooted at the current repository.
    """

    values: dict[str, object] = {
        "project_root": Path(__file__).resolve().parents[2],
        "training_observations": 20,
        "backtest_start": "2024-01-01",
        "backtest_end": "2024-01-12",
        "rolling_window": 3,
        "entry_z": 1.0,
        "exit_z": 0.2,
        "stop_z": 3.0,
        "initial_capital_usd": 100_000.0,
        "gross_exposure_multiple": 1.0,
        "transaction_cost_bps": 5.0,
        "short_borrow_rate_annual": 0.01,
        "financing_rate_annual": 0.05,
        "trading_days_per_year": 252,
        "cointegration_significance": 0.05,
    }
    values.update(overrides)
    return ResearchConfig(**values)  # type: ignore[arg-type]


def make_fit() -> CointegrationFit:
    """Return a fixed relation that passes the formal trading gate.

    Returns
    -------
    CointegrationFit
        Relation ``KO = 10 + 0.5 * PEP + residual``.
    """

    return CointegrationFit(10.0, 0.5, 0.9, -4.0, 0.01, -4.0, 0.01, 100)


def test_signal_does_not_use_current_or_future_residuals() -> None:
    """Changing a future price must not alter earlier rolling statistics."""

    dates = pd.bdate_range("2023-12-20", periods=12, name="date")
    prices = pd.DataFrame({"KO": np.arange(12.0) + 60.0, "PEP": 100.0}, index=dates)
    baseline = compute_causal_signal(prices, make_fit(), rolling_window=3)
    changed = prices.copy()
    changed.iloc[-1, changed.columns.get_loc("KO")] += 1000.0
    revised = compute_causal_signal(changed, make_fit(), rolling_window=3)
    pd.testing.assert_series_equal(
        baseline["z_score"].iloc[:-1], revised["z_score"].iloc[:-1], check_names=False
    )
    assert baseline["rolling_mean_usd"].iloc[-1] == revised["rolling_mean_usd"].iloc[-1]


def test_holdings_replicate_the_residual_hedge_sign_and_ratio() -> None:
    """Long and short holdings must satisfy PEP shares = -beta * KO shares."""

    config = make_config()
    long_ko, long_pep = _target_holdings(60.0, 100.0, 0.5, 1, config)
    short_ko, short_pep = _target_holdings(60.0, 100.0, 0.5, -1, config)
    assert np.isclose(long_pep, -0.5 * long_ko)
    assert long_ko > 0.0 and long_pep < 0.0
    assert np.isclose(short_ko, -long_ko) and np.isclose(short_pep, -long_pep)


def test_costs_reduce_daily_marked_equity() -> None:
    """Explicit costs must lower final equity without changing gross P&L."""

    dates = pd.bdate_range("2023-12-20", periods=20, name="date")
    residual = np.array(
        [0, 1, -1, 0, 1, -1, 0, 1, -1, 0, 3, 2, 0, -2, 0, 2, 0, -2, 0, 0], dtype=float
    )
    prices = pd.DataFrame({"PEP": 100.0, "KO": 60.0 + residual}, index=dates)
    with_cost = run_backtest(prices, make_fit(), make_config())
    no_cost_config = make_config(
        transaction_cost_bps=0.0,
        short_borrow_rate_annual=0.0,
        financing_rate_annual=0.0,
    )
    without_cost = run_backtest(prices, make_fit(), no_cost_config)
    assert len(with_cost.daily) == len(prices.loc["2024-01-01":"2024-01-12"])
    assert with_cost.daily["equity_usd"].nunique() > 1
    # Holdings selected at close t-1 must explain exactly the gross P&L at t.
    prior_holdings = with_cost.daily[["ko_shares", "pep_shares"]].shift(1).fillna(0.0)
    price_changes = (
        with_cost.daily[["ko_price_usd", "pep_price_usd"]].diff().fillna(0.0)
    )
    traced_gross_pnl = (
        prior_holdings["ko_shares"] * price_changes["ko_price_usd"]
        + prior_holdings["pep_shares"] * price_changes["pep_price_usd"]
    )
    np.testing.assert_allclose(with_cost.daily["gross_pnl_usd"], traced_gross_pnl)
    assert np.isclose(
        with_cost.trades["net_pnl_usd"].sum(), with_cost.daily["net_pnl_usd"].sum()
    )
    assert np.isclose(
        with_cost.metrics["gross_pnl_usd"], without_cost.metrics["gross_pnl_usd"]
    )
    assert with_cost.metrics["net_pnl_usd"] < without_cost.metrics["net_pnl_usd"]
    assert with_cost.metrics["total_cost_usd"] > 0.0


def test_cointegration_result_is_reported_as_a_research_gate() -> None:
    """The summary must label a failed prerequisite without hiding diagnostics."""

    dates = pd.bdate_range("2023-12-20", periods=20, name="date")
    residual = np.array(
        [0, 1, -1, 0, 1, -1, 0, 1, -1, 0, 3, 2, 0, -2, 0, 2, 0, -2, 0, 0], dtype=float
    )
    prices = pd.DataFrame({"PEP": 100.0, "KO": 60.0 + residual}, index=dates)
    failed_fit = CointegrationFit(10.0, 0.5, 0.9, -2.0, 0.20, -2.0, 0.20, 100)
    result = run_backtest(prices, failed_fit, make_config())
    assert result.metrics["cointegration_passed"] == 0.0
    assert len(result.daily) > 0

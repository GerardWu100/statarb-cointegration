"""Typed configuration for the causal cointegration backtest."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


@dataclass(frozen=True, slots=True)
class ResearchConfig:
    """Research parameters loaded from ``config.toml``.

    Parameters
    ----------
    project_root
        Repository root used to resolve all input and output paths.
    training_observations
        Number of daily observations in the cointegrating regression.
    backtest_start, backtest_end
        Inclusive ISO dates for the out-of-sample evaluation.
    rolling_window
        Number of prior residuals used for the causal z-score.
    entry_z, exit_z, stop_z
        Absolute z-score thresholds for entry, mean-reversion exit, and stop.
    initial_capital_usd
        Starting account value in US dollars.
    gross_exposure_multiple
        Target gross market value divided by starting capital at entry.
    transaction_cost_bps
        One-way cost per dollar traded, in basis points.
    short_borrow_rate_annual, financing_rate_annual
        Annual rates charged on short and long market value.
    trading_days_per_year
        Annualization factor for costs and performance statistics.
    cointegration_significance
        Engle-Granger p-value threshold reported as the research prerequisite.
    """

    project_root: Path
    training_observations: int
    backtest_start: str
    backtest_end: str
    rolling_window: int
    entry_z: float
    exit_z: float
    stop_z: float
    initial_capital_usd: float
    gross_exposure_multiple: float
    transaction_cost_bps: float
    short_borrow_rate_annual: float
    financing_rate_annual: float
    trading_days_per_year: int
    cointegration_significance: float
    prices_path: Path = field(init=False)
    outputs_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        """Derive project paths and reject internally inconsistent settings."""

        if not 0.0 <= self.exit_z < self.entry_z < self.stop_z:
            raise ValueError("Thresholds must satisfy 0 <= exit_z < entry_z < stop_z.")
        if self.rolling_window < 2 or self.training_observations <= self.rolling_window:
            raise ValueError("Training history must exceed a rolling window of at least two observations.")
        if self.initial_capital_usd <= 0.0 or self.gross_exposure_multiple <= 0.0:
            raise ValueError("Capital and gross exposure must be positive.")
        object.__setattr__(
            self,
            "prices_path",
            self.project_root / "data" / "processed" / "ko_pep_combined_adj_close_price.parquet",
        )
        object.__setattr__(self, "outputs_dir", self.project_root / "outputs")


def load_config(path: Path | None = None) -> ResearchConfig:
    """Load the single project configuration file.

    Parameters
    ----------
    path
        Optional TOML path. The repository ``config.toml`` is the default.

    Returns
    -------
    ResearchConfig
        Validated immutable research parameters.
    """

    project_root = Path(__file__).resolve().parents[2]
    config_path = path or project_root / "config.toml"
    with config_path.open("rb") as stream:
        values = tomllib.load(stream)["research"]
    return ResearchConfig(project_root=project_root, **values)

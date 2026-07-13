"""Command-line entrypoint for the cointegration study."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    """Run the configured study and print its scalar results."""

    parser = argparse.ArgumentParser(description="Run the causal KO-PEP cointegration backtest.")
    parser.add_argument("--config", type=Path, help="Optional TOML configuration path.")
    arguments = parser.parse_args()
    result = run_pipeline(arguments.config)
    for metric, value in result.metrics.items():
        print(f"{metric}: {value:.6f}")


if __name__ == "__main__":
    main()

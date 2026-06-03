# Statistical Arbitrage Cointegration Study: Coca-Cola vs Pepsi

Preserves the notebook workflow as ordered Python step scripts for data download, spread modeling, Monte Carlo simulation, and backtesting.

The original notebook is preserved unchanged in `docs/reference/statarb-cointegration.ipynb`. The execution notebook in `notebooks/demo.ipynb` only calls the Python backend under `src/`.

## Layout

```text
statarb-cointegration/
├── README.md
├── pyproject.toml
├── scripts/              # thin CLI wrappers
├── src/statarb_cointegration/
│   ├── cli.py            # command-line entrypoint
│   ├── pipeline.py
│   └── steps/            # notebook-derived section scripts
├── notebooks/demo.ipynb
├── data/processed/       # local project inputs
├── outputs/              # figures, tables, reports, runs (generated)
├── docs/reference/       # original notebook and split map
└── docs/user/            # how to run
```

## Run

```bash
uv sync
uv run statarb-pipeline
uv run statarb-pipeline --smoke
uv run python scripts/run_pipeline.py --smoke
```

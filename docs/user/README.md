# User guide

## Run the pipeline

From the project root:

```bash
uv sync
uv run statarb-pipeline
uv run statarb-pipeline --smoke
uv run python scripts/run_pipeline.py --smoke
```

## Notebook

Open `notebooks/demo.ipynb` and run all cells. It imports `statarb_cointegration.pipeline.run_pipeline` directly.

## Outputs

- Processed prices: `data/processed/`
- Figures: `outputs/figures/`
- Tables: `outputs/tables/`

Original notebook and section-to-script map: `docs/reference/`.

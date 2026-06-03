# GUIDE_src.md

## Part 1: Conceptual Explanation

The `src/` tree holds the installable Python package for this project. All executable logic lives under `statarb_cointegration/`: path configuration, pipeline orchestration, the command-line entrypoint, and notebook-derived step scripts. Scripts at the repository root (`scripts/`) and notebooks only import and call this package.

## Part 2: Code Reference

- `statarb_cointegration/`: Main package. See `statarb_cointegration/GUIDE_statarb_cointegration.md`.
- `GUIDE_src.md`: This file — overview of the `src/` layout.

## Part 3: Short Journal

- 2026-05-20: Aligned layout with standard `src/` package structure; CLI moved into the package.

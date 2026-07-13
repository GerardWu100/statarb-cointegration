# GUIDE_src.md

## Part 1: Conceptual Explanation

The `src/` tree contains the installable research package. Its functions expose the fitted relation, residual tests, causal signal, matched holdings, daily accounting, and generated outputs as ordinary typed Python. Scripts and notebooks call this package instead of owning research logic.

## Part 2: Code Reference

- `statarb_cointegration/`: Main package. See its local guide for formulas, timing, files, and entry points.

## Part 3: Short Journal

- 2026-07-13: Removed notebook-style shared state so tests can inspect individual research stages and causal timing directly.

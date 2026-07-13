# Outline proposal

## Project scan summary

- Project archetype candidate: `strategy-backtest` with a statistical-model gate.
- Supporting evidence from files: `research.py` estimates and tests the residual, creates causal signals, matches holdings to the regression hedge, and accounts for costs and daily equity. The frozen price sample supports a complete historical result.

## Blueprint selection

- Problem: determine whether the KO-PEP residual is stationary and then measure the financial consequence of trading it consistently.
- Options: `strategy-backtest`, `risk-model`, and `mixed`.
- Selected blueprint: `strategy-backtest`.
- Why this blueprint fits this project: the central evidence is a formal pre-trade statistical gate followed by one historical trading state machine. The retired Monte Carlo model no longer defines the live research path.
- Planned section order: hypothesis; residual test; causal z-score; hedge-consistent positions; cost and mark-to-market derivation; corrected results; parameter-stability diagnosis; limitations and primary references.
- Verify: the post must distinguish the failed cointegration premise from the diagnostic backtest and trace every result to frozen data.

## Planned equations

1. Price regression and residual.
   - Purpose: define the exact linear combination under test.
   - Symbols: KO price $P^{KO}_t$, PEP price $P^{PEP}_t$, intercept $\alpha$, hedge ratio $\beta$, residual $\varepsilon_t$.
   - Delimiter: display.
2. Augmented Dickey-Fuller regression.
   - Purpose: define the unit-root null and stationary alternative.
   - Symbols: residual change $\Delta\varepsilon_t$, autoregressive coefficient $\rho$, lag coefficients $\gamma_i$, error $u_t$.
   - Delimiter: display.
3. Lagged rolling z-score.
   - Purpose: prove that current and future residuals do not enter normalization.
   - Symbols: lookback $L$, lagged mean $\bar\varepsilon_{t,L}$, standard deviation $s_{t,L}$, z-score $z_t$.
   - Delimiter: display.
4. Holdings and profit-and-loss identity.
   - Purpose: make signal and portfolio hedge definitions identical.
   - Symbols: side $s_t$, KO scale $q_t$, signed holdings $q^{KO}_t$ and $q^{PEP}_t$, gross profit and loss $\Pi^{gross}_t$.
   - Delimiter: display.
5. Transaction cost, carrying cost, and daily equity.
   - Purpose: define units and show the path from gross to net performance.
   - Symbols: turnover rate $c$, long and short market values, net profit and loss $\Pi^{net}_t$, equity $E_t$.
   - Delimiter: display.

## Planned code excerpts

1. File: `src/statarb_cointegration/research.py`.
   - Function/block: ADF and Engle-Granger calls.
   - Why include this excerpt: it shows that the formal residual test is executable evidence.
2. File: `src/statarb_cointegration/research.py`.
   - Function/block: shifted rolling mean and standard deviation.
   - Why include this excerpt: it makes the causal timing easy to audit.

## Planned technical graphs

1. Graph type: fixed residual with lagged mean and entry band.
   - Source: generate from the frozen adjusted-close parquet.
   - Expected takeaway: the residual migrated after training despite rolling normalization.
2. Graph type: regression slope, fit, and residual volatility by period.
   - Source: generate as a post-mortem diagnostic from the same frozen sample.
   - Expected takeaway: the hedge ratio changed sign and the relationship weakened.
3. Graph type: daily gross and net equity with drawdown.
   - Source: generate from the corrected backtest's daily ledger.
   - Expected takeaway: open-position marking reveals the path, while carrying costs deepen an already negative gross result.

## Risks, gaps, and assumptions

- Data gaps: daily adjusted closes provide no executable spread, market impact, locate availability, point-in-time corporate actions, or broker collateral terms.
- Assumptions: the fixed pre-period relation is intentionally retained through the diagnostic test; 200% gross exposure, 5 basis points of turnover cost, 1% short borrow, and 5% long financing are configurable scenarios.
- Validation checks: run unit tests, lint, full pipeline, chart regeneration, blog validator, image resolution, protected-block comparison, and link checks.
- Canonical workspace: `/home/ai4000/projects/one-time-projects/statarb-cointegration/blog/`.
- Deployment note: the user deferred website publication. No website files, Hugo build, website commit, or website push are in scope.

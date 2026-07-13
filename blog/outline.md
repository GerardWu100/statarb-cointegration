# Outline proposal

## Project scan summary

- Project archetype candidate: mixed `strategy-backtest` and `risk-model`.
- Supporting evidence from files: `04_4_pairs_trading_simulation_setup.py` estimates the hedge ratio and spread; `06_6_generate_correlated_price_paths_with_mean_reversion.py` combines correlated geometric Brownian motion with an Ornstein-Uhlenbeck spread correction; `09_8_risk_metrics_for_october_16_2023.py` and `16_comparison_of_var_methods_historical_simulation_vs_monte_carlo_vs_parametric.py` estimate tail risk; `15_14_mean_reversion_trading_strategy_on_60_day_simulations.py` simulates the strategy; `17_key_observations.py` runs the later historical backtest and diagnoses parameter drift.

## Blueprint selection

- Problem: explain why an attractive simulated pairs trade failed when the historical relationship changed.
- Options: `strategy-backtest`, `risk-model`, and `mixed`.
- Selected blueprint: `mixed`, with the strategy-backtest sequence carrying the article and risk-model material used to explain the simulation.
- Why this blueprint fits this project: the repository contains both a Monte Carlo risk engine and an explicit entry/exit backtest. Neither one alone explains the central result.
- Planned section order:
  1. The apparent KO-PEP relative-value opportunity.
  2. Hedge-ratio and spread construction.
  3. Correlated price simulation with an Ornstein-Uhlenbeck correction.
  4. Position sizing, signal rules, and Value at Risk.
  5. Simulated result versus the 500-day historical backtest.
  6. Diagnosis: hedge-ratio sign change, mean shift, and volatility expansion.
  7. What a production version would need.
- Verify: the draft must connect every performance figure to the deterministic smoke run or the frozen price sample, and it must make the 34.01% backtest loss more prominent than the favorable simulated Sharpe ratio.

## Planned equations

1. Ordinary least-squares price relationship and spread.
   - Purpose: define the hedge ratio and the residual being traded.
   - Symbols: Coca-Cola price $P^{KO}_t$, Pepsi price $P^{PEP}_t$, intercept $\alpha$, hedge ratio $\beta$, residual $\varepsilon_t$, spread $S_t$.
   - Delimiter: display.
2. Rolling z-score.
   - Purpose: convert the spread into an entry and exit signal.
   - Symbols: spread $S_t$, rolling mean $\bar S_{t,L}$, rolling standard deviation $s_{t,L}$, lookback $L=60$.
   - Delimiter: display.
3. Correlated geometric Brownian motion.
   - Purpose: explain the simulated marginal price paths.
   - Symbols: price $P_{i,t}$, drift $\mu_i$, volatility $\sigma_i$, time step $\Delta t$, correlated shock $\epsilon_{i,t}$.
   - Delimiter: display.
4. Ornstein-Uhlenbeck spread process and half-life.
   - Purpose: show the imposed mean-reversion assumption.
   - Symbols: spread $S_t$, reversion speed $\kappa$, target $\theta$, diffusion $\sigma_S$, Brownian motion $W_t$, half-life $h$.
   - Delimiter: display.
5. Value at Risk and Expected Shortfall.
   - Purpose: define the loss convention used in the project.
   - Symbols: horizon loss $L_H$, confidence level $c$, loss quantile $q_c$, Value at Risk $\operatorname{VaR}_c$, Expected Shortfall $\operatorname{ES}_c$.
   - Delimiter: display.

## Planned code excerpts

1. File: `src/statarb_cointegration/steps/06_6_generate_correlated_price_paths_with_mean_reversion.py`.
   - Function/block: variance-based allocation of the Ornstein-Uhlenbeck adjustment.
   - Why include this excerpt: it captures the project’s least obvious implementation detail and the identity $w_{KO}+\beta w_{PEP}=1$.
2. File: `src/statarb_cointegration/steps/17_key_observations.py`.
   - Function/block: rolling signal and trade exit logic.
   - Why include this excerpt: it shows how the statistical idea becomes a testable trading rule.

## Planned technical graphs

1. Graph type: spread time series with the pre-trade mean, two-standard-deviation band, and trade date.
   - Source: generate from the repository’s adjusted-price parquet file and freeze the plotted sample under `blog/data/`.
   - Expected takeaway: the post-trade spread migrated far outside the calibration regime.
2. Graph type: period-by-period hedge ratio, coefficient of determination, and spread volatility comparison.
   - Source: generate from the same frozen sample.
   - Expected takeaway: the hedge ratio changed from positive to negative and fit quality weakened.
3. Graph type: historical backtest equity curve with completed-trade marks.
   - Source: reproduce the project’s 60-day rolling z-score strategy from the frozen sample.
   - Expected takeaway: 21 completed trades reduced the account from $100,000 to about $65,986 before costs.

## Risks, gaps, and assumptions

- Data gaps: the project uses adjusted daily close data and has no intraday execution data, bid-ask spreads, borrow fees, dividends on the short leg, market impact, or financing constraints.
- Assumptions: prices are treated as the variables in the long-run regression; the 20-year hedge ratio is used unchanged in the backtest; the Monte Carlo model fixes a 10-trading-day half-life; historical bootstrap returns are sampled independently.
- Validation checks to run before final draft: run `uv run statarb-pipeline --smoke`; regenerate all blog charts; compare computed trade count, total profit and loss, period betas, and spread volatilities with pipeline output; run the skill validator on both Markdown files; verify all image paths.
- Canonical workspace: `/home/ai4000/projects/one-time-projects/statarb-cointegration/blog/`.
- Deployment note: the normal publish bundle would be `~/projects/website/content/post/statarb-cointegration/`, but the user explicitly deferred publishing. No website files, Hugo build, website commit, or website push will occur in this task.

## Outline review

- Evidence coverage: the plan includes the method, simulation, backtest, failure diagnosis, and limitations; it does not rely on a simulated success narrative.
- Mathematical coverage: every planned symbol is defined, and the Ornstein-Uhlenbeck allocation identity is included because it is specific to this implementation.
- Graph coverage: all three technical graphs answer different questions and are reproducible from one frozen input sample.
- Scope check: all authored and generated materials remain under `blog/`; the project source and website repository remain untouched.

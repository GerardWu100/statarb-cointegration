---
title: "When a Cointegration Trade Fails Its Own Test"
description: "A causal KO-PEP pairs backtest with formal residual testing, beta-consistent holdings, explicit costs, and daily mark-to-market accounting."
date: 2026-07-13
image: images/cover-cointegration-regime-break.png
categories: ["Quantitative Research", "Risk Management"]
---

# When a Cointegration Trade Fails Its Own Test

Coca-Cola and Pepsi look like a natural pair. Their businesses share customers, inputs, and broad consumer cycles. Their stock prices also produced an ordinary least-squares regression with $R^2=0.960$ over 5,000 trading days. The first version of this project mistook that close fit for evidence of cointegration and built a mean-reversion trade around it.

The formal test says otherwise. On the frozen training sample, the Engle-Granger test has a p-value of 0.225. At the usual 5% significance level, the residual fails to reject a unit root. A corrected historical backtest is still useful as a diagnostic, but it is not evidence for a deployable cointegration strategy.

I rebuilt the research path around that distinction. The new version freezes the regression before the test period and normalizes each residual with lagged data. It sizes the holdings from the same hedge ratio as the signal, charges trading and carrying costs, and marks the account every day. The result is hard to excuse. 13 completed trades lose $34,869 before costs and $46,228 after costs. The account ends at $53,772 from $100,000 of starting capital.

## What cointegration claims

Let $P^{KO}_t$ be Coca-Cola's adjusted closing price in US dollars per share on trading day $t$. Let $P^{PEP}_t$ be Pepsi's adjusted closing price in the same units. The training regression is

$$
P^{KO}_t = \alpha + \beta P^{PEP}_t + \varepsilon_t,
$$

where $\alpha$ is an intercept in US dollars, $\beta$ is the number of PEP shares hedged per KO share, and $\varepsilon_t$ is the residual in US dollars per KO share. Solving for the residual gives the linear combination the strategy claims will revert:

$$
\varepsilon_t=P^{KO}_t-\alpha-\beta P^{PEP}_t.
$$

The fitted values are $\alpha=4.573$ and $\beta=0.3345$. The intercept changes the residual's level but not the profit and loss of a self-financing trade because $\Delta\alpha=0$.

A high $R^2$ only says the two price levels moved together in the training sample. Cointegration requires $\varepsilon_t$ to be stationary, meaning its probability distribution does not keep drifting with time. A common diagnostic is the Augmented Dickey-Fuller (ADF) regression

$$
\Delta\varepsilon_t = \rho\varepsilon_{t-1} + \sum_{i=1}^{p}\gamma_i\Delta\varepsilon_{t-i}+u_t,
$$

where $\Delta\varepsilon_t=\varepsilon_t-\varepsilon_{t-1}$ is the one-day residual change, $p$ is the number of lagged changes, $\gamma_i$ are nuisance coefficients, and $u_t$ is an unpredictable error. The null hypothesis is $\rho=0$, which implies a unit root. The stationary alternative is $\rho<0$.

The ordinary ADF test gives a statistic of -2.630 and a p-value of 0.087. Because this residual was estimated rather than observed, the Engle-Granger test uses the appropriate MacKinnon distribution. It returns a statistic of -2.631 and a p-value of 0.225. Neither rejects the unit-root null at 5%.

| Training diagnostic | Value | 5% decision |
|---|---:|---|
| Price-regression $R^2$ | 0.960 | Not a stationarity test |
| ADF residual p-value | 0.087 | Do not reject a unit root |
| Engle-Granger p-value | 0.225 | Do not reject no cointegration |

The research code reports this failed prerequisite rather than hiding it:

```python
adf_statistic, adf_pvalue, *_ = adfuller(residual, regression="c", autolag="AIC")
eg_statistic, eg_pvalue, _ = coint(y, x, trend="c", autolag="aic")
```

The second call is the formal residual-based cointegration test. The first remains useful because it exposes the underlying autoregressive test directly.

## A causal signal

Let $L=60$ be the rolling window. The mean used at close $t$ includes residuals through $t-1$ only:

$$
\bar\varepsilon_{t,L}=\frac{1}{L}\sum_{j=1}^{L}\varepsilon_{t-j}.
$$

Its sample standard deviation is

$$
s_{t,L}=\sqrt{\frac{1}{L-1}\sum_{j=1}^{L}
(\varepsilon_{t-j}-\bar\varepsilon_{t,L})^2}.
$$

The signal is therefore

$$
z_t=\frac{\varepsilon_t-\bar\varepsilon_{t,L}}{s_{t,L}}.
$$

The shift by one day matters. If today's residual were included in its own mean and standard deviation, the threshold would partly adapt to the observation that triggers the trade. The implementation makes the timing visible:

```python
residual = prices["KO"] - fit.alpha_usd - fit.beta * prices["PEP"]
lagged = residual.shift(1)
rolling_mean = lagged.rolling(rolling_window).mean()
rolling_std = lagged.rolling(rolling_window).std(ddof=1)
z_score = (residual - rolling_mean) / rolling_std
```

A signal observed at close $t$ sets the holdings after that close. Those holdings earn the price changes from $t$ to $t+1$. No position receives a price move that occurred before its signal existed.

The strategy enters a long residual for $-2.5<z_t\leq-1.5$ and a short residual for $1.5\leq z_t<2.5$. It exits when $|z_t|\leq0.2$, stops when $|z_t|\geq2.5$, and closes any remaining position at the sample end. A flat strategy does not open a new trade beyond the stop boundary.

![Fixed KO-PEP residual and lagged entry band](images/01_spread_regime_shift.png)

The residual's post-2023 rise is not a sequence of isolated threshold touches. Its level migrated. A rolling z-score can normalize that drift, but normalization cannot turn a non-stationary relation into a stationary one.

## Making the holdings match the equation

The old portfolio used approximately equal dollar legs even though its signal was $P^{KO}_t-\beta P^{PEP}_t$. Those are different portfolios. The corrected holdings replicate the fitted residual.

Let $s_t\in\{-1,0,1\}$ denote short, flat, or long residual. Let $q_t>0$ be the base number of KO shares. The holdings after close $t$ are

$$
q^{KO}_t=s_tq_t,
$$

$$
q^{PEP}_t=-s_t\beta q_t.
$$

Their one-day gross profit and loss is

$$
\Pi^{gross}_{t+1}=q^{KO}_t\Delta P^{KO}_{t+1}
+q^{PEP}_t\Delta P^{PEP}_{t+1}.
$$

Substituting the holdings gives

$$
\Pi^{gross}_{t+1}=s_tq_t
(\Delta P^{KO}_{t+1}-\beta\Delta P^{PEP}_{t+1})
=s_tq_t\Delta\varepsilon_{t+1}.
$$

Now the traded profit and loss is exactly the change in the modeled residual, scaled by $s_tq_t$. The hedge sign is explicit: a long residual buys KO and shorts $\beta$ PEP shares for each KO share when $\beta>0$.

At each entry, the target gross exposure is $G=2C_0$, where $C_0=$100{,}000$ is initial capital. The scale is

$$
q_t=\frac{G}{P^{KO}_t+|\beta|P^{PEP}_t}.
$$

This produces 200% gross exposure while preserving the regression hedge ratio. It does not guarantee market beta neutrality, sector neutrality, or dollar neutrality. Those are separate constraints and would require a different construction.

## Costs and daily marking

The backtest charges 5 basis points (bps) per dollar of one-way turnover. One basis point is 0.01%, so 5 bps is 0.05%. If $c=5/10{,}000$ and $\Delta q^i_t$ is the change in shares of asset $i$, transaction cost is

$$
C^{trade}_t=c\sum_i|\Delta q^i_t|P^i_t.
$$

Short market value incurs a 1% annual borrow rate. Long market value incurs a 5% annual financing rate. With $252$ trading days per year,

$$
C^{carry}_t=\frac{0.01\,V^{short}_{t-1}+0.05\,V^{long}_{t-1}}{252},
$$

where $V^{short}_{t-1}$ and $V^{long}_{t-1}$ are positive dollar market values at the prior close. These are simplified assumptions. Actual prime-broker terms, dividends owed on short stock, locate availability, bid-ask spreads, and market impact can all change the bill.

Net daily profit and loss is

$$
\Pi^{net}_t=\Pi^{gross}_t-C^{trade}_t-C^{carry}_t,
$$

and daily marked equity follows

$$
E_t=E_{t-1}+\Pi^{net}_t.
$$

This accounting records open-trade gains and losses every day. The former completed-trade curve could not measure the path between exits, so it could not support a proper drawdown or margin analysis.

## Corrected result

The test uses 494 daily closes from October 11, 2023 through September 30, 2025. All regression coefficients are frozen using the preceding 5,000 observations.

| Metric | Corrected value |
|---|---:|
| Completed trades | 13 |
| Profitable trades | 30.8% |
| Gross profit and loss | -\$34,869 |
| Transaction costs | \$2,613 |
| Short-borrow costs | \$1,580 |
| Long-financing costs | \$7,167 |
| Total costs | \$11,359 |
| Net profit and loss | -\$46,228 |
| Total return | -46.23% |
| Annualized daily Sharpe ratio | -1.77 |
| Maximum daily drawdown | -47.31% |

The annualized Sharpe ratio is the mean daily net return divided by its sample standard deviation, multiplied by $\sqrt{252}$. No risk-free-rate subtraction is applied because the financing charge is already explicit in daily profit and loss.

![Daily gross and net equity with drawdown](images/03_backtest_equity.png)

Costs explain $11,359 of the loss, but they do not rescue the strategy. Gross trading profit and loss was already -$34,869. Financing dominates the cost model because the strategy spends long periods holding roughly 200% gross exposure.

The corrected version completes 13 trades rather than the earlier 21. Three changes drive that difference: holdings now follow the fitted $\beta$, the entry rule refuses to initiate beyond the stop threshold, and positions are evaluated with one causal state machine instead of completed-trade bookkeeping.

## The relation was unstable as well as non-stationary

Refitting the regression by period is not part of the trading rule. It is a post-mortem stability check.

![Regression stability across samples](images/02_parameter_drift.png)

The three panels agree. The fitted slope did not persist, explanatory power fell sharply, and the residual became much more volatile during the test.

| Sample | $\beta$ | $R^2$ | Residual volatility |
|---|---:|---:|---:|
| 5,000-day training sample | 0.335 | 0.960 | \$2.72 |
| Prior two years | 0.198 | 0.436 | \$2.14 |
| Backtest period | -0.216 | 0.197 | \$5.09 |

The hedge ratio changes sign in the test period, the regression fit collapses, and residual volatility nearly doubles relative to the long training sample. This table uses future test-period data for diagnosis only. Feeding those estimates back into earlier trades would be lookahead bias.

## What the result does and does not establish

This study establishes that the original KO-PEP specification did not pass its stated statistical premise and lost money under consistent historical accounting. It does not establish that KO and PEP can never support a relative-value trade. Another specification might use log prices, a shorter estimation window, corporate fundamentals, market and sector factor hedges, or a time-varying coefficient. Each alternative creates a new hypothesis that needs its own untouched test sample.

Adjusted closes are also an imperfect execution proxy. They incorporate split and dividend adjustments into historical prices, while a live short position pays dividends in cash and trades at unadjusted market prices. A production backtest should use point-in-time corporate actions, executable bid and ask prices, borrow availability, and a broker-specific financing model.

I would stop at the failed Engle-Granger test. The diagnostic backtest remains in the project because it prices the decision to ignore that result. The high $R^2$ was real. It answered the wrong question.

## References

- Robert F. Engle and Clive W. J. Granger, [“Co-integration and Error Correction: Representation, Estimation, and Testing”](https://doi.org/10.2307/1913236), *Econometrica*, 1987.
- David A. Dickey and Wayne A. Fuller, [“Distribution of the Estimators for Autoregressive Time Series With a Unit Root”](https://doi.org/10.1080/01621459.1979.10482531), *Journal of the American Statistical Association*, 1979.
- James G. MacKinnon, [“Critical Values for Cointegration Tests”](http://qed.econ.queensu.ca/working_papers/papers/qed_wp_1227.pdf), Queen's Economics Department Working Paper 1227, 2010.
- Evan Gatev, William N. Goetzmann, and K. Geert Rouwenhorst, [“Pairs Trading: Performance of a Relative-Value Arbitrage Rule”](https://doi.org/10.1093/rfs/hhj020), *Review of Financial Studies*, 2006.
- statsmodels developers, [`coint` Engle-Granger test documentation](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html), version 0.14.6 interface used by this project.

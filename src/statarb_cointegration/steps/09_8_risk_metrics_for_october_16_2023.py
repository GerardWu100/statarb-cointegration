"""Notebook section: 8 risk metrics for october 16 2023."""

# Day 7 risk metrics: reuse one percentile pass for prints and downstream steps.
day_7_returns = day_7_pnl / initial_portfolio_value

expected_pnl_day7 = day_7_pnl.mean()
pnl_std_day7 = day_7_pnl.std()
expected_return_day7 = day_7_returns.mean()
return_std_day7 = day_7_returns.std()

pnl_percentiles = {p: np.percentile(day_7_pnl, p) for p in (1, 5, 25, 50, 75, 95, 99)}
percentile_5_day7 = pnl_percentiles[5]
percentile_95_day7 = pnl_percentiles[95]
# VaR/CVaR use the loss convention: positive numbers mean potential loss.
var_95_day7 = -percentile_5_day7
cvar_95_day7 = -day_7_pnl[day_7_pnl <= percentile_5_day7].mean()

prob_profit_day7 = (day_7_pnl > 0).mean()

print("=" * 70)
print("OCTOBER 16, 2023 (DAY 7) - RISK ANALYSIS")
print("=" * 70)
print(f"\nExpected P&L:      ${expected_pnl_day7:,.2f} ({expected_return_day7:.2%})")
print(f"P&L Std Dev:       ${pnl_std_day7:,.2f} ({return_std_day7:.2%})")
print(f"Probability Profit: {prob_profit_day7:.2%}")

print(f"\nRisk Metrics (Loss Convention - Positive = Loss):")
print(f"  VaR 95% (5th %ile):  ${var_95_day7:,.2f}")
print(f"  CVaR 95%:            ${cvar_95_day7:,.2f}")

print(f"\nP&L Distribution Percentiles:")
for label, suffix in ((1, 'st'), (5, 'th'), (25, 'th'), (50, 'th'), (75, 'th'), (95, 'th'), (99, 'th')):
    pnl_at_pct = pnl_percentiles[label]
    print(f"  {label}{suffix}: ${pnl_at_pct:>10,.2f} ({pnl_at_pct / initial_portfolio_value:>6.2%})")

print(f"\n90% Confidence Interval: [${percentile_5_day7:,.2f}, ${percentile_95_day7:,.2f}]")

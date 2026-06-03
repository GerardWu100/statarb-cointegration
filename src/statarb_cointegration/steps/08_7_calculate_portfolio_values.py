"""Notebook section: 7 calculate portfolio values."""

# Calculate portfolio values over 60 days
cash_values = np.zeros((n_paths, n_days + 1))
cash_values[:, 0] = cash_position

# Cash grows at risk-free rate
for day in range(1, n_days + 1):
    cash_values[:, day] = cash_values[:, day - 1] * (1 + risk_free_rate_daily)

# Portfolio value = cash + long positions - short positions
# We are LONG PEP and SHORT KO
pep_position_values = pep_shares * pep_prices      # Long position (positive)
ko_position_values = ko_shares * ko_prices         # Short position (subtract this)
portfolio_values = cash_values + pep_position_values - ko_position_values
pnl = portfolio_values - initial_portfolio_value   # P&L relative to initial $100k

# Focus on Day 7 (October 16, 2023) - 5 trading days after entry
day_7_index = 5
day_7_pnl = pnl[:, day_7_index]
day_7_portfolio_values = portfolio_values[:, day_7_index]

print("=" * 70)
print("DAY 7 (OCTOBER 16, 2023) - SIMULATION RESULTS")
print("=" * 70)
print(f"\nPortfolio Statistics:")
print(f"  Mean Value:   ${day_7_portfolio_values.mean():,.2f}")
print(f"  Median Value: ${np.median(day_7_portfolio_values):,.2f}")
print(f"  Range:        [${day_7_portfolio_values.min():,.2f}, ${day_7_portfolio_values.max():,.2f}]")
print(f"\nP&L Statistics:")
print(f"  Mean P&L:     ${day_7_pnl.mean():,.2f}")
print(f"  Median P&L:   ${np.median(day_7_pnl):,.2f}")
print(f"  Std Dev:      ${day_7_pnl.std():,.2f}")
print("=" * 70)

"""Notebook section: 10 entry and exit strategy for pairs trading."""

# Entry/Exit Strategy Analysis - 60-Day Rolling Window

# Calculate spread from historical data
spread_historical = historical_data['KO'] - beta * historical_data['PEP']

# Use 60-day rolling window for adaptive strategy
rolling_window = 60
spread_rolling_mean = spread_historical.rolling(window=rolling_window).mean()
spread_rolling_std = spread_historical.rolling(window=rolling_window).std()

# Get rolling statistics at trade date (last day before Oct 9)
spread_mean_rolling = spread_rolling_mean.iloc[-1]
spread_std_rolling = spread_rolling_std.iloc[-1]

# Calculate current spread and z-score
current_spread_oct9 = ko_price_trade - beta * pep_price_trade
z_score_oct9_rolling = (current_spread_oct9 - spread_mean_rolling) / spread_std_rolling

# Define entry and exit thresholds (±2σ for entry, mean for exit)
entry_threshold_short_ko = spread_mean_rolling + 2.0 * spread_std_rolling  # SHORT KO / LONG PEP
entry_threshold_long_ko = spread_mean_rolling - 2.0 * spread_std_rolling   # LONG KO / SHORT PEP
exit_threshold_mean = spread_mean_rolling  # Exit at mean reversion
stop_loss_threshold = spread_mean_rolling + 3.0 * spread_std_rolling  # Stop loss at ±3σ

print("=" * 80)
print("ENTRY/EXIT STRATEGY - 60-DAY ROLLING WINDOW")
print("=" * 80)

print(f"\nRolling Statistics (60 days):")
print(f"  Mean Spread:  ${spread_mean_rolling:.4f}")
print(f"  Std Dev:      ${spread_std_rolling:.4f}")

print(f"\nCurrent Position (Oct 9, 2023):")
print(f"  Spread:       ${current_spread_oct9:.4f}")
print(f"  Z-score:      {z_score_oct9_rolling:.2f}σ")
print(f"  Position:     SHORT KO / LONG PEP")

print(f"\nEntry Thresholds:")
print(f"  SHORT KO / LONG PEP when:  St > ${entry_threshold_short_ko:.4f} (+2σ)")
print(f"  LONG KO / SHORT PEP when:  St < ${entry_threshold_long_ko:.4f} (-2σ)")

print(f"\nExit Thresholds:")
print(f"  Target (mean reversion):   St ≈ ${exit_threshold_mean:.4f}")
print(f"  Stop Loss:                 St < ${spread_mean_rolling - 3*spread_std_rolling:.4f} or > ${stop_loss_threshold:.4f} (±3σ)")


# Analyze simulated exit performance - vectorized for speed
spread_simulated = ko_prices - beta * pep_prices

# Vectorized approach: find first crossing for each path
if current_spread_oct9 < spread_mean_rolling:
    # Long position: waiting for spread to rise to mean
    crosses_mean = spread_simulated >= exit_threshold_mean
else:
    # Short position: waiting for spread to fall to mean
    crosses_mean = spread_simulated <= exit_threshold_mean

# First crossing day per path; paths that never cross keep the horizon length.
first_cross_day = crosses_mean.argmax(axis=1)
crossed_mean = crosses_mean[np.arange(n_paths), first_cross_day]
mean_reversion_day = np.where(crossed_mean, first_cross_day, n_days)

pct_exited = (mean_reversion_day < n_days).mean()

print(f"\nSimulation Results:")
print(f"  Paths hitting exit target:  {pct_exited:.1%}")
if pct_exited > 0:
    print(f"  Avg days to exit:           {mean_reversion_day[mean_reversion_day < n_days].mean():.1f} days")

    # P&L at exit
    exit_mask = mean_reversion_day < n_days
    exit_days = mean_reversion_day[exit_mask].astype(int)
    exit_pnl = pnl[exit_mask, exit_days]
    print(f"\n  P&L at exit (mean):         ${exit_pnl.mean():,.2f}")
    print(f"  P&L at exit (5th-95th):     [${np.percentile(exit_pnl, 5):,.2f}, ${np.percentile(exit_pnl, 95):,.2f}]")

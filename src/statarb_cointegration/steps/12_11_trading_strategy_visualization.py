"""Notebook section: 11 trading strategy visualization."""

# Visualize Trading Strategy
fig = plt.figure(figsize=(16, 8))

# 1. Historical Spread with Entry/Exit Thresholds
ax1 = plt.subplot(2, 1, 1)
# Plot last 252 trading days (1 year)
recent_historical = spread_historical.tail(252)
plt.plot(recent_historical.index, recent_historical.values, 
         linewidth=1, color='blue', label='Spread (KO - β*PEP)')

# Rolling mean and bands
recent_rolling_mean = spread_rolling_mean.tail(252)
recent_rolling_std = spread_rolling_std.tail(252)

plt.plot(recent_rolling_mean.index, recent_rolling_mean.values, 
         color='green', linestyle='--', linewidth=2, label='60-day Rolling Mean')
plt.fill_between(recent_rolling_mean.index, 
                 recent_rolling_mean - 2*recent_rolling_std,
                 recent_rolling_mean + 2*recent_rolling_std,
                 alpha=0.2, color='yellow', label='±2σ Entry Zone')
plt.fill_between(recent_rolling_mean.index, 
                 recent_rolling_mean - 3*recent_rolling_std,
                 recent_rolling_mean + 3*recent_rolling_std,
                 alpha=0.1, color='red', label='±3σ Stop Loss Zone')

# Mark current position - convert trade_date string to datetime
trade_date_dt = pd.to_datetime(trade_date)
plt.scatter(trade_date_dt, current_spread_oct9, color='red', s=200, zorder=5, 
           marker='o', edgecolors='black', linewidths=2, label=f'Oct 9 Entry: ${current_spread_oct9:.2f}')

plt.title('Historical Spread with Entry/Exit Thresholds (Last 252 Days)', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('Spread ($)')
plt.legend(loc='best')
plt.grid(True, alpha=0.3)

# 2. Simulated Spread Paths with Thresholds
ax2 = plt.subplot(2, 1, 2)
n_sample_strategy = 50
sample_strategy_idx = np.random.choice(n_paths, n_sample_strategy, replace=False)
days_strategy = np.arange(n_days + 1)

for idx in sample_strategy_idx:
    plt.plot(days_strategy, spread_simulated[idx, :], alpha=0.2, linewidth=0.5, color='purple')

plt.plot(days_strategy, spread_simulated.mean(axis=0), color='darkviolet', 
         linewidth=2, label='Mean Simulated Spread')

# Entry/Exit thresholds
plt.axhline(y=exit_threshold_mean, color='green', linestyle='--', linewidth=2, 
           label=f'Exit Target: ${exit_threshold_mean:.2f}')
plt.axhline(y=entry_threshold_short_ko, color='orange', linestyle='--', linewidth=1.5, 
           label=f'Entry (+2σ): ${entry_threshold_short_ko:.2f}')
plt.axhline(y=entry_threshold_long_ko, color='orange', linestyle='--', linewidth=1.5, 
           label=f'Entry (-2σ): ${entry_threshold_long_ko:.2f}')
plt.axhline(y=stop_loss_threshold, color='red', linestyle='--', linewidth=1.5, 
           label=f'Stop Loss (+3σ): ${stop_loss_threshold:.2f}')
plt.axhline(y=spread_mean_rolling - 3*spread_std_rolling, color='red', linestyle='--', 
           linewidth=1.5, label=f'Stop Loss (-3σ): ${spread_mean_rolling - 3*spread_std_rolling:.2f}')

# Mark Day 7
plt.axvline(x=day_7_index, color='darkgreen', linestyle='--', linewidth=2, alpha=0.7, 
           label='Day 7 (Oct 16)')

plt.title('Simulated Spread Evolution with Entry/Exit Strategy', fontsize=14, fontweight='bold')
plt.xlabel('Trading Days')
plt.ylabel('Spread ($)')
plt.legend(loc='best', fontsize=9)
plt.grid(True, alpha=0.3)
plt.xlim(0, 30)  # Focus on first 30 days

plt.tight_layout()
plt.show()

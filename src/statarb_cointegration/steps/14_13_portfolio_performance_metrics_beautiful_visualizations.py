"""Notebook section: 13 portfolio performance metrics beautiful visualizations."""

# Beautiful Portfolio Analysis Visualizations
from matplotlib.gridspec import GridSpec

fig = plt.figure(figsize=(20, 10))
gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)

# Custom color palette
colors_palette = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']

# 1. Portfolio Value Fan Chart (Confidence Intervals)
ax1 = fig.add_subplot(gs[0, :2])
days_fan = min(30, n_days)
days_array = np.arange(days_fan + 1)

percentiles = [1, 5, 25, 50, 75, 95, 99]
percentile_values = np.zeros((len(percentiles), days_fan + 1))
for i, p in enumerate(percentiles):
    percentile_values[i, :] = np.percentile(portfolio_values[:, :days_fan+1], p, axis=0)

# Plot confidence bands
ax1.fill_between(days_array, percentile_values[0, :], percentile_values[6, :], 
                alpha=0.15, color=colors_palette[0], label='1st-99th %ile')
ax1.fill_between(days_array, percentile_values[1, :], percentile_values[5, :], 
                alpha=0.25, color=colors_palette[1], label='5th-95th %ile')
ax1.fill_between(days_array, percentile_values[2, :], percentile_values[4, :], 
                alpha=0.4, color=colors_palette[2], label='25th-75th %ile')
ax1.plot(days_array, percentile_values[3, :], linewidth=3, color='darkblue', 
        label='Median', zorder=10)
ax1.axhline(y=initial_portfolio_value, color='red', linestyle='--', linewidth=2, 
           label=f'Initial: ${initial_portfolio_value:,.0f}')
ax1.axvline(x=day_7_index, color='darkgreen', linestyle='--', linewidth=2, 
           alpha=0.7, label='Day 7 (Oct 16)')

ax1.set_xlabel('Trading Days', fontsize=11)
ax1.set_ylabel('Portfolio Value ($)', fontsize=11)
ax1.set_title('Portfolio Value Evolution with Confidence Intervals', 
             fontsize=14, fontweight='bold', pad=15)
ax1.legend(loc='best', fontsize=9)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

# 2. Sharpe Ratio Evolution
ax2 = fig.add_subplot(gs[0, 2])
days_sharpe = min(30, n_days)
sharpe_ratios = np.zeros(days_sharpe + 1)
for day in range(1, days_sharpe + 1):
    returns_day = (portfolio_values[:, day] - initial_portfolio_value) / initial_portfolio_value
    sharpe_ratios[day] = returns_day.mean() / returns_day.std() * np.sqrt(252 / day)

sharpe_ratios[0] = 0  # No Sharpe ratio at day 0

ax2.plot(np.arange(days_sharpe + 1), sharpe_ratios, linewidth=2.5, 
        color=colors_palette[3], marker='o', markersize=4)
ax2.axvline(x=day_7_index, color='darkgreen', linestyle='--', linewidth=2, 
           alpha=0.7, label='Day 7')
ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax2.set_xlabel('Trading Days', fontsize=11)
ax2.set_ylabel('Annualized Sharpe Ratio', fontsize=11)
ax2.set_title('Sharpe Ratio Evolution', fontsize=13, fontweight='bold', pad=15)
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, linestyle='--')

# 3. Probability of Profit Over Time
ax3 = fig.add_subplot(gs[1, 0])
days_prob = min(30, n_days)
prob_profit = np.zeros(days_prob + 1)
for day in range(days_prob + 1):
    prob_profit[day] = (pnl[:, day] > 0).mean() * 100

ax3.plot(np.arange(days_prob + 1), prob_profit, linewidth=2.5, 
        color=colors_palette[4], marker='s', markersize=4)
ax3.axvline(x=day_7_index, color='darkgreen', linestyle='--', linewidth=2, 
           alpha=0.7, label='Day 7')
ax3.axhline(y=50, color='red', linestyle='--', linewidth=1, alpha=0.7, label='50%')
ax3.fill_between(np.arange(days_prob + 1), 50, prob_profit, 
                where=(prob_profit >= 50), alpha=0.3, color='green', 
                interpolate=True, label='Above 50%')
ax3.fill_between(np.arange(days_prob + 1), prob_profit, 50, 
                where=(prob_profit < 50), alpha=0.3, color='red', 
                interpolate=True, label='Below 50%')
ax3.set_xlabel('Trading Days', fontsize=11)
ax3.set_ylabel('Probability (%)', fontsize=11)
ax3.set_title('Probability of Profit Over Time', fontsize=13, fontweight='bold', pad=15)
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.set_ylim([0, 105])

# 4. Expected Return vs Risk (Return-Risk Scatter)
ax4 = fig.add_subplot(gs[1, 1])
days_scatter = [1, 3, 5, 7, 10, 15, 20, 30]
days_scatter = [d for d in days_scatter if d <= n_days]
expected_returns = []
risk_std = []

for day in days_scatter:
    returns_day = (portfolio_values[:, day] - initial_portfolio_value) / initial_portfolio_value
    expected_returns.append(returns_day.mean() * 100)
    risk_std.append(returns_day.std() * 100)

scatter = ax4.scatter(risk_std, expected_returns, s=200, c=days_scatter, 
                     cmap='viridis', edgecolors='black', linewidths=2, alpha=0.8)

# Annotate day 7
day_7_idx = days_scatter.index(day_7_index) if day_7_index in days_scatter else None
if day_7_idx is not None:
    ax4.annotate(f'Day {day_7_index}', 
                xy=(risk_std[day_7_idx], expected_returns[day_7_idx]),
                xytext=(10, 10), textcoords='offset points',
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', lw=2))

ax4.set_xlabel('Risk (Std Dev %)', fontsize=11)
ax4.set_ylabel('Expected Return (%)', fontsize=11)
ax4.set_title('Risk-Return Trade-off', fontsize=13, fontweight='bold', pad=15)
ax4.grid(True, alpha=0.3, linestyle='--')
cbar = plt.colorbar(scatter, ax=ax4)
cbar.set_label('Trading Day', rotation=270, labelpad=20)

# 5. Maximum Drawdown Over Time
ax5 = fig.add_subplot(gs[1, 2])
days_dd = min(30, n_days)
max_drawdown = np.zeros(days_dd + 1)

for day in range(days_dd + 1):
    portfolio_cummax = np.maximum.accumulate(portfolio_values[:, :day+1], axis=1)
    drawdown = (portfolio_values[:, :day+1] - portfolio_cummax) / portfolio_cummax
    max_drawdown[day] = drawdown.min() * 100

ax5.fill_between(np.arange(days_dd + 1), max_drawdown, 0, 
                alpha=0.5, color='crimson', label='Max Drawdown')
ax5.plot(np.arange(days_dd + 1), max_drawdown, linewidth=2.5, 
        color='darkred', marker='v', markersize=4)
ax5.axvline(x=day_7_index, color='darkgreen', linestyle='--', linewidth=2, 
           alpha=0.7, label='Day 7')
ax5.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax5.set_xlabel('Trading Days', fontsize=11)
ax5.set_ylabel('Maximum Drawdown (%)', fontsize=11)
ax5.set_title('Maximum Drawdown Evolution', fontsize=13, fontweight='bold', pad=15)
ax5.legend(fontsize=9)
ax5.grid(True, alpha=0.3, linestyle='--')

plt.suptitle('Comprehensive Portfolio Performance Analysis', 
            fontsize=16, fontweight='bold', y=0.995)
plt.show()

# Print Day 7 Performance Summary
print("\n" + "=" * 80)
print("DAY 7 PERFORMANCE SUMMARY")
print("=" * 80)
print(f"\nExpected Return:        {expected_return_day7:.2%}")
print(f"Volatility (Std Dev):   {return_std_day7:.2%}")
print(f"Sharpe Ratio (Ann.):    {sharpe_ratios[day_7_index]:.2f}")
print(f"Probability of Profit:  {prob_profit[day_7_index]:.1f}%")
print(f"Max Drawdown:           {max_drawdown[day_7_index]:.2f}%")
print(f"VaR 95%:                ${var_95_day7:,.2f}")
print(f"CVaR 95%:               ${cvar_95_day7:,.2f}")
print("=" * 80)

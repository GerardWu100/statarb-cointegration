"""Notebook section: 12 enhanced visualizations risk analysis."""

# Enhanced Risk Visualizations
plt.style.use('seaborn-v0_8-darkgrid')
fig = plt.figure(figsize=(20, 12))

# 1. Heatmap: P&L Distribution by Day
ax1 = plt.subplot(2, 3, 1)
days_heatmap = min(30, n_days)
pnl_percentiles = np.zeros((9, days_heatmap + 1))
percentile_levels = [1, 5, 10, 25, 50, 75, 90, 95, 99]
for i, p in enumerate(percentile_levels):
    pnl_percentiles[i, :] = np.percentile(pnl[:, :days_heatmap+1], p, axis=0)

im1 = ax1.imshow(pnl_percentiles, aspect='auto', cmap='RdYlGn', 
                 extent=[0, days_heatmap, 0, len(percentile_levels)])
ax1.set_yticks(np.arange(len(percentile_levels)) + 0.5)
ax1.set_yticklabels([f'{p}th' for p in percentile_levels])
ax1.set_xlabel('Trading Days')
ax1.set_ylabel('Percentile')
ax1.set_title('P&L Heatmap by Percentile', fontsize=12, fontweight='bold')
ax1.axvline(x=day_7_index, color='black', linestyle='--', linewidth=2, alpha=0.7)
cbar1 = plt.colorbar(im1, ax=ax1)
cbar1.set_label('P&L ($)', rotation=270, labelpad=20)

# 2. Day 7 P&L vs Returns Scatter with Density
ax2 = plt.subplot(2, 3, 2)
day_7_ko_returns = (ko_prices[:, day_7_index] - ko_price_trade) / ko_price_trade
day_7_pep_returns = (pep_prices[:, day_7_index] - pep_price_trade) / pep_price_trade

# Sample for visibility
sample_size = 5000
sample_idx = np.random.choice(n_paths, sample_size, replace=False)
scatter = ax2.scatter(day_7_ko_returns[sample_idx], day_7_pep_returns[sample_idx], 
                     c=day_7_pnl[sample_idx], cmap='RdYlGn', alpha=0.4, s=10, 
                     vmin=np.percentile(day_7_pnl, 5), vmax=np.percentile(day_7_pnl, 95))
ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax2.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax2.set_xlabel('KO Return (%)')
ax2.set_ylabel('PEP Return (%)')
ax2.set_title('Day 7: Stock Returns vs P&L', fontsize=12, fontweight='bold')
ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x*100:.1f}%'))
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y*100:.1f}%'))
cbar2 = plt.colorbar(scatter, ax=ax2)
cbar2.set_label('P&L ($)', rotation=270, labelpad=20)
ax2.grid(True, alpha=0.3)

# 3. Cumulative Portfolio Value Distribution (Day 7)
ax3 = plt.subplot(2, 3, 3)
sorted_portfolio = np.sort(day_7_portfolio_values)
cumulative_prob = np.arange(1, len(sorted_portfolio) + 1) / len(sorted_portfolio)
ax3.plot(sorted_portfolio, cumulative_prob * 100, linewidth=2, color='steelblue')
ax3.axvline(x=initial_portfolio_value, color='red', linestyle='--', linewidth=2, label='Break-even')
ax3.axvline(x=day_7_portfolio_values.mean(), color='green', linestyle='--', linewidth=2, 
           label=f'Mean: ${day_7_portfolio_values.mean():,.0f}')
ax3.axhline(y=5, color='orange', linestyle='--', linewidth=1, alpha=0.7)
ax3.axhline(y=95, color='purple', linestyle='--', linewidth=1, alpha=0.7)
ax3.fill_betweenx([0, 100], np.percentile(day_7_portfolio_values, 5), 
                  np.percentile(day_7_portfolio_values, 95), alpha=0.2, color='yellow')
ax3.set_xlabel('Portfolio Value ($)')
ax3.set_ylabel('Cumulative Probability (%)')
ax3.set_title('Day 7: Cumulative Portfolio Value Distribution', fontsize=12, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# 4. Correlation Dynamics Over Time
ax4 = plt.subplot(2, 3, 4)
days_corr = min(30, n_days)
rolling_corr = np.zeros(days_corr + 1)
for day in range(days_corr + 1):
    ko_returns_day = (ko_prices[:, day] - ko_price_trade) / ko_price_trade
    pep_returns_day = (pep_prices[:, day] - pep_price_trade) / pep_price_trade
    rolling_corr[day] = np.corrcoef(ko_returns_day, pep_returns_day)[0, 1]

ax4.plot(np.arange(days_corr + 1), rolling_corr, linewidth=2, color='darkblue', marker='o', markersize=4)
ax4.axhline(y=correlation, color='red', linestyle='--', linewidth=2, label=f'Historical: {correlation:.3f}')
ax4.axvline(x=day_7_index, color='green', linestyle='--', linewidth=2, alpha=0.7, label='Day 7')
ax4.set_xlabel('Trading Days')
ax4.set_ylabel('Correlation (KO, PEP)')
ax4.set_title('Return Correlation Evolution', fontsize=12, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)
ax4.set_ylim([0.5, 0.9])

# 5. Spread Distribution Evolution
ax5 = plt.subplot(2, 3, 5)
spread_days = [0, 1, 3, 5, 7, 14, 30]
spread_days = [d for d in spread_days if d <= n_days]
colors_spread = plt.cm.viridis(np.linspace(0, 1, len(spread_days)))

for i, day in enumerate(spread_days):
    spread_day = ko_prices[:, day] - beta * pep_prices[:, day]
    ax5.hist(spread_day, bins=80, alpha=0.4, color=colors_spread[i], 
            label=f'Day {day}', density=True, edgecolor='black', linewidth=0.5)

ax5.axvline(x=spread_mean, color='red', linestyle='--', linewidth=2, label='Long-term Mean')
ax5.axvline(x=(ko_price_trade - beta * pep_price_trade), color='orange', 
           linestyle='--', linewidth=2, label='Initial Spread')
ax5.set_xlabel('Spread ($)')
ax5.set_ylabel('Density')
ax5.set_title('Spread Distribution Evolution', fontsize=12, fontweight='bold')
ax5.legend(fontsize=8, ncol=2)
ax5.grid(True, alpha=0.3)

# 6. VaR and CVaR Evolution
ax6 = plt.subplot(2, 3, 6)
days_var = min(30, n_days)
var_evolution = np.zeros(days_var + 1)
cvar_evolution = np.zeros(days_var + 1)
for day in range(days_var + 1):
    pnl_day = pnl[:, day]
    var_evolution[day] = -np.percentile(pnl_day, 5)  # VaR at 95% confidence
    cvar_evolution[day] = -pnl_day[pnl_day <= np.percentile(pnl_day, 5)].mean()

ax6.plot(np.arange(days_var + 1), var_evolution, linewidth=2, color='orange', 
        marker='o', markersize=3, label='VaR 95%')
ax6.plot(np.arange(days_var + 1), cvar_evolution, linewidth=2, color='red', 
        marker='s', markersize=3, label='CVaR 95%')
ax6.axvline(x=day_7_index, color='green', linestyle='--', linewidth=2, alpha=0.7, label='Day 7')
ax6.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax6.set_xlabel('Trading Days')
ax6.set_ylabel('Risk Measure ($)')
ax6.set_title('Risk Evolution: VaR & CVaR (95% Confidence)', fontsize=12, fontweight='bold')
ax6.legend(fontsize=9)
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

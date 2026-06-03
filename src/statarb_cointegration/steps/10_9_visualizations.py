"""Notebook section: 9 visualizations."""

# Improve spacing between the two plots
fig = plt.figure(figsize=(18, 6))

# 1. Day 7 portfolio value distribution (main focus)
day_7_value_percentiles = np.percentile(day_7_portfolio_values, [5, 95])
ax4 = fig.add_subplot(1, 2, 1)
ax4.hist(day_7_portfolio_values, bins=100, alpha=0.7, color='steelblue', edgecolor='black', density=True)
ax4.axvline(x=initial_portfolio_value, color='red', linestyle='--', linewidth=2, label='Break-even')
ax4.axvline(x=day_7_portfolio_values.mean(), color='green', linestyle='-', linewidth=2,
            label=f'Mean: ${day_7_portfolio_values.mean():,.0f}')
ax4.axvline(x=day_7_value_percentiles[0], color='orange', linestyle='--', linewidth=2,
            label=f'5th %ile: ${day_7_value_percentiles[0]:,.0f}')
ax4.axvline(x=day_7_value_percentiles[1], color='purple', linestyle='--', linewidth=2,
            label=f'95th %ile: ${day_7_value_percentiles[1]:,.0f}')
ax4.set_title('Day 7 Portfolio Value Distribution (October 16, 2023)', fontsize=12, fontweight='bold')
ax4.set_xlabel('Portfolio Value ($)')
ax4.set_ylabel('Density')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

# 2. P&L evolution (show first 7 days)
ax5 = fig.add_subplot(1, 2, 2)
days_to_show_7 = 7
days_axis_7 = np.arange(days_to_show_7 + 1)
percentiles_to_plot = [5, 25, 50, 75, 95]
colors = ['red', 'orange', 'green', 'blue', 'purple']
for p, color in zip(percentiles_to_plot, colors):
    portfolio_percentile = np.percentile(portfolio_values[:, :days_to_show_7+1], p, axis=0)
    ax5.plot(days_axis_7, portfolio_percentile, label=f'{p}th %ile', color=color, linewidth=2)

ax5.axhline(y=initial_portfolio_value, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Break-even')
ax5.set_title('Portfolio Value Evolution - Percentiles (first 7 days)', fontsize=12, fontweight='bold')
ax5.set_xlabel('Trading Days')
ax5.set_ylabel('Portfolio Value ($)')
ax5.legend()
ax5.grid(True, alpha=0.3)

# Increase horizontal spacing between subplots
fig.subplots_adjust(wspace=0.45)
plt.show()

# --- Notebook Cell Boundary ---

# Broader path visualizations over the full 60-day simulation horizon.
fig = plt.figure(figsize=(16, 12))
n_sample_paths = 100
sample_indices = np.random.choice(n_paths, n_sample_paths, replace=False)

# Show first 60 days (focusing on Day 7)
days_to_show = 60
days_axis = np.arange(days_to_show + 1)

# 1. Sample KO price paths (0 to Day 60, with Day 7 marker)
ax1 = plt.subplot(2, 2, 1)
for idx in sample_indices:
    plt.plot(days_axis, ko_prices[idx, :days_to_show+1], color='red', alpha=0.1, linewidth=0.5)
plt.plot(days_axis, ko_prices[sample_indices, :days_to_show+1].mean(axis=0), color='darkred', 
         linewidth=2, label='Mean Path')

plt.axvline(x=day_7_index, color='green', linestyle='--', linewidth=2, label='Day 7 (Oct 16)')
plt.title('KO Price Paths (100 samples)', fontsize=12, fontweight='bold')
plt.xlabel('Trading Days')
plt.ylabel('KO Price ($)')
plt.legend()
plt.grid(True, alpha=0.3)

# 2. Sample PEP price paths
ax2 = plt.subplot(2, 2, 2)
for idx in sample_indices:
    plt.plot(days_axis, pep_prices[idx, :days_to_show+1], color='blue', alpha=0.1, linewidth=0.5)
plt.plot(days_axis, pep_prices[sample_indices, :days_to_show+1].mean(axis=0), color='darkblue', 
         linewidth=2, label='Mean Path')
plt.axhline(y=pep_price_trade, color='black', linestyle='--', linewidth=1, label='Initial Price')
plt.axvline(x=day_7_index, color='green', linestyle='--', linewidth=2, label='Day 7 (Oct 16)')
plt.title('PEP Price Paths (100 samples)', fontsize=12, fontweight='bold')
plt.xlabel('Trading Days')
plt.ylabel('PEP Price ($)')
plt.legend()
plt.grid(True, alpha=0.3)

# 3. Portfolio value paths
ax3 = plt.subplot(2, 2, 3)
for idx in sample_indices:
    plt.plot(days_axis, portfolio_values[idx, :days_to_show+1], color='green', alpha=0.1, linewidth=0.5)

plt.axvline(x=day_7_index, color='orange', linestyle='--', linewidth=2, label='Day 7 (Oct 16)')
plt.title('Portfolio Value Paths (100 samples)', fontsize=12, fontweight='bold')
plt.xlabel('Trading Days')
plt.ylabel('Portfolio Value ($)')
plt.legend()
plt.grid(True, alpha=0.3)


# 4. Spread evolution with Day 7 marker
ax6 = plt.subplot(2, 2, 4)
spread_paths = ko_prices - beta * pep_prices
for idx in sample_indices[:50]:
    plt.plot(days_axis, spread_paths[idx, :days_to_show+1], alpha=0.2, linewidth=0.5, color='purple')
plt.plot(days_axis, spread_paths[:, :days_to_show+1].mean(axis=0), color='darkviolet', 
         linewidth=2, label='Mean Spread')
plt.axhline(y=spread_mean, color='green', linestyle='--', linewidth=2, label='Long-term Mean')
plt.axhline(y=(ko_price_trade - beta * pep_price_trade), color='red', linestyle='--', 
            linewidth=1, label='Initial Spread')
plt.axvline(x=day_7_index, color='orange', linestyle='--', linewidth=2, label='Day 7')
plt.title(f'Spread Evolution: KO - {beta:.3f}*PEP ', fontsize=12, fontweight='bold')
plt.xlabel('Trading Days')
plt.ylabel('Spread ($)')
plt.legend(fontsize=9)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

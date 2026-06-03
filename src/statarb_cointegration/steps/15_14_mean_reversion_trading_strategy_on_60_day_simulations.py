"""Notebook section: 14 mean reversion trading strategy on 60 day simulations."""

# Trading Strategy Implementation on 60-Day Simulations
print("=" * 80)
print("60-DAY SIMULATED TRADING STRATEGY")
print("=" * 80)


def spread_trade_pnl(side: int, entry_ko: float, entry_pep: float, exit_ko: float, exit_pep: float) -> float:
    """Return dollar P&L for one spread trade at fixed share counts.

    side == 1 is long spread (long KO, short PEP); side == -1 is short spread.
    """
    ko_move = (exit_ko - entry_ko) * ko_shares
    pep_move = (exit_pep - entry_pep) * pep_shares
    if side == 1:
        return ko_move - pep_move
    return -ko_move + pep_move


# Strategy parameters
strategy_entry_threshold = 1.5  # Entry when |z-score| > 1.5
strategy_exit_threshold = 0.2   # Exit when |z-score| < 0.2 (near mean)
strategy_stop_loss = 2.5        # Stop loss when |z-score| > 2.5

# Calculate z-scores for all simulated paths
spread_all = ko_prices - beta * pep_prices
z_scores = (spread_all - spread_mean) / spread_std

# Initialize tracking arrays
positions = np.zeros((n_paths, n_days + 1), dtype=int)  # 0=no position, 1=long spread, -1=short spread
strategy_pnl = np.zeros(n_paths)
trade_count = np.zeros(n_paths)
entry_days = np.full(n_paths, -1)
exit_days = np.full(n_paths, -1)

# Execute strategy for each path
for path in range(n_paths):
    position = 0
    entry_day = -1
    entry_ko_price = 0
    entry_pep_price = 0
    
    for day in range(1, n_days + 1):
        z = z_scores[path, day]
        
        if position == 0:
            # Entry signals
            if z < -strategy_entry_threshold:
                position = 1  # Long spread (buy KO, short PEP)
                entry_ko_price = ko_prices[path, day]
                entry_pep_price = pep_prices[path, day]
                entry_day = day
                trade_count[path] += 1
            elif z > strategy_entry_threshold:
                position = -1  # Short spread (sell KO, buy PEP)
                entry_ko_price = ko_prices[path, day]
                entry_pep_price = pep_prices[path, day]
                entry_day = day
                trade_count[path] += 1
        
        else:
            # Exit signals: mean reversion or stop loss
            exit_signal = abs(z) < strategy_exit_threshold or abs(z) > strategy_stop_loss
            
            if exit_signal:
                # Calculate P&L for this trade
                exit_ko_price = ko_prices[path, day]
                exit_pep_price = pep_prices[path, day]
                
                strategy_pnl[path] += spread_trade_pnl(
                    position, entry_ko_price, entry_pep_price, exit_ko_price, exit_pep_price
                )
                
                # Record exit
                if exit_days[path] == -1:  # Record first exit
                    exit_days[path] = day
                    entry_days[path] = entry_day
                
                position = 0
        
        positions[path, day] = position

# Calculate final P&L for paths still holding positions at day 60
for path in range(n_paths):
    if positions[path, n_days] != 0:
        # Find entry day for this path
        entry_day_idx = -1
        for day in range(1, n_days + 1):
            if positions[path, day] != 0 and positions[path, day-1] == 0:
                entry_day_idx = day
                break
        
        if entry_day_idx > 0:
            entry_ko_price = ko_prices[path, entry_day_idx]
            entry_pep_price = pep_prices[path, entry_day_idx]
            exit_ko_price = ko_prices[path, n_days]
            exit_pep_price = pep_prices[path, n_days]
            
            strategy_pnl[path] += spread_trade_pnl(
                positions[path, n_days],
                entry_ko_price,
                entry_pep_price,
                exit_ko_price,
                exit_pep_price,
            )

# Performance metrics
winning_trades = strategy_pnl > 0
losing_trades = strategy_pnl < 0

win_rate = winning_trades.mean() * 100
avg_win = strategy_pnl[winning_trades].mean() if winning_trades.any() else 0
avg_loss = strategy_pnl[losing_trades].mean() if losing_trades.any() else 0
profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
max_gain = strategy_pnl.max()
max_loss = strategy_pnl.min()
median_pnl = np.median(strategy_pnl)

# Sharpe ratio for strategy
strategy_returns = strategy_pnl / initial_capital
mean_return = strategy_returns.mean()
std_return = strategy_returns.std()
sharpe_strategy = (mean_return / std_return) * np.sqrt(252 / 60) if std_return != 0 else 0

print(f"\nStrategy Performance (60-Day Simulation, {n_paths:,} paths):")
print(f"  Win rate:                {win_rate:.1f}%")
print(f"  Average winning trade:   ${avg_win:,.2f}")
print(f"  Average losing trade:    ${avg_loss:,.2f}")
print(f"  Profit factor:           {profit_factor:.2f}")
print(f"  Max gain:                ${max_gain:,.2f}")
print(f"  Max loss:                ${max_loss:,.2f}")
print(f"  Median P&L:              ${median_pnl:,.2f}")
print(f"  Sharpe ratio:            {sharpe_strategy:.2f}")
print(f"  Probability of profit:   {win_rate:.1f}%")
print(f"  Paths with trades:       {(trade_count > 0).sum():,} ({(trade_count > 0).mean()*100:.1f}%)")
print("=" * 80)

# --- Notebook Cell Boundary ---

# Visualize Strategy Results
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# 1. Strategy P&L Distribution
ax1 = axes[0, 0]
ax1.hist(strategy_pnl, bins=100, color='steelblue', alpha=0.7, edgecolor='black')
ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Break-even')
ax1.axvline(x=median_pnl, color='green', linestyle='--', linewidth=2, label=f'Median: ${median_pnl:,.0f}')
ax1.axvline(x=strategy_pnl.mean(), color='orange', linestyle='--', linewidth=2, 
           label=f'Mean: ${strategy_pnl.mean():,.0f}')
ax1.set_xlabel('Strategy P&L ($)', fontsize=11)
ax1.set_ylabel('Frequency', fontsize=11)
ax1.set_title(f'Strategy P&L Distribution (Win Rate: {win_rate:.1f}%)', 
             fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# 2. Sample Trading Paths
ax2 = axes[0, 1]
n_sample = 5
sample_idx = np.random.choice(np.where(trade_count > 0)[0], min(n_sample, (trade_count > 0).sum()), replace=False)
colors_sample = ['green' if strategy_pnl[i] > 0 else 'red' for i in sample_idx]

for i, idx in enumerate(sample_idx):
    ax2.plot(np.arange(n_days + 1), z_scores[idx, :], linewidth=2, alpha=0.7, 
            color=colors_sample[i], label=f'Path {idx}: ${strategy_pnl[idx]:,.0f}')
    
    # Mark entry and exit
    if entry_days[idx] > 0:
        ax2.scatter(entry_days[idx], z_scores[idx, entry_days[idx]], marker='^', 
                   s=150, color=colors_sample[i], edgecolors='black', linewidths=2, zorder=5)
    if exit_days[idx] > 0:
        ax2.scatter(exit_days[idx], z_scores[idx, exit_days[idx]], marker='o', 
                   s=120, color=colors_sample[i], edgecolors='black', linewidths=2, zorder=5)

ax2.axhline(y=strategy_entry_threshold, color='orange', linestyle='--', linewidth=1, alpha=0.5, 
           label='Entry threshold')
ax2.axhline(y=-strategy_entry_threshold, color='orange', linestyle='--', linewidth=1, alpha=0.5)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5, label='Mean')
ax2.axhline(y=strategy_stop_loss, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Stop loss')
ax2.axhline(y=-strategy_stop_loss, color='red', linestyle=':', linewidth=1, alpha=0.5)
ax2.set_xlabel('Trading Days', fontsize=11)
ax2.set_ylabel('Z-Score', fontsize=11)
ax2.set_title('Sample Trading Paths', fontsize=13, fontweight='bold')
ax2.legend(fontsize=8, loc='best')
ax2.grid(True, alpha=0.3)

# 3. Cumulative P&L Distribution
ax3 = axes[1, 0]
sorted_pnl = np.sort(strategy_pnl)
cumulative_prob = np.arange(1, len(sorted_pnl) + 1) / len(sorted_pnl)
ax3.plot(sorted_pnl, cumulative_prob * 100, linewidth=2, color='darkblue')
ax3.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Break-even')
ax3.axvline(x=median_pnl, color='green', linestyle='--', linewidth=2, label=f'Median: ${median_pnl:,.0f}')
ax3.axhline(y=5, color='orange', linestyle='--', linewidth=1, alpha=0.7, label='5th percentile')
ax3.axhline(y=95, color='purple', linestyle='--', linewidth=1, alpha=0.7, label='95th percentile')
ax3.fill_betweenx([0, 100], np.percentile(strategy_pnl, 5), np.percentile(strategy_pnl, 95), 
                  alpha=0.2, color='yellow', label='5th-95th %ile')
ax3.set_xlabel('Strategy P&L ($)', fontsize=11)
ax3.set_ylabel('Cumulative Probability (%)', fontsize=11)
ax3.set_title('Cumulative P&L Distribution', fontsize=13, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# 4. Win Rate vs Number of Trades
ax4 = axes[1, 1]
# Compare strategy vs buy-and-hold at 60 days
comparison_data = {
    'Buy & Hold\n(60d)': [(pnl[:, n_days] > 0).mean() * 100, pnl[:, n_days].mean()],
    'Trading\nStrategy': [win_rate, strategy_pnl.mean()]
}
labels = list(comparison_data.keys())
win_rates = [comparison_data[k][0] for k in labels]
avg_pnls = [comparison_data[k][1] for k in labels]

x = np.arange(len(labels))
width = 0.35

bars1 = ax4.bar(x - width/2, win_rates, width, label='Win Rate (%)', color='steelblue', alpha=0.7)
ax4_twin = ax4.twinx()
bars2 = ax4_twin.bar(x + width/2, avg_pnls, width, label='Avg P&L ($)', color='orange', alpha=0.7)

ax4.set_xlabel('Strategy', fontsize=11)
ax4.set_ylabel('Win Rate (%)', fontsize=11, color='steelblue')
ax4_twin.set_ylabel('Average P&L ($)', fontsize=11, color='orange')
ax4.set_title('Strategy Comparison: Trading vs Buy & Hold', fontsize=13, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(labels)
ax4.tick_params(axis='y', labelcolor='steelblue')
ax4_twin.tick_params(axis='y', labelcolor='orange')
ax4.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

for bar in bars2:
    height = bar.get_height()
    ax4_twin.text(bar.get_x() + bar.get_width()/2., height,
                 f'${height:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.show()

print("\nStrategy visualization complete!")

# --- Notebook Cell Boundary ---

# Extract 60-day statistics for blog
print("=" * 80)
print("60-DAY PORTFOLIO STATISTICS FOR BLOG")
print("=" * 80)

# Portfolio values at day 60
final_portfolio = portfolio_values[:, 60]

# VaR calculations
var_90 = np.percentile(final_portfolio, 10)
var_95 = np.percentile(final_portfolio, 5)
var_99 = np.percentile(final_portfolio, 1)

# CVaR calculation
var_threshold_95 = np.percentile(final_portfolio, 5)
cvar_95 = final_portfolio[final_portfolio <= var_threshold_95].mean()

# Portfolio distribution percentiles
p1 = np.percentile(final_portfolio, 1)
p5 = np.percentile(final_portfolio, 5)
p50 = np.percentile(final_portfolio, 50)
p95 = np.percentile(final_portfolio, 95)
p99 = np.percentile(final_portfolio, 99)

print(f"\n60-Day Portfolio Value Distribution:")
print(f"  1st percentile:   ${p1:,.2f}")
print(f"  5th percentile:   ${p5:,.2f} (VaR 95%)")
print(f"  Median:           ${p50:,.2f}")
print(f"  95th percentile:  ${p95:,.2f}")
print(f"  99th percentile:  ${p99:,.2f}")

print(f"\n60-Day VaR Results:")
print(f"  VaR 90%: ${var_90:,.2f} (loss: ${initial_capital - var_90:,.2f})")
print(f"  VaR 95%: ${var_95:,.2f} (loss: ${initial_capital - var_95:,.2f})")
print(f"  VaR 99%: ${var_99:,.2f} (loss: ${initial_capital - var_99:,.2f})")

print(f"\n60-Day CVaR:")
print(f"  CVaR 95%: ${cvar_95:,.2f} (avg loss in worst 5%: ${initial_capital - cvar_95:,.2f})")

# Maximum drawdown
portfolio_cummax = np.maximum.accumulate(portfolio_values, axis=1)
drawdown_all = (portfolio_values - portfolio_cummax) / portfolio_cummax
max_dd_per_path = drawdown_all.min(axis=1)

print(f"\nMaximum Drawdown Statistics:")
print(f"  Average max drawdown: {max_dd_per_path.mean()*100:.2f}%")
print(f"  Median max drawdown:  {np.median(max_dd_per_path)*100:.2f}%")
print(f"  Worst drawdown:       {max_dd_per_path.min()*100:.2f}%")

# Sharpe ratio for buy-and-hold
returns_60d = (final_portfolio - initial_capital) / initial_capital
mean_ret = returns_60d.mean()
std_ret = returns_60d.std()
sharpe_bh = (mean_ret / std_ret) * np.sqrt(252 / 60)

print(f"\nBuy-and-Hold Performance:")
print(f"  Expected return:  {mean_ret*100:.2f}%")
print(f"  Std deviation:    {std_ret*100:.2f}%")
print(f"  Sharpe ratio:     {sharpe_bh:.2f}")

print("=" * 80)

"""Notebook section: key observations."""

# Download 2 years of historical data for backtest
backtest_start = '2023-10-11'
backtest_end = '2025-10-09'

print(f"Downloading backtest data from {backtest_start} to {backtest_end}...")
ko_backtest = yf.download('KO', start=backtest_start, end=backtest_end, auto_adjust=False, progress=False)['Adj Close']
pep_backtest = yf.download('PEP', start=backtest_start, end=backtest_end, auto_adjust=False, progress=False)['Adj Close']

# Align dates
backtest_data = pd.concat([ko_backtest, pep_backtest], axis=1).dropna()
backtest_data.columns = ['KO', 'PEP']

print(f"\nBacktest data loaded: {len(backtest_data)} trading days")
print(f"Date range: {backtest_data.index[0].strftime('%Y-%m-%d')} to {backtest_data.index[-1].strftime('%Y-%m-%d')}")
print(f"\nInitial prices:")
print(f"  KO:  ${backtest_data['KO'].iloc[0]:.2f}")
print(f"  PEP: ${backtest_data['PEP'].iloc[0]:.2f}")

# --- Notebook Cell Boundary ---

# Calculate spread and rolling statistics
lookback_window = 60

spread_backtest = backtest_data['KO'] - beta * backtest_data['PEP']
rolling_mean_backtest = spread_backtest.rolling(window=lookback_window).mean()
rolling_std_backtest = spread_backtest.rolling(window=lookback_window).std()
z_score_backtest = (spread_backtest - rolling_mean_backtest) / rolling_std_backtest

print("Backtest spread statistics:")
print(f"  Mean spread: ${spread_backtest.mean():.2f}")
print(f"  Std dev:     ${spread_backtest.std():.2f}")
print(f"  Min spread:  ${spread_backtest.min():.2f}")
print(f"  Max spread:  ${spread_backtest.max():.2f}")

# --- Notebook Cell Boundary ---

# DIAGNOSTIC: Compare simulation parameters vs actual backtest behavior
print("=" * 80)
print("DIAGNOSTIC: SIMULATION ASSUMPTIONS vs BACKTEST REALITY")
print("=" * 80)

print("\n1. SPREAD PARAMETERS USED IN SIMULATION:")
print(f"  Historical mean (60-day window before Oct 9): ${spread_mean:.2f}")
print(f"  Historical std (60-day window before Oct 9):  ${spread_std:.2f}")
print(f"  Beta (hedge ratio): {beta:.4f}")

print("\n2. ACTUAL BACKTEST PERIOD (Oct 2023 - Oct 2025):")
print(f"  Actual spread mean: ${spread_backtest.mean():.2f}")
print(f"  Actual spread std:  ${spread_backtest.std():.2f}")

print("\n3. KEY DIFFERENCES:")
mean_diff = spread_backtest.mean() - spread_mean
std_diff = spread_backtest.std() - spread_std
print(f"  Mean shift: ${mean_diff:+.2f} ({mean_diff/spread_mean*100:+.1f}%)")
print(f"  Volatility shift: ${std_diff:+.2f} ({std_diff/spread_std*100:+.1f}%)")

# Check if mean reversion assumption held
print("\n4. MEAN REVERSION ASSUMPTION:")
print(f"  Assumed mean reversion speed: κ={kappa:.4f} (half-life={half_life_days} days)")
print(f"  This assumes spread reverts to ${spread_mean:.2f}")
print(f"  BUT actual spread during backtest averaged ${spread_backtest.mean():.2f}")
print(f"  → Mean reversion TARGET WAS WRONG by ${mean_diff:.2f}!")

# Check entry timing (current_spread_oct9 was set in the entry/exit strategy step).
z_score_entry = (current_spread_oct9 - spread_mean) / spread_std
print(f"\n5. ENTRY TIMING (Oct 9, 2023):")
print(f"  Spread value: ${current_spread_oct9:.2f}")
print(f"  Z-score from historical mean: {z_score_entry:.2f}")
print(f"  Distance from backtest mean: ${current_spread_oct9 - spread_backtest.mean():.2f}")

# Check volatility regime
print(f"\n6. VOLATILITY REGIME:")
print(f"  Simulated with σ = ${spread_std:.2f}")
print(f"  Actual volatility = ${spread_backtest.std():.2f}")
print(f"  → Volatility was {spread_backtest.std()/spread_std:.1f}x higher than expected!")

print("\n7. POTENTIAL ISSUES:")
issues = []
if abs(mean_diff) > spread_std:
    issues.append(f"  ✗ Spread mean shifted by >1σ ({abs(mean_diff)/spread_std:.1f}σ)")
if abs(std_diff) > spread_std * 0.5:
    issues.append(f"  ✗ Volatility changed significantly ({abs(std_diff)/spread_std*100:.1f}%)")
if abs(mean_diff/spread_mean) > 0.2:
    issues.append(f"  ✗ Mean shift >20% invalidates mean-reversion assumption")

if issues:
    for issue in issues:
        print(issue)
else:
    print("  ✓ Parameters appear reasonable")

print("=" * 80)

# --- Notebook Cell Boundary ---

# Check if beta changed over time
print("=" * 80)
print("BETA ANALYSIS: Has the hedge ratio changed?")
print("=" * 80)

# Calculate beta for different periods
periods = [
    ("Historical (20 years)", combined_data[combined_data.index < '2023-10-09'].tail(5000)),
    ("Recent (2 years before)", combined_data[(combined_data.index >= '2021-10-09') & (combined_data.index < '2023-10-09')]),
    ("Backtest period", backtest_data)
]

for name, data in periods:
    if len(data) > 30:
        X_period = data['PEP'].values
        y_period = data['KO'].values
        beta_period, alpha_period = np.polyfit(X_period, y_period, 1)
        y_pred_period = beta_period * X_period + alpha_period
        r2_period = 1 - (np.sum((y_period - y_pred_period) ** 2) / np.sum((y_period - y_period.mean()) ** 2))
        
        # Calculate spread with this beta
        spread_period = data['KO'] - beta_period * data['PEP']
        
        print(f"\n{name}:")
        print(f"  Beta: {beta_period:.4f} (vs historical {beta:.4f})")
        print(f"  R²: {r2_period:.4f}")
        print(f"  Spread mean: ${spread_period.mean():.2f}")
        print(f"  Spread std: ${spread_period.std():.2f}")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("If beta changed significantly, using old beta creates a biased spread!")
print("=" * 80)

# --- Notebook Cell Boundary ---

def backtest_spread_pnl(side: int, entry_ko: float, entry_pep: float, exit_ko: float, exit_pep: float) -> float:
    """Return dollar P&L for one backtest spread trade at fixed share counts."""
    ko_move = (exit_ko - entry_ko) * ko_shares_backtest
    pep_move = (exit_pep - entry_pep) * pep_shares_backtest
    if side == 1:
        return ko_move - pep_move
    return -ko_move + pep_move


# Execute backtest with mean-reversion strategy
# Use SAME position sizing as Monte Carlo: FULL $100k long PEP, FULL $100k short KO
initial_capital_backtest = 100_000

# Use initial prices from backtest period
initial_ko_price = backtest_data['KO'].iloc[0]
initial_pep_price = backtest_data['PEP'].iloc[0]

ko_shares_backtest = int(initial_capital_backtest / initial_ko_price)    # Short KO
pep_shares_backtest = int(initial_capital_backtest / initial_pep_price)  # Long PEP

print(f"\nBacktest position sizing:")
print(f"  Long PEP:  {pep_shares_backtest:,} shares × ${initial_pep_price:.2f} = ${pep_shares_backtest * initial_pep_price:,.2f}")
print(f"  Short KO:  {ko_shares_backtest:,} shares × ${initial_ko_price:.2f} = ${ko_shares_backtest * initial_ko_price:,.2f}")
print(f"  Gross exposure: ${pep_shares_backtest * initial_pep_price + ko_shares_backtest * initial_ko_price:,.2f}")

# Strategy parameters
entry_threshold = 1.5
exit_threshold = 0.2
stop_loss_threshold = 2.5

# Trading variables
position = 0  # 0 = no position, 1 = long spread, -1 = short spread
trades = []
equity_curve = [initial_capital_backtest]
entry_idx = None

# Execute strategy
for i in range(lookback_window, len(z_score_backtest)):
    current_z = z_score_backtest.iloc[i]
    
    if np.isnan(current_z):
        continue
    
    if position == 0:
        # Entry signals
        if current_z < -entry_threshold:
            position = 1  # Long spread (buy KO, sell PEP)
            entry_idx = i
            entry_price_ko = backtest_data['KO'].iloc[i]
            entry_price_pep = backtest_data['PEP'].iloc[i]
            entry_z = current_z
            entry_date = backtest_data.index[i]
            
        elif current_z > entry_threshold:
            position = -1  # Short spread (sell KO, buy PEP)
            entry_idx = i
            entry_price_ko = backtest_data['KO'].iloc[i]
            entry_price_pep = backtest_data['PEP'].iloc[i]
            entry_z = current_z
            entry_date = backtest_data.index[i]
    
    else:
        # Exit signals: mean reversion or stop loss
        exit_signal = abs(current_z) < exit_threshold or abs(current_z) > stop_loss_threshold
        
        if exit_signal:
            exit_price_ko = backtest_data['KO'].iloc[i]
            exit_price_pep = backtest_data['PEP'].iloc[i]
            exit_z = current_z
            exit_date = backtest_data.index[i]
            
            pnl = backtest_spread_pnl(position, entry_price_ko, entry_price_pep, exit_price_ko, exit_price_pep)
            
            # Record trade
            trades.append({
                'entry_date': entry_date,
                'exit_date': exit_date,
                'position_type': 'Long Spread' if position == 1 else 'Short Spread',
                'entry_z': entry_z,
                'exit_z': exit_z,
                'exit_reason': 'Mean Reversion' if abs(current_z) < exit_threshold else 'Stop Loss',
                'holding_days': (exit_date - entry_date).days,
                'pnl': pnl
            })
            
            # Update equity
            equity_curve.append(equity_curve[-1] + pnl)
            
            position = 0
            entry_idx = None

# Convert trades to DataFrame
trades_df = pd.DataFrame(trades)

print(f"\n{'='*80}")
print("BACKTEST RESULTS - 2 YEAR STRATEGY PERFORMANCE")
print(f"{'='*80}")
print(f"\nNumber of trades: {len(trades_df)}")

if len(trades_df) > 0:
    winning_trades = trades_df[trades_df['pnl'] > 0]
    losing_trades = trades_df[trades_df['pnl'] <= 0]
    
    print(f"Winning trades:   {len(winning_trades)} ({len(winning_trades)/len(trades_df)*100:.1f}%)")
    print(f"Losing trades:    {len(losing_trades)} ({len(losing_trades)/len(trades_df)*100:.1f}%)")
    print(f"\nTotal P&L:        ${trades_df['pnl'].sum():,.2f}")
    print(f"Average P&L:      ${trades_df['pnl'].mean():,.2f}")
    print(f"Best trade:       ${trades_df['pnl'].max():,.2f}")
    print(f"Worst trade:      ${trades_df['pnl'].min():,.2f}")
    
    if len(winning_trades) > 0:
        print(f"Avg winning:      ${winning_trades['pnl'].mean():,.2f}")
    if len(losing_trades) > 0:
        print(f"Avg losing:       ${losing_trades['pnl'].mean():,.2f}")
    
    if len(losing_trades) > 0 and losing_trades['pnl'].mean() != 0:
        profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum())
        print(f"Profit factor:    {profit_factor:.2f}")
    
    total_return = (equity_curve[-1] - initial_capital_backtest) / initial_capital_backtest
    annualized_return = ((1 + total_return) ** (252 / len(backtest_data))) - 1
    
    print(f"\nTotal return:     {total_return*100:.2f}%")
    print(f"Annualized:       {annualized_return*100:.2f}%")
    print(f"Avg hold time:    {trades_df['holding_days'].mean():.1f} days")
    
    print(f"{'='*80}")

# --- Notebook Cell Boundary ---

# Visualize backtest results
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# 1. Equity Curve
ax1 = axes[0]
dates_equity = [backtest_data.index[lookback_window]] + [t['exit_date'] for t in trades]
ax1.plot(dates_equity, equity_curve, linewidth=2.5, color='darkblue', marker='o', markersize=4)
ax1.axhline(y=initial_capital_backtest, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Initial Capital')
ax1.fill_between(dates_equity, initial_capital_backtest, equity_curve, 
                 where=np.array(equity_curve) >= initial_capital_backtest,
                 alpha=0.3, color='green', interpolate=True)
ax1.fill_between(dates_equity, equity_curve, initial_capital_backtest,
                 where=np.array(equity_curve) < initial_capital_backtest,
                 alpha=0.3, color='red', interpolate=True)
ax1.set_ylabel('Portfolio Value ($)', fontsize=11)
ax1.set_title('Backtest Equity Curve (2023-2025)', fontsize=13, fontweight='bold', pad=15)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

# 2. Z-Score with Entry/Exit Points
ax2 = axes[1]
ax2.plot(backtest_data.index[lookback_window:], z_score_backtest.iloc[lookback_window:], 
        linewidth=1, color='purple', alpha=0.7)
ax2.axhline(y=entry_threshold, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Entry thresholds')
ax2.axhline(y=-entry_threshold, color='green', linestyle='--', linewidth=1, alpha=0.5)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5, label='Mean')
ax2.axhline(y=stop_loss_threshold, color='darkred', linestyle=':', linewidth=1, alpha=0.5, label='Stop loss')
ax2.axhline(y=-stop_loss_threshold, color='darkred', linestyle=':', linewidth=1, alpha=0.5)

# Mark entry points
for trade in trades:
    if trade['position_type'] == 'Long Spread':
        ax2.scatter(trade['entry_date'], trade['entry_z'], marker='^', s=100, 
                   color='green', edgecolors='black', linewidths=1.5, zorder=5)
    else:
        ax2.scatter(trade['entry_date'], trade['entry_z'], marker='v', s=100,
                   color='red', edgecolors='black', linewidths=1.5, zorder=5)
    
    # Mark exit points
    exit_color = 'blue' if trade['exit_reason'] == 'Mean Reversion' else 'orange'
    ax2.scatter(trade['exit_date'], trade['exit_z'], marker='o', s=80,
               color=exit_color, edgecolors='black', linewidths=1.5, zorder=5)

ax2.set_ylabel('Z-Score', fontsize=11)
ax2.set_title('Z-Score Evolution with Trade Signals', fontsize=13, fontweight='bold', pad=15)
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.set_ylim([-4, 4])

# 3. Trade P&L Distribution
ax3 = axes[2]
if len(trades_df) > 0:
    colors_pnl = ['green' if x > 0 else 'red' for x in trades_df['pnl']]
    bars = ax3.bar(range(len(trades_df)), trades_df['pnl'], color=colors_pnl, alpha=0.7, edgecolor='black')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    ax3.set_xlabel('Trade Number', fontsize=11)
    ax3.set_ylabel('P&L ($)', fontsize=11)
    ax3.set_title(f'Individual Trade P&L (Win Rate: {len(winning_trades)/len(trades_df)*100:.1f}%)', 
                 fontsize=13, fontweight='bold', pad=15)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.1f}K'))

plt.tight_layout()
plt.show()

print("\nBacktest visualization complete!")

"""Notebook section: comparison of var methods historical simulation vs monte carlo vs parametric."""

# Calculate VaR using three methods for 60-day horizon

# Method 1: Monte Carlo (already computed above)
mc_var_90 = initial_capital - var_90
mc_var_95 = initial_capital - var_95
mc_var_99 = initial_capital - var_99

# Method 2: Historical Simulation
# Use actual historical returns over rolling 60-day windows
ko_hist_returns = historical_data['KO'].pct_change().dropna()
pep_hist_returns = historical_data['PEP'].pct_change().dropna()

# Create historical portfolio returns (short KO, long PEP)
historical_portfolio_returns = -ko_hist_returns + pep_hist_returns

# Bootstrap 60-day compounded returns from the historical daily portfolio return series.
n_bootstrap = OVERRIDES.get('n_bootstrap', 1_000_000)
horizon_days = 60

np.random.seed(42)
sampled_daily_returns = np.random.choice(
    historical_portfolio_returns.values,
    size=(n_bootstrap, horizon_days),
    replace=True,
)
hist_sim_returns = np.prod(1 + sampled_daily_returns, axis=1) - 1

# Calculate portfolio values from historical simulation
hist_sim_portfolio = initial_capital * (1 + hist_sim_returns)

# Historical Simulation VaR
hist_var_90 = initial_capital - np.percentile(hist_sim_portfolio, 10)
hist_var_95 = initial_capital - np.percentile(hist_sim_portfolio, 5)
hist_var_99 = initial_capital - np.percentile(hist_sim_portfolio, 1)

# Method 3: Parametric (Variance-Covariance) Method
# Assumes returns are normally distributed
portfolio_std_daily = historical_portfolio_returns.std()
portfolio_mean_daily = historical_portfolio_returns.mean()

# Scale to 60-day horizon
portfolio_mean_60d = portfolio_mean_daily * 60
portfolio_std_60d = portfolio_std_daily * np.sqrt(60)

# Calculate VaR using normal distribution quantiles
from scipy import stats
z_90 = stats.norm.ppf(0.10)  # 10th percentile
z_95 = stats.norm.ppf(0.05)  # 5th percentile
z_99 = stats.norm.ppf(0.01)  # 1st percentile

# Parametric portfolio values at confidence levels
param_portfolio_90 = initial_capital * (1 + portfolio_mean_60d + z_90 * portfolio_std_60d)
param_portfolio_95 = initial_capital * (1 + portfolio_mean_60d + z_95 * portfolio_std_60d)
param_portfolio_99 = initial_capital * (1 + portfolio_mean_60d + z_99 * portfolio_std_60d)

# Parametric VaR
param_var_90 = initial_capital - param_portfolio_90
param_var_95 = initial_capital - param_portfolio_95
param_var_99 = initial_capital - param_portfolio_99

print("=" * 80)
print("VaR COMPARISON: THREE METHODS (60-Day Horizon)")
print("=" * 80)

print("\nVaR 90% (10th percentile):")
print(f"  Monte Carlo:          ${mc_var_90:,.2f}")
print(f"  Historical Simulation: ${hist_var_90:,.2f}")
print(f"  Parametric (VCV):     ${param_var_90:,.2f}")

print("\nVaR 95% (5th percentile):")
print(f"  Monte Carlo:          ${mc_var_95:,.2f}")
print(f"  Historical Simulation: ${hist_var_95:,.2f}")
print(f"  Parametric (VCV):     ${param_var_95:,.2f}")

print("\nVaR 99% (1st percentile):")
print(f"  Monte Carlo:          ${mc_var_99:,.2f}")
print(f"  Historical Simulation: ${hist_var_99:,.2f}")
print(f"  Parametric (VCV):     ${param_var_99:,.2f}")

# Calculate percentage differences from Monte Carlo (baseline)
print("\n" + "=" * 80)
print("DIFFERENCE FROM MONTE CARLO (baseline)")
print("=" * 80)

print("\nVaR 90%:")
print(f"  Historical Simulation: {(hist_var_90 - mc_var_90) / mc_var_90 * 100:+.2f}%")
print(f"  Parametric (VCV):     {(param_var_90 - mc_var_90) / mc_var_90 * 100:+.2f}%")

print("\nVaR 95%:")
print(f"  Historical Simulation: {(hist_var_95 - mc_var_95) / mc_var_95 * 100:+.2f}%")
print(f"  Parametric (VCV):     {(param_var_95 - mc_var_95) / mc_var_95 * 100:+.2f}%")

print("\nVaR 99%:")
print(f"  Historical Simulation: {(hist_var_99 - mc_var_99) / mc_var_99 * 100:+.2f}%")
print(f"  Parametric (VCV):     {(param_var_99 - mc_var_99) / mc_var_99 * 100:+.2f}%")

print("=" * 80)

# --- Notebook Cell Boundary ---

# Visualize VaR comparison across three methods
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. VaR Comparison Bar Chart
ax1 = axes[0, 0]
methods = ['Monte\nCarlo', 'Historical\nSimulation', 'Parametric\n(VCV)']
var_90_values = [mc_var_90, hist_var_90, param_var_90]
var_95_values = [mc_var_95, hist_var_95, param_var_95]
var_99_values = [mc_var_99, hist_var_99, param_var_99]

x = np.arange(len(methods))
width = 0.25

bars1 = ax1.bar(x - width, var_90_values, width, label='VaR 90%', color='steelblue', alpha=0.8)
bars2 = ax1.bar(x, var_95_values, width, label='VaR 95%', color='coral', alpha=0.8)
bars3 = ax1.bar(x + width, var_99_values, width, label='VaR 99%', color='darkred', alpha=0.8)

ax1.set_xlabel('VaR Method', fontsize=12, fontweight='bold')
ax1.set_ylabel('Value at Risk (USD)', fontsize=12, fontweight='bold')
ax1.set_title('60-Day VaR Comparison Across Methods', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(methods)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')

# Add value labels
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:,.0f}', ha='center', va='bottom', fontsize=9)

# 2. Distribution Comparison
ax2 = axes[0, 1]
ax2.hist(initial_capital - final_portfolio, bins=100, density=True, 
         alpha=0.5, label='Monte Carlo', color='steelblue', edgecolor='black')
ax2.hist(initial_capital - hist_sim_portfolio, bins=100, density=True,
         alpha=0.5, label='Historical Sim', color='coral', edgecolor='black')

# Add parametric distribution
x_range = np.linspace(-20000, 20000, 1000)
param_pdf = stats.norm.pdf(x_range, 
                           loc=-portfolio_mean_60d * initial_capital,
                           scale=portfolio_std_60d * initial_capital)
ax2.plot(x_range, param_pdf, 'r-', linewidth=2, label='Parametric (Normal)', alpha=0.8)

ax2.axvline(x=0, color='black', linestyle='--', linewidth=2, alpha=0.5)
ax2.set_xlabel('Portfolio Loss (USD)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Probability Density', fontsize=12, fontweight='bold')
ax2.set_title('Loss Distribution Comparison', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(-15000, 15000)

# 3. VaR 95% Relative Differences
ax3 = axes[1, 0]
var_95_diff_hist = (hist_var_95 - mc_var_95) / mc_var_95 * 100
var_95_diff_param = (param_var_95 - mc_var_95) / mc_var_95 * 100

methods_diff = ['Historical\nSimulation', 'Parametric\n(VCV)']
differences = [var_95_diff_hist, var_95_diff_param]
colors_diff = ['green' if d < 0 else 'red' for d in differences]

bars = ax3.bar(methods_diff, differences, color=colors_diff, alpha=0.7, edgecolor='black', linewidth=2)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=2)
ax3.set_ylabel('Difference from Monte Carlo (%)', fontsize=12, fontweight='bold')
ax3.set_title('VaR 95% Relative Difference from Monte Carlo', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# Add value labels
for bar in bars:
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:+.1f}%', ha='center', 
            va='bottom' if height > 0 else 'top', 
            fontsize=11, fontweight='bold')

# 4. Q-Q Plot: Monte Carlo vs Historical Simulation
ax4 = axes[1, 1]
mc_losses = initial_capital - final_portfolio
hist_losses = initial_capital - hist_sim_portfolio

# Sort both distributions
mc_sorted = np.sort(mc_losses)
hist_sorted = np.sort(hist_losses)

# Sample evenly spaced quantiles
n_quantiles = 1000
quantile_indices = np.linspace(0, len(mc_sorted)-1, n_quantiles).astype(int)
mc_quantiles = mc_sorted[quantile_indices]
hist_quantiles = hist_sorted[quantile_indices]

ax4.scatter(mc_quantiles, hist_quantiles, alpha=0.3, s=10, color='steelblue')
ax4.plot([-15000, 15000], [-15000, 15000], 'r--', linewidth=2, label='Perfect Match')
ax4.set_xlabel('Monte Carlo Loss Quantiles (USD)', fontsize=12, fontweight='bold')
ax4.set_ylabel('Historical Simulation Loss Quantiles (USD)', fontsize=12, fontweight='bold')
ax4.set_title('Q-Q Plot: Monte Carlo vs Historical Simulation', fontsize=14, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3)
ax4.set_xlim(-12000, 12000)
ax4.set_ylim(-12000, 12000)

plt.tight_layout()
plt.show()

print("VaR comparison visualization complete!")

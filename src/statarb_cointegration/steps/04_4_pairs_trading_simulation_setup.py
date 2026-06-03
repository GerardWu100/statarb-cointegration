"""Notebook section: 4 pairs trading simulation setup."""

# Calculate historical parameters
trade_date = '2023-10-09'
lookback_period = 5000  # ~20 years

historical_data = combined_data[combined_data.index < trade_date].tail(lookback_period)

# Calculate returns and statistics
ko_returns = historical_data['KO'].pct_change().dropna()
pep_returns = historical_data['PEP'].pct_change().dropna()

ko_mean, ko_std = ko_returns.mean(), ko_returns.std()
pep_mean, pep_std = pep_returns.mean(), pep_returns.std()
correlation = ko_returns.corr(pep_returns)

# Linear regression for hedge ratio: KO = alpha + beta * PEP
X = historical_data['PEP'].values
y = historical_data['KO'].values
beta, alpha = np.polyfit(X, y, 1)

# Calculate R²
y_pred = beta * X + alpha
r_squared = 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - y.mean()) ** 2))

# Spread statistics - use 60-day rolling window for current regime
linear_spread = historical_data['KO'] - beta * historical_data['PEP']
rolling_window_for_sim = 60
spread_mean = linear_spread.tail(rolling_window_for_sim).mean()  # Recent mean
spread_std = linear_spread.tail(rolling_window_for_sim).std()    # Recent std
spread_mean_all = linear_spread.mean()  # Historical mean for reference
spread_std_all = linear_spread.std()    # Historical std for reference

# Mean reversion parameters for O-U process
# Use a conservative estimate: kappa reflects typical mean reversion in equity spreads
# Use half-life 10 days
half_life_days = 10
kappa = np.log(2) / half_life_days  # Mean reversion speed

# Trade date prices
ko_price_trade = combined_data.loc[trade_date, 'KO']
pep_price_trade = combined_data.loc[trade_date, 'PEP']

print("Historical Parameters (20 years):")
print("=" * 60)
print(f"KO:  μ={ko_mean:.6f} ({ko_mean*252:.2%}/yr), σ={ko_std:.6f} ({ko_std*np.sqrt(252):.2%}/yr)")
print(f"PEP: μ={pep_mean:.6f} ({pep_mean*252:.2%}/yr), σ={pep_std:.6f} ({pep_std*np.sqrt(252):.2%}/yr)")
print(f"Correlation: {correlation:.4f}")
print(f"\nHedge Ratio: β={beta:.4f}, α={alpha:.4f}, R²={r_squared:.4f}")
print(f"Spread (St=KO-β*PEP):")
print(f"  Historical (all data): μ=${spread_mean_all:.4f}, σ=${spread_std_all:.4f}")
print(f"  Recent (60-day):       μ=${spread_mean:.4f}, σ=${spread_std:.4f} [USED FOR SIMULATION]")
print(f"Mean Reversion: κ={kappa:.4f} (half-life ~{half_life_days} days)")
print(f"\nPrices on {trade_date}: KO=${ko_price_trade:.2f}, PEP=${pep_price_trade:.2f}")
print(f"Current Spread: ${ko_price_trade - beta * pep_price_trade:.4f}")

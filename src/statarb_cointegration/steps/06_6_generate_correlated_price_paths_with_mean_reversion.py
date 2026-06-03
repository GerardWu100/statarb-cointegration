"""Notebook section: 6 generate correlated price paths with mean reversion."""

np.random.seed(111111)

# Correlation structure
corr_matrix = np.array([[1.0, correlation], [correlation, 1.0]])
cholesky = np.linalg.cholesky(corr_matrix)

# Initialize price arrays
ko_prices = np.zeros((n_paths, n_days + 1))
pep_prices = np.zeros((n_paths, n_days + 1))
ko_prices[:, 0] = ko_price_trade
pep_prices[:, 0] = pep_price_trade

# O-U spread volatility
spread_volatility = spread_std * np.sqrt(2 * kappa)

print(f"Generating {n_paths:,} correlated price paths with O-U mean reversion...")

# Monte Carlo simulation: GBM + Ornstein-Uhlenbeck mean reversion
dt = 1

# Correct O-U adjustment weights based on variance contributions
# These ensure that ΔKO_ou - β * ΔPEP_ou = ou_adjustment (100% of mean-reversion force)
weight_ko = 1 / (1 + beta**2)
weight_pep = beta / (1 + beta**2)

print(f"O-U adjustment weights: KO={weight_ko:.6f}, PEP={weight_pep:.6f}")
print(f"Verification: {weight_ko:.6f} - β*(-{weight_pep:.6f}) = {weight_ko + beta * weight_pep:.6f} ✓")

for day in range(n_days):
    # Generate random shocks (3 sources: 2 for stocks, 1 for spread)
    z = np.random.standard_normal((n_paths, 3))
    corr_z = z[:, :2] @ cholesky.T  # Correlated stock shocks
    
    # GBM returns
    ko_return = (ko_mean - 0.5 * ko_std**2) * dt + ko_std * np.sqrt(dt) * corr_z[:, 0]
    pep_return = (pep_mean - 0.5 * pep_std**2) * dt + pep_std * np.sqrt(dt) * corr_z[:, 1]
    
    # O-U mean reversion adjustment
    current_spread = ko_prices[:, day] - beta * pep_prices[:, day]
    ou_drift = kappa * (spread_mean - current_spread) * dt
    ou_diffusion = spread_volatility * np.sqrt(dt) * z[:, 2]
    ou_adjustment = ou_drift + ou_diffusion
    
    # Distribute O-U adjustment to stocks using variance-based weights
    # This ensures the full mean-reversion force is applied to the spread
    ko_ou_return = (ou_adjustment * weight_ko) / ko_prices[:, day]
    pep_ou_return = -(ou_adjustment * weight_pep) / pep_prices[:, day]
    
    # Update prices
    ko_prices[:, day + 1] = ko_prices[:, day] * np.exp(ko_return + ko_ou_return)
    pep_prices[:, day + 1] = pep_prices[:, day] * np.exp(pep_return + pep_ou_return)

final_spreads = ko_prices[:, -1] - beta * pep_prices[:, -1]
print(f"Complete! KO: ${ko_prices.min():.2f}-${ko_prices.max():.2f}, PEP: ${pep_prices.min():.2f}-${pep_prices.max():.2f}")
print(f"Final spread: μ=${final_spreads.mean():.2f}, σ=${final_spreads.std():.2f}")

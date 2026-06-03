"""Notebook section: 5 portfolio construction risk metrics."""

# Simulation parameters; CLI --smoke lowers n_paths via OVERRIDES.
n_paths = OVERRIDES.get('n_paths', 1_000_000)
n_days = 60
initial_capital = 100_000
risk_free_rate_annual = 0.05
risk_free_rate_daily = (1 + risk_free_rate_annual) ** (1/252) - 1

# Initial positions - FULL $100k LONG PEP, FULL $100k SHORT KO (NOT HEDGED!)
# IMPORTANT: We use $100k to buy PEP AND $100k to short KO = $200k gross exposure
pep_shares = int(initial_capital / pep_price_trade)  # LONG: 664 shares
ko_shares = int(initial_capital / ko_price_trade)    # SHORT: 2008 shares (positive = number shorted)

# Cash flows:
# - Start with $100k
# - Spend $100k buying PEP → -$100k
# - Receive $100k from shorting KO → +$100k
# - Result: $100k cash remaining
pep_cost = pep_shares * pep_price_trade              # Money spent on PEP
ko_proceeds = ko_shares * ko_price_trade             # Money received from shorting KO
cash_position = initial_capital - pep_cost + ko_proceeds  # Net cash = $100k

# Portfolio value = cash + long positions - short positions
initial_portfolio_value = cash_position + (pep_shares * pep_price_trade) - (ko_shares * ko_price_trade)

print("Initial Trading Position:")
print("=" * 60)
print(f"Starting Capital:     ${initial_capital:,.2f}")
print(f"\nLong PEP:  {pep_shares:,} shares × ${pep_price_trade:.2f} = ${pep_cost:,.2f} (spent)")
print(f"Short KO:  {ko_shares:,} shares × ${ko_price_trade:.2f} = ${ko_proceeds:,.2f} (received)")
print(f"\nGross Exposure:       ${pep_cost + ko_proceeds:,.2f} (200% of capital)")
print(f"Net Cash Remaining:   ${cash_position:,.2f}")
print(f"\nPosition Values:")
print(f"  LONG  PEP: ${pep_shares * pep_price_trade:,.2f}")
print(f"  SHORT KO:  ${ko_shares * ko_price_trade:,.2f}")
print(f"\nInitial Portfolio Value: ${initial_portfolio_value:,.2f}")
print(f"Initial Spread: S₀ = KO - β*PEP = ${ko_price_trade - beta * pep_price_trade:.2f}")

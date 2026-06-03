"""Notebook section: verification mean reversion correction."""

# Verify the O-U adjustment: Mathematical proof that weights are correct
print("=" * 70)
print("MATHEMATICAL VERIFICATION: O-U Adjustment Weights")
print("=" * 70)

print(f"\nGiven: β = {beta:.4f}")
print(f"\nWeights used:")
print(f"  weight_ko  = 1 / (1 + β²) = {weight_ko:.6f}")
print(f"  weight_pep = β / (1 + β²) = {weight_pep:.6f}")

print(f"\nProof that spread change = ou_adjustment:")
print(f"  ΔS = ΔKO_ou - β * ΔPEP_ou")
print(f"     = (ou_adjustment * {weight_ko:.6f}) - β * (ou_adjustment * (-{weight_pep:.6f}))")
print(f"     = ou_adjustment * ({weight_ko:.6f} + β * {weight_pep:.6f})")
print(f"     = ou_adjustment * {weight_ko + beta * weight_pep:.6f}")
print(f"     = ou_adjustment * (1 + β²)/(1 + β²)")
print(f"     = ou_adjustment  ✓")

print(f"\nThis ensures 100% of the mean-reversion force is applied to the spread.")
print(f"\nNote: Previous approach using 1/(1+β) would only apply:")
print(f"  (1 + β²)/(1 + β) = {(1 + beta**2)/(1 + beta):.6f} ≈ {(1 + beta**2)/(1 + beta)*100:.1f}% of the adjustment")
print("=" * 70)

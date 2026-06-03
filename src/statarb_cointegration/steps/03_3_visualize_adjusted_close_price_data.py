"""Notebook section: 3 visualize adjusted close price data."""

# Visualize price data
fig, axes = plt.subplots(2, 1, figsize=(14, 7))

# Absolute prices
axes[0].plot(combined_data.index, combined_data['KO'], label='KO', linewidth=2)
axes[0].plot(combined_data.index, combined_data['PEP'], label='PEP', linewidth=2)
axes[0].set_title('Historical Adjusted Close Prices', fontsize=14, fontweight='bold')
axes[0].set_ylabel('Price (USD)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Normalized prices
normalized_data = combined_data / combined_data.iloc[0] * 100
axes[1].plot(normalized_data.index, normalized_data['KO'], label='KO', linewidth=2)
axes[1].plot(normalized_data.index, normalized_data['PEP'], label='PEP', linewidth=2)
axes[1].set_title('Normalized Prices (Base = 100)', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Date')
axes[1].set_ylabel('Normalized Price')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print(f"KO: ${combined_data['KO'].min():.2f} - ${combined_data['KO'].max():.2f}")
print(f"PEP: ${combined_data['PEP'].min():.2f} - ${combined_data['PEP'].max():.2f}")

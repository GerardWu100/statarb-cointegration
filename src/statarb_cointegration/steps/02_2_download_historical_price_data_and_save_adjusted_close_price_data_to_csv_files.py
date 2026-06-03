"""Notebook section: 2 download historical price data and save adjusted close price data to parquet files."""

tickers = ['KO', 'PEP']
start_date = '1980-01-01'
end_date = '2025-10-01'

print(f"Downloading data for {tickers} from {start_date} to {end_date}...")

# One multi-ticker request keeps KO and PEP on the same calendar before alignment.
raw_prices = yf.download(
    tickers,
    start=start_date,
    end=end_date,
    auto_adjust=False,
    progress=False,
)
combined_data = raw_prices['Adj Close'].dropna().sort_index()
combined_data.columns = ['KO', 'PEP']

combined_data.to_parquet(PROCESSED_DATA_DIR / 'ko_pep_combined_adj_close_price.parquet')
print(f"\nData saved! Shape: {combined_data.shape}")
print(f"Date range: {combined_data.index[0].strftime('%Y-%m-%d')} to {combined_data.index[-1].strftime('%Y-%m-%d')}")

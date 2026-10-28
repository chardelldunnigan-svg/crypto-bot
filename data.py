"""
data.py — Fetches live price data from Coinbase.
"""

import requests #internet requests
import pandas as pd 
from config import CONFIG # calling dictionary from settings file.


class DataFeed:
    # Check for symbols in settings 
    def __init__(self, config):
        self.symbol = config.get("symbol", "BTC-USD")
    
    def get_market_data(self):
        # Get current price
        response = requests.get(f"https://api.coinbase.com/v2/prices/{self.symbol}/spot")
        data = response.json()
        price = float(data["data"]["amount"])

        # Get recent candles
        candle_url = f"https://api.exchange.coinbase.com/products/{self.symbol}/candles?granularity=300"
        response = requests.get(candle_url)
        raw = response.json()

        candles = pd.DataFrame(raw, columns=["time", "low", "high", "open", "close", "volume"])
        for col in ["open", "high", "low", "close", "volume"]:
            candles[col] = candles[col].astype(float)

        return price, candles
"""
Settings for the bot configuration.

API credentials are loaded from environment variables (via a local .env
file) instead of being hardcoded here, so they never end up committed to
git. See .env.example for the variable names you need to set.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in this folder (if present) into the environment

API_KEY = os.environ.get("COINBASE_API_KEY")
API_SECRET = os.environ.get("COINBASE_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError(
        "Missing COINBASE_API_KEY / COINBASE_API_SECRET. "
        "Copy .env.example to .env and fill in your real Coinbase API key/secret."
    )

CONFIG = {
    "api_key": API_KEY,
    "api_secret": API_SECRET,

    # --- Coins and their optimized settings ---
    "symbols": {
        "BTC-USD":  {"grid_spacing": 0.008, "order_size_usd": 20},
        "ETH-USD":  {"grid_spacing": 0.005, "order_size_usd": 20},
        "SOL-USD":  {"grid_spacing": 0.01,  "order_size_usd": 20},
        # DOGE skipped — not performing
    },

    # Mode - TRUE = Paper trading, FALSE = Live trading
    "paper_trade": True,

    # How many buy levels and sell levels to place above and below the current price.
    "grid_levels": 5,

    # Risk settings
    "max_open_orders":  10,
    "daily_loss_limit": 50,
    "stop_loss_pct":    0.03,

    # Checks prices every __ seconds
    "poll_interval_seconds": 10,
    "candle_interval":       "FIVE_MINUTE",
    "candle_limit":           100,
}

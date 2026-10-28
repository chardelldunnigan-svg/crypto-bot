"""
optimize.py — Tests all 4 coins across multiple grid spacings.
Finds the best settings before going live.
Run with: python optimize.py
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from strategy import GridStrategy
from config import CONFIG


COINS = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]
SPACINGS = [0.001, 0.003, 0.005, 0.008, 0.01]
DAYS = 90  # 3 months
CHUNKS = 31  # 3 day chunks


def get_historical_data(symbol):
    print(f"  Downloading {symbol}...")
    all_candles = []
    end = datetime.now(timezone.utc)

    for i in range(CHUNKS):
        chunk_end = end - timedelta(days=3 * i)
        chunk_start = chunk_end - timedelta(days=3)
        url = (
            f"https://api.exchange.coinbase.com/products/{symbol}/candles"
            f"?granularity=3600"
            f"&start={chunk_start.isoformat()}"
            f"&end={chunk_end.isoformat()}"
        )
        response = requests.get(url)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            all_candles.extend(data)

    df = pd.DataFrame(all_candles, columns=["time", "low", "high", "open", "close", "volume"])
    df["close"] = df["close"].astype(float)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.drop_duplicates("time").sort_values("time").reset_index(drop=True)
    return df


def run_backtest(df, spacing):
    config = CONFIG.copy()
    config["grid_spacing"] = spacing
    config["order_size_usd"] = 20
    config["grid_levels"] = 5

    strategy = GridStrategy(config)
    cash = 1000.0
    btc = 0.0
    trades = []

    for i, row in df.iterrows():
        price = row["close"]
        historical = df.iloc[:i+1]
        signal = strategy.evaluate(price, historical)

        if signal == "BUY":
            size_usd = config["order_size_usd"]
            if cash >= size_usd:
                qty = size_usd / price
                cash -= size_usd
                btc += qty
                trades.append("BUY")

        elif signal == "SELL":
            size_usd = config["order_size_usd"]
            qty = size_usd / price
            if btc >= qty:
                btc -= qty
                cash += size_usd
                trades.append("SELL")

    final_price = df["close"].iloc[-1]
    final_value = cash + (btc * final_price)
    profit = final_value - 1000.0
    pct = (profit / 1000.0) * 100
    return pct, len(trades)


def show_results(results):
    print("\n")
    print("=" * 65)
    print(f"{'OPTIMIZATION RESULTS — 3 MONTHS':^65}")
    print("=" * 65)
    print(f"{'Coin':<12} {'Spacing':>10} {'Return %':>10} {'Trades':>10}")
    print("-" * 65)

    best = {}
    for coin, spacing, pct, trades in sorted(results, key=lambda x: x[2], reverse=True):
        marker = " ← BEST" if coin not in best else ""
        if coin not in best:
            best[coin] = (spacing, pct)
        print(f"{coin:<12} {spacing*100:>9.1f}% {pct:>+9.2f}% {trades:>10}  {marker}")

    print("=" * 65)
    print("\nBEST SETTINGS PER COIN:")
    for coin, (spacing, pct) in best.items():
        print(f"  {coin:<12} grid_spacing={spacing}  return={pct:+.2f}%")

    # Chart — best return per coin
    coins = list(best.keys())
    returns = [best[c][1] for c in coins]
    colors = ["green" if r > 0 else "red" for r in returns]

    plt.figure(figsize=(10, 5))
    bars = plt.bar(coins, returns, color=colors, edgecolor="white", linewidth=0.5)
    plt.axhline(y=0, color="gray", linestyle="--", linewidth=1)
    plt.title("Best Return Per Coin — 3 Month Backtest")
    plt.ylabel("Return %")
    for bar, val in zip(bars, returns):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f"{val:+.2f}%", ha="center", va="bottom", fontsize=10)
    plt.tight_layout()
    plt.savefig("optimize_results.png")
    plt.show()
    print("\nChart saved as optimize_results.png")


if __name__ == "__main__":
    print("Downloading data for all 4 coins...")
    coin_data = {}
    for coin in COINS:
        coin_data[coin] = get_historical_data(coin)

    print("\nRunning optimization across all spacings...")
    results = []
    for coin in COINS:
        for spacing in SPACINGS:
            pct, trades = run_backtest(coin_data[coin], spacing)
            results.append((coin, spacing, pct, trades))
            print(f"  {coin} spacing={spacing*100:.1f}%  return={pct:+.2f}%  trades={trades}")

    show_results(results)
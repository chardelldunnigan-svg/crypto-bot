"""
backtest.py — Tests the grid strategy against 1 year of real BTC price data.
Run with: python backtest.py
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from strategy import GridStrategy
from config import CONFIG


def get_historical_data():
    print("Downloading 1 year of BTC price data in chunks...")
    all_candles = []
    end = datetime.now(timezone.utc)

    for i in range(31
                   ):
        chunk_end = end - timedelta(days=3 * i)
        chunk_start = chunk_end - timedelta(days=3)
        url = (
            f"https://api.exchange.coinbase.com/products/BTC-USD/candles"
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
    print(f"Got {len(df)} hourly candles from {df['time'].iloc[0].date()} to {df['time'].iloc[-1].date()}")
    return df


def run_backtest(df):
    config = CONFIG.copy()
    config["grid_spacing"] = 0.003
    config["order_size_usd"] = 20
    config["grid_levels"] = 5

    strategy = GridStrategy(config)

    cash = 1000.0
    btc = 0.0
    trades = []
    balance_over_time = []

    print(f"Starting balance: ${cash:.2f}")
    print("Running backtest...\n")

    for i, row in df.iterrows():
        price = row["close"]
        date = row["time"]

        # Pass all candles up to this point so trend filter sees real history
        historical = df.iloc[:i+1]
        signal = strategy.evaluate(price, historical)

        if signal == "BUY":
            size_usd = config["order_size_usd"]
            if cash >= size_usd:
                qty = size_usd / price
                cash -= size_usd
                btc += qty
                trades.append({"date": date, "signal": "BUY", "price": price, "size_usd": size_usd})

        elif signal == "SELL":
            size_usd = config["order_size_usd"]
            qty = size_usd / price
            if btc >= qty:
                btc -= qty
                cash += size_usd
                trades.append({"date": date, "signal": "SELL", "price": price, "size_usd": size_usd})

        total_value = cash + (btc * price)
        balance_over_time.append({"date": date, "value": total_value, "price": price})

    return trades, balance_over_time, cash, btc


def show_results(trades, balance_over_time, final_cash, final_btc, df):
    balance_df = pd.DataFrame(balance_over_time)
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()

    final_price = df["close"].iloc[-1]
    final_value = final_cash + (final_btc * final_price)
    profit = final_value - 1000.0
    pct = (profit / 1000.0) * 100

    print("=" * 40)
    print("BACKTEST RESULTS")
    print("=" * 40)
    print(f"Starting balance:  $1000.00")
    print(f"Final value:       ${final_value:.2f}")
    print(f"Profit / Loss:     ${profit:.2f} ({pct:.1f}%)")
    print(f"Total trades:      {len(trades)}")
    if not trades_df.empty:
        buys = len(trades_df[trades_df["signal"] == "BUY"])
        sells = len(trades_df[trades_df["signal"] == "SELL"])
        print(f"Buys:              {buys}")
        print(f"Sells:             {sells}")
    print("=" * 40)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle("Grid Bot Backtest — BTC/USD (1 Year)", fontsize=14)

    ax1.plot(balance_df["date"], balance_df["value"], color="green", linewidth=1.5)
    ax1.axhline(y=1000, color="gray", linestyle="--", linewidth=1, label="Starting balance")
    ax1.set_title("Portfolio Value Over Time")
    ax1.set_ylabel("USD")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(balance_df["date"], balance_df["price"], color="orange", linewidth=1.5)
    ax2.set_title("BTC Price Over Time")
    ax2.set_ylabel("USD")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("backtest_results.png")
    plt.show()
    print("\nChart saved as backtest_results.png")


if __name__ == "__main__":
    df = get_historical_data()
    trades, balance_over_time, final_cash, final_btc = run_backtest(df)
    show_results(trades, balance_over_time, final_cash, final_btc, df)
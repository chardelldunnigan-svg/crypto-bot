from flask import Flask, render_template_string
import pandas as pd
import requests
from datetime import datetime
from config import CONFIG

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Bot Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0d1117; color: #e6edf3; font-family: 'Segoe UI', sans-serif; padding: 20px; }
        h1 { color: #58a6ff; margin-bottom: 6px; font-size: 24px; }
        .subtitle { color: #8b949e; font-size: 13px; margin-bottom: 24px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
        .card h3 { color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }
        .card .value { font-size: 24px; font-weight: bold; color: #58a6ff; }
        .card .sub { font-size: 12px; color: #8b949e; margin-top: 4px; }
        .positive { color: #3fb950 !important; }
        .negative { color: #f85149 !important; }
        .section { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 24px; }
        .section h2 { color: #58a6ff; font-size: 16px; margin-bottom: 16px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { color: #8b949e; text-align: left; padding: 8px; border-bottom: 1px solid #30363d; }
        td { padding: 8px; border-bottom: 1px solid #21262d; }
        .buy { color: #3fb950; font-weight: bold; }
        .sell { color: #f85149; font-weight: bold; }
        .coin-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #21262d; }
        .coin-row:last-child { border-bottom: none; }
        .coin-price { font-size: 18px; color: #58a6ff; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .badge-win { background: #0d2b17; color: #3fb950; }
        .badge-loss { background: #2b0d0d; color: #f85149; }
        .badge-open { background: #1c2333; color: #8b949e; }
        .refresh { color: #8b949e; font-size: 12px; margin-top: 16px; }
    </style>
</head>
<body>
    <h1>Crypto Bot Dashboard</h1>
    <p class="subtitle">Paper trading — refreshes every 10 seconds — {{ timestamp }}</p>

    <div class="grid">
        <div class="card">
            <h3>Total Trades</h3>
            <div class="value">{{ total_trades }}</div>
            <div class="sub">{{ buys }} buys / {{ sells }} sells</div>
        </div>
        <div class="card">
            <h3>Completed Pairs</h3>
            <div class="value">{{ total_pairs }}</div>
            <div class="sub">{{ wins }} wins / {{ losses }} losses</div>
        </div>
        <div class="card">
            <h3>Win Rate</h3>
            <div class="value">{{ win_rate }}%</div>
            <div class="sub">of completed pairs</div>
        </div>
        <div class="card">
            <h3>Total P&L</h3>
            <div class="value">${{ total_pnl }}</div>
            <div class="sub">paper trading</div>
        </div>
        <div class="card">
            <h3>Bot Status</h3>
            <div class="value positive">LIVE</div>
            <div class="sub">Watching 3 coins</div>
        </div>
    </div>

    <div class="section">
        <h2>Live Prices</h2>
        {% for coin, price in prices.items() %}
        <div class="coin-row">
            <span style="font-weight:bold">{{ coin }}</span>
            <span class="coin-price">${{ price }}</span>
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Trade History</h2>
        {% if pairs %}
        <table>
            <tr>
                <th>Buy time</th>
                <th>Buy price</th>
                <th>Sell time</th>
                <th>Sell price</th>
                <th>P&L</th>
                <th>Result</th>
            </tr>
            {% for pair in pairs %}
            <tr>
    <td>{{ pair.symbol }}</td>
    <td>{{ pair.buy_time }}</td>
    <td class="buy">${{ pair.buy_price }}</td>
    <td>{{ pair.sell_time }}</td>
    <td class="sell">${{ pair.sell_price }}</td>
    <td>{% if pair.pnl != None %}${{ pair.pnl }}{% else %}—{% endif %}</td>
    <td>
        {% if pair.result == 'WIN' %}<span class="badge badge-win">WIN</span>
        {% elif pair.result == 'LOSS' %}<span class="badge badge-loss">LOSS</span>
        {% else %}<span class="badge badge-open">OPEN</span>{% endif %}
    </td>
</tr>
            {% endfor %}
        </table>
        {% else %}
        <p style="color:#8b949e">No trades yet — bot is running and waiting for grid triggers.</p>
        {% endif %}
    </div>

    <p class="refresh">Auto-refreshing every 10 seconds</p>
</body>
</html>
"""


def get_prices():
    prices = {}
    for symbol in CONFIG["symbols"].keys():
        try:
            response = requests.get(f"https://api.coinbase.com/v2/prices/{symbol}/spot")
            data = response.json()
            price = float(data["data"]["amount"])
            prices[symbol] = f"{price:,.2f}"
        except:
            prices[symbol] = "N/A"
    return prices


def get_trade_pairs():
    try:
        df = pd.read_csv("trades.csv")
        if df.empty:
            return [], 0, 0, 0, 0, 0, 0, "0.00"

        total = len(df)
        all_pairs = []
        wins = 0
        losses = 0
        total_pnl = 0.0

        # Group by coin and match buys to sells per coin
        symbols = df["symbol"].unique() if "symbol" in df.columns else ["UNKNOWN"]
        for symbol in symbols:
            coin_df = df[df["symbol"] == symbol].reset_index(drop=True)
            buys  = coin_df[coin_df["signal"] == "BUY"].reset_index(drop=True)
            sells = coin_df[coin_df["signal"] == "SELL"].reset_index(drop=True)

            min_pairs = min(len(buys), len(sells))
            for i in range(min_pairs):
                buy_price  = float(buys.loc[i, "price"])
                sell_price = float(sells.loc[i, "price"])
                size_usd   = float(buys.loc[i, "size_usd"])
                qty        = size_usd / buy_price
                pnl        = round((sell_price - buy_price) * qty, 4)
                total_pnl += pnl
                result     = "WIN" if pnl >= 0 else "LOSS"
                if pnl >= 0:
                    wins += 1
                else:
                    losses += 1

                all_pairs.append({
                    "symbol":     symbol,
                    "buy_time":   str(buys.loc[i, "timestamp"])[:19],
                    "buy_price":  f"{buy_price:,.2f}",
                    "sell_time":  str(sells.loc[i, "timestamp"])[:19],
                    "sell_price": f"{sell_price:,.2f}",
                    "pnl":        pnl,
                    "result":     result,
                })

            # Open positions
            for i in range(min_pairs, len(buys)):
                all_pairs.append({
                    "symbol":     symbol,
                    "buy_time":   str(buys.loc[i, "timestamp"])[:19],
                    "buy_price":  f"{float(buys.loc[i, 'price']):,.2f}",
                    "sell_time":  "—",
                    "sell_price": "—",
                    "pnl":        None,
                    "result":     "OPEN",
                })

        all_pairs.reverse()
        total_pairs = wins + losses
        win_rate = int(round(wins / total_pairs * 100)) if total_pairs > 0 else 0
        buys_count  = len(df[df["signal"] == "BUY"])
        sells_count = len(df[df["signal"] == "SELL"])

        return all_pairs, total, buys_count, sells_count, wins, losses, win_rate, f"{total_pnl:+.4f}"

    except Exception as e:
        print("Error reading trades:", e)
        return [], 0, 0, 0, 0, 0, 0, "0.00"


@app.route("/")
def index():
    prices = get_prices()
    pairs, total, buys, sells, wins, losses, win_rate, total_pnl = get_trade_pairs()
    return render_template_string(
        TEMPLATE,
        prices=prices,
        pairs=pairs,
        total_trades=total,
        buys=buys,
        sells=sells,
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        total_pnl=total_pnl,
        total_pairs=min(buys, sells),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


if __name__ == "__main__":
    print("Dashboard running at http://localhost:5000")
    app.run(debug=True, port=5000)
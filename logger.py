"""
logger.py — Records every trade and prints a performance summary.
Saves trades to trades.csv so you can analyse them in Excel or Python.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)
CSV_PATH = Path("trades.csv")


class TradeLogger:
    def __init__(self):
        self.trades = []
        # Write CSV header if file doesn't exist
        if not CSV_PATH.exists():
            with open(CSV_PATH, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "mode", "symbol", "signal", "qty", "price", "size_usd"])
                writer.writeheader()

    def record(self, order):
        if not order:
            return
        self.trades.append(order)
        # Append to CSV
        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "mode", "symbol", "signal", "qty", "price", "size_usd"])
            writer.writerow({k: order.get(k, "") for k in writer.fieldnames})

    def summary(self):
        buys  = [t for t in self.trades if t["signal"] == "BUY"]
        sells = [t for t in self.trades if t["signal"] == "SELL"]
        log.info("=== Session summary ===")
        log.info("Total trades: %d  |  Buys: %d  |  Sells: %d",
                 len(self.trades), len(buys), len(sells))
        if self.trades:
            log.info("Trades saved to %s", CSV_PATH.resolve())

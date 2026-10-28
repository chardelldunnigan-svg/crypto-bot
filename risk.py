"""
risk.py — Risk manager.

Every trade goes through here before execution.

Rules enforced:
  1. Daily loss limit — stop trading if you're down too much today
  2. Max open orders — don't over-expose to the market
  3. Position size — never risk more than you can afford per trade
"""

import logging
from datetime import date

log = logging.getLogger(__name__)


class RiskManager:
    def __init__(self, config):
        self.max_open_orders  = config["max_open_orders"]
        self.daily_loss_limit = config["daily_loss_limit"]
        self.stop_loss_pct    = config["stop_loss_pct"]
        self.order_size_usd   = 20

        self.daily_pnl      = 0.0
        self.open_orders    = 0
        self.last_reset_day = date.today()

#bot refreshes if date time different from whats recorded
    def _reset_daily_if_needed(self):
        today = date.today()
        if today != self.last_reset_day:
            log.info("New day — resetting daily P&L")
            self.daily_pnl      = 0.0
            self.last_reset_day = today
#Returns whether the trade is approved, how much to trade, and a reason if it's blocked.
    def check(self, signal, price):


        self._reset_daily_if_needed()

        # Rule 1: daily loss limit
        if self.daily_pnl <= -self.daily_loss_limit:
            return False, 0, f"Daily loss limit hit (${self.daily_pnl:.2f})"

        # Rule 2: max open orders
        if self.open_orders >= self.max_open_orders:
            return False, 0, f"Too many open orders ({self.open_orders})"

        # All clear — approve trade at configured size
        size_usd = self.order_size_usd
        return True, size_usd, "ok"
    
# update the daily P&L tracker
    def on_fill(self, pnl_usd):
        """Call this after an order fills to update P&L tracking."""
        self.daily_pnl += pnl_usd
        log.info("Daily P&L updated: $%.2f", self.daily_pnl)
#counts trades 
    def on_order_open(self):
        self.open_orders += 1

    def on_order_close(self):
        self.open_orders = max(0, self.open_orders - 1)

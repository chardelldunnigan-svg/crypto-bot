"""
strategy.py — brain/ trading strategy
"""


class GridStrategy:
    def __init__(self, config):
        self.spacing = config["grid_spacing"]
        self.levels  = config["grid_levels"]
        self.grid    = {}
        self.anchor  = None

    def _build_grid(self, price):
        self.anchor = price
        self.grid   = {}
        for i in range(1, self.levels + 1):
            buy_level  = round(price * (1 - self.spacing * i), 2)
            sell_level = round(price * (1 + self.spacing * i), 2)
            self.grid[buy_level]  = "BUY"
            self.grid[sell_level] = "SELL"
# Calculates the 200-period moving average trend direction
    def evaluate(self, price, candles):
        # Trend filter — only buy if price is above 200 period moving average
        if len(candles) >= 200:
            ma200 = candles["close"].tail(200).mean()
            in_uptrend = price > ma200
        else:
            in_uptrend = True

        if not self.grid:
            self._build_grid(price)
            return "HOLD"

#Grid stays alive moving with the price. 
#New opposite level gets added on the other side
        for level, signal in list(self.grid.items()):
            if abs(price - level) / level < 0.001:
                del self.grid[level]

                if signal == "BUY":
                    new_level = round(level * (1 + self.spacing), 2)
                    self.grid[new_level] = "SELL"
                else:
                    new_level = round(level * (1 - self.spacing), 2)
                    self.grid[new_level] = "BUY"

                # Block buys during downtrend
                if signal == "BUY" and not in_uptrend:
                    return "HOLD"

                return signal

        return "HOLD"

    def reset(self, price):
        if self.anchor and abs(price - self.anchor) / self.anchor > 0.05:
            self._build_grid(price)
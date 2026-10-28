import time
import hmac
import hashlib
import json
import requests
import logging
from datetime import datetime
from config import CONFIG

log = logging.getLogger(__name__)


def get_headers(method, path, body=""):
    api_key = CONFIG["api_key"]
    api_secret = CONFIG["api_secret"]
    timestamp = str(int(time.time()))
    message = timestamp + method + path + body
    signature = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()
    return {
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json",
    }


class OrderExecutor:
    def __init__(self, config):
        self.paper = config["paper_trade"]
        self.symbol = config.get("symbol", "BTC-USD")  
        self.base_url = "https://api.coinbase.com"
        self.paper_cash = 1000.0
        self.paper_btc = 0.0

    def place(self, signal, size_usd, price):
        qty = round(size_usd / price, 6)
        if self.paper:
            return self._paper_order(signal, qty, price, size_usd)
        else:
            return self._live_order(signal, qty)

    def _paper_order(self, signal, qty, price, size_usd):
        if signal == "BUY":
            if self.paper_cash < size_usd:
                log.warning("Paper: not enough USD (have $%.2f)", self.paper_cash)
                return None
            self.paper_cash -= size_usd
            self.paper_btc += qty
        else:
            if self.paper_btc < qty:
                log.warning("Paper: not enough BTC to sell")
                return None
            self.paper_btc -= qty
            self.paper_cash += size_usd

        order = {
            "mode": "PAPER",
            "symbol": self.symbol,
            "signal": signal,
            "qty": qty,
            "price": price,
            "size_usd": size_usd,
            "timestamp": datetime.utcnow().isoformat(),
            "balance": {"USD": self.paper_cash, "BTC": self.paper_btc},
        }
        log.info("PAPER ORDER: %s %.6f @ $%.4f | Balance: $%.2f USD + %.6f",
                 signal, qty, price, self.paper_cash, self.paper_btc)
        return order

    def _live_order(self, signal, qty):
        path = "/api/v3/brokerage/orders"
        body = json.dumps({
            "client_order_id": str(int(time.time())),
            "product_id": self.symbol,
            "side": signal,
            "order_configuration": {
                "market_market_ioc": {
                    "base_size": str(qty)
                }
            }
        })
        headers = get_headers("POST", path, body)
        response = requests.post(self.base_url + path, headers=headers, data=body)
        order = response.json()
        log.info("LIVE ORDER placed: %s", order)
        return order
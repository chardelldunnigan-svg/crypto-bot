"""
bot.py — Multi-coin grid bot with optimized settings per coin.
Trades BTC, ETH, and SOL simultaneously.
"""

import time
import logging
from config import CONFIG
from data import DataFeed
from strategy import GridStrategy
from risk import RiskManager
from executor import OrderExecutor
from logger import TradeLogger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def run():
    log.info("Starting multi-coin bot — paper mode: %s", CONFIG["paper_trade"])
    log.info("Trading: %s", ", ".join(CONFIG["symbols"].keys()))

    coins = {}
    for symbol, settings in CONFIG["symbols"].items():
        coin_config = CONFIG.copy()
        coin_config["symbol"] = symbol
        coin_config["grid_spacing"] = settings["grid_spacing"]
        coin_config["order_size_usd"] = settings["order_size_usd"]
        coins[symbol] = {
            "feed":     DataFeed(coin_config),
            "strategy": GridStrategy(coin_config),
            "executor": OrderExecutor(coin_config),
        }

    risk   = RiskManager(CONFIG)
    logger = TradeLogger()

    while True:
        try:
            for symbol, components in coins.items():
                try:
                    price, candles = components["feed"].get_market_data()
                    log.info("[%s] Price: %.4f", symbol, price)

                    signal = components["strategy"].evaluate(price, candles)

                    if signal != "HOLD":
                        approved, size, reason = risk.check(signal, price)
                        if approved:
                            order = components["executor"].place(signal, size, price)
                            if order:
                                logger.record(order)
                                log.info("[%s] %s order placed @ %.4f", symbol, signal, price)
                        else:
                            log.info("[%s] Blocked: %s", symbol, reason)
                    else:
                        log.info("[%s] HOLD", symbol)

                except Exception as e:
                    log.error("[%s] Error: %s", symbol, e)

            time.sleep(CONFIG["poll_interval_seconds"])

        except KeyboardInterrupt:
            log.info("Bot stopped.")
            logger.summary()
            break


if __name__ == "__main__":
    run()
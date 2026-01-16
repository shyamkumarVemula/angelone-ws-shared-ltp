import time
import threading
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from core.shared_memory import set_ltp
from config.constants import *

class AngelWebSocket:
    def __init__(self, name, auth, api, client, feed, token_map, token_list):
        self.name = name
        self.token_map = token_map
        self.token_list = token_list

        self.last_tick = time.time()
        self.retry = 0
        self.running = True

        self.ws = SmartWebSocketV2(auth, api, client, feed)
        self.ws.on_data = self.on_data
        self.ws._on_open = self.on_open
        self.ws._on_error = self.on_error
        self.ws._on_close = self.on_close

    # ---------------- WS CALLBACKS ---------------- #

    def on_open(self, ws):
        print(f"🟢 [{self.name}] connected")
        self.retry = 0
        self.subscribe()

    def on_data(self, ws, msg):
        self.last_tick = time.time()
        symbol = self.token_map.get(str(msg.get("token")))
        if symbol:
            ltp = msg.get("last_traded_price")
            if ltp is not None:
                set_ltp(symbol, ltp / 100)

    def on_error(self, ws, err):
        print(f"❌ [{self.name}] error: {err}")

    def on_close(self, ws, code, msg):
        print(f"🔴 [{self.name}] closed (code={code})")

    # ---------------- SUBSCRIBE ---------------- #

    def subscribe(self):
        print(f"🟦 [{self.name}] subscribing tokens")

        for exch in self.token_list:
            tokens = exch["tokens"]

            for i in range(0, len(tokens), MAX_TOKENS_PER_BATCH):
                self.ws.subscribe(
                    "corr",
                    1,
                    [{
                        "exchangeType": exch["exchangeType"],
                        "tokens": tokens[i:i + MAX_TOKENS_PER_BATCH]
                    }]
                )
                time.sleep(1)

    # ---------------- HEARTBEAT ---------------- #

    def heartbeat(self):
        while self.running:
            try:
                self.ws.sendPing()
            except Exception:
                pass
            time.sleep(PING_INTERVAL)

    # ---------------- WATCHDOG (NO RECONNECT HERE) ---------------- #

    def watchdog(self):
        while self.running:
            if time.time() - self.last_tick > WATCHDOG_TIMEOUT:
                print(f"⚠️ [{self.name}] no ticks for {WATCHDOG_TIMEOUT}s")
            time.sleep(10)

    # ---------------- MAIN START (RECONNECT BACKOFF HERE) ---------------- #

    def start(self):
        print(f"🟦 [{self.name}] websocket start loop")

        threading.Thread(target=self.heartbeat, daemon=True).start()
        threading.Thread(target=self.watchdog, daemon=True).start()

        while self.running:
            try:
                print(f"🟦 [{self.name}] connecting websocket")
                self.ws.connect()
                self.retry = 0

                # Block until connection drops
                while self.running:
                    time.sleep(1)

            except Exception as e:
                self.retry += 1
                wait = min(5 * self.retry, 60)

                print(f"❌ [{self.name}] connection error: {e}")
                print(f"🔴 [{self.name}] reconnecting in {wait}s")

                time.sleep(wait)

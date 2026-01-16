from multiprocessing import freeze_support, Process
from core.shared_memory import init_shared_memory, get_latest_prices
import requests

print("🟦 [START_ALL] script loaded")
import os
import json
import time
import requests

INSTRUMENT_FILE = "OpenAPIScripMaster.json"
INSTRUMENT_URL = (
    "https://margincalculator.angelbroking.com/"
    "OpenAPI_File/files/OpenAPIScripMaster.json"
)


def load_instruments():
    # 1️⃣ Try local cache
    if os.path.exists(INSTRUMENT_FILE):
        try:
            print("🟩 [START_ALL] loading instruments from local cache")
            with open(INSTRUMENT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not data or not isinstance(data, list):
                raise ValueError("Invalid instrument file")

            print(f"🟩 [START_ALL] instruments loaded (cached): {len(data)}")
            return data

        except Exception as e:
            print(f"🟥 [START_ALL] cached instrument file invalid: {e}")
            print("🟥 [START_ALL] deleting corrupted cache")
            os.remove(INSTRUMENT_FILE)

    # 2️⃣ Download fresh copy
    print("🟦 [START_ALL] downloading instrument master")

    for attempt in range(1, 4):
        try:
            resp = requests.get(INSTRUMENT_URL, timeout=30)
            resp.raise_for_status()

            data = resp.json()

            if not data or not isinstance(data, list):
                raise ValueError("Downloaded instrument file invalid")

            with open(INSTRUMENT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)

            print(f"🟩 [START_ALL] instruments downloaded: {len(data)}")
            return data

        except Exception as e:
            print(f"🟥 [START_ALL] download failed (attempt {attempt}): {e}")
            time.sleep(3)

    raise RuntimeError("❌ Unable to load instrument master after retries")


def main():
    print("🟦 [START_ALL] main() entered")

    # 1️⃣ Init shared memory
    init_shared_memory()
    print("🟩 [START_ALL] shared memory initialized")

    # 2️⃣ Login
    from core.login import angel_login
    login_ctx = angel_login()
    print("🟩 [START_ALL] angel login done")

    # 3️⃣ Load instruments
    allinst = load_instruments()

    # 3.5 Start Collector (Consumer)
    from collector.collect_ltp import start_collector
    shared_prices = get_latest_prices()
    p_collector = Process(target=start_collector, args=(shared_prices,))
    p_collector.start()
    print("🟦 [START_ALL] collector process started")

    # 4️⃣ Start websocket
    from feeds.ws_nifty import start_nifty
    print("🟦 [START_ALL] starting NIFTY websocket")

    start_nifty(login_ctx, allinst)

    print("🟩 [START_ALL] ws_nifty started")


if __name__ == "__main__":
    freeze_support()
    print("🟦 [START_ALL] __main__ block")
    main()

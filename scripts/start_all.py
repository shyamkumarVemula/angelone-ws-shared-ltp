from multiprocessing import freeze_support, Process
from core.shared_memory import init_shared_memory, get_latest_prices
import requests

print("🟦 [START_ALL] script loaded")
from core.expiry import get_current_nifty_expiry, get_nifty_strikes_for_expiry, find_atm_strike, get_option_symbol
from angel import helper_angel as helper
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

    # 3.1️⃣ Pre-fetch Historical Data (To avoid 14-min wait for RSI)
    print("🟦 [START_ALL] Pre-fetching historical data for indicators...")
    preloaded_history = {}
    
    try:
        # Logic duplicated from ws_nifty to identify symbols
        expiry = get_current_nifty_expiry(allinst)
        if expiry:
            # Get Spot to find ATM
            df_spot = helper.getHistorical("NSE:NIFTY", 1, 1)
            if not df_spot.empty:
                spot = float(df_spot["close"].iloc[-1])
                strikes = get_nifty_strikes_for_expiry(allinst, expiry)
                atm = find_atm_strike(strikes, spot)
                
                # Select strikes (ATM +/- 5)
                idx = strikes.index(atm)
                selected_strikes = strikes[max(0, idx-5): idx+6]
                
                symbols_to_fetch = ["NSE:NIFTY"]
                for strike in selected_strikes:
                    ce, _ = get_option_symbol(allinst, expiry, strike, "CE")
                    pe, _ = get_option_symbol(allinst, expiry, strike, "PE")
                    if ce: symbols_to_fetch.append(ce)
                    if pe: symbols_to_fetch.append(pe)
                
                print(f"🟦 [START_ALL] Fetching history for {len(symbols_to_fetch)} symbols...")
                
                for sym in symbols_to_fetch:
                    # Fetch last 1 day of 1-minute data
                    df = helper.getHistorical(sym, 1, 1)
                    if not df.empty:
                        # Convert last 50 candles to list of dicts
                        records = df.tail(50).reset_index().to_dict('records')
                        preloaded_history[sym] = records
    except Exception as e:
        print(f"⚠️ [START_ALL] Error pre-fetching history: {e}")

    # 3.5 Start Collector (Consumer)
    from collector.collect_ltp import start_collector
    shared_prices = get_latest_prices()
    p_collector = Process(target=start_collector, args=(shared_prices, preloaded_history))
    p_collector.start()
    print("🟦 [START_ALL] collector process started")

    # 4️⃣ Start websocket
    from feeds.ws_nifty import start_nifty
    print("🟦 [START_ALL] starting NIFTY websocket")

    start_nifty(login_ctx, allinst)

    print("🟩 [START_ALL] ws_nifty started")

    # Keep the main process running to maintain SharedMemory Manager
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 [START_ALL] Stopping...")

if __name__ == "__main__":
    freeze_support()
    print("🟦 [START_ALL] __main__ block")
    main()

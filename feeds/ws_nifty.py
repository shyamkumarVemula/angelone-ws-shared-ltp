from core.ws_base import AngelWebSocket
from core.expiry import get_current_nifty_expiry
from core.expiry import find_atm_strike
from core.expiry import get_nifty_strikes_for_expiry
from core.expiry import get_option_symbol
from angel import helper_angel as helper
from core.shared_memory import set_ltp
print("🟦 [WS_NIFTY] module imported")

def start_nifty(session, allinst):
    print(f"🟩 [WS_NIFTY] instruments received: {len(allinst)}")

    # 1️⃣ Get nearest NIFTY expiry from JSON
    expiry = get_current_nifty_expiry(allinst)
    if not expiry:
        print("❌ [WS_NIFTY] No NIFTY expiry found")
        return

    print(f"📅 [WS_NIFTY] Using expiry: {expiry}")

    # 2️⃣ Get spot price safely
    df = helper.getHistorical1("NSE:NIFTY", 1, 1)
    if df is None or df.empty or "close" not in df.columns:
        print("⚠️ [WS_NIFTY] No historical data for NIFTY spot yet")
        return

    spot = float(df["close"].iloc[-1])
    print(f"📈 [WS_NIFTY] NIFTY Spot: {spot}")

    # 3️⃣ Get available strikes from JSON for this expiry
    strikes = get_nifty_strikes_for_expiry(allinst, expiry)
    if not strikes:
        print("❌ [WS_NIFTY] No strikes found for expiry")
        return

    # 4️⃣ Find ATM from available strikes
    atm = find_atm_strike(strikes, spot)
    print(f"🎯 [WS_NIFTY] ATM Strike: {atm}")

    # 5️⃣ Select strikes around ATM (±5)
    idx = strikes.index(atm)
    selected = strikes[max(0, idx-5): idx+6]

    # 6️⃣ Build symbols using JSON (NOT string math)
    symbols = ["NSE:NIFTY"]

    for strike in selected:
        ce, _ = get_option_symbol(allinst, expiry, strike, "CE")
        pe, _ = get_option_symbol(allinst, expiry, strike, "PE")

        if ce:
            symbols.append(ce)
        if pe:
            symbols.append(pe)

    print(f"🟦 [WS_NIFTY] Subscribing symbols: {len(symbols)}")

    # 7️⃣ Build token map
    token_map, raw_tokens = helper.build_tokens(symbols, allinst)

    if not raw_tokens:
        print("❌ [WS_NIFTY] No tokens resolved")
        return

    print(f"🟩 [WS_NIFTY] Tokens resolved: {len(raw_tokens)}")

    # 1. Invert map for WS (Token -> Symbol)
    ws_token_map = {v: k for k, v in token_map.items()}

    # 2. Group tokens by exchange (NSE=1, NFO=2)
    exch_groups = {1: [], 2: []}
    for sym, token in token_map.items():
        if sym.startswith("NSE:"):
            exch_groups[1].append(token)
        elif sym.startswith("NFO:"):
            exch_groups[2].append(token)

    formatted_token_list = [
        {"exchangeType": etype, "tokens": tokens}
        for etype, tokens in exch_groups.items() if tokens
    ]

    # 8️⃣ Start WebSocket
    ws = AngelWebSocket(
        "NIFTY",
        session["auth"],
        session["api"],
        session["client"],
        session["feed"],
        ws_token_map,
        formatted_token_list
    )

    print("🟩 [WS_NIFTY] websocket starting")
    ws.on_tick = on_tick
    ws.start()

def on_tick(symbol, ltp):
    # Update shared memory
    set_ltp(symbol, ltp)
    # print(f"🟨 [WS_NIFTY] tick {symbol} {ltp}")

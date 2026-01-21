import time
import sys
import os
import logging

# Ensure we can import from sibling directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.shared_memory import get_latest_prices
from collector.collect_ltp import StrikeData

def start_strategy(shared_prices=None):
    print("🟦 [STRATEGY] Trading Logic Module started")
    
    # Local state to track candles and indicators for strategy
    symbol_map = {}
    positions = {} # Track open positions: {symbol: {'buy_price': float, 'highest_price': float}}
    
    if shared_prices is None:
        shared_prices = get_latest_prices()
        
    if shared_prices is None:
        print("🟥 [STRATEGY] Shared memory not initialized.")
        return

    # Setup Logging for Signals
    logging.basicConfig(filename='trading_signals.log', level=logging.INFO, format='%(asctime)s %(message)s')
    print("🟩 [STRATEGY] Monitoring markets for signals...")

    while True:
        try:
            snapshot = dict(shared_prices)
            
            if snapshot:
                # Debug print to confirm scanning
                print(f"🔍 [STRATEGY] Scanning {len(snapshot)} symbols...")
                
                for symbol, data in snapshot.items():
                    if isinstance(data, (tuple, list)):
                        ltp, vol = data[0], data[1]
                    else:
                        ltp, vol = data, 0

                    if symbol not in symbol_map:
                        symbol_map[symbol] = StrikeData(symbol)
                    
                    # Update candle data
                    data_obj = symbol_map[symbol]
                    data_obj.process_tick(ltp, vol)
                    
                    # Get Indicators
                    indicators = data_obj.get_indicators()
                    
                    if indicators:
                        check_signals(symbol, ltp, indicators, positions)
            
            time.sleep(0.5) # Fast poll for strategy

        except Exception as e:
            print(f"🟥 [STRATEGY] Error: {e}")
            time.sleep(1)

def check_signals(symbol, ltp, indicators, positions):
    rsi = indicators.get("RSI")
    atr = indicators.get("ATR")
    sma = indicators.get("SMA9", 0)
    vwap = indicators.get("VWAP", 0)    
    macd = indicators.get("MACD", 0)
    signal = indicators.get("Signal", 0)
    bb_lower = indicators.get("BB_Lower", 0)
    bb_upper = indicators.get("BB_Upper", 0)
    
    # --- 1. MANAGE OPEN POSITIONS ---
    if symbol in positions:
        pos = positions[symbol]
        buy_price = pos['buy_price']
        
        # Update Highest Price (for trailing)
        if ltp > pos['highest_price']:
            pos['highest_price'] = ltp
            
        # A) Stop Loss: 40% drop from Buy Price
        stop_loss_price = buy_price * 0.60
        
        # B) Trailing Stop: Activate at +20%, Trail 1 for 1
        trailing_trigger = buy_price * 1.20
        trailing_sl = 0
        
        if pos['highest_price'] >= trailing_trigger:
            # SL starts at Cost (buy_price) when trigger is hit
            # Moves up 1 rupee for every 1 rupee gain in highest_price
            trailing_sl = buy_price + (pos['highest_price'] - trailing_trigger)
        
        # Check Exits
        exit_msg = None
        if ltp <= stop_loss_price:
            exit_msg = f"🛑 [STOP LOSS] {symbol} @ {ltp} (Entry: {buy_price}, -40%)"
        elif trailing_sl > 0 and ltp <= trailing_sl:
            exit_msg = f"💰 [TRAILING EXIT] {symbol} @ {ltp} (High: {pos['highest_price']}, Trailed SL: {trailing_sl})"
            
        if exit_msg:
            print(exit_msg)
            logging.info(exit_msg)
            del positions[symbol]
            
        return # Skip entry logic if we are holding (or just exited)

    # --- 2. ENTRY LOGIC ---
    
    # BUY Condition: RSI Oversold (<30) OR (Price < BB_Lower) AND Price above VWAP
    if (rsi < 30 or (bb_lower > 0 and ltp < bb_lower)) and ltp > vwap:
        msg = f"🚀 [BUY SIGNAL] {symbol} @ {ltp} | RSI:{rsi} BB_Low:{bb_lower} VWAP:{vwap}"
        print(msg)
        logging.info(msg)
        
        # Record Position
        positions[symbol] = {'buy_price': ltp, 'highest_price': ltp}

    # SELL Condition: RSI Overbought (>70) OR Price > BB_Upper
    elif rsi > 70 or (bb_upper > 0 and ltp > bb_upper):
        msg = f"🔻 [SELL SIGNAL] {symbol} @ {ltp} | RSI:{rsi} BB_Up:{bb_upper}"
        print(msg)
        logging.info(msg)
        # place_order(symbol, "SELL", ...)

    # EXIT Condition (Trailing Stop example using ATR)
    # This would require tracking open positions
    # stop_loss = ltp - (2 * atr)

if __name__ == "__main__":
    start_strategy()

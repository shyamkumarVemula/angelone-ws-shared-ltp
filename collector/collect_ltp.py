import time
import datetime
import pandas as pd
import numpy as np
from core.shared_memory import get_latest_prices

class StrikeData:
    def __init__(self, symbol):
        self.symbol = symbol
        self.current_minute_prices = []
        self.last_minute = None
        # Store history of closed candles (Close Price)
        self.history = [] 

    def process_tick(self, ltp):
        now = datetime.datetime.now()
        current_minute = now.minute

        # Initialize last_minute on first run
        if self.last_minute is None:
            self.last_minute = current_minute

        # Check for minute change (Candle Close)
        if current_minute != self.last_minute:
            if self.current_minute_prices:
                # Finalize candle (Close is the last sampled price)
                close_price = self.current_minute_prices[-1]
                self.history.append(close_price)
                
                # Keep history manageable (e.g., last 50 candles)
                if len(self.history) > 50:
                    self.history.pop(0)
                
                # Reset for new minute
                self.current_minute_prices = []
            
            self.last_minute = current_minute

        # Add current tick (Sampled)
        self.current_minute_prices.append(ltp)

    def get_indicators(self):
        if len(self.history) < 14:
            return None
        
        # Convert to Series for calculation
        closes = pd.Series(self.history)
        
        # RSI 14 (Wilder's Smoothing)
        delta = closes.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        rsi = 100 - (100 / (1 + rs))
        
        return {
            "RSI": round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else 0,
            "SMA9": round(closes.rolling(window=9).mean().iloc[-1], 2)
        }

def start_collector(shared_prices=None):
    print("🟦 [COLLECTOR] Module started")
    
    # Local state to track candles for each symbol
    symbol_map = {}

    # 1. Get reference to the shared memory dictionary
    # This works because the Manager is initialized in the parent process (start_all.py)
    if shared_prices is not None:
        latest_prices = shared_prices
    else:
        latest_prices = get_latest_prices()
    
    if latest_prices is None:
        print("🟥 [COLLECTOR] Shared memory not initialized. Ensure start_all.py calls init_shared_memory()")
        return

    print("🟩 [COLLECTOR] Monitoring shared prices...")

    while True:
        try:
            # 2. Access data safely
            # Converting to dict creates a snapshot to avoid locking the shared memory 
            # while you perform heavy indicator calculations.
            snapshot = dict(latest_prices)
            
            if snapshot:
                # Process each symbol in the snapshot
                for symbol, ltp in snapshot.items():
                    if symbol not in symbol_map:
                        symbol_map[symbol] = StrikeData(symbol)
                    
                    # Update state
                    symbol_map[symbol].process_tick(ltp)
                
                # Print sample indicators for the first symbol found (to avoid console spam)
                first_sym = list(snapshot.keys())[0]
                indicators = symbol_map[first_sym].get_indicators()
                
                if indicators:
                    print(f"📊 [COLLECTOR] {first_sym} LTP:{snapshot[first_sym]} | {indicators}")
                else:
                    print(f"📊 [COLLECTOR] Tracking {len(snapshot)} symbols. Building history for {first_sym}...")
            
            time.sleep(1) # Poll every second

        except Exception as e:
            print(f"🟥 [COLLECTOR] Error: {e}")
            time.sleep(1)

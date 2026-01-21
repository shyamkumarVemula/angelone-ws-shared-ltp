import time
import datetime
import pandas as pd
import numpy as np
from core.shared_memory import get_latest_prices
import logging

class StrikeData:
    def __init__(self, symbol):
        self.symbol = symbol
        self.history = []  # List of dicts: {open, high, low, close, volume}
        
        # Current Candle State
        self.open = 0
        self.high = 0
        self.low = 0
        self.close = 0
        self.start_vol = 0
        self.current_vol = 0
        
        self.last_minute = None

    def process_tick(self, ltp, vol=0):
        now = datetime.datetime.now()
        current_minute = now.minute

        # Initialize on first tick
        if self.last_minute is None:
            self.last_minute = current_minute
            self.open = self.high = self.low = self.close = ltp
            self.start_vol = vol
            self.current_vol = vol

        # Check for minute change (Candle Close)
        if current_minute != self.last_minute:
            # Calculate volume for this minute (Cumulative Now - Cumulative Start)
            minute_vol = max(0, self.current_vol - self.start_vol)
            
            candle = {
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume": minute_vol
            }
            self.history.append(candle)
            
            # Keep history manageable
            if len(self.history) > 50:
                self.history.pop(0)
            
            # Reset for new minute
            self.last_minute = current_minute
            self.open = self.high = self.low = self.close = ltp
            self.start_vol = self.current_vol # Start of new candle is end of last
            self.current_vol = vol
        else:
            # Update current candle
            self.high = max(self.high, ltp)
            self.low = min(self.low, ltp)
            self.close = ltp
            self.current_vol = vol

    def get_indicators(self):
        # 1. Create a snapshot including the current forming candle
        # This allows indicators to update every second, not just every minute
        current_candle = {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": max(0, self.current_vol - self.start_vol)
        }
        
        # Combine history + current
        data = self.history + [current_candle]
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        closes = df['close']
        
        # RSI 14 (Wilder's Smoothing)
        delta = closes.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        
        # Wilder's Smoothing (alpha = 1/14)
        ema_up = up.ewm(alpha=1/14, adjust=False, min_periods=1).mean()
        ema_down = down.ewm(alpha=1/14, adjust=False, min_periods=1).mean()
        rs = ema_up / ema_down
        
        rsi = 100 - (100 / (1 + rs))

        # VWAP (Session VWAP based on collected history)
        # VWAP = Sum(Typical Price * Volume) / Sum(Volume)
        if 'volume' in df.columns and df['volume'].sum() > 0:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
            vwap_val = round(vwap.iloc[-1], 2)
        else:
            # Handle Indices or 0 volume data
            vwap_val = 0

        # Dynamic SMA (Use 9 or whatever length is available if < 9)
        sma_window = min(len(closes), 9)
        sma = closes.rolling(window=sma_window).mean()
        
        # --- MACD (12, 26, 9) ---
        exp1 = closes.ewm(span=12, adjust=False).mean()
        exp2 = closes.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        
        # --- Bollinger Bands (20, 2) ---
        sma20 = closes.rolling(window=20).mean()
        std20 = closes.rolling(window=20).std()
        bb_upper = sma20 + (2 * std20)
        bb_lower = sma20 - (2 * std20)
        
        # --- ATR 14 ---
        prev_close = closes.shift(1)
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - prev_close).abs()
        tr3 = (df['low'] - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14, min_periods=1).mean()
        
        # --- ADX 14 ---
        high = df['high']
        low = df['low']
        prev_high = high.shift(1)
        prev_low = low.shift(1)
        
        up_move = high - prev_high
        down_move = prev_low - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        
        plus_dm = pd.Series(plus_dm, index=df.index)
        minus_dm = pd.Series(minus_dm, index=df.index)
        
        tr_smooth = tr.ewm(alpha=1/14, adjust=False, min_periods=1).mean()
        plus_dm_smooth = plus_dm.ewm(alpha=1/14, adjust=False, min_periods=1).mean()
        minus_dm_smooth = minus_dm.ewm(alpha=1/14, adjust=False, min_periods=1).mean()
        
        with np.errstate(divide='ignore', invalid='ignore'):
            plus_di = 100 * (plus_dm_smooth / tr_smooth)
            minus_di = 100 * (minus_dm_smooth / tr_smooth)
            dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))

        # After calculation, fill any NaNs (from 0/0 divisions) with 0
        dx.fillna(0, inplace=True)
        adx = dx.ewm(alpha=1/14, adjust=False, min_periods=1).mean()

        return {
            "RSI": round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else 50.0,
            "SMA9": round(sma.iloc[-1], 2) if not pd.isna(sma.iloc[-1]) else 0,
            "VWAP": vwap_val,
            "MACD": round(macd_line.iloc[-1], 2) if not pd.isna(macd_line.iloc[-1]) else 0,
            "Signal": round(signal_line.iloc[-1], 2) if not pd.isna(signal_line.iloc[-1]) else 0,
            "BB_Upper": round(bb_upper.iloc[-1], 2) if not pd.isna(bb_upper.iloc[-1]) else 0,
            "BB_Lower": round(bb_lower.iloc[-1], 2) if not pd.isna(bb_lower.iloc[-1]) else 0,
            "ATR": round(atr.iloc[-1], 2) if not pd.isna(atr.iloc[-1]) else 0,
            "ADX": round(adx.iloc[-1], 2) if not pd.isna(adx.iloc[-1]) else 0
        }

def start_collector(shared_prices=None, preloaded_history=None):
    print("🟦 [COLLECTOR] Module started")
    
    # Setup logging for data
    logging.basicConfig(filename='collect_ltp_data.log', level=logging.INFO, format='%(asctime)s %(message)s')
    
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
                print(f"📊 [COLLECTOR] Snapshot Size: {len(snapshot)}")
                # Process each symbol in the snapshot
                for symbol, data in snapshot.items():
                    # Unpack tuple (price, vol)
                    if isinstance(data, (tuple, list)):
                        ltp, vol = data[0], data[1]
                    else:
                        ltp, vol = data, 0

                    if symbol not in symbol_map:
                        symbol_map[symbol] = StrikeData(symbol)
                        
                        # Inject preloaded history if available
                        if preloaded_history and symbol in preloaded_history:
                            print(f"📜 [COLLECTOR] Injected {len(preloaded_history[symbol])} hist candles for {symbol}")
                            symbol_map[symbol].history = preloaded_history[symbol]
                    
                    # Update state and get/log indicators
                    data_obj = symbol_map[symbol]
                    data_obj.process_tick(ltp, vol)
                    inds = data_obj.get_indicators()
                    if inds:
                        log_entry = f"{symbol} LTP:{(ltp, vol)} | {inds}"
                        print(f"📊 [COLLECTOR] {log_entry}")
                        logging.info(log_entry)
            
            time.sleep(1) # Poll every second

        except Exception as e:
            print(f"🟥 [COLLECTOR] Error: {e}")
            time.sleep(1)

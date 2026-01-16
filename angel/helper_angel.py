#DISCLAIMER:
#1) This sample code is for learning purposes only.
#2) Always be very careful when dealing with codes in which you can place orders in your account.
#3) The actual results may or may not be similar to backtested results. The historical results do not guarantee any profits or losses in the future.
#4) You are responsible for any losses/profits that occur in your account in case you plan to take trades in your account.
#5) TFU and Aseem Singhal do not take any responsibility of you running these codes on your account and the corresponding profits and losses that might occur.
#6) The running of the code properly is dependent on a lot of factors such as internet, broker, what changes you have made, etc. So it is always better to keep checking the trades as technology error can come anytime.
#7) This is NOT a tip providing service/code.
#8) This is NOT a software. Its a tool that works as per the inputs given by you.
#9) Slippage is dependent on market conditions.
#10) Option trading and automatic API trading are subject to market risks

# from SmartWebsocketv2 import SmartWebSocketV2

from SmartApi import SmartConnect
import datetime
import time
import requests
from datetime import timedelta
from pytz import timezone
import pandas as pd
import pyotp
import traceback
from tenacity import retry, wait_exponential, stop_after_attempt
######PIVOT POINTS##########################
####################__INPUT__#####################
# trading_api_key= '6L9HcEAl'
# hist_api_key = '6L9HcEAl'
# username = 'P792853'
# password = '1317'   #This is 4 digit MPIN
# otp_token = 'NJMJOV5A6NTO7HJ4DTN4UOFFOI'
# allinst = pd.read_json('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json')

trading_api_key= 'dWOPTBqa'
hist_api_key = 'dWOPTBqa'
username = 'S1552849'
password = '9010'   #This is 4 digit MPIN
otp_token = 'FPFMVA27U2ECQYG43NYZAH67HQ'
# allinst = pd.read_json('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json')
# helper_angel.py
import pandas as pd
import os
print("🟦 [HELPER] helper_angel module loaded")

SCRIPT_DIR = os.path.dirname(__file__)
CACHE_FILE = os.path.join(SCRIPT_DIR, "OpenAPIScripMaster.json")

def load_instruments(force_refresh=False):
    """
    Loads Angel instrument master safely.
    Uses local cache if internet is unavailable.
    """
    if os.path.exists(CACHE_FILE) and not force_refresh:
        return pd.read_json(CACHE_FILE)

    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        df = pd.read_json(url)
        df.to_json(CACHE_FILE)
        return df
    except Exception as e:
        if os.path.exists(CACHE_FILE):
            print("⚠️ Using cached instrument file (no internet)")
            return pd.read_json(CACHE_FILE)
        raise RuntimeError("❌ Cannot load instrument master (no internet & no cache)") from e
allinst=load_instruments()
def login_trading():
    global trading_obj
    totp=pyotp.TOTP(otp_token).now()

    trading_obj=SmartConnect(api_key=trading_api_key)
    trading_session=trading_obj.generateSession(username,password,totp)
    print(trading_session)

    if trading_session['message'] == 'SUCCESS':
        trading_refreshToken= trading_session['data']['refreshToken']  #till here
        #trading_authToken = trading_session['data']['jwtToken']
        #trading_feedToken=trading_obj.getfeedToken()
        #print(".........................................")
        #print(trading_feedToken)
        #print("Connection Successful")
    else:
        print(trading_session['message'])

    #SmartWebSocketV2OBJ = SmartWebSocketV2(trading_authToken, trading_api_key, username, trading_feedToken)
hist_obj = None

def init_historical(obj):
    global hist_obj
    hist_obj = obj
    print("🟩 [HELPER] hist_obj initialized")
def build_tokens(symbols, allinst):
    """
    symbols   : list of symbols like ['NSE:NIFTY', 'NFO:BANKNIFTY13JAN2646000CE']
    allinst   : instrument master list (JSON)

    returns:
        token_map  : { 'NSE:NIFTY': '99926000', ... }
        token_list : ['99926000', ...]
    """

    token_map = {}
    token_list = []

    for sym in symbols:
        exch, tsym = sym.split(":")

        found = False
        for inst in allinst:
            if (
                inst.get("exch_seg") == exch
                and inst.get("symbol") == tsym
            ):
                token = inst.get("token")
                token_map[sym] = token
                token_list.append(token)
                found = True
                break

        if not found:
            print(f"⚠️ [HELPER] token not found for {sym}")

    print(f"🟩 [HELPER] tokens built: {len(token_list)}")
    return token_map, token_list

def login_historical():
    global hist_obj
    totp=pyotp.TOTP(otp_token).now()
    hist_obj=SmartConnect(api_key=hist_api_key)
    hist_session=hist_obj.generateSession(username,password,totp)
    print(hist_session)

    if hist_session['message'] == 'SUCCESS':
        hist_refreshToken= hist_session['data']['refreshToken']
        #hist_authToken = hist_session['data']['jwtToken']
        #hist_feedToken=hist_obj.getfeedToken()
        #print(".........................................")
        #print(hist_feedToken)
        #print("Connection Successful")
    else:
        print(hist_session['message'])



def get_tokens(symbols):
    for i in range(len(allinst)):
        if symbols[4:] == "NIFTY":
            return 99926000
        elif symbols[4:] == "BANKNIFTY":
            return 99926009
        elif symbols[4:] == "FINNIFTY":
            return 99926037
        elif allinst['symbol'][i] == symbols[4:] and allinst['exch_seg'][i] == symbols[:3]:
            if allinst['expiry'][i] == "":
                exch = get_exch_type(symbols, 'NO')
            else:
                exch = get_exch_type(symbols, 'YES')
            # print(exch)
            # symbol_token=allinst['token'][i]
            print(allinst['token'][i])
            return allinst['token'][i]


def get_exch_type(symbol, exp):
    if exp == 'NO':
        if symbol[:3] == 'NSE': return 1
        elif symbol[:3] == 'BSE': return 3
    if exp == 'YES':
        if symbol[:3] == 'NFO': return 2
        elif symbol[:3] == 'BSE': return 4
        elif symbol[:3] == 'MCX': return 5
        elif symbol[:3] == 'NCDEX': return 6
        elif symbol[:3] == 'CDS': return 7



def getNiftyExpiryDate():
    nifty_expiry = {
            datetime.datetime(2026, 1, 2).date(): "06JAN26",
            datetime.datetime(2026, 1, 13).date(): "13JAN26",     
            datetime.datetime(2026, 1, 20).date(): "20JAN26",        
            datetime.datetime(2026, 1, 27).date(): "27JAN26",
            datetime.datetime(2026, 2, 3).date(): "03FEB26",
            datetime.datetime(2026, 2, 24).date(): "24FEB26",                        
    }

    today = datetime.datetime.now().date()

    for date_key, value in nifty_expiry.items():
        if today <= date_key:
            print(value)
            return value
            
def getNaturalGasExpiryDate():
    naturalgas_expiry = {
        datetime.datetime(2024, 11, 21).date(): "21NOV24",
        datetime.datetime(2024, 12, 22).date(): "23DEC24",
        datetime.datetime(2026, 1, 24).date(): "24JAN26",  
    }
    today = datetime.datetime.now().date()

    for date_key, value in naturalgas_expiry.items():
        if today <= date_key:
            print(value)
            return value
    
def getBankNiftyExpiryDate():
    banknifty_expiry = {
       datetime.datetime(2024, 12, 4).date(): "04DEC24",
        datetime.datetime(2024, 12, 11).date(): "11DEC24",
        datetime.datetime(2024, 12, 18).date(): "18DEC24",        
        datetime.datetime(2024, 12, 24).date(): "24DEC24",
        datetime.datetime(2026, 1, 28).date(): "28JAN26",
        datetime.datetime(2026, 4, 24).date(): "24APR26",
        datetime.datetime(2026, 5, 29).date(): "29MAY26",         
        datetime.datetime(2026, 6, 26).date(): "26JUN26",    
        datetime.datetime(2026, 7, 31).date(): "31JUL26",          
    }

    today = datetime.datetime.now().date()

    for date_key, value in banknifty_expiry.items():
        if today <= date_key:
            print(value)
            return value

def getFinNiftyExpiryDate():
    finnifty_expiry = {
        datetime.datetime(2024, 12, 31).date(): "31DEC24",
        datetime.datetime(2026, 1, 28).date(): "28JAN26",
    }

    today = datetime.datetime.now().date()

    for date_key, value in finnifty_expiry.items():
        if today <= date_key:
            print(value)
            return value

def get_expiry_date(stock):
    if stock == "BANKNIFTY":
        return getBankNiftyExpiryDate()
    elif stock == "NIFTY":
        return getNiftyExpiryDate()
    elif stock == "FINNIFTY":
        return getFinNiftyExpiryDate()
    return None
def getIndexSpot(stock):
    print(stock)
    if stock == "BANKNIFTY":
        name = "NSE:BANKNIFTY"
    elif stock == "NIFTY":
        name = "NSE:NIFTY"
    elif stock == "FINNIFTY":
        name = "NSE:FINNIFTY"
    elif stock == "MIDCAP":
        name = "NSE:MIDCPNIFTY"
    return name

def getOptionFormat(stock, intExpiry, strike, ce_pe):
    return "NFO:" + str(stock) + str(intExpiry)+str(strike)+str(ce_pe)

def find_strike_price_atm(stock):
    ltp = getLTP(getIndexSpot(stock))
    if stock == "BANKNIFTY":
        return int(round((ltp / 100), 0) * 100)
    elif stock == "MIDCAP":
        return int(round((ltp / 25), 0) * 25)
    elif stock == "NIFTY" or stock == "FINNIFTY":
        return int(round((ltp / 50), 0) * 50)
    return None

def getLTP(instrument):
    url = "http://localhost:4000/ltp?instrument=" + instrument
    try:
        resp = requests.get(url)
    except Exception as e:
        print(e)
    data = resp.json()
    return data

def manualLTP(symbol):
    global hist_obj
    exch = symbol[:3]
    sym = symbol[4:]
    tok = get_tokens(symbol)
    ltp = hist_obj.ltpData(exch, symbol, tok)
    time.sleep(1)
    return (ltp['data']['ltp'])

def placeOrder(inst ,t_type,qty,order_type,price,variety, papertrading=1):
    global trading_obj
    variety = 'NORMAL'
    exch = inst[:3]
    symbol_name = inst[4:]
    if(order_type=="MARKET"):
        price = 0
    #papertrading = 0 #if this is 1, then real trades will be placed
    token = get_tokens(inst)

    try:
        if (papertrading == 1):
            Targetorderparams = {
                "variety": "NORMAL",
                "tradingsymbol": symbol_name,
                "symboltoken": token,
                "transactiontype": t_type,
                "exchange": exch,
                "ordertype": order_type,
                "producttype": "INTRADAY", #
                "duration": "DAY",
                "price": price,
                "squareoff": 0,
                "stoploss": 0,
                "triggerprice": 0,
                "trailingStopLoss": 0,
                "quantity": qty
            }

            print(Targetorderparams)
            orderId = trading_obj.placeOrder(Targetorderparams)
            print("The order id is: {}".format(orderId))
            return orderId
        else:
            return 0
    except Exception as e:
        traceback.print_exc()
        print("Order placement failed: {}".format(e.message))
        
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def getHistorical1(ticker,interval,duration):
    exch = ticker[:3]
    sym = ticker[4:]
    tok = get_tokens(ticker)

    time_intervals = {
        1: "ONE_MINUTE",
        3: "THREE_MINUTE",
        5: "FIVE_MINUTE",
        10: "TEN_MINUTE",
        15: "FIFTEEN_MINUTE",
        30: "THIRTY_MINUTE",
        60: "ONE_HOUR"
    }

    interval_str = time_intervals.get(interval, "Key not found")
    # interval_str = "ONE_MINUTE"

    #find todate
    current_time = datetime.datetime.now()
    previous_minute_time = current_time - timedelta(minutes=1)
    start_date = previous_minute_time - timedelta(days=duration)
    to_date_string = previous_minute_time.strftime("%Y-%m-%d %H:%M")
    start_date_string = start_date.strftime("%Y-%m-%d %H:%M")

    historyparams = {
        "exchange": str(exch),
        #  "tradingsymbol":str(sym),
        "symboltoken": str(tok),
        "interval": interval_str,
        "fromdate": start_date_string,
        "todate": to_date_string
    }
 
    hist_data = hist_obj.getCandleData(historicDataParams= historyparams)
    hist_data = pd.DataFrame(hist_data['data'])
    hist_data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    hist_data['datetime2'] = hist_data['timestamp'].copy()
    hist_data['timestamp'] = pd.to_datetime(hist_data['timestamp'])
    hist_data.set_index('timestamp', inplace=True)
    #finaltimeframe = str(interval)  + "min"
    if interval < 375:
        finaltimeframe = str(interval)  + "min"
    elif interval == 375:
        finaltimeframe = "D"


    # Resample to a specific time frame, for example, 30 minutes
    resampled_df = hist_data.resample(finaltimeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'datetime2': 'first'
    })

    # If you want to fill any missing values with a specific method, you can use fillna
    #resampled_df = resampled_df.fillna(method='ffill')  # Forward fill

    resampled_df = resampled_df.dropna(subset=['open'])
    return (resampled_df)

import datetime
from datetime import timedelta
import pandas as pd

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def getHistorical2(ticker, interval, duration):
    """
    Returns resampled historical candle DataFrame.
    Safe for options (empty / zero candles handled).
    """

    try:
        exch = ticker[:3]
        sym = ticker[4:]
        tok = get_tokens(ticker)

        time_intervals = {
            1: "ONE_MINUTE",
            3: "THREE_MINUTE",
            5: "FIVE_MINUTE",
            10: "TEN_MINUTE",
            15: "FIFTEEN_MINUTE",
            30: "THIRTY_MINUTE",
            60: "ONE_HOUR"
        }

        interval_str = time_intervals.get(interval)
        if not interval_str:
            return pd.DataFrame()

        # -----------------------------
        # Time window
        # -----------------------------
        current_time = datetime.datetime.now()
        previous_minute_time = current_time - timedelta(minutes=1)
        start_date = previous_minute_time - timedelta(days=duration)

        historyparams = {
            "exchange": str(exch),
            "symboltoken": str(tok),
            "interval": interval_str,
            "fromdate": start_date.strftime("%Y-%m-%d %H:%M"),
            "todate": previous_minute_time.strftime("%Y-%m-%d %H:%M")
        }

        # -----------------------------
        # Fetch historical data
        # -----------------------------
        hist_resp = hist_obj.getCandleData(
            historicDataParams=historyparams
        )

        # -----------------------------
        # Defensive checks
        # -----------------------------
        if not hist_resp or "data" not in hist_resp or not hist_resp["data"]:
            return pd.DataFrame()

        hist_data = pd.DataFrame(hist_resp["data"])

        if hist_data.empty or len(hist_data.columns) < 5:
            return pd.DataFrame()

        hist_data.columns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]

        # -----------------------------
        # Time handling
        # -----------------------------
        hist_data["datetime2"] = hist_data["timestamp"]
        hist_data["timestamp"] = pd.to_datetime(hist_data["timestamp"])
        hist_data.set_index("timestamp", inplace=True)

        # -----------------------------
        # Resampling
        # -----------------------------
        if interval < 375:
            finaltimeframe = f"{interval}min"
        else:
            finaltimeframe = "D"

        resampled_df = hist_data.resample(finaltimeframe).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "datetime2": "first"
        })

        resampled_df = resampled_df.dropna(subset=["open"])

        return resampled_df

    except Exception as e:
        print(f"❌ getHistorical failed for {ticker}: {e}")
        return pd.DataFrame()

import datetime
import pandas as pd

import datetime
from datetime import timedelta
import pandas as pd


def getHistorical(ticker, interval, duration):
    """
    Returns 1-minute historical candles as DataFrame.
    Safe for options & Angel API quirks.
    """

    try:
        exch = ticker[:3]
        tok = get_tokens(ticker)

        time_intervals = {
            1: "ONE_MINUTE",
            3: "THREE_MINUTE",
            5: "FIVE_MINUTE",
            10: "TEN_MINUTE",
            15: "FIFTEEN_MINUTE",
            30: "THIRTY_MINUTE",
            60: "ONE_HOUR"
        }

        interval_str = time_intervals.get(interval)
        if not interval_str:
            return pd.DataFrame()

        # -----------------------------
        # Time window (FULL DAY)
        # -----------------------------
        today = datetime.datetime.now().date()
        fromdate = datetime.datetime.combine(today, datetime.time(9, 15))
        todate = datetime.datetime.now()

        historyparams = {
            "exchange": exch,
            "symboltoken": str(tok),
            "interval": interval_str,
            "fromdate": fromdate.strftime("%Y-%m-%d %H:%M"),
            "todate": todate.strftime("%Y-%m-%d %H:%M")
        }

        hist_resp = hist_obj.getCandleData(
            historicDataParams=historyparams
        )

        # -----------------------------
        # Normalize Angel response
        # -----------------------------
        if hist_resp is None:
            return pd.DataFrame()

        if isinstance(hist_resp, dict):
            data = hist_resp.get("data")
        else:
            data = hist_resp

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        if df.empty or df.shape[1] < 5:
            return pd.DataFrame()

        df.columns = ["timestamp", "open", "high", "low", "close", "volume"]

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        if df.index.tz is None:
            df.index = df.index.tz_localize("Asia/Kolkata")
        else:
            df.index = df.index.tz_convert("Asia/Kolkata")

        return df

    except Exception as e:
        print(f"❌ getHistorical TypeError for {ticker}: {e}")
        return pd.DataFrame()


import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


def get_opening_range(symbol, timeframe_minutes):
    df = getHistorical(symbol, interval=1, duration=1)

    if df.empty:
        return None, None

    # df.index is now tz-aware (Asia/Kolkata)
    today = df.index[0].date()

    start = IST.localize(
        datetime.datetime.combine(today, datetime.time(9, 15))
    )
    end = start + datetime.timedelta(minutes=timeframe_minutes)

    opening_df = df[(df.index >= start) & (df.index < end)]

    if opening_df.empty:
        return None, None

    low = opening_df["low"].min()
    high = opening_df["high"].max()
    orb_volume = opening_df["volume"].sum()
    print("orb_volume",orb_volume)
    volume = opening_df["volume"].max()
    print("volume_max",volume)
    volume = opening_df["volume"].min()
    print("volume_min",volume)
    volume = opening_df["volume"].mean()
    print("volume_mean",volume)
    volume = opening_df["volume"].iloc[0]
    print("volume_1",volume)

   

    if high <= low:
        return None, None

    return round(low, 2), round(high, 2)


@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def getHistoricalPrevDayClose(ticker,interval,duration):
    exch = ticker[:3]
    sym = ticker[4:]
    tok = get_tokens(ticker)

    time_intervals = {
        1: "ONE_MINUTE",
        3: "THREE_MINUTE",
        5: "FIVE_MINUTE",
        10: "TEN_MINUTE",
        15: "FIFTEEN_MINUTE",
        30: "THIRTY_MINUTE",
        60: "ONE_HOUR"
    }

    interval_str = time_intervals.get(interval, "Key not found")
    # interval_str = "ONE_MINUTE"

    #find todate
    current_time = datetime.datetime.now()
    previous_minute_time = current_time - timedelta(minutes=1)
    start_date = previous_minute_time - timedelta(days=duration)
    yesterday_date = datetime.datetime.now() - datetime.timedelta(days=1)
    start_time = datetime.datetime.combine(yesterday_date,datetime.time(9,15))
    end_time = datetime.datetime.combine(yesterday_date,datetime.time(15,15))
    
    to_date_string = end_time.strftime("%Y-%m-%d %H:%M")
    start_date_string = start_time.strftime("%Y-%m-%d %H:%M")

    historyparams = {
        "exchange": str(exch),
        #  "tradingsymbol":str(sym),
        "symboltoken": str(tok),
        "interval": interval_str,
        "fromdate": start_date_string,
        "todate": to_date_string
    }
    hist_data = hist_obj.getCandleData(historicDataParams= historyparams)
    hist_data = pd.DataFrame(hist_data['data'])
    hist_data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    hist_data['datetime2'] = hist_data['timestamp'].copy()
    hist_data['timestamp'] = pd.to_datetime(hist_data['timestamp'])
    hist_data.set_index('timestamp', inplace=True)
    #finaltimeframe = str(interval)  + "min"
    if interval < 375:
        finaltimeframe = str(interval)  + "min"
    elif interval == 375:
        finaltimeframe = "D"


    # Resample to a specific time frame, for example, 30 minutes
    resampled_df = hist_data.resample(finaltimeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'datetime2': 'first'
    })

    # If you want to fill any missing values with a specific method, you can use fillna
    #resampled_df = resampled_df.fillna(method='ffill')  # Forward fill

    resampled_df = resampled_df.dropna(subset=['open'])
    return (resampled_df)

def getHistorical_old(ticker,interval,duration):
    exch = ticker[:3]
    sym = ticker[4:]
    tok = get_tokens(ticker)

    time_intervals = {
        1: "ONE_MINUTE",
        3: "THREE_MINUTE",
        5: "FIVE_MINUTE",
        10: "TEN_MINUTE",
        15: "FIFTEEN_MINUTE",
        30: "THIRTY_MINUTE",
        60: "ONE_HOUR"
    }

    interval_str = time_intervals.get(interval, "Key not found")

    #find todate
    current_time = datetime.datetime.now()
    previous_minute_time = current_time - timedelta(minutes=1)
    start_date = previous_minute_time - timedelta(days=duration)
    to_date_string = previous_minute_time.strftime("%Y-%m-%d %H:%M")
    start_date_string = start_date.strftime("%Y-%m-%d %H:%M")

    historyparams = {
        "exchange": str(exch),
        #  "tradingsymbol":str(sym),
        "symboltoken": str(tok),
        "interval": interval_str,
        "fromdate": start_date_string,
        "todate": to_date_string
    }
    hist_data = hist_obj.getCandleData(historicDataParams= historyparams)
    hist_data = pd.DataFrame(hist_data['data'])
    hist_data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return (hist_data)

def getorders():
    orders = hist_obj.tradeBook()
    print(orders)
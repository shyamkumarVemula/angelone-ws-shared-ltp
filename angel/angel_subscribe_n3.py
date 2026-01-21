import datetime
import threading
import time
#from SmartWebsocketv2 import SmartWebSocketV2
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2

import pyotp
import pandas as pd
from flask import Flask, request
# from angel import helper_angel as helper
import helper_angel as helper
#PUT MARKET DATA API
api_key= 'v9Ddf9Kx'
username = 'S1552849'
password = '9010'   #This is 4 digit MPIN
otp_token = 'FPFMVA27U2ECQYG43NYZAH67HQ'
totp=pyotp.TOTP(otp_token).now()


obj=SmartConnect(api_key=api_key)
master=obj
print(master)
session=obj.generateSession(username,password,totp)
print(session)

if session['message'] == 'SUCCESS':
    refreshToken= session['data']['refreshToken']
    authToken = session['data']['jwtToken']
    feedToken=obj.getfeedToken()
    print(".........................................")
    print(feedToken)
    print("Connection Successful")
else:
    print(session['message'])

SmartWebSocketV2OBJ = SmartWebSocketV2(authToken, api_key, username, feedToken)

correlation_id = "dft_test1"
action = 1
mode = 1
# token_list = [
#               {"exchangeType": 5, "tokens": []}
#               ]
token_list = [{"exchangeType": 1, "tokens": []},
              {"exchangeType": 2, "tokens": []},
              {"exchangeType": 3, "tokens": []},
              {"exchangeType": 4, "tokens": []},
              {"exchangeType": 5, "tokens": []},
              {"exchangeType": 7, "tokens": []},
              {"exchangeType": 13, "tokens": []}
              ]
symb_token_map = {}
ltpDict = {}

allinst = pd.read_json('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json')
print(allinst)
allinst.to_csv("angel_master.csv")

intExpiry=helper.getNiftyExpiryDate()
intExpiry_BN=helper.getBankNiftyExpiryDate()
intExpiry_Fin=helper.getFinNiftyExpiryDate()
intExpiry_Naturalgas=helper.getNaturalGasExpiryDate()
strikeList=[]
symbolList = []

#NIFTY
time.sleep(10)
helper.login_historical()
a = helper.getHistorical1("NSE:NIFTY",1,1)
if a.empty:
    print("❌ [ERROR] Could not fetch NIFTY data. Using default LTP.")
    nifty_ltp = 24000 # Fallback to avoid crash
else:
    nifty_ltp = (a['close'].iloc[-1])
print(nifty_ltp)
# b = helper.getHistorical("NSE:BANKNIFTY",1,1)
# banknifty_ltp = (b['close'].iloc[-1])
# print(banknifty_ltp)
# c = helper.getHistorical("NSE:FINNIFTY",1,1)
# finnifty_ltp = (c['close'].iloc[-1])
# print(finnifty_ltp)
# d = helper.getHistorical("MCX:NATURALGAS28JUL25FUT",1,1)
# naturalgas_ltp = (d['close'].iloc[-1])
# print(naturalgas_ltp)

print(nifty_ltp)
# print(banknifty_ltp)
#nifty_ltp = 22000
#banknifty_ltp = 48500

for i in range(-5, 5):
    strike = (int(nifty_ltp / 100) + i) * 100
    strikeList.append(strike)
    strikeList.append(strike+50)

#Add Index
symbolList.append('NSE:NIFTY')

#Add CE
for strike in strikeList:
    ltp_option = "NFO:NIFTY" + str(intExpiry)+str(strike)+"CE"
    symbolList.append(ltp_option)

#Add PE
for strike in strikeList:
    ltp_option = "NFO:NIFTY" + str(intExpiry)+str(strike)+"PE"
    symbolList.append(ltp_option)

# strikeList=[]
# #BANKNIFTY
# for i in range(-5, 5):
#     strike = (int(banknifty_ltp / 100) + i) * 100
#     strikeList.append(strike)

# #Add Index
# symbolList.append('NSE:BANKNIFTY')

# #Add CE
# for strike in strikeList:
#     ltp_option = "NFO:BANKNIFTY" + str(intExpiry_BN)+str(strike)+"CE"
#     symbolList.append(ltp_option)

# #Add PE
# for strike in strikeList:
#     ltp_option = "NFO:BANKNIFTY" + str(intExpiry_BN)+str(strike)+"PE"
#     symbolList.append(ltp_option)

# strikeList=[]
# #FINNifty
# for i in range(-5, 5):
#     strike = (int(finnifty_ltp / 100) + i) * 100
#     strikeList.append(strike)
#     strikeList.append(strike+50)

# #Add Index
# symbolList.append('NSE:FINNIFTY')

# #Add CE
# for strike in strikeList:
#     ltp_option = "NFO:FINNIFTY" + str(intExpiry_Fin)+str(strike)+"CE"
#     symbolList.append(ltp_option)

# #Add PE
# for strike in strikeList:
#     ltp_option = "NFO:FINNIFTY" + str(intExpiry_Fin)+str(strike)+"PE"
#     symbolList.append(ltp_option)

# strikeList=[]
# #FINNifty
# for i in range(-5, 5):
#     strike = (int(naturalgas_ltp / 5) + i) * 5
#     strikeList.append(strike)
#     strikeList.append(strike+5)

    
# #Add Index
# symbolList.append('MCX:NATURALGAS24JUL25FUT')

# #Add CE
# for strike in strikeList:
#     ltp_option = "MCX:NATURALGAS" + str(intExpiry_Naturalgas)+str(strike)+"CE"
#     symbolList.append(ltp_option)

# #Add PE
# for strike in strikeList:
#     ltp_option = "MCX:NATURALGAS" + str(intExpiry_Naturalgas)+str(strike)+"PE"
#     symbolList.append(ltp_option)
# symbolList1 = [
#               'MCX:NATURALGAS24JUL25FUT'
#             ]
symbolList1 =[]
symbolList = symbolList + symbolList1
print("BELOW IS THE COMPLETE INSTRUMENT LIST")
print(symbolList)

df=pd.DataFrame()

print("!! Started getltpDict.py !!")

app = Flask(__name__)

@app.route('/')
def hello_world():
	return 'Hello World'

@app.route('/ltp')
def getLtp():
    global ltpDict
    print(ltpDict)
    ltp = -1
    instrumet = request.args.get('instrument')
    try:
        ltp = ltpDict[instrumet]
    except Exception as e :
        print("EXCEPTION occured while getting ltpDict()")
        print(e)
    return str(ltp)


def get_tokens(symbols):
    for h in range(len(symbols)):
        if symbols[h][4:] == "NIFTY":
            temp_token = 99926000
            exch = 1
            symb_token_map[str(temp_token)] = symbols[h]
            token_list[exch-1]['tokens'].append(temp_token)
        elif symbols[h][4:] == "BANKNIFTY":
            temp_token = 99926009
            exch = 1
            symb_token_map[str(temp_token)] = symbols[h]
            token_list[exch-1]['tokens'].append(temp_token)
        elif symbols[h][4:] == "FINNIFTY":
            temp_token = 99926037
            exch = 1
            symb_token_map[str(temp_token)] = symbols[h]
            token_list[exch-1]['tokens'].append(temp_token)
        else:
            try:
                temp_exp = allinst[(allinst['symbol'] == symbols[h][4:]) & (allinst['exch_seg'] == symbols[h][:3])]['expiry'].iloc[0]
                temp_token = allinst[(allinst['symbol'] == symbols[h][4:]) & (allinst['exch_seg'] == symbols[h][:3])]['token'].iloc[0]
                #print(h,"TEMP EXP: ", temp_exp, "TEMP TOKEN: ", temp_token)
                if temp_exp == "":
                    exch = get_exch_type(symbols[h], 'NO')
                else:
                    exch = get_exch_type(symbols[h], 'YES')

                symb_token_map[str(temp_token)] = symbols[h]
                token_list[exch-1]['tokens'].append(temp_token)
                print(temp_token)
            except IndexError as e:
                print("Skipping", symbols[h])

def get_tokens2(symbols):
    for h in range(len(symbols)):
        for i in range(len(allinst)):
            if allinst['symbol'][i] == symbols[h][4:] and allinst['exch_seg'][i] == symbols[h][:3]:
                if allinst['expiry'][i] == "":
                    exch = get_exch_type(symbols[h], 'NO')
                else:
                    exch = get_exch_type(symbols[h], 'YES')
                # print(exch)
                # symbol_token=allinst['token'][i]
                symb_token_map[str(allinst['token'][i])] = symbols[h]
                token_list[exch-1]['tokens'].append(allinst['token'][i])
                print(allinst['token'][i])

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

def callhi():
    print("Hi"+df)
def connectFeed(SmartWebSocketV2):
    try:
        print("AAAAAA")
        def on_data(ws, msg):
            print("ON DATA")
            try:
                #print("Ticksr: {}".format(msg))
                # tickMessageArray=[]
                # tickMessageArray.append(msg)
                # print(msg['last_traded_price'])
                ltpDict[symb_token_map[str(msg['token'])]] = msg['last_traded_price']/100
                print('Symbol: ', symb_token_map[str(msg['token'])], ',  ', 'Token: ', msg['token'], ',  ', 'LTP: ', msg['last_traded_price']/100)
                # global tokenList
                # tickerDataFrame = pd.DataFrame(tickMessageArray,columns=['token', 'exchange_timestamp', 'last_traded_price'])
                # #tickerDataFrame['exchange_timestamp'] = pd.to_datetime(tickerDataFrame['exchange_timestamp'], unit='ms').dt.tz_localize("Asia/Kolkata")
                # tickerDataFrame['exchange_timestamp']=pd.to_datetime(tickerDataFrame['exchange_timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata').dt.time
                # tickerDataFrame['last_traded_price'] = tickerDataFrame['last_traded_price'] /100
                # print(tickerDataFrame.iloc[-1].tolist())
                # print(str(tokenList[0])[:-2])
                # print(tickerDataFrame['token'][0])
                # print(tickerDataFrame['last_traded_price'])
                # print(tickerDataFrame)
                
                        # sheet[f'c{i+2}'].value = '25489'
                        # print('hello')
                        # print(tickerDataFrame['token'])
            except Exception as e:
                ltpDict[symb_token_map[str(msg['token'])]] = -1
                print(e)
        def on_message(ws, message):
            print("ON MESSAGE")
            print("Ticks1: {}".format(message))

        def on_open(ws):
            print("on open1")
            SmartWebSocketV2.subscribe(correlation_id, mode, token_list)

        def on_error(ws, error):
            print("ON ERROR")
            print(ws, error)

        def on_close(ws):
            print("ON CLOSE")
            print(ws)
    except Exception as e:
        print(e)

    # Assign the callbacks.
    SmartWebSocketV2.on_data = on_data
    SmartWebSocketV2._on_open = on_open
    SmartWebSocketV2._on_message = on_message
    SmartWebSocketV2._on_error = on_error
    SmartWebSocketV2._on_close = on_close
    threading.Thread(target = SmartWebSocketV2.connect).start()
    
def startServer():
    print("Inside startServer()")
    app.run(host='0.0.0.0', port=4000)

print(symbolList)
get_tokens(symbolList)
print(token_list)

# token_list = [{"exchangeType": 5, "tokens": ["255000"]}]
# print(token_list)
# try:
t1 = threading.Thread(target=startServer)
t1.start()
connectFeed(SmartWebSocketV2OBJ)
# except Exception as e:
#     print(e)


while True:
    df.head()
    time.sleep(2)

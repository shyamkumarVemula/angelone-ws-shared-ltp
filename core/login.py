import pyotp
from SmartApi import SmartConnect
from config.credentials import *
from angel import helper_angel as helper
def angel_login():
    otp = pyotp.TOTP(TOTP_SECRET).now()
    obj = SmartConnect(api_key=API_KEY)
    print("🟦 [LOGIN] module imported")
    session = obj.generateSession(CLIENT_CODE, MPIN, otp)
    if session["message"] != "SUCCESS":
        raise Exception("Login failed")
    helper.init_historical(obj)  
   
    print("🟩 [LOGIN] angel login SUCCESS")

    return {
        "auth": session["data"]["jwtToken"],
        "feed": obj.getfeedToken(),
        "api": API_KEY,
        "client": CLIENT_CODE,
        "obj": obj
    }

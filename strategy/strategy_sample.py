from core.shared_memory import get_ltp
import time

while True:
    ce = get_ltp("NFO:NIFTY13JAN2626100CE")
    if ce > 50:
        print("BUY SIGNAL:", ce)
    time.sleep(0.2)

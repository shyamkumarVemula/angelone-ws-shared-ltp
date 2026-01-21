from multiprocessing import Manager

manager = None
latest_prices = None


def init_shared_memory():
    global manager, latest_prices
    print("🟦 [SHARED_MEMORY] init called")

    manager = Manager()
    latest_prices = manager.dict()

    print("🟩 [SHARED_MEMORY] Manager started")
    print("🟩 [SHARED_MEMORY] latest_prices dict created")


def set_ltp(symbol, price, vol=0):
    if latest_prices is None:
        print("🟥 [SHARED_MEMORY] set_ltp called before init")
        return

    latest_prices[symbol] = (price, vol)
    # print(f"🟨 [SHARED_MEMORY] LTP updated {symbol} = {price} Vol={vol}")


def get_latest_prices():
    print("🟨 [SHARED_MEMORY] get_latest_prices called")
    return latest_prices

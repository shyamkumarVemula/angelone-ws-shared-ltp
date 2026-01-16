import websocket

ws = websocket.WebSocket()
ws.connect("wss://smartapisocket.angelbroking.com/smart-stream", timeout=10)
print("CONNECTED")
ws.close()

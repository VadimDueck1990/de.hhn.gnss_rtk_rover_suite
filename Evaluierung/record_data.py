import websocket
import datetime


def on_message(ws, message):
    with open("websocket_gnss_data.txt", "a") as f:
        now = create_timestamp()
        f.write(message + " timestamp: " + now + "\n")

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("Closed websocket connection")

def on_open(ws):
    print("Hello, world!")

def create_timestamp():
    current_time = datetime.datetime.now()
    return current_time.strftime("%H%M%S%f")

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://192.168.43.101/",
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
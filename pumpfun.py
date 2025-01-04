import websocket
import json
from colorama import Fore, Style
import telegram
import threading
import asyncio
import time  # To keep the main thread alive

MIN = 300_000_000
MAX = 400_000_000

TELEGRAM_BOT_TOKEN = "7954689222:AAErBcRaKoYy4x_2UK7HSVIFA7MLuLbqMic"

print("Starting telegram bot...")
bot = telegram.Bot(TELEGRAM_BOT_TOKEN)
id = -1
print("Waiting for a message in the target channel...")

# Async runner for threads
def run_coroutine_threadsafe(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coroutine)
    loop.close()

def on_open(ws):
    print("[*] Connected! Sending subscription request...")
    ws.send(json.dumps({"method": "subscribeNewToken"}))
    print("[*] Sent! Waiting for a response...")

def on_error(ws, error):
    print(Fore.RED + f"\n[!] Error: {error}" + Style.RESET_ALL)

def on_close(ws, close_status_code, close_msg):
    print(f"[*] Connection closed with code {close_status_code}, message: {close_msg}")

def on_message(ws, message):
    data = json.loads(message)
    if "message" in data:
        return
    print(Fore.BLUE + f"[TOKEN] Received a message about token {data['symbol']}!{' ' * 8}\t{data['initialBuy']:,.2f}{' ' * 16}" + Style.RESET_ALL, end="\r", flush=True)

    if MIN <= data["initialBuy"] <= MAX:
        print()
        print(Fore.GREEN + f"[FOUND] Token {data['symbol']} has an initial buy of {data['initialBuy']} ({data['solAmount']:.8f} SOL)!" + Style.RESET_ALL)
        print(Fore.LIGHTGREEN_EX + f"[FOUND] Token {data['symbol']} has a 'mint' value of '{data['mint']}'" + Style.RESET_ALL)
        # Run telegram_send safely in the thread
        threading.Thread(target=run_coroutine_threadsafe, args=(telegram_send(data),)).start()

async def telegram_send(data):
    async with bot:
        global id
        if id == -1:
            updates = await bot.get_updates()
            if updates:
                id = updates[0].message.from_user.id
        await bot.send_message(chat_id=id, text=f"Token {data['symbol']} has an initial buy of {data['initialBuy']} ({data['solAmount']:.8f} SOL)!")
        await bot.send_message(chat_id=id, text=f"Token {data['symbol']} has a 'mint' value of '{data['mint']}'")

def start_websocket():
    ws = websocket.WebSocketApp(
        "wss://pumpportal.fun/api/data",
        on_open=on_open,
        on_error=on_error,
        on_close=on_close,
        on_message=on_message
    )
    ws.run_forever()

async def init_telegram():
    global id
    async with bot:
        updates = await bot.get_updates()
        if updates:
            id = updates[0].message.from_user.id
            print(f"Received message from user {id}!")
        else:
            print("No updates available.")

# Keep the program running
def keep_main_alive():
    while True:
        time.sleep(1)

# Start the websocket in a thread
websocket_thread = threading.Thread(target=start_websocket, daemon=True)
websocket_thread.start()

# Initialize the Telegram bot
print("Started websocket in a separate thread...")

if __name__ == '__main__':
    asyncio.run(init_telegram())  # Initialize Telegram bot
    keep_main_alive()  # Keep the main program alive

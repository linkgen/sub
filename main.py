import requests
import base64
import random
import time
from Crypto.Cipher import AES
from flask import Flask
from threading import Thread
from colorama import Fore, Style, init

# === Initialize colorama for terminal coloring ===
init(autoreset=True)

# === Flask app for Railway keep-alive ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

# === AES Encryption Functions ===
def pad_pkcs5(data):
    pad_len = AES.block_size - (len(data) % AES.block_size)
    return data + bytes([pad_len] * pad_len)

def encrypt_aes_cbc(plain_hex, key_hex, iv_hex):
    key = bytes.fromhex(key_hex)
    iv = bytes.fromhex(iv_hex)
    plaintext = bytes.fromhex(plain_hex)
    padded = pad_pkcs5(plaintext)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode()

# === AES Key & IV (from Frida or reverse analysis) ===
key_hex = "36523641426d346b4e6736264266254655454563372138613d5663744659465a"
iv_hex  = "4633743772637233475174654c454d70"

# === Headers used for all API requests ===
headers = {
    "App-Locale": "en",
    "Authorization": "Sub4Sub 192219dbb53da290fb361a6064a522cc6fef8f2c",
    "Package-Name": "com.tubeforces.get_sub",
    "Apk-Version": "129",
    "Time-Zone": "Asia_Kolkata",
    "Host": "sub.tubeforces.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": "okhttp/3.14.9"
}

# === GET URL pool ===
get_urls = [
    "https://sub.tubeforces.com/api/campaign/v3/campaigns/item/?type=view&auto_play_state=false",
    "https://sub.tubeforces.com/api/campaign/v3/campaigns/item/?type=subscribe&auto_play_state=false",
    "https://sub.tubeforces.com/api/campaign/v3/campaigns/item/?type=like&auto_play_state=false"
]

# === Extract the campaign type from GET URL ===
def extract_type_from_url(url):
    if "subscribe" in url:
        return "subscribe"
    elif "like" in url:
        return "like"
    return "view"

# === Main loop ===
while True:
    try:
        # Shuffle URLs to randomize
        random.shuffle(get_urls)
        campaign_data = None
        campaign_type = None

        # Try each GET URL until a valid campaign is found
        for url in get_urls:
            campaign_type = extract_type_from_url(url)
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                cid = int(data.get("id", 0))
                duration = int(data.get("view_duration", 0))
                timestamp = float(data.get("current_timestamp", 0))
                if cid and duration and timestamp:
                    campaign_data = {"id": cid, "duration": duration, "timestamp": timestamp}
                    break

        # If none were valid
        if not campaign_data:
            print(Fore.RED + "[!] No valid campaign found, retrying...\n")
            time.sleep(2)
            continue

        # Prepare values for encryption
        final_ts = int(campaign_data["timestamp"] + campaign_data["duration"] * 1000)
        plain_text = f'{campaign_data["id"]}::{final_ts}'
        plain_hex = plain_text.encode("ascii").hex()
        token = encrypt_aes_cbc(plain_hex, key_hex, iv_hex)

        # POST request
        post_url = "https://sub.tubeforces.com/api/campaign/v3/campaigns/action/"
        post_data = {
            "action_multiplier": False,
            "auto_play_state": False,
            "campaign": campaign_data["id"],
            "token": token,
            "type": campaign_type
        }

        post_res = requests.post(post_url, headers=headers, json=post_data)

        # Show result
        if post_res.status_code == 201:
            coins = post_res.json().get("user_details", {}).get("coins", "N/A")
            print(
                Fore.GREEN + Style.BRIGHT + f"✅ [{campaign_type.upper()}] ID: {campaign_data['id']}"
                + Fore.YELLOW + f" | Coins: {coins}"
                + Fore.CYAN + f" | Token: {token[:10]}...{token[-6:]}"
            )
        else:
            print(Fore.RED + f"[X] POST failed: {post_res.status_code}\n{post_res.text}")

    except Exception as e:
        print(Fore.RED + f"[!] Error: {e}")

    time.sleep(3)  # Delay between cycles

import requests
import base64
import random
import time
from Crypto.Cipher import AES
from colorama import Fore, Style, init

init(autoreset=True)  # Enables color auto-reset

# ========== Telegram Setup ==========
YOUR_BOT_TOKEN = "8014670303:AAEhi9_ajm8rZvu_LKUmBTMkIZNYnkxypok"
YOUR_CHAT_ID = "7742052478"
last_milestone_sent = [0]  # To track last milestone sent (e.g., 1000, 2000)

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{YOUR_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": YOUR_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(Fore.RED + f"[!] Telegram failed: {response.text}")
    except Exception as e:
        print(Fore.RED + f"[!] Telegram Error: {e}")

# ========== Encryption Helpers ==========
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

# ========== AES Keys ==========
key_hex = "36523641426d346b4e6736264266254655454563372138613d5663744659465a"
iv_hex  = "4633743772637233475174654c454d70"

# ========== Headers ==========
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

# ========== GET Endpoints ==========
get_urls = [
    "https://sub.tubeforces.com/api/campaign/v3/campaigns/item/?type=view&auto_play_state=false",
    "https://sub.tubeforces.com/api/campaign/v3/campaigns/item/?type=view&auto_play_state=false",
    "https://sub.tubeforces.com/api/campaign/v3/campaigns/item/?type=subscribe&auto_play_state=false",
    "https://sub.tubeforces.com/api/campaign/v3/campaigns/item/?type=like&auto_play_state=false"
]

# ========== Detect Type from URL ==========
def extract_type_from_url(url):
    if "type=subscribe" in url:
        return "subscribe"
    elif "type=like" in url:
        return "like"
    else:
        return "view"

# ========== Core Campaign Logic (One Loop) ==========
def run_campaign_loop_once():
    try:
        random.shuffle(get_urls)
        campaign_data = None
        campaign_type = None

        for url in get_urls:
            campaign_type = extract_type_from_url(url)
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                cid = int(data.get("id", 0))
                duration = int(data.get("view_duration", 0))
                timestamp = float(data.get("current_timestamp", 0))
                if cid and duration and timestamp:
                    campaign_data = {"id": cid, "duration": duration, "timestamp": timestamp}
                    break  # found a valid campaign

        if not campaign_data:
            print(Fore.RED + "[!] No valid campaign found, retrying...\n")
            return

        final_ts = int(campaign_data["timestamp"] + campaign_data["duration"] * 1000)
        plain = f'{campaign_data["id"]}::{final_ts}'
        hexed = plain.encode("ascii").hex()
        token = encrypt_aes_cbc(hexed, key_hex, iv_hex)

        # Prepare POST request
        post_url = "https://sub.tubeforces.com/api/campaign/v3/campaigns/action/"
        post_data = {
            "action_multiplier": False,
            "auto_play_state": False,
            "campaign": campaign_data["id"],
            "token": token,
            "type": campaign_type
        }

        post_resp = requests.post(post_url, headers=headers, json=post_data)

        if post_resp.status_code == 201:
            coins = post_resp.json().get("user_details", {}).get("coins", 0)

            # ✅ Send milestone alert if passed new 1000s
            milestone = (coins // 1000) * 1000
if milestone != last_milestone_sent[0]:
    last_milestone_sent[0] = milestone
    send_telegram(f"🎉 Coins just reached *{coins}*! 🪙 New milestone passed ✅")

            print(
                Fore.GREEN + Style.BRIGHT + f"✅ [{campaign_type.upper()}] ID: {campaign_data['id']}"
                + Fore.YELLOW + f" | Coins: {coins}"
                + Fore.CYAN + f" | Token: {token[:12]}...{token[-6:]}"
            )
        else:
            print(Fore.RED + f"[X] POST failed: {post_resp.status_code}\n{post_resp.text}")

    except Exception as e:
        print(Fore.RED + f"[!] Error: {str(e)}")

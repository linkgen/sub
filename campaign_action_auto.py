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
                    break

        if not campaign_data:
            print(Fore.RED + "[!] No valid campaign found, retrying...\n")
            return

        final_ts = int(campaign_data["timestamp"] + campaign_data["duration"] * 1000)
        plain = f'{campaign_data["id"]}::{final_ts}'
        hexed = plain.encode("ascii").hex()
        token = encrypt_aes_cbc(hexed, key_hex, iv_hex)

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
            coins = post_resp.json().get("user_details", {}).get("coins", "N/A")
            print(
                Fore.GREEN + Style.BRIGHT + f"✅ [{campaign_type.upper()}] ID: {campaign_data['id']}"
                + Fore.YELLOW + f" | Coins: {coins}"
                + Fore.CYAN + f" | Token: {token[:12]}...{token[-6:]}"
            )
        else:
            print(Fore.RED + f"[X] POST failed: {post_resp.status_code}\n{post_resp.text}")

    except Exception as e:
        print(Fore.RED + f"[!] Error: {str(e)}")

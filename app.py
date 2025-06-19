from flask import Flask
import threading, time
import campaign_action_auto

app = Flask(__name__)

@app.route("/")
def ping():
    return "🟢 Alive"

def background_loop():
    while True:
        campaign_action_auto.run_campaign_loop_once()
        time.sleep(3)

threading.Thread(target=background_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

from flask import Flask
import threading, time
import campaign_action_auto  # your existing script as module

app = Flask(__name__)

@app.route("/")
def ping():
    return "🟢 OK"

def run_loop():
    while True:
        try:
            campaign_action_auto.run_campaign_loop_once()
        except Exception as e:
            print("Error in loop:", e)
        time.sleep(3)  # interval

threading.Thread(target=run_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

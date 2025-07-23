from flask import Flask, request
import telegram
import threading
import time

# Replace these with your actual values
TOKEN = "8124226038:AAEo8iGZujc7MQiGn2-Uz2w--Y4VH6orkiA"
CHAT_ID = -1002343871318

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

jobcards = {}  # Dictionary to track active jobcards

def send_reminder(vehicle, deadline, grace=3):
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        if vehicle not in jobcards:
            return
        time.sleep(60)  # Check every 1 minute
    for i in range(grace):
        if vehicle not in jobcards:
            return
        bot.send_message(chat_id=CHAT_ID, text=f"⏰ Reminder: Jobcard {vehicle} has exceeded the deadline!")
        time.sleep(3600)  # Wait 1 hour

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if not text.startswith("JC "):
            return "ok"

        parts = text.strip().split()
        if len(parts) < 2:
            return "ok"

        vehicle = parts[1].upper()
        command = parts[2].lower() if len(parts) > 2 else "start"

        if command == "start":
            jobcards[vehicle] = time.time() + 3600  # 1 hour deadline
            bot.send_message(chat_id=chat_id, text=f"✅ Jobcard {vehicle} has been STARTED.")
            threading.Thread(target=send_reminder, args=(vehicle, jobcards[vehicle])).start()

        elif command == "close":
            if vehicle in jobcards:
                del jobcards[vehicle]
                bot.send_message(chat_id=chat_id, text=f"✅ Jobcard {vehicle} has been CLOSED.")
            else:
                bot.send_message(chat_id=chat_id, text=f"⚠️ Jobcard {vehicle} not found.")

        elif command.isdigit():
            extra_minutes = int(command)
            if vehicle in jobcards:
                jobcards[vehicle] += extra_minutes * 60
                bot.send_message(chat_id=chat_id, text=f"🔄 Jobcard {vehicle} extended by {extra_minutes} minutes.")
            else:
                bot.send_message(chat_id=chat_id, text=f"⚠️ Jobcard {vehicle} not found.")

    return "ok"

@app.route("/")
def index():
    return "Bot is running."

if __name__ == "__main__":
    app.run(port=5000)

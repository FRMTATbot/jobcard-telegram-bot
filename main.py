import os
from flask import Flask, request
import telegram
from datetime import datetime, timedelta
import threading

# Set your Bot Token and Group Chat ID
BOT_TOKEN = "8124226038:AAEo8iGZujc7MQiGn2-Uz2w--Y4VH6orkiA"
GROUP_CHAT_ID = -1002343871318

bot = telegram.Bot(token=BOT_TOKEN)
app = Flask(__name__)

# In-memory storage for jobcards
jobcards = {}

def send_reminders(vehicle_number):
    job = jobcards.get(vehicle_number)
    if not job or job["closed"]:
        return

    deadline = job["deadline"]
    now = datetime.now()

    alerts = [
        (deadline - timedelta(minutes=30), f"⏳ 30 mins left for {vehicle_number} deadline."),
        (deadline - timedelta(minutes=15), f"⚠️ 15 mins left for {vehicle_number} deadline."),
        (deadline, f"⛔ Time's up for {vehicle_number}"),
    ]

    for alert_time, message in alerts:
        delay = (alert_time - now).total_seconds()
        if delay > 0:
            threading.Timer(delay, lambda: bot.send_message(chat_id=GROUP_CHAT_ID, text=message)).start()

    # Hourly reminders for 3 hours after deadline
    for i in range(1, 4):
        reminder_time = deadline + timedelta(hours=i)
        delay = (reminder_time - now).total_seconds()
        if delay > 0:
            threading.Timer(delay, lambda: check_and_remind(vehicle_number)).start()

def check_and_remind(vehicle_number):
    if vehicle_number in jobcards and not jobcards[vehicle_number]["closed"]:
        bot.send_message(chat_id=GROUP_CHAT_ID, text=f"🔁 {vehicle_number} still not closed. Follow up needed.")

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    
    if update.message and update.message.chat.id == GROUP_CHAT_ID:
        text = update.message.text.strip()
        parts = text.split()

        if len(parts) >= 2 and parts[0].lower() == "jc":
            vehicle_number = parts[1].upper()

            if len(parts) == 2:
                # Start a new jobcard
                deadline = datetime.now() + timedelta(hours=1)
                jobcards[vehicle_number] = {"start": datetime.now(), "deadline": deadline, "closed": False}
                bot.send_message(chat_id=GROUP_CHAT_ID, text=f"✅ Jobcard {vehicle_number} started. Deadline in 1 hour.")
                send_reminders(vehicle_number)

            elif len(parts) == 3 and parts[2].lower() == "close":
                if vehicle_number in jobcards and not jobcards[vehicle_number]["closed"]:
                    jobcards[vehicle_number]["closed"] = True
                    bot.send_message(chat_id=GROUP_CHAT_ID, text=f"🛑 Jobcard {vehicle_number} closed.")
                else:
                    bot.send_message(chat_id=GROUP_CHAT_ID, text=f"⚠️ Jobcard {vehicle_number} was not active or already closed.")

    return "OK"

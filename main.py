import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from threading import Thread
from datetime import datetime, timedelta

BOT_TOKEN = "8124226038:AAEo8iGZujc7MQiGn2-Uz2w--Y4VH6orkiA"
CHAT_ID = -1002343871318
DEFAULT_TIME_HOURS = 3
GRACE_PERIOD_HOURS = 3

jobcards = {}

logging.basicConfig(level=logging.INFO)

def parse_time(tstr):
    try:
        parts = tstr.split('.')
        hours = int(parts[0])
        minutes = int(float("0." + parts[1]) * 60) if len(parts) > 1 else 0
        return timedelta(hours=hours, minutes=minutes)
    except:
        return timedelta(hours=0)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()
    if len(parts) < 2 or parts[0].lower() != "jc":
        return

    vehicle = parts[1].upper()

    if len(parts) == 2:
        deadline = datetime.now() + timedelta(hours=DEFAULT_TIME_HOURS)
        jobcards[vehicle] = {
            "start": datetime.now(),
            "deadline": deadline,
            "closed": False
        }
        await context.bot.send_message(chat_id=CHAT_ID, text=f"✅ JC for {vehicle} started. Deadline in {DEFAULT_TIME_HOURS} hours.")
    elif parts[2].lower() == "close":
        if vehicle in jobcards:
            jobcards[vehicle]["closed"] = True
            await context.bot.send_message(chat_id=CHAT_ID, text=f"✅ JC for {vehicle} is now closed.")
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ JC for {vehicle} not found.")
    else:
        if vehicle in jobcards:
            extra_time = parse_time(parts[2])
            jobcards[vehicle]["deadline"] += extra_time
            await context.bot.send_message(chat_id=CHAT_ID, text=f"⏱️ Extra {parts[2]} hours added to JC {vehicle}.")
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ JC for {vehicle} not found.")

async def reminder_loop(app):
    while True:
        now = datetime.now()
        for vehicle, data in jobcards.items():
            if data["closed"]:
                continue
            remaining = data["deadline"] - now
            total_limit = data["deadline"] + timedelta(hours=GRACE_PERIOD_HOURS)

            if remaining <= timedelta(minutes=15) and remaining > timedelta(minutes=14):
                await app.bot.send_message(chat_id=CHAT_ID, text=f"🔔 15 minutes left for JC {vehicle}.")
            elif remaining <= timedelta(minutes=30) and remaining > timedelta(minutes=29):
                await app.bot.send_message(chat_id=CHAT_ID, text=f"🔔 30 minutes left for JC {vehicle}.")
            elif remaining <= timedelta(seconds=1) and remaining > timedelta(seconds=-1):
                await app.bot.send_message(chat_id=CHAT_ID, text=f"⛔ Time's up for JC {vehicle}!")
            elif now > total_limit:
                jobcards[vehicle]["closed"] = True
                await app.bot.send_message(chat_id=CHAT_ID, text=f"❌ JC {vehicle} auto-closed after grace period.")

        time.sleep(60)

def start_reminder_thread(app):
    thread = Thread(target=lambda: app.run_async(reminder_loop(app)))
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    start_reminder_thread(app)
    app.run_polling()
